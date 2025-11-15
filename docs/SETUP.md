# Installation & Setup Guide

## Prerequisites

- Python 3.9 or higher
- Linux environment

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/kvxb/Zenith.git
cd Zenith
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

## Running the Application

### Web Version

```bash
flet run --web
```

The application will open at `http://localhost:8550`.

### Development Mode (Hot Reload)

```bash
flet run -d -r --web
```

## Current Features

**Note:** This is an early development version. The application currently provides:

- A single UI component (`MusicListItem`) that displays song information
- Playback controls for one hardcoded song (`gorosei.mp3`)
- Basic play/pause/replay functionality

## Project Structure

```
Zenith/
├── main.py              # Application entry point
├── assets/              # Audio files (gorosei.mp3)
└── src/
    ├── ui/components/   # UI components (MusicListItem)
    └── backend/         # Backend logic (planned)
```
