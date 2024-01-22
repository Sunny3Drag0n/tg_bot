from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from modules.yt_loader import YtLoader
from keyboards.keyboards_for_questions import get_single_choice_kb

yt = YtLoader()
router = Router()

video_quality_options=None
audio_quality_options=None
video_selected=None
audio_selected=None

@router.message(Command("download"))
async def cmd_download(message: Message):
    video_quality_options = yt.get_video_quality_options()
    video_choices=[]
    for option in video_quality_options:
        video_choices.append(f"{option.quality()}: {option.file_size()}")
        
    await message.answer(
        "Выберите качество видео",
        reply_markup=get_single_choice_kb(choices=video_choices, callback_prefix="video_quality_options")
    )

def options_selected_index(callback: CallbackQuery, prefix):
    text = callback.data
    index=int(text[len(prefix) + 1:])
    return index

@router.callback_query(F.data.startswith("video_quality_options"))
async def video_quality_options_selected(callback: CallbackQuery):
    !!!!!!!!!!!!!!!!
    video_selected=video_quality_options[options_selected_index("video_quality_options")]
    
    audio_quality_options = yt.get_audio_quality_options()
    audio_choices=[]
    for option in audio_quality_options:
        audio_choices.append(f"{option.quality()}: {option.file_size()}")
    
    # await callback.message.answer(
    #     "Выберите качество аудио",
    #     reply_markup=get_single_choice_kb(choices=audio_choices, callback_prefix="audio_quality_options")
    # )


# @router.callback_query(F.data.startswith("audio_quality_options"))
# async def audio_quality_options_selected(callback: CallbackQuery):
#     audio_selected=audio_quality_options[options_selected_index("audio_quality_options")]
    
#     await callback.message.answer(
#         f"selected: {video_selected.quality()} {audio_selected.quality()}"
#     )

@router.message(F.text.lower() == "да")
async def answer_yes(message: Message):
    await message.answer(
        "Это здорово!",
        reply_markup=ReplyKeyboardRemove()
    )

    
def asd():
    return 0
    yt.open_youtube_link(link="https://www.youtube.com/watch?v=JKcBghlT_RE")

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
    