import json, os, logging
from typing import Optional
from pytube import YouTube, Stream
from moviepy.editor import VideoFileClip, AudioFileClip

class StreamInfo():
    def __init__(self, stream : Stream):
        self.stream = stream

    def quality(self):
        if self.stream.includes_audio_track:
            return self.stream.abr
        else:
            return self.stream.resolution

    def file_size(self):
        return f"{self.stream.filesize / (1024 * 1024):.2f} MB"

class YtLoader:
    def __init__(self, config_path='configs/yt_loader.json'):
        self.config = self._load_config(config_path)
        self.video_qualities = []
        self.audio_qualities = []

    def _load_config(self, config_path):
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config

    def open_youtube_link(self, link):
        self.video_qualities.clear()
        self.audio_qualities.clear()
        try:
            self._yt = YouTube(link)
            self._yt.check_availability()
            self._streams = self._yt.streams
            for stream in self._streams:
                if stream.includes_audio_track:
                    self.audio_qualities.append(StreamInfo(stream))
                else:
                    self.video_qualities.append(StreamInfo(stream))
            return True
        except Exception as e:
            print(f"Ошибка при открытии ссылки: {str(e)}")
            return False

    def get_video_quality_options(self):
        return self.video_qualities

    def get_audio_quality_options(self):
        return self.audio_qualities

    def download_media(self, video_stream : Optional[StreamInfo] = None, audio_stream : Optional[StreamInfo] = None):
        save_path=self.config.get('save_path', '.')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        title=self._yt.title
        if audio_stream:
            logging.info(f"[yt_loader:download_media] audio loading")
            audio_path = os.path.join(save_path, f'{title}_{audio_stream.quality()}.mp3')
            audio_stream.stream.download(filename=audio_path)
            result_file=audio_path
            logging.info(f"[yt_loader:download_media] audio ready")
        if video_stream:
            logging.info(f"[yt_loader:download_media] video loading")
            video_path = os.path.join(save_path, f'{title}_{video_stream.quality()}.mp4')
            video_stream.stream.download(filename=video_path)
            result_file=video_path
            logging.info(f"[yt_loader:download_media] video ready")
            if audio_stream:
                logging.info(f"[yt_loader:download_media] union clip")
                # Объединяем видео и аудио с использованием moviepy
                video_clip = VideoFileClip(video_path)
                audio_clip = AudioFileClip(audio_path)
                video_clip = video_clip.set_audio(audio_clip)
                result_file=os.path.join(save_path, f'{title}_{video_stream.quality()}_{audio_stream.quality()}.mp4')
                video_clip.write_videofile(result_file)
                # Удаляем временные файлы
                os.remove(video_path)
                os.remove(audio_path)
        if result_file:
            logging.info(f"Файл успешно загружен: {result_file}")
        return result_file


    def split_video(self, video_path):
        max_file_size = 1024 * 1024 * self.config.get('max_file_size', 100)  # Default to 100 MB
        file_size = os.path.getsize(video_path)

        split_files = []
        if file_size <= max_file_size:
            split_files.append(video_path)
            return split_files

        max_chunk_size = 1024 * 1024 * self.config.get('max_chunk_size', 10)  # Default to 10 MB
        num_chunks = file_size // max_chunk_size + (file_size % max_chunk_size > 0)

        with open(video_path, 'rb') as video_file:
            for i in range(num_chunks):
                chunk_data = video_file.read(max_chunk_size)
                chunk_file_path = f"{video_path}_part_{i+1}"
                split_files.append(chunk_file_path)
                with open(chunk_file_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)

        return split_files
