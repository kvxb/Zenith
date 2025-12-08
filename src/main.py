import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
import traceback
import os

print("Starting Zenith app...", flush=True)
print(f"FLET_PLATFORM: {os.environ.get('FLET_PLATFORM', 'not set')}", flush=True)
sys.stdout.flush()

try:
    import flet as ft

    print("Flet imported successfully", flush=True)
    import uuid
    from flet_audio import Audio

    print("flet_audio imported successfully", flush=True)
    from ui import PlaylistManager

    print("PlaylistManager imported successfully", flush=True)
    from backend import TrackModel, PlaylistModel
    from backend.music_manager import MusicManager

    print("Backend modules imported successfully", flush=True)
except Exception as e:
    print(f"Import error: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)


def main(page: ft.Page):
    page.title = "Zenith"
    page.theme_mode = ft.ThemeMode.DARK
    # page.theme = ft.Theme(color_scheme_seed=ft.Colors.CYAN_100)

    try:
        music_manager = MusicManager()
        print("MusicManager created", flush=True)
        playlist_manager = PlaylistManager(music_manager)
        print("PlaylistManager created", flush=True)
        playlist_manager.add_to_page(page)
        print("UI added to page", flush=True)
    except Exception as e:
        print(f"Error in main(): {e}", flush=True)
        traceback.print_exc()
        page.add(ft.Text(f"Error: {e}", color="red"))
        page.update()

    def on_event(e: ft.WindowEvent, page: ft.Page):
        if e.type == ft.WindowEventType.CLOSE:
            print("Application is closing.")
            playlist_manager.pause()
            playlist_manager.audio_manager.clear_audio()
            page.window.destroy()

    page.window.prevent_close = True
    page.window.on_event = lambda e: on_event(e, page)

    page.update()


ft.app(target=main, assets_dir="assets")
