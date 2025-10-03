# SpeechScan

A lightweight desktop application (PyQt5) that **transcribes
recordings** using **AssemblyAI** and **counts word occurrences**. The
input can be either an **`.mp3` file** or a **YouTube link** (audio is
automatically downloaded via `yt-dlp`). It supports multiple languages,
automatically detected by AssemblyAI (~99 languages, including English,
Polish, German, French, Spanish, Italian, Portuguese, Russian, Japanese,
Turkish...).

> **License:** `CC0-1.0` *(with exceptions, see LICENSE file)*      
> **Requirements:** `Python 3.12–3.14`, `PyQt5`, `requests`, `yt-dlp`

------------------------------------------------------------------------

## Features

-   **Two input modes**
    -   File -- select a local `.mp3` file.
    -   YouTube -- paste a URL, the audio will be downloaded
        automatically.
-   **Cloud transcription (AssemblyAI)**
    -   Upload file → create transcription job → poll until complete →
        fetch text.
    -   Automatic language detection -- ~99 supported languages
        (English, Polish, German, French, Spanish, Italian, Portuguese,
        Russian, Japanese, Turkish...).
-   **Word counting**
    -   Text cleaning (removing punctuation, normalization) and
        returning a list of words with counts.
-   **PyQt5 GUI**
    -   Windows: Start, File, YouTube. I/O operations run in **Qt
        threads** to keep the UI responsive.

------------------------------------------------------------------------

## Requirements & Dependencies

-   **Python:** 3.12--3.14
-   **System:** packaged with PyQt5 dependencies for **Windows** (see
    `requirements.txt`).
    On other systems, install a compatible PyQt5 version manually.
-   **Runtime libraries:**
    `PyQt5`, `requests`, `yt-dlp`
-   **Dev (optional):** `pytest`, `ruff`, `black`, `pyinstaller`, etc.
    (see `requirements-dev.txt`)

------------------------------------------------------------------------

## Installation

### Poetry

**Users** (runtime dependencies only):

``` bash
poetry install --without dev
poetry run speechscan
```

**Developers** (runtime + dev dependencies):

``` bash
poetry install
poetry run speechscan
```

### Pip (from local repo)

**Users** (runtime dependencies only):

``` bash
pip install -r requirements.txt
pip install -e .
speechscan
# or:
python -m speechscan
```

**Developers** (runtime + dev dependencies):

``` bash
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
speechscan
```

------------------------------------------------------------------------

## Run (Quick Start)

1.  Launch the app:

    ``` bash
    speechscan
    ```

2.  Choose input mode:

    -   **File** -- select an `.mp3` file.
    -   **YouTube** -- paste a video URL (audio downloads
        automatically).

3.  Enter your **API key** (AssemblyAI), click **Count**, and wait for
    the transcription and word list (processing time depends on file
    length).

------------------------------------------------------------------------

## Project Structure

    speechscan/
    ├─ __main__.py                 # entry point (main + logging)
    ├─ app.py                      # QApplication init, style loading, UI setup
    ├─ logging_config.py           # colored/file logging + ANSI detection
    ├─ services/
    │  ├─ transcription/
    │  │  └─ transcribe_audio.py   # AssemblyAI client (upload, job, polling)
    │  └─ text/
    │     └─ count_words.py        # transcript cleaning + word counting
    ├─ threads/                    # Qt threads for I/O tasks
    │  ├─ download_video_thread.py # YouTube audio download (yt-dlp)
    │  ├─ check_url_thread.py      # URL validation
    │  └─ count_words_thread.py    # run transcription + counting
    ├─ ui/                         # PyQt5 windows (Start/File/YouTube) + .ui files
    │  ├─ start_window.py
    │  ├─ file_window.py
    │  ├─ youtube_window.py
    │  └─ views/
    │     ├─ open_window.ui
    │     ├─ file_window.ui
    │     └─ youtube_window.ui
    ├─ assets/
    │  ├─ img/                     # icons, loading.gif
    │  └─ style/style.qss          # application stylesheet
    └─ utils/paths.py              # resource paths (dev/exe)

------------------------------------------------------------------------

## API / Module Documentation

Full project documentation: **[API Reference -
speechscan](reference/speechscan/index.md)**.

------------------------------------------------------------------------

## License

This project is released under **CC0-1.0** (public domain). You may
copy, modify, distribute, and use it commercially without additional
permissions.

⚠️ **Note:** not all files in the repository are under CC0. See the
**LICENSE** file for details.
