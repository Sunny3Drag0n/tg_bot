import asyncio
from loaders import Loader
from pathlib import Path

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