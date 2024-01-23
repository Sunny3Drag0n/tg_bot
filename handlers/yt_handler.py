import logging
import os
from re import Match
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from modules.yt_loader import YtLoader
from keyboards.keyboards_for_questions import get_single_choice_kb

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
        await message.answer("Это ссылка на видео! /download ?")
    else:
        await message.answer("Ты что.. Дурак???\nЭто какая-то неправильная ссылка..")

@router.message(Command("download"))
async def yt_loader_cmd_download(message: Message):
    await message.delete()
    
    selected.video_quality_options = yt.get_video_quality_options()
    video_choices=[]
    for option in selected.video_quality_options:
        video_choices.append(f"{option.quality()}: {option.file_size()}")
    
    if len(video_choices) == 0:
        await message.answer(
            "Ошибка! Нет доступа к материалам"
        )
    else:
        video_choices.append("Без видео")
        await message.answer(
            "Выберите качество видео",
            reply_markup=get_single_choice_kb(choices=video_choices, callback_prefix="video_quality_options")
        )

@router.callback_query(F.data.startswith("video_quality_options"))
async def yt_loader_video_quality_options_selected(callback: CallbackQuery):
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
            reply_markup=get_single_choice_kb(choices=audio_choices, callback_prefix="audio_quality_options")
        )

@router.callback_query(F.data.startswith("audio_quality_options"))
async def yt_loader_audio_quality_options_selected(callback: CallbackQuery):
    selected.set_audio_choice(callback=callback)

    await callback.message.delete()
    
    await callback.message.answer(
        f"Параметры загрузки: видео {selected.video_selected.quality() if selected.video_selected else None}, аудио {selected.audio_selected.quality() if selected.audio_selected else None}"
    )
    file=yt.download_media(video_stream=selected.video_selected, audio_stream=selected.audio_selected)
    # !!!!
    if file:
        root, ext = os.path.split(file)
        media_group = MediaGroupBuilder(caption="Media group caption")
        if "mp3" in ext:
            media_group.add(type="audio", media=FSInputFile(file))
        if "mp4" in ext:
            media_group.add(type="video", media=FSInputFile(file))
        await callback.message.answer_media_group(media=file)



@router.message(F.text.lower() == "да")
async def answer_yes(message: Message):
    pass
    await message.answer(
        "Это здорово!",
        reply_markup=ReplyKeyboardRemove()
    )

    
def asd():
    return 0

    video_quality_options = yt.get_video_quality_options()
    audio_quality_options = yt.get_audio_quality_options()

    print("\nДоступные варианты качества видео:")
    for index, option in enumerate(video_quality_options):
        print(f"[{index}] {option.quality()}: {option.file_size()}")
        
    selected_video_index = int(input("Введите индекс желаемого качества видео: "))
    if 0 <= selected_video_index < len(video_quality_options):
        video_stream=video_quality_options[selected_video_index]
    else:
        video_stream=None

    print("\nДоступные варианты качества аудио:")
    for index, option in enumerate(audio_quality_options):
        print(f"[{index}] {option.quality()}: {option.file_size()}")

    selected_audio_index = int(input("Введите индекс желаемого качества аудио: "))
    if 0 <= selected_audio_index < len(audio_quality_options):
        audio_stream=audio_quality_options[selected_audio_index]
    else:
        audio_stream=None

    print(f"\nВыбран: video {video_stream.quality()}, audio {audio_stream.quality()}")
    result=yt.download_media(video_stream=video_stream, audio_stream=audio_stream)
    print(result)
    