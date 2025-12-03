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

        self.on_card_click = lambda id: print(f"Item clicked {id}")
        self.key = track_id

        self.is_playing = False
        self.number_text_control = self._number_text()
        self.playing_icon = ft.Icon(
            name=ft.Icons.VOLUME_UP_ROUNDED,
            size=24,
            color=ft.Colors.CYAN_400,
            visible=False,
        )

        name_author_column = self._name_author_column()
        row_data = ft.Row(
            controls=[
                ft.Stack(
                    controls=[
                        self.number_text_control,
                        self.playing_icon,
                    ],
                    width=40,
                ),
                ft.Draggable(
                    content=name_author_column,
                    content_feedback=self.content_feedback(),
                    content_when_dragging=ft.Container(
                        content=name_author_column,
                        opacity=0.3,
                    ),
                ),
                ft.Container(
                    expand=True,
                ),
                self._album_text(),
                self._duration_text(),
            ],
        )
        self.content = ft.GestureDetector(
            content=row_data,
            on_enter=self._on_enter_event,
            on_exit=self._on_exit_event,
            on_tap=lambda e: self.on_card_click(self.id),
        )

        # Container styling
        self.padding = ft.padding.all(10)
        self.margin = ft.margin.only(bottom=10)
        self.border = ft.border.all(0.1, ft.Colors.GREY_400)
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
        return ft.Text(self.album, size=18, color=ft.Colors.GREY_700, width=150)

    def _duration_text(self):
        return ft.Text(self.duration, size=18, color=ft.Colors.GREY_600, width=60)

    def content_feedback(self):
        return ft.Icon(
            name=ft.Icons.DRAG_INDICATOR,
            size=30,
            color=ft.Colors.BLUE_400,
        )

    def highlight(self, show: bool):
        """Highlight this item as currently playing"""
        self.playing_icon.visible = show
        self.number_text_control.visible = not show
        if show:
            self.bgcolor = ft.Colors.CYAN_900
            self.border = ft.border.all(1, ft.Colors.CYAN_400)
        else:
            self.bgcolor = ft.Colors.TRANSPARENT
            self.border = ft.border.all(0.1, ft.Colors.GREY_400)
        self.update()

    def _on_enter_event(self, e):
        if not self.playing_icon.visible:
            self.bgcolor = ft.Colors.BLUE_300
            self.update()

    def _on_exit_event(self, e):
        if not self.playing_icon.visible:
            self.bgcolor = ft.Colors.TRANSPARENT
            if self.page:
                self.update()
        else:
            self.bgcolor = ft.Colors.CYAN_900
            if self.page:
                self.update()
