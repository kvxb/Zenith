import flet as ft


class PlaylistItem(ft.Container):
    """Music list item with number, name, author, album and timestamp"""

    def __init__(
        self,
        track_id: str,
        number: int,
        name: str,
        author: str,
        album: str,
        duration: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.id = track_id
        self.number = number
        self.name = name
        self.author = author
        self.album = album
        self.duration = duration

        self.on_card_click = lambda track_id: print(f"Item clicked {track_id}")
        self.on_delete = lambda track_id: print(f"Delete track {track_id}")
        self.on_copy = lambda track_id: print(f"Copy track {track_id}")
        self.on_loop = lambda track_id: print(f"Loop track {track_id}")
        self.key = track_id

        self.is_playing = False
        self.is_reordering = False
        self.number_text_control = self._number_text()
        self.playing_icon = ft.Icon(
            name=ft.Icons.VOLUME_UP_ROUNDED,
            size=24,
            color=ft.Colors.PRIMARY,
            visible=False,
        )

        name_author_column = self._name_author_column()

        self.menu_button = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    text="Loop Track",
                    icon=ft.Icons.REPEAT_ONE,
                    on_click=lambda e: self.on_loop(self.id),
                ),
                ft.PopupMenuItem(
                    text="Copy Track",
                    icon=ft.Icons.CONTENT_COPY,
                    on_click=lambda e: self.on_copy(self.id),
                ),
                ft.PopupMenuItem(),  # Divider
                ft.PopupMenuItem(
                    text="Delete from Playlist",
                    icon=ft.Icons.DELETE,
                    on_click=lambda e: self.on_delete(self.id),
                ),
            ],
            icon=ft.Icons.MORE_VERT,
            icon_color=ft.Colors.TRANSPARENT,
        )

        row_data = ft.Row(
            controls=[
                ft.Stack(
                    controls=[
                        self.number_text_control,
                        self.playing_icon,
                    ],
                    width=40,
                ),
                ft.Container(
                    content=ft.Draggable(
                        group="playlist_tracks",
                        content=name_author_column,
                        content_feedback=self.content_feedback(),
                        content_when_dragging=ft.Container(
                            content=name_author_column,
                            opacity=0.3,
                        ),
                        data=track_id,
                    ),
                    expand=True,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                self._album_text(),
                self._duration_text(),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content = ft.Row(
            controls=[
                ft.GestureDetector(
                    content=row_data,
                    on_enter=lambda e: self._on_enter_event(e),
                    on_exit=lambda e: self._on_exit_event(e),
                    on_tap=lambda e: self.on_card_click(self.id),
                    expand=True,
                ),
                ft.Container(
                    content=ft.GestureDetector(
                        content=self.menu_button,
                        on_enter=lambda e: self._on_enter_event(e),
                        on_exit=lambda e: self._on_exit_event(e),
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(right=30),
                ),
            ],
            expand=True,
        )

        # Container styling
        self.padding = ft.padding.all(10)
        self.margin = ft.margin.only(bottom=10)
        self.border = ft.border.all(0.1, ft.Colors.OUTLINE)
        self.border_radius = 5
        self.bgcolor = ft.Colors.TRANSPARENT
        self.ink = True

    def _number_text(self):
        return ft.Text(str(self.number), size=18, width=40, color=ft.Colors.GREY_600)

    def _name_author_column(self) -> ft.Column:
        return ft.Column(
            [
                ft.Text(
                    self.name,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                ),
                ft.Text(
                    self.author,
                    size=20,
                    color=ft.Colors.GREY_600,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                ),
            ],
            spacing=2,
            expand=True,
        )

    def _album_text(self):
        return ft.Text(
            self.album,
            size=18,
            color=ft.Colors.GREY_700,
            width=150,
            overflow=ft.TextOverflow.ELLIPSIS,
            no_wrap=True,
        )

    def _duration_text(self):
        return ft.Text(
            self.duration,
            size=18,
            color=ft.Colors.GREY_600,
            width=60,
            no_wrap=True,
        )

    def content_feedback(self):
        return ft.Icon(
            name=ft.Icons.DRAG_INDICATOR,
            size=30,
            color=ft.Colors.BLUE_400,
        )

    def highlight(self, show: bool):
        self.is_playing = show
        self.playing_icon.visible = show
        self.number_text_control.visible = not show
        if show:
            self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
            self.border = ft.border.all(1, ft.Colors.PRIMARY)
        else:
            self.bgcolor = ft.Colors.TRANSPARENT
            self.border = ft.border.all(0.1, ft.Colors.OUTLINE)

        print(f"Updating playlist item highlight {show}")

    def toggle_loop_style(self, is_looping: bool):
        """Toggle visual style to indicate track is looping"""
        if is_looping:
            # Add visual indicator for looping track (e.g., different border color)
            self.border = ft.border.all(2, ft.Colors.PRIMARY)
        else:
            # Reset to normal border
            if self.is_playing:
                self.border = ft.border.all(1, ft.Colors.PRIMARY)
            else:
                self.border = ft.border.all(0.1, ft.Colors.OUTLINE)
        self.update()

    def _on_enter_event(self, e):
        # if self.page:
        self.menu_button.icon_color = ft.Colors.PRIMARY
        self.menu_button.update()

    def _on_exit_event(self, e):
        # if self.page:
        self.menu_button.icon_color = ft.Colors.TRANSPARENT
        self.menu_button.update()
