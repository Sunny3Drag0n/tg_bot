import json, os, logging, re, pathlib, subprocess
from typing import Optional
from pytube import YouTube, Stream
from moviepy.editor import VideoFileClip, AudioFileClip

def get_media_info(file_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running ffprobe:", result.stderr)
        return None
    media_info = json.loads(result.stdout)
    return media_info

class MediaContainer:
    def __init__(self, file, stream : Stream):
        self.is_audio = not stream.includes_video_track
        self.is_video = stream.includes_video_track
        self.set_source_file(file)

    def get_source_file(self):
        return os.path.join(self.dir, f"{self.name}{self.ext}")

    def set_source_file(self, file):
        self.dir = pathlib.Path(file).parent
        self.ext = pathlib.Path(file).suffix
        self.name = pathlib.Path(file).stem
        self.filesize_bytes = os.path.getsize(self.get_source_file())
        if self.is_audio:
            self._audio_clip = AudioFileClip(file)
            self.clip = self._audio_clip
        elif self.is_video:
            self._video_clip = VideoFileClip(file)
            self.clip = self._video_clip
        else:
            raise Exception('MediaContainer is not media')

    def split_video_ffmpeg(self, clip_max_duration):
        output_file = os.path.join(self.dir, f"{self.name}_chunk_%03d{self.ext}")
        logging.info(f"[yt_loader:split_video_ffmpeg] segment_time {clip_max_duration}")
        command = f'ffmpeg -i {self.get_source_file()} -c:v copy -c:a copy -segment_time {clip_max_duration} -map 0 -f segment {output_file}'
        subprocess.call(command, shell=True)
        paths = sorted(pathlib.Path(self.dir).glob(f'{self.name}_chunk_*'))
        return list(map(str, paths))

    def split_media_into_chunks(self, chunk_size_mb):
        target_size_bytes = chunk_size_mb * 1024 * 1024
        if self.filesize_bytes < target_size_bytes:
            logging.info(f"[yt_loader:split_media_into_chunks] no need split")
            return [self.get_source_file()]
        
        clip_duration = target_size_bytes * self.clip.duration / self.filesize_bytes
        logging.info(f"[yt_loader:split_media_into_chunks] try split. duration {clip_duration}/{self.clip.duration}")
        ready = False
        while not ready:
            files = media.split_video_ffmpeg(clip_max_duration = clip_duration)
            ready = True
            for file in files:
                size = os.path.getsize(file)
                if size > target_size_bytes:
                    clip_duration /= 1.8
                    ready = False
                    logging.info(f"[yt_loader:split_media_into_chunks] too large chunks. Retry with duration: {clip_duration}")
                    break
        return files


class YtLoader:
    def __init__(self, config_path='configs/yt_loader.json'):
        self.config = self._load_config(config_path)
        self.video_streams : list[Stream] = []
        self.audio_streams : list[Stream] = []
        self.link = None
        self.media : MediaContainer = None

    def _load_config(self, config_path):
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config

    def open_youtube_link(self, link) -> bool:
        self.video_streams.clear()
        self.audio_streams.clear()
        try:
            self._yt = YouTube(link)
            self.link = link
            return True
        except Exception as e:
            print(f"Ошибка при открытии ссылки: {str(e)}")
            return False

    def get_video_streams(self) -> list[Stream]:
        if len(self.video_streams) == 0:
            for stream in self._yt.streams:
                if stream.type == 'video':
                    self.video_streams.append(stream)
                elif stream.type == 'audio':
                    self.audio_streams.append(stream)
        return self.video_streams
    
    def get_audio_streams(self) -> list[Stream]:
        if len(self.audio_streams) == 0:
            for stream in self._yt.streams:
                if stream.type == 'video':
                    self.video_streams.append(stream)
                elif stream.type == 'audio':
                    self.audio_streams.append(stream)
        return self.audio_streams
    
    def download_media(self, video_stream : Optional[Stream] = None, audio_stream : Optional[Stream] = None) -> MediaContainer:
        if not video_stream and not audio_stream:
            return None
        save_path=self.config.get('save_path', '.')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        title=self._yt.title
        title = re.sub(r'[^\w]', ' ', title)
        title=title.replace(' ','_')
        
        audio_media : MediaContainer = None
        
        if audio_stream:
            logging.info(f"[yt_loader:download_media] audio loading")
            audio_path = os.path.join(save_path, f'{title}_{audio_stream.abr}.mp3')
            audio_stream.download(filename=audio_path)
            logging.info(f"[yt_loader:download_media] audio ready. Creating container")
            audio_media=MediaContainer(file=audio_path, stream=audio_stream)
            media=audio_media
            logging.info(f"[yt_loader:download_media] audio container ready")

        if video_stream:
            logging.info(f"[yt_loader:download_media] video loading")
            video_path = os.path.join(save_path, f'{title}_{video_stream.resolution}.{video_stream.subtype}')
            video_stream.download(filename=video_path)
            logging.info(f"[yt_loader:download_media] video ready. Creating container")
            media=MediaContainer(file=video_path, stream=video_stream)
            logging.info(f"[yt_loader:download_media] video container ready")
            if audio_media:
                logging.info(f"[yt_loader:download_media] set_audio")
                # Объединяем видео и аудио с использованием moviepy
                media.clip.set_audio(audio_media.clip)
                result_file=os.path.join(save_path, f'{title}_{video_stream.resolution}_{audio_stream.abr}.{video_stream.subtype}')
                media.clip.write_videofile(result_file)
                logging.info(f"[yt_loader:download_media] write_videofile ok")
                media.set_source_file(file=result_file)
                # Удаляем временные файлы
                audio_media.clip.close()
                os.remove(video_path)
                os.remove(audio_path)
        return media

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    yt = YtLoader()
    if yt.open_youtube_link('https://www.youtube.com/watch?v=5DJ8GVAwpBE'):
        audio = yt.get_audio_streams()
        video = yt.get_video_streams()
        # media = yt.download_media(video_stream=video[3], audio_stream=None)
        media = yt.download_media(video_stream=video[0], audio_stream=audio[4])
        files = media.split_media_into_chunks(chunk_size_mb = 49.9)
        print(f'files: {files}')
