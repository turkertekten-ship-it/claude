---
date: 2022-11-02T17:34:01+0000
source: https://pypi.org/project/filetype/
---
Small and dependency free Python package to infer file type and MIME
type checking the magic numbers signature of a file or buffer.

This is a Python port from filetype Go package.

## Features

- Simple and friendly API
- Supports a wide range of file types
- Provides file extension and MIME type inference
- File discovery by extension or MIME type
- File discovery by kind (image, video, audio…)
- Pluggable: add new custom type matchers
- Fast, even processing large files
- Only first 261 bytes representing the max file header is required, so
you can just pass a list of bytes
- Dependency free (just Python code, no C extensions, no libmagic
bindings)
- Cross-platform file recognition

## Installation

```
pip install filetype
```

## API

See annotated API reference.

## Examples

Simple file type checking

```
import filetype

def main():
    kind = filetype.guess('tests/fixtures/sample.jpg')
    if kind is None:
        print('Cannot guess file type!')
        return

    print('File extension: %s' % kind.extension)
    print('File MIME type: %s' % kind.mime)

if __name__ == '__main__':
    main()
```

## Supported types

### Image

- dwg - image/vnd.dwg
- xcf - image/x-xcf
- jpg - image/jpeg
- jpx - image/jpx
- png - image/png
- apng - image/apng
- gif - image/gif
- webp - image/webp
- cr2 - image/x-canon-cr2
- tif - image/tiff
- bmp - image/bmp
- jxr - image/vnd.ms-photo
- psd - image/vnd.adobe.photoshop
- ico - image/x-icon
- heic - image/heic
- avif - image/avif

### Video

- 3gp - video/3gpp
- mp4 - video/mp4
- m4v - video/x-m4v
- mkv - video/x-matroska
- webm - video/webm
- mov - video/quicktime
- avi - video/x-msvideo
- wmv - video/x-ms-wmv
- mpg - video/mpeg
- flv - video/x-flv

### Audio

- aac - audio/aac
- mid - audio/midi
- mp3 - audio/mpeg
- m4a - audio/mp4
- ogg - audio/ogg
- flac - audio/x-flac
- wav - audio/x-wav
- amr - audio/amr
- aiff - audio/x-aiff

### Archive

- br - application/x-brotli
- rpm - application/x-rpm
- dcm - application/dicom
- epub - application/epub+zip
- zip - application/zip
- tar - application/x-tar
- rar - application/x-rar-compressed
- gz - application/gzip
- bz2 - application/x-bzip2
- 7z - application/x-7z-compressed
- xz - application/x-xz
- pdf - application/pdf
- exe - application/x-msdownload
- swf - application/x-shockwave-flash
- rtf - application/rtf
- eot - application/octet-stream
- ps - application/postscript
- sqlite - application/x-sqlite3
- nes - application/x-nintendo-nes-rom
- crx - application/x-google-chrome-extension
- cab - application/vnd.ms-cab-compressed
- deb - application/x-deb
- ar - application/x-unix-archive
- Z - application/x-compress
- lzo - application/x-lzop
- lz - application/x-lzip
- lz4 - application/x-lz4
- zstd - application/zstd

### Document

- doc - application/msword
- docx - application/vnd.openxmlformats-officedocument.wordprocessingml.document
- odt - application/vnd.oasis.opendocument.text
- xls - application/vnd.ms-excel
- xlsx - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- ods - application/vnd.oasis.opendocument.spreadsheet
- ppt - application/vnd.ms-powerpoint
- pptx - application/vnd.openxmlformats-officedocument.presentationml.presentation
- odp - application/vnd.oasis.opendocument.presentation

### Font

- woff - application/font-woff
- woff2 - application/font-woff
- ttf - application/font-sfnt
- otf - application/font-sfnt

### Application

- wasm - application/wasm
