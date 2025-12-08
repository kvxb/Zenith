import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import flet as ft
import uuid
from flet_audio import Audio
from ui import PlaylistManager
from backend import TrackModel, PlaylistModel
from backend.music_manager import MusicManager


def main(page: ft.Page):
    page.title = "Zenith"

    page.theme_mode = ft.ThemeMode.DARK
    # page.theme = ft.Theme(color_scheme_seed=ft.Colors.CYAN_100)

    music_manager = MusicManager()
    playlist_manager = PlaylistManager(music_manager)
    playlist_manager.add_to_page(page)

    def on_event(e: ft.WindowEvent, page: ft.Page):
        if e.type == ft.WindowEventType.CLOSE:
            print("Application is closing.")
            playlist_manager.pause()
            playlist_manager.audio_manager.clear_audio()
            page.window.destroy()

    page.window.prevent_close = True
    page.window.on_event = lambda e: on_event(e, page)

    page.update()


if __name__ == "__main__":
    ft.app(main, assets_dir="assets", port=8550)
