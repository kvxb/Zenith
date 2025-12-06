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
        self.on_name_change = lambda new_name: print(f"Name changed to {new_name}")

        self.name_field = ft.TextField(
            value=self.name,
            text_size=20,
            border=ft.InputBorder.NONE,
            content_padding=0,
            on_submit=lambda e: self._on_name_submit(e.control.value),
            on_blur=lambda e: self._on_name_submit(e.control.value),
        )

        self.inner_row = ft.Row(
            controls=[
                ft.Column(
                    [
                        self.name_field,
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

    def _on_name_submit(self, new_name: str):
        """Handle name change when user submits or loses focus"""
        if new_name != self.name:
            if not new_name:
                new_name = "Untitled Playlist"
            self.name = new_name
            self.on_name_change(new_name)

        self.name_field.value = self.name
        self.update()

    def set_active(self, is_active: bool):
        """Set visual state for active (focused) playlist"""
        if is_active:
            self.margin = ft.margin.all(2)
            self.shadow_color = ft.Colors.CYAN_400
            self.elevation = 16
        else:
            self.margin = ft.margin.all(5)
            self.shadow_color = None
            self.elevation = 1
        self.update()

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
