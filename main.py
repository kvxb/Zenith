import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import flet as ft
from src.ui import AudioLabel, MusicListItem


def main(page: ft.Page):
    counter = ft.Text("0", size=50, data=0)
    page.title = "Zenith"
    
    audio_label = MusicListItem(
        number=0,
        name="Gorosei theme",
        author="Oda",
        album="Mu",
        duration="3:14",
        audio_src="gorosei.mp3"
    )
    
    page.add(
        ft.Column([
            audio_label,
        ])
    )


if __name__ == "__main__":
    ft.app(main, assets_dir="assets")
