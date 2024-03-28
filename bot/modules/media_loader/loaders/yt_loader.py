from .loader import Loader
from pytube import YouTube, Stream
from typing import Optional, Tuple
import re

class StreamLoader(Loader):
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

    def __init__(self, video_stream : Optional[Stream] = None, audio_stream : Optional[Stream] = None):
        file=""
        second_file=""
        self.filetype=''
        if video_stream:
            file=video_stream.url
            self.filetype = "video"

        if audio_stream:
            if video_stream:
                second_file=audio_stream.url
            else:
                file=audio_stream.url
                self.filetype = "audio"

        if not file:
            raise Exception("download: empty source")

        result_name, ext, self.src_title = StreamLoader.get_result_name_ext(video_stream, audio_stream)

        Loader.__init__(self, source_file1=file, result_file_name=result_name, source_file2=second_file, result_ext=ext)


def open_link(link) -> Tuple[list[Stream], list[Stream]]:
    """return video_streams, audio_streams"""
    yt = YouTube(link)
    video_streams = []
    audio_streams = []
    for stream in yt.streams:
        if stream.type == 'video':
            video_streams.append(stream)
        elif stream.type == 'audio':
            audio_streams.append(stream)
    if not len(video_streams) and not len(audio_streams):
        raise Exception(f"Невозможно получить YouTubeю.streams")

    return video_streams, audio_streams
