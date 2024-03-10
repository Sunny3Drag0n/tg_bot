import json, os, logging, re, pathlib, subprocess
from typing import Optional, Tuple
from pytube import YouTube, Stream
from moviepy.editor import VideoFileClip, AudioFileClip
from datetime import datetime
import asyncio

def get_media_info(file_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running ffprobe:", result.stderr)
        return None
    media_info = json.loads(result.stdout)
    return media_info

def get_result_name_ext(video_stream : Optional[Stream] = None, audio_stream : Optional[Stream] = None) -> Tuple[str, str, str]:
    src_title = ""
    video_reso = ""
    audio_reso = ""
    ext = ""

    if video_stream:
        src_title = video_stream.title
        video_reso = video_stream.resolution
        ext = video_stream.subtype
        
    if audio_stream:
        audio_reso = audio_stream.abr
        if not video_stream:
            src_title = audio_stream.title
            ext = audio_stream.subtype
    
    title = re.sub(r'[^\w]', ' ', src_title)
    title = title.replace(' ','_')
    reso = f'{video_reso}_{audio_reso}'if video_reso and audio_reso else f'{video_reso}{audio_reso}'
    
    return f'{title}_{reso}', ext, src_title

class DownloadResult:
    def __init__(self, src_title : str, filetype : str, chunks : list[str]):
        self.src_title = src_title
        self.chunks = chunks
        self.filetype = filetype
            
    def print(self):
        print(f'Downloaded {self.filetype}: {self.src_title}')
        for file in self.chunks:
            print(f'    - {file}')
        print('')

class DownloadInfo:
    progress_pattern = re.compile(r'size=\s*([^\s]+)\s+time=(\d+:\d+:\d+\.\d+)\s+bitrate=\s*([^\s]+)\s+speed=\s*([^\s]+)')
    duration_pattern = re.compile(r'Duration: (\d+:\d+:\d+\.\d+)')
    
    def __init__(self, src_title, filetype):
        self.lock = asyncio.Lock()
        self.duration = '00:00:00.00'
        self.time = '00:00:00.00'
        self.percentage : float = 0.0
        self.src_title = src_title
        self.filetype = filetype
        
    async def _update_progress(self):
        duration = datetime.strptime(self.duration, "%H:%M:%S.%f") - datetime.strptime('00:00:00.00', "%H:%M:%S.%f")
        elapsed = datetime.strptime(self.time, "%H:%M:%S.%f") - datetime.strptime('00:00:00.00', "%H:%M:%S.%f")
        self.percentage = (elapsed.total_seconds() / duration.total_seconds()) * 100 if duration.total_seconds() > 0 else 0
        
    async def parse_info(self, log_line : str):
        duration_match = re.match(DownloadInfo.duration_pattern, log_line.strip())
        progress_match = re.match(DownloadInfo.progress_pattern, log_line.strip())
        if duration_match or progress_match:
            async with self.lock:
                if duration_match:
                        self.duration = duration_match.group(1)
                if progress_match:
                        self.time = progress_match.group(2)
                await self._update_progress()

    async def get_progress(self):
        async with self.lock:
            return self.percentage

class Downloader:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.info : DownloadInfo = None
        self.result : DownloadResult = None

    async def _create_chunks(self, source_file1 : str, result_file_name : str, ext : str, source_file2='', segment_len=600, result_dir='./downloads'):
        if len(source_file2):
            source_file2=f' -i \"{source_file2}\"'
        command = f'ffmpeg -i \"{source_file1}\"{source_file2} -c:v copy -c:a copy -progress pipe:2 -f segment -segment_time {segment_len} -reset_timestamps 1 \"{result_dir}/{result_file_name}_segment_%03d.{ext}\"'
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            async with self.lock:
                await self.info.parse_info(line.decode())
        
        await process.wait()
        if process.returncode != 0:
            raise Exception(f"Ошибка при выполнении команды: {command}. Код возврата: {process.returncode}")
        
        paths = sorted(pathlib.Path(result_dir).glob(f'{result_file_name}_segment_*{ext}'))
        async with self.lock:
            self.result = DownloadResult(src_title = self.info.src_title, filetype = self.info.filetype, chunks = list(map(str, paths)))

    async def download(self, video_stream : Optional[Stream] = None, audio_stream : Optional[Stream] = None, result_dir = './downloads'):
        file=""
        second_file=""
        if video_stream:
            file=video_stream.url
            filetype = "video"
            
        if audio_stream:
            if video_stream:
                second_file=audio_stream.url
            else:
                file=audio_stream.url
                filetype = "audio"
                
        if not file:
            raise Exception("download: empty source")
        
        result_name, ext, src_title = get_result_name_ext(video_stream, audio_stream)
        async with self.lock:
            self.info = DownloadInfo(src_title = src_title, filetype = filetype)
            
        await self._create_chunks(source_file1 = file, source_file2 = second_file, result_file_name = result_name, ext = ext, result_dir = result_dir)

    async def has_info(self):
        async with self.lock:
            return bool(self.info)
        
    async def has_result(self):
        async with self.lock:
            return bool(self.result)

# async def split_file(file : str, src_title : str, filetype : str, segment_len=600):
#     pfile = pathlib.Path(file)
    
#     result_dir = pfile.parent
#     ext = pfile.suffix
#     name = pfile.stem
#     downloader = DownloadExecutor(src_title = src_title, filetype = filetype)
#     await downloader._create_chunks(file=file, segment_len = segment_len, result_dir = result_dir, file_name=name, ext=ext)
#     return downloader

class MediaContainer:
    def __init__(self, file, stream : Stream):
        self.is_audio = not stream.includes_video_track
        self.is_video = stream.includes_video_track
        self.set_source_file(file)
        
    def close(self):
        self.clip.close()


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

    def split_video_ffmpeg(self, clip_max_duration) -> list[str]:
        output_file = os.path.join(self.dir, f"{self.name}_chunk_%03d{self.ext}")
        logging.info(f"[yt_loader:split_video_ffmpeg] segment_time {clip_max_duration}")
        if self.is_audio:
            command = f'ffmpeg -i {self.get_source_file()} -c:a copy -segment_time {clip_max_duration} -map 0 -f segment {output_file}'
        else:
            command = f'ffmpeg -i {self.get_source_file()} -c:v copy -c:a copy -segment_time {clip_max_duration} -map 0 -f segment {output_file}'
        result = subprocess.run(command, shell=True)
        if result.returncode != 0:
            print("Error running ffprobe:", result.stderr)
            return None
        paths = sorted(pathlib.Path(self.dir).glob(f'{self.name}_chunk_*{self.ext}'))
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
            audio_path = os.path.join(save_path, f'{title}_{audio_stream.abr}.{audio_stream.subtype}')
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

async def run_example():
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    yt = YtLoader()
    # if yt.open_youtube_link('https://www.youtube.com/watch?v=81RWdKEnt4Y'):
    if yt.open_youtube_link('https://www.youtube.com/watch?v=aHiVHZYM9m4'):
        audio = yt.get_audio_streams()
        video = yt.get_video_streams()
        
        # for video_stream, audio_stream in [(video[15], None), (video[14], None), (None, audio[4]), (video[15], audio[4]), (video[14], audio[4])]:
        # for video_stream, audio_stream in [(None, None), (video[1], None)]:
        for video_stream, audio_stream in [(None, None), (video[1], None), (video[1], audio[0]), (None, audio[0])]:
            try:
                downloader = Downloader()
                # await downloader.download(video_stream=video_stream, audio_stream=audio_stream)
                download_task = asyncio.create_task(downloader.download(video_stream=video_stream, audio_stream=audio_stream))
                print(f'let`s try download: {video_stream}, {audio_stream}')
                while not download_task.done():
                    if await downloader.has_info():
                        progress = await downloader.info.get_progress()
                        if progress > 0:
                            print(f'progress: {progress:.3f}%')
                    await asyncio.sleep(0.5)
                            
                if not download_task.exception():
                    while not await downloader.has_result():
                        pass
                    downloader.result.print()
                
            except Exception as e:
                    print(f'Exeption: {str(e)}')

if __name__ == "__main__":
    asyncio.run(run_example())