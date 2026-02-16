# winnow

A lightweight, non-destructive media culling tool for quickly sorting through images and videos.

## Features
- **Visual Feedback**: Top bar indicators clearly show "Reject" and "Keep" actions.
- **Fast Navigation**: Preloads the next image for instant switching.
- **Non-Destructive**: Rejected files are moved to a `_rejected` subdirectory instead of being deleted.
- **Media Support**: Handles common image formats (JPG, PNG, GIF, WEBP), video formats (MP4, MKV, MOV), and PDFs.
- **Minimalist UI**: Focuses entirely on the content with a responsive, aspect-ratio-preserving viewer.

## Requirements

- Python 3.6+
- PyQt6

## Installation

1. Clone or download this repository.
2. Install the required dependencies:

```bash
pip install PyQt6
```

## Usage

Run the script by providing the directory containing the media you want to cull:

```bash
python3 winnow.py /path/to/your/photos
```

If no directory is provided, it defaults to the current working directory.

## Controls

| Key | Action |
| --- | --- |
| **Right Arrow** | **Keep**: Skip to the next file |
| **Left Arrow** | **Reject**: Move current file to `_rejected` folder |
| **Esc** | **Exit**: Close the application |

## How it Works

1. The application scans the target directory for supported media files.
2. Files are displayed one by one.
3. When you "Reject" a file, it is immediately moved to a `_rejected` folder inside the target directory. If the folder doesn't exist, it is created automatically.
4. If a file with the same name already exists in `_rejected`, the rejected file is renamed with a unique suffix to prevent data loss.

_Built with Gemini on Antigravity_

_[rphlhuang.github.io](https://rphlhuang.github.io)_
