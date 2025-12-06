import flet as ft


class PlaylistCard(ft.Card):
    def __init__(
        self, playlist_id: str, name: str, count: int, duration: int, **kwargs
    ):
        super().__init__(**kwargs)
        self.id = playlist_id
        self.name = name
        self.count = count
        self.duration = duration
        self.on_click = lambda id: print(id)
        self.on_drop = lambda track_id: print(
            f"Track {track_id} dropped on playlist {playlist_id}"
        )

        self.inner_row = ft.Row(
            controls=[
                ft.Column(
                    [
                        ft.Text(
                            self.name,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"{self.count} tracks • {self.format_duration()}",
                            size=14,
                            color=ft.Colors.GREY_600,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    expand=True,
                    spacing=5,
                )
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.playing_indicator = ft.Icon(
            name=ft.Icons.MUSIC_NOTE,
            size=20,
            color=ft.Colors.CYAN_400,
            visible=False,
        )

        self.inner_row.controls.insert(0, self.playing_indicator)

        # Wrap content in DragTarget to accept drops
        self.drag_target = ft.DragTarget(
            group="playlist_tracks",
            content=ft.Container(
                content=self.inner_row,
                padding=ft.padding.all(10),
                on_click=lambda e: self.on_click(self.id),
            ),
            on_accept=self._on_accept_drop,
        )

        self.content = self.drag_target

        # Set default border
        self.margin = ft.margin.all(5)

    def _on_accept_drop(self, e: ft.DragTargetEvent):
        """Handle track drop on this playlist card"""
        if not e.src_id or not self.page:
            return

        draggable_control = self.page.get_control(str(e.src_id))

        if draggable_control and hasattr(draggable_control, "data"):
            self.on_drop(draggable_control.data)

    def highlight(self, show: bool):
        """Highlight this playlist card"""
        self.playing_indicator.visible = show
        if show:
            self.color = ft.Colors.CYAN_700
        else:
            self.color = None
        self.update()

    def format_duration(self) -> str:
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"

    def __repr__(self):
        return f"PlaylistCard(id={self.id}, name={self.name}, count={self.count}, duration={self.duration})"
