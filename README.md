# winnow

A lightweight, non-destructive media culling tool for quickly sorting through images and videos.

## Features
- **Tinder, but for your Downloads folder**: Swipe left to reject, swipe right to keep.
- **Fast Navigation**: Preloads the next image for instant switching.
- **Non-Destructive**: Rejected files are moved to a `_rejected` subdirectory instead of being deleted.
- **Media Support**: Handles images, videos, PDFs, CSVs, and text files.
- **Generic Support**: Browses all file types and folders with a unique summary view.
- **Custom Folders**: Use A/S/D/F to sort files into 4 color-coded, renameable folders.

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
| **Left Arrow** | **Reject**: Move current file to `_rejected` folder |
| **Right Arrow** | **Keep**: Skip to the next file |
| **A / S / D / F** | **Sort**: File into respective folders (Renameable in UI) |
| **Esc** | **Back/Exit**: Unfocus text inputs, or Exit if idle |
| **Cmd + R** | **Reset**: Reset viewed log and review all files again |

## How it Works

1. The application scans the target directory for supported media files.
2. Files are displayed one by one.
3. When you "Reject" a file, it is immediately moved to a `_rejected` folder inside the target directory. If the folder doesn't exist, it is created automatically.
4. If a file with the same name already exists in `_rejected`, the rejected file is renamed with a unique suffix to prevent data loss.

_Built with Gemini on Antigravity_

_[rphlhuang.github.io](https://rphlhuang.github.io)_
