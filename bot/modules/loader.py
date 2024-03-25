import asyncio
from typing import Optional, Callable

class AsyncExecutor:
    def __init__(self, command, progress_parser : Callable[[str], float]):
        self.command = command
        self.progress_parser = progress_parser
        self.progress = 0
        self.done = False

    async def wait(self, update_callback : Optional[Callable[[float], None]]):
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
            progress = await self.progress_parser(line.decode())
            if progress - self.progress > 0.5:
                self.progress = progress
                await update_callback(progress)
        
        await self.process.wait()
        if self.process.returncode != 0:
            raise Exception(f"Ошибка при выполнении команды: {self.command}. Код возврата: {self.process.returncode}")
        self.done = True

    async def execute(self):
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

import re
from datetime import datetime
from pathlib import Path

class Loader(AsyncExecutor):
    progress_pattern = re.compile(r'size=\s*([^\s]+)\s+time=(\d+:\d+:\d+\.\d+)\s+bitrate=\s*([^\s]+)\s+speed=\s*([^\s]+)')
    duration_pattern = re.compile(r'Duration: (\d+:\d+:\d+\.\d+)')
    def __init__(self, source_file1 : str, result_file_name : str, result_ext : str, source_file2='', segment_len=600, result_dir='./downloads'):
        if len(source_file2):
            source_file2=f' -i \"{source_file2}\"'

        if not Path(result_dir).exists():
            Path.mkdir(result_dir)
            
        self._result_dir = result_dir
        self._result_file_suffix = result_file_name
        self._result_ext = result_ext

        command = f"""ffmpeg \
        -i \"{source_file1}\"{source_file2} \
        -c:v copy -c:a copy \
        -progress pipe:2 \
        -f segment -segment_time {segment_len} \
        -reset_timestamps 1 \
        \"{result_dir}/{result_file_name}_segment_%03d.{result_ext}\""""
        
        self.duration = '00:00:00.00'
        self.time = '00:00:00.00'
        
        AsyncExecutor.__init__(self, command=command, progress_parser=self.parse_info)

    async def parse_info(self, log_line : str):
        duration_match = re.match(Loader.duration_pattern, log_line.strip())
        progress_match = re.match(Loader.progress_pattern, log_line.strip())
        if duration_match or progress_match:
            if duration_match:
                self.duration = duration_match.group(1)
            if progress_match:
                self.time = progress_match.group(2)
                
        duration = datetime.strptime(self.duration, "%H:%M:%S.%f") - datetime.strptime('00:00:00.00', "%H:%M:%S.%f")
        elapsed = datetime.strptime(self.time, "%H:%M:%S.%f") - datetime.strptime('00:00:00.00', "%H:%M:%S.%f")
        return (elapsed.total_seconds() / duration.total_seconds()) * 100 if duration.total_seconds() > 0 else 0

    async def get_resources(self) -> list[str]:
        paths = sorted(Path(self._result_dir).glob(f'{self._result_file_suffix}_segment_*{self._result_ext}'))
        return list(map(str, paths))


## testing
if __name__ == "__main__":
    async def _progress_cb(progress : float):
        print(f'progressbar: {progress}%')

    async def _download():
        try:
            source_file1='downloads/C___с_нуля_до_джуна___C___ROADMAP___Подробный_план_обучения_720p_48kbps_segment_000.mp4'
            result_ext = Path(source_file1).suffix[1:]
            d = Loader(source_file1=source_file1, result_file_name='other', result_ext=result_ext)
            task = await asyncio.create_task(d.execute())
            await d.wait(_progress_cb)
            if d.done:
                print(await d.get_resources())

        except Exception as e:
            print(e)
    asyncio.run(_download())