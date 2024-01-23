import filetype

def main():
    kind = filetype.guess('C:\\Users\\Sunny\\Documents\\projects\\python\\tg_bot\\audio_50kbps.mp3')
    if kind is None:
        print('Cannot guess file type!')
        return

    print('File extension: %s' % kind.extension)
    print('File MIME type: %s' % kind.mime)

if __name__ == '__main__':
    main()