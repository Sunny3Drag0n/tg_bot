import logging, pathlib
from re import Match
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from modules.yt_loader import YtLoader
import keyboards as GUI

router = Router()
yt_loaders : dict[int, YtLoader] = {}

class DownloadState(StatesGroup):
    download_type_selection = State()
    video_stream_selection = State()
    audio_stream_selection = State()

def get_info(stream):
    info = ''
    if stream.includes_video_track:
        info = f'[video:{stream.resolution}]'
    if stream.includes_audio_track:
        info = f'{info}[audio:{stream.abr}]'
    
    return f'{info}[size:{stream.filesize_mb} Mb]'
        
async def select_download(message : Message, state: FSMContext):
    await state.set_state(DownloadState.download_type_selection)
    await message.answer(
            text="Качаем?🙈",
            reply_markup=GUI.inline_callback_keyboards.cmd_inline_btn([
                ["Скачать видео 📼", "yt_loader_download_video"],
                ["Скачать аудио 🎶", "yt_loader_download_audio"],
                ["Отмена😕", "yt_loader_pass"]
            ])
        )

async def select_video(message : Message, state: FSMContext) -> bool:
    # Выбираем видеопоток
    yt = yt_loaders[message.chat.id]
    video_choices=[]
    for stream in yt.get_video_streams():
        video_choices.append(get_info(stream))

    if len(video_choices) == 0:
        await message.answer("Ошибка! Нет доступа к материалам")
        return False
    else:
        await message.answer(
            "Выберите качество видео",
            reply_markup=GUI.inline_callback_keyboards.get_single_choice_kb(choices=video_choices, callback_prefix="yt_loader_video_selection_")
        )
        await state.set_state(DownloadState.video_stream_selection)
        return True

async def select_audio(message : Message, state: FSMContext) -> bool:
    # Выбираем аудиопоток
    yt = yt_loaders[message.chat.id]
    audio_choices=[]
    for stream in yt.get_audio_streams():
        audio_choices.append(get_info(stream))

    if len(audio_choices) == 0:
        await message.answer("Ошибка! Нет доступа к материалам")
        return False
    else:
        current_state_data = await state.get_data()
        video_selected = current_state_data.get('video_stream')
        if video_selected:
            audio_choices.append("Без звука")
        await message.answer(
            "Выберите качество аудио",
            reply_markup=GUI.inline_callback_keyboards.get_single_choice_kb(choices=audio_choices, callback_prefix="yt_loader_audio_selection_")
        )
        await state.set_state(DownloadState.audio_stream_selection)
        return True

async def on_download_error(message : Message):
    await message.answer(
        text="Ууупс.. Попробуем снова?😅",
        reply_markup=GUI.inline_callback_keyboards.cmd_inline_btn([
            ["Погнали😎", "yt_loader_download_again"],
            ["Отмена😕", "yt_loader_pass"]
        ])
    )

async def download_media(message : Message, state: FSMContext):
    try:
        yt : YtLoader = yt_loaders[message.chat.id]
        current_state_data = await state.get_data()
        video_stream = current_state_data.get('video_stream')
        audio_stream = current_state_data.get('audio_stream')
        msg = await message.answer(
            f"Ожидание завершения загрузки: видеопоток {video_stream.resolution if video_stream else None}, аудиопоток {audio_stream.abr if audio_stream else None}", 
        )
        media_container = yt.download_media(video_stream=video_stream, audio_stream=audio_stream)
        if media_container:
            resources = media_container.split_media_into_chunks(chunk_size_mb=49)
            for chunk in resources:
                media_group = MediaGroupBuilder()
                if media_container.is_audio:
                    media_group.add_audio(media=FSInputFile(chunk))
                if media_container.is_video:
                    media_group.add_video(media=FSInputFile(chunk))
                await message.answer_media_group(
                    media=media_group.build()
                )
            await msg.delete()
        else:
            await on_download_error(message=message)
    except Exception as e:
        logging.error(f"Ошибка при загрузке медиа: {str(e)}")
        await on_download_error(message=message)

@router.message(F.text.regexp("^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$").as_("link"))
async def yt_loader_link_message(message: Message, link : Match[str], state: FSMContext):
    yt = yt_loaders.get(message.chat.id)
    if yt and yt.link == link.string:
        logging.info(f"[handler yt_loader_link_message]: {link.string} already opened")
        await state.update_data(link = link.string)
        await select_download(message, state)
    else:
        yt_loaders[message.chat.id] = YtLoader()
        yt = yt_loaders.get(message.chat.id)
        logging.info(f"[handler yt_loader_link_message]: {link.string}")
        if yt.open_youtube_link(link.string):
            await state.update_data(link = link)
            await select_download(message, state)
        else:
            await message.answer("Неправильная ссылка..😕")
            await state.clear()

@router.callback_query(F.data.startswith("yt_loader_pass"))
async def yt_loader_pass(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()

@router.callback_query(F.data.startswith("yt_loader_download_video"))
async def yt_loader_download_video(callback: CallbackQuery, state: FSMContext):
    if await select_video(callback.message, state):
        await callback.message.delete()

@router.callback_query(F.data.startswith("yt_loader_download_audio"))
async def yt_loader_download_audio(callback: CallbackQuery, state: FSMContext):
    if await select_audio(callback.message, state):
        await callback.message.delete()
    
@router.callback_query(F.data.startswith("yt_loader_video_selection"))
async def yt_loader_video_selected(callback: CallbackQuery, state: FSMContext):
    option = callback.data
    index=int(option.removeprefix('yt_loader_video_selection_'))
    yt : YtLoader = yt_loaders[callback.message.chat.id]
    video_stream = yt.get_video_streams()[index]
    await state.update_data(video_stream=video_stream)
    await callback.message.delete()
    if not video_stream.includes_audio_track:
        # Предложить добавить аудиодорожку
        await select_audio(callback.message, state)
    else:
        await download_media(callback.message, state)

@router.callback_query(F.data.startswith("yt_loader_audio_selection"))
async def yt_loader_audio_selected(callback: CallbackQuery, state: FSMContext):
    option = callback.data
    index=int(option.removeprefix('yt_loader_audio_selection_'))
    yt : YtLoader = yt_loaders[callback.message.chat.id]
    streams = yt.get_audio_streams()
    if index >= len(streams):
        audio_stream = None
    else:
        audio_stream = streams[index]
    await state.update_data(audio_stream=audio_stream)
    await callback.message.delete()
    await download_media(callback.message, state)

@router.callback_query(F.data.startswith("yt_loader_download_again"))
async def yt_loader_audio_selected(callback: CallbackQuery, state: FSMContext):
    pass
    await callback.message.delete()
    await state.clear()
    await select_download(callback.message, state)

# надо с выбором что грузить