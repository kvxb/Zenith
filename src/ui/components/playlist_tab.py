import flet as ft
from typing import Optional
from .playlist_card import PlaylistCard
from .playlist import Playlist
from .now_playing import NowPlaying
from src.backend.playlist_model import PlaylistModel, TrackModel


class PlaylistTabArea(ft.Container):
    def _playlist_search_bar(self):
        return ft.TextField(
            hint_text="Search playlists...",
            prefix_icon=ft.Icons.SEARCH,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE,
            filled=True,
            bgcolor=ft.Colors.TRANSPARENT,
            on_submit=lambda e: self.on_search(e.control.value),
            expand=True,
        )

    def _library_label(self):
        return ft.Row(
            controls=[
                ft.TextField(value="My Library", expand=True),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip="Add Playlist",
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _playlist_card_list_header(self):
        return ft.Column(
            controls=[
                self._library_label(),
                self._playlist_search_bar(),
            ]
        )

    def _playlist_card_list(self):

        self.playlist_card_list: ft.ReorderableListView = ft.ReorderableListView(
            expand=True,
            on_reorder=self._on_playlist_card_reorder,
        )
        return self.playlist_card_list

    def _on_playlist_card_reorder(self, e: ft.OnReorderEvent):
        old_index = e.old_index or 0
        new_index = e.new_index or 0
        target = self.playlist_card_list

        print(f"Reordering playlist cards from {old_index} to {new_index}")
        element_to_move = target.controls.pop(old_index)
        target.controls.insert(new_index, element_to_move)

        if isinstance(element_to_move, PlaylistCard):
            element_to_move.on_click = lambda id: self._on_card_click(id)

        target.update()

    def _header(self):
        self.header = ft.Column(
            controls=[
                self._playlist_card_list_header(),
                self._playlist_card_list(),
            ],
        )
        return self.header

    def _play_button(self):
        self.play_button: ft.IconButton = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW, on_click=self.on_play_button_click
        )
        return self.play_button

    def _body_header(self):
        return ft.Row(
            controls=[
                self._play_button(),
                ft.IconButton(icon=ft.Icons.SHUFFLE, on_click=self._on_shuffle),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.Icons.UPLOAD_FILE),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    def _playlist_stack(self):
        self.playlist_stack: ft.Stack = ft.Stack(expand=True)
        return self.playlist_stack

    def _body(self):
        self.now_playing = NowPlaying()
        self.body = ft.Column(
            controls=[
                self.now_playing,
                self._body_header(),
                self._playlist_stack(),
            ]
        )
        return self.body

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._active_tab_uuid = ""
        self.on_play = lambda id: None
        self.on_reorder = lambda id, old_idx, new_idx: None
        self.on_loop = lambda: None
        self.on_search = lambda query: None

        self.header_container = ft.Container(
            content=self._header(),
            width=300,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        self.body_container = ft.Container(
            content=self._body(),
            expand=3,
        )

        self.content = ft.Row(
            controls=[
                self.header_container,
                ft.GestureDetector(
                    content=ft.VerticalDivider(width=5, color=ft.Colors.GREY_400),
                    on_pan_update=self._on_divider_drag,
                    mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                ),
                self.body_container,
            ],
            expand=True,
        )
        self.expand = True

    def did_mount(self):
        super().did_mount()
        if self.playlist_card_list.controls:
            first_control = self.playlist_card_list.controls[0]
            if isinstance(first_control, PlaylistCard):
                self.focus(first_control.id)

    def add_playlist(self, playlist_card: PlaylistCard, playlist: Playlist):

        playlist_card.on_click = self._on_card_click
        playlist.on_card_click = self._on_item_click
        playlist.on_reorder_callback = (
            lambda id, old_idx, new_idx: self._on_reorder_internal(id, old_idx, new_idx)
        )
        # Add to controls
        self.playlist_card_list.controls.append(playlist_card)
        self.playlist_stack.controls.append(playlist)

        # Hide playlist by default (show only when card is clicked)
        playlist.visible = False

    def _on_reorder_internal(self, id: str, old_idx: int | None, new_idx: int | None):
        self.on_reorder(id, old_idx, new_idx)

    def show_playlist(self, playlist_id: str):
        """Show playlist and hide all others"""
        for control in self.playlist_stack.controls:
            if isinstance(control, Playlist):
                control.visible = control.id == playlist_id
        self.playlist_stack.update()

    def get_playslist_card(self, uuid: str) -> Optional[PlaylistCard]:
        for control in self.playlist_card_list.controls:
            if isinstance(control, PlaylistCard) and control.id == uuid:
                return control
        return None

    def get_playlist(self, uuid: str) -> Optional[Playlist]:
        for control in self.playlist_stack.controls:
            if isinstance(control, Playlist) and control.id == uuid:
                return control
        return None

    def get_active_playlist(self) -> Optional[Playlist]:
        for control in self.playlist_stack.controls:
            if isinstance(control, Playlist) and control.id == self._active_tab_uuid:
                return control
        return None

    def focus(self, playlist_id: str):
        if self._active_tab_uuid == playlist_id:
            return

        # Remove highlight from previous active card
        if self._active_tab_uuid:
            previous_card = self.get_playslist_card(self._active_tab_uuid)
            if previous_card is not None:
                previous_card.margin = ft.margin.all(5)
                previous_card.shadow_color = None
                previous_card.elevation = 1
                previous_card.update()

        self._active_tab_uuid = playlist_id
        self.show_playlist(playlist_id)

        # Add subtle highlight to new active card
        active_card = self.get_playslist_card(playlist_id)
        if active_card is not None:
            print(f"Adding highlight to active card {playlist_id}")
            active_card.margin = ft.margin.all(2)
            active_card.shadow_color = ft.Colors.CYAN_400
            active_card.elevation = 16
            active_card.update()

    def _on_card_click(self, id: str):
        if self._active_tab_uuid == id:
            return
        self.focus(id)

    def _on_divider_drag(self, e: ft.DragUpdateEvent):
        header_width = self.header_container.width

        if header_width is not None:
            new_width = max(1, header_width + e.delta_x * 1.01)

            self.header_container.width = new_width
            self.update()

    def _on_shuffle(self, e):
        playlist = self.get_active_playlist()
        if playlist is not None:
            playlist.shuffle()

    def _on_loop(self, e):
        self.on_loop()

    def _on_item_click(self, id: str):
        print(f"Item clicked in tab area: {id}")
        self.on_play(id)

    def on_play_button_click(self, e):
        self.on_play(None)

    def update_play_button_state(self, is_playing: bool):
        if is_playing:
            self.play_button.icon = ft.Icons.PAUSE
        else:
            self.play_button.icon = ft.Icons.PLAY_ARROW
        self.play_button.update()

    def update_ui_on_play(
        self,
        previous_playlist_model: PlaylistModel | None,
        previous_track: TrackModel | None,
        active_playlist_model: PlaylistModel,
        is_playing: bool,
    ):
        self.update_play_button_state(is_playing)

        new_track = active_playlist_model.get_active_track()
        if new_track is None:
            return

        now_playing = self.now_playing

        if previous_playlist_model is not None and previous_track is not None:
            last_playlist_ui = self.get_playlist(previous_playlist_model.id)

            if last_playlist_ui is not None:
                last_track_item = last_playlist_ui.get_track_item(previous_track.id)
                if last_track_item is not None:
                    last_track_item.highlight(False)

        # Clear previous playlist card highlight only if switching playlists
        if (
            previous_playlist_model is not None
            and previous_playlist_model.id != active_playlist_model.id
        ):
            last_playlist_card = self.get_playslist_card(previous_playlist_model.id)
            if last_playlist_card is not None:
                last_playlist_card.highlight(False)

        # Set new playlist highlights if playing
        if is_playing:
            active_playlist_card = self.get_playslist_card(active_playlist_model.id)
            new_playlist_ui = self.get_playlist(active_playlist_model.id)

            if active_playlist_card is not None:
                active_playlist_card.highlight(True)

            if new_playlist_ui is not None:
                new_track_item = new_playlist_ui.get_track_item(new_track.id)
                if new_track_item is not None:
                    new_track_item.highlight(True)

        # Update the entire playlist UI once after all highlights are set
        self.playlist_stack.update()

        if now_playing.current_track != new_track:
            self.now_playing.load_track_info(new_track)

        now_playing.play_pause_btn.icon = (
            ft.Icons.PAUSE_CIRCLE_FILLED if is_playing else ft.Icons.PLAY_CIRCLE_FILLED
        )
        now_playing.play_pause_btn.update()
