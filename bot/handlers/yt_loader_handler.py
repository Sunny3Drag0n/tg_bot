import logging, os
from re import Match
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from modules.yt_loader import YtLoader
import keyboards as GUI

class Selected:
    def __init__(self):
        pass

    def options_selected_index(self, callback: CallbackQuery, prefix):
        text = callback.data
        index=int(text[len(prefix) + 1:])
        return index

    def set_video_choice(self, callback: CallbackQuery):
        index=self.options_selected_index(callback=callback, prefix="video_quality_options")
        if index >= len(self.video_quality_options):
            self.video_selected=None
        else:
            self.video_selected=self.video_quality_options[index]

    def set_audio_choice(self, callback: CallbackQuery):
        index=self.options_selected_index(callback=callback, prefix="audio_quality_options")
        if index >= len(self.audio_quality_options):
            self.audio_selected=None
        else:
            self.audio_selected=self.audio_quality_options[index]

yt = YtLoader()
router = Router()
selected = Selected()

@router.message(F.text.regexp("^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$").as_("link"))
async def yt_loader_link_message(message: Message, link : Match[str]):
    logging.info(f"handler yt_link_message: {link.string}")
    if yt.open_youtube_link(link.string):
        await message.answer(
            text="Качаем?🙈",
            reply_markup=GUI.inline_callback_keyboards.cmd_inline_btn([["Погнали😎", "yt_loader_download"], ["Отмена😕", "yt_loader_pass"]])
        )
    else:
        await message.answer("Ты что..🤬 Дурак???\nЭто какая-то неправильная ссылка..")

@router.callback_query(F.data.startswith("yt_loader_pass"))
async def yt_loader_cmd_pass(callback: CallbackQuery):
    # Заглушка
    await callback.message.delete()

@router.callback_query(F.data.startswith("yt_loader_download"))
async def yt_loader_cmd_download(callback: CallbackQuery):
    # Обработчик callback`а для скачивания файла по переданной выше ссылке 
    await callback.message.delete()

    selected.video_quality_options = yt.get_video_quality_options()
    video_choices=[]
    for option in selected.video_quality_options:
        video_choices.append(f"{option.quality()}: {option.file_size()}")

    if len(video_choices) == 0:
        await callback.message.answer(
            "Ошибка! Нет доступа к материалам"
        )
    else:
        video_choices.append("Без видео")
        await callback.message.answer(
            "Выберите качество видео",
            reply_markup=GUI.inline_callback_keyboards.get_single_choice_kb(choices=video_choices, callback_prefix="video_quality_options")
        )

@router.callback_query(F.data.startswith("video_quality_options"))
async def yt_loader_video_quality_options_selected(callback: CallbackQuery):
    # Обработчик выбора видео. Продолжаем выбор качества для аудио
    selected.set_video_choice(callback=callback)

    await callback.message.delete()

    selected.audio_quality_options = yt.get_audio_quality_options()
    audio_choices=[]
    for option in selected.audio_quality_options:
        audio_choices.append(f"{option.quality()}: {option.file_size()}")

    if len(audio_choices) == 0:
        await callback.message.answer(
            "Ошибка! Нет доступа к материалам"
        )
    else:
        audio_choices.append("Без звука")
        await callback.message.answer(
            "Выберите качество аудио",
            reply_markup=GUI.inline_callback_keyboards.get_single_choice_kb(choices=audio_choices, callback_prefix="audio_quality_options")
        )

@router.callback_query(F.data.startswith("audio_quality_options"))
async def yt_loader_audio_quality_options_selected(callback: CallbackQuery):
    # Обработчик выбора аудио. После выбора начинается загрузка файла выбранного качества
    selected.set_audio_choice(callback=callback)

    await callback.message.delete()
    msg = await callback.message.answer(
        f"Ожидание завершения загрузки: видео {selected.video_selected.quality() if selected.video_selected else None}, аудио {selected.audio_selected.quality() if selected.audio_selected else None}", 
    )
    try:
        file=yt.download_media(video_stream=selected.video_selected, audio_stream=selected.audio_selected)
        if file:
            _, ext = os.path.split(file)
            media_group = MediaGroupBuilder()
            if "mp3" in ext:
                media_group.add_audio(media=FSInputFile(file))
            if "mp4" in ext:
                media_group.add_video(media=FSInputFile(file))
            await callback.message.answer_media_group(
                media=media_group.build()
            )
            try:
                await msg.delete()
            except Exception as e:
                logging.error(f"Ошибка при попытке удалить сообщение {msg.message_id}: {str(e)}")
            return
    except Exception as e:
        logging.error(f"Ошибка при загрузке медиа: {str(e)}")

    try:
        await msg.delete()
    except Exception as e:
        logging.error(f"Ошибка при попытке удалить сообщение {msg.message_id}: {str(e)}")
    await callback.message.answer(
        text="Ууупс.. Попробуем снова?😅",
        reply_markup=GUI.inline_callback_keyboards.cmd_inline_btn([["Погнали😎", "yt_loader_download"], ["Отмена😕", "yt_loader_pass"]])
    )
