from loaders import StreamLoader, open_link, Stream

# Example | test
if __name__ == "__main__":
    import sys
    import logging
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    import asyncio
    from pprint import pprint
    # pprint(sys.path)

    async def _progress_cb(progress : float):
        print(f'progressbar: {progress}%')

    async def run_example():
        try:
            video, audio = open_link('https://www.youtube.com/watch?v=aHiVHZYM9m4')#('https://www.youtube.com/watch?v=81RWdKEnt4Y'):
            for video_stream, audio_stream in [(None, None), (video[1], None), (video[1], audio[0]), (None, audio[0])]:
        # for video_stream, audio_stream in [(video[15], None), (video[14], None), (None, audio[4]), (video[15], audio[4]), (video[14], audio[4])]:
        # for video_stream, audio_stream in [(None, None), (video[1], None)]:
                try:
                    d = StreamLoader(video_stream, audio_stream)
                    task = await asyncio.create_task(d.execute())
                    await d.wait(_progress_cb)
                    if d.done:
                        pprint(await d.get_resources())

                except Exception as e:
                        print(f'StreamLoader exception: {str(e)}')
        except Exception as e:
            print(f'Невалидая ссылка на видео: {str(e)}')

    asyncio.run(run_example())