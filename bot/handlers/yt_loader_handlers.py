import logging, asyncio
from re import Match
from typing import Tuple

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keyboards as GUI

from modules.media_loader import StreamLoader, open_link, Stream

router = Router()
cashed_links : dict[str, Tuple[list[Stream], list[Stream]]] = {}

class DownloadState(StatesGroup):
    download_type_selection = State()
    video_stream_selection = State()
    audio_stream_selection = State()

class DownloadProgress:
    def __init__(self, message : Message):
        self._message = message
    
    async def handler(self, value : float):
        await self._message.edit_text(test = f'Скачано: {value}%')

def format_stream_info(stream):
    info = ''
    if stream.includes_video_track:
        info = f'[video:{stream.resolution}]'
    if stream.includes_audio_track:
        info = f'{info}[audio:{stream.abr}]'
    
    return f'{info}[size:{stream.filesize_mb} Mb]'
        
async def select_download(message : Message, state: FSMContext):
    logging.debug(f"[select_download] set_state download_type_selection")
    await state.set_state(DownloadState.download_type_selection)
    
    logging.debug(f"[select_download] get current_state_data")
    current_state_data = await state.get_data()
    link = current_state_data.get('link')
    video_streams, audio_streams = cashed_links[link]
    
    logging.debug(f"[select_download] create message text")
    l = []
    if len(video_streams):
        l.append(["Скачать видео 📼", "yt_loader_select_video"])
    if len(audio_streams):
        l.append(["Скачать аудио 🎶", "yt_loader_select_audio"])
    l.append(["Отмена😕", "yt_loader_pass"])
    
    await message.answer(
            text="Качаем?🙈",
            reply_markup=GUI.inline_callback_keyboards.cmd_inline_btn(l)
        )

async def select_video(message : Message, state: FSMContext) -> bool:
    """Выбираем видеопоток"""
    # Получаем из кэша ссылку и список доступных потоков
    current_state_data = await state.get_data()
    link = current_state_data.get('link')
    video_streams, _ = cashed_links[link]
    
    video_choices=[]
    for stream in video_streams:
        video_choices.append(format_stream_info(stream))

    if len(video_choices) == 0:
        await message.answer("Ошибка! Нет доступа к материалам")
        return False
    else:
        await message.answer(
            "Выберите качество видео",
            reply_markup=GUI.inline_callback_keyboards.get_single_choice_kb(
                choices=video_choices, 
                callback_prefix="yt_loader_video_selected_"
            )
        )
        await state.set_state(DownloadState.video_stream_selection)
        return True

async def select_audio(message : Message, state: FSMContext) -> bool:
    """Выбираем аудиопоток"""
    # Получаем из кэша ссылку и список доступных потоков
    current_state_data = await state.get_data()
    link = current_state_data.get('link')
    _, audio_streams = cashed_links[link]
    
    audio_choices=[]
    for stream in audio_streams:
        audio_choices.append(format_stream_info(stream))

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
            reply_markup=GUI.inline_callback_keyboards.get_single_choice_kb(
                choices=audio_choices, callback_prefix="yt_loader_audio_selected_"
            )
        )
        await state.set_state(DownloadState.audio_stream_selection)
        return True

async def on_download_error(message_string : str,  message : Message):
    await message.answer(
        text="Ууупс.. {message_string} Попробуем снова?😅",
        reply_markup=GUI.inline_callback_keyboards.cmd_inline_btn([
            ["Погнали😎", "yt_loader_download_again"],
            ["Отмена😕", "yt_loader_pass"]
        ])
    )

async def download_media(message : Message, state: FSMContext):
    try:
        current_state_data = await state.get_data()
        video_stream = current_state_data.get('video_stream')
        audio_stream = current_state_data.get('audio_stream')
        is_video = video_stream.includes_video_track if video_stream else False
        
        # Создаю изменяемое сообщение, для обработки процесса загрузки
        msg = await message.answer(
            f"""Ожидание завершения загрузки: 
            видеопоток {video_stream.resolution if video_stream else None}, 
            аудиопоток {audio_stream.abr if audio_stream else None}""", 
        )
        # Создаю объект с обработчиком процесса загрузки и указателем на сообщение
        progress = DownloadProgress(message = msg)
        
        loader_instance = StreamLoader(video_stream, audio_stream)
        await asyncio.create_task(loader_instance.execute())
        await loader_instance.wait(progress.handler)
        
        if loader_instance.done:
            media_group = MediaGroupBuilder()
            for resource in await loader_instance.get_resources():
                if is_video:
                    media_group.add_video(media=FSInputFile(resource))
                else:
                    media_group.add_audio(media=FSInputFile(resource))

            await msg.delete()    
            await message.answer_media_group(
                media=media_group.build()
            )
        else:
            raise Exception('После загрузки: not loader_instance.done')

    except Exception as e:
        logging.error(f"[download_media]: {str(e)}")
        await on_download_error(message_string = f"[download_media]: {str(e)}", message=message)



@router.message(F.text.regexp("^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$").as_("link"))
async def yt_loader_link_message(message: Message, link_match : Match[str], state: FSMContext):
    """Обработчик на youtube ссылку"""
    link = link_match.string
    logging.info(f"[handler yt_loader_link_message]: {link}")
    try:
        # Кеширую для ссылки
        if not link in cashed_links:
            video_streams, audio_streams = open_link(link)
            cashed_links[link] = Tuple[video_streams, audio_streams]
            logging.debug(f"create cash for link: {link}")

        await state.update_data(link = link)
        await select_download(message, state)
        
    except Exception as e:
        await message.answer(str(e))
        await state.clear()

@router.callback_query(F.data.startswith("yt_loader_pass"))
async def yt_loader_pass(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()

@router.callback_query(F.data.startswith("yt_loader_select_video"))
async def yt_loader_select_video(callback: CallbackQuery, state: FSMContext):
    if await select_video(callback.message, state):
        await callback.message.delete()

@router.callback_query(F.data.startswith("yt_loader_select_audio"))
async def yt_loader_select_audio(callback: CallbackQuery, state: FSMContext):
    if await select_audio(callback.message, state):
        await callback.message.delete()
    
@router.callback_query(F.data.startswith("yt_loader_video_selected"))
async def yt_loader_video_selected(callback: CallbackQuery, state: FSMContext):
    option = callback.data
    index=int(option.removeprefix('yt_loader_video_selected_'))
    
    current_state_data = await state.get_data()
    link = current_state_data.get('link')
    video_streams, _ = cashed_links[link]
    
    video_stream = video_streams[index]
    await state.update_data(video_stream=video_stream)
    
    await callback.message.delete()
    if not video_stream.includes_audio_track:
        # Предложить добавить аудиодорожку
        await select_audio(callback.message, state)
    else:
        await download_media(callback.message, state)

@router.callback_query(F.data.startswith("yt_loader_audio_selected"))
async def yt_loader_audio_selected(callback: CallbackQuery, state: FSMContext):
    option = callback.data
    index=int(option.removeprefix('yt_loader_audio_selected_'))
    
    current_state_data = await state.get_data()
    link = current_state_data.get('link')
    _, audio_streams = cashed_links[link]
    
    if index >= len(audio_streams):
        audio_stream = None
    else:
        audio_stream = audio_streams[index]
        
    await state.update_data(audio_stream=audio_stream)
    await callback.message.delete()
    await download_media(callback.message, state)
