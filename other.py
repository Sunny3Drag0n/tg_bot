
from pytube import YouTube

async def process_video_url(message: types.Message):
    video_url = message.text

    try:
        yt = YouTube(video_url)
        video_title = yt.title
        video_caption = f"Вы хотите скачать видео: <b>{video_title}</b>?"

        markup = InlineKeyboardMarkup(row_width=2)
        download_btn = InlineKeyboardButton("Скачать", callback_data=f"download_{video_url}")
        ignore_btn = InlineKeyboardButton("Проигнорировать", callback_data="ignore")
        markup.add(download_btn, ignore_btn)

        await message.reply(video_caption, reply_markup=markup, parse_mode=types.ParseMode.HTML)

    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")

@router.message(F.text.startswith('download'))
async def process_download_callback(callback_query: types.CallbackQuery):
    video_url = callback_query.data.split('_')[1]

    try:
        yt = YouTube(video_url)
        video = yt.streams.filter(file_extension='mp4', progressive=True).first()
        video.download('downloads/')

        await bot.send_video(callback_query.from_user.id, open(video.file_path, 'rb'), caption=f"Видео '{yt.title}' успешно скачано!")
    except Exception as e:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка при скачивании: {str(e)}")

    await bot.answer_callback_query(callback_query.id, text="")

@router.message(F.text.startswith('ignore'))
async def process_ignore_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id, text="Скачивание видео отменено.")
