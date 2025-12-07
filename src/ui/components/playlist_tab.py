import flet as ft
from typing import Optional, Callable
from .playlist_card import PlaylistCard
from .playlist import Playlist
from .now_playing import NowPlaying
from backend.playlist_model import PlaylistModel, TrackModel


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
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(
                            text="Create Empty Playlist",
                            icon=ft.Icons.PLAYLIST_ADD,
                            on_click=lambda e: self._on_add_empty_playlist(),
                        ),
                        ft.PopupMenuItem(
                            text="Import from Spotify",
                            icon=ft.Icons.LIBRARY_MUSIC,
                            on_click=lambda e: self._on_add_from_spotify(),
                        ),
                    ],
                    icon=ft.Icons.ADD,
                    tooltip="Add new playlist",
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
        target.update()
        target.controls.insert(new_index, element_to_move)
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
            icon=ft.Icons.PLAY_ARROW,
            tooltip="Play playlist",
            on_click=self.on_play_button_click
        )
        return self.play_button

    def _loop_button(self):
        self.loop_button: ft.IconButton = ft.IconButton(
            icon=ft.Icons.REPEAT,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Loop playlist",
            on_click=self._on_loop_playlist,
        )
        return self.loop_button

    def _body_header(self):
        self.menu_button = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    text="Paste Track",
                    icon=ft.Icons.CONTENT_PASTE,
                    on_click=lambda e: self._on_paste_track(),
                    disabled=True,  # Will be enabled when there's a track in clipboard
                ),
                ft.PopupMenuItem(),  # Divider
                ft.PopupMenuItem(
                    text="Delete Playlist",
                    icon=ft.Icons.DELETE,
                    on_click=lambda e: self._on_delete_playlist(),
                ),
            ],
            icon=ft.Icons.MORE_VERT,
        )

        return ft.Row(
            controls=[
                self._play_button(),
                ft.IconButton(
                    icon=ft.Icons.SHUFFLE,
                    tooltip="Shuffle playlist",
                    on_click=self._on_shuffle
                ),
                self._loop_button(),
                ft.Container(expand=True),
                self.menu_button,
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
        self.on_play = lambda playlist_id, track_id: None
        self.on_reorder = lambda id, old_idx, new_idx: None
        self.on_loop_playlist = lambda playlist_id: None
        self.on_loop_track = lambda track_id: None
        self.on_search = lambda query: None
        self.on_drop = lambda playlist_id, track_id: None
        self.on_focus_change = lambda playlist_id: None
        self.on_delete_playlist = lambda playlist_id: None
        self.on_paste_track = lambda playlist_id: None
        self.on_add_empty_playlist = lambda: None
        self.on_add_from_spotify = lambda: None
        self.on_rename_playlist = lambda playlist_id, new_name: None
        self.on_delete_track = lambda playlist_id, track_id: None
        self.on_copy_track = lambda playlist_id, track_id: None

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
        playlist.on_card_click = lambda track_id: self._on_item_click(
            playlist_card.id, track_id
        )
        playlist_card.on_drop = lambda track_id: self.on_drop(
            playlist_card.id, track_id
        )
        playlist_card.on_name_change = lambda new_name: self.on_rename_playlist(
            playlist_card.id, new_name
        )
        playlist.on_reorder_callback = (
            lambda id, old_idx, new_idx: self._on_reorder_internal(id, old_idx, new_idx)
        )
        playlist.on_delete_track = lambda track_id: self.on_delete_track(
            playlist_card.id, track_id
        )
        playlist.on_copy_track = lambda track_id: self.on_copy_track(
            playlist_card.id, track_id
        )
        playlist.on_loop_track = lambda track_id: self.on_loop_track(track_id)
        # Add to controls
        self.playlist_card_list.controls.append(playlist_card)
        self.playlist_stack.controls.append(playlist)

        # Hide playlist by default (show only when card is clicked)
        playlist.visible = False

        if self.page and len(self.playlist_stack.controls) == 1:
            self.toggle_body_header(True)

    def remove_playlist(self, playlist_id: str):
        card_ui = self.get_playslist_card(playlist_id)
        playlist_ui = self.get_playlist(playlist_id)

        if card_ui is not None:
            self.playlist_card_list.controls.remove(card_ui)
        if playlist_ui is not None:
            self.playlist_stack.controls.remove(playlist_ui)

        if playlist_id == self._active_tab_uuid:
            self.focus("first")

        if self.is_empty():
            self.toggle_body_header(False)

        self.update()

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
        if self.is_empty() or self._active_tab_uuid == playlist_id:
            return

        if playlist_id == "first":
            first_control = self.playlist_card_list.controls[0]
            if isinstance(first_control, PlaylistCard):
                self.focus(first_control.id)
            return

        if playlist_id == "last":
            last_control = self.playlist_card_list.controls[-1]
            if isinstance(last_control, PlaylistCard):
                self.focus(last_control.id)
            return

        # Remove active state from previous card
        if self._active_tab_uuid:
            previous_card = self.get_playslist_card(self._active_tab_uuid)
            if previous_card is not None:
                previous_card.set_active(False)

        self._active_tab_uuid = playlist_id
        self.show_playlist(playlist_id)

        # Set active state on new card
        active_card = self.get_playslist_card(playlist_id)
        if active_card is not None:
            active_card.set_active(True)

        # Notify that focus has changed
        self.on_focus_change(playlist_id)

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

    def _on_loop_playlist(self, e):
        """Toggle loop for the active playlist"""
        playlist_id = self._active_tab_uuid
        if playlist_id:
            # Toggle the button color to show state
            if self.loop_button.icon_color == ft.Colors.OUTLINE:
                self.loop_button.icon_color = ft.Colors.PRIMARY
            else:
                self.loop_button.icon_color = ft.Colors.OUTLINE
            self.loop_button.update()
            self.on_loop_playlist(playlist_id)

    def _on_delete_playlist(self):
        """Handle delete playlist from menu"""
        playlist_id = self._active_tab_uuid
        if playlist_id:
            self.on_delete_playlist(playlist_id)

    def _on_paste_track(self):
        """Handle paste track from menu"""
        playlist_id = self._active_tab_uuid
        if playlist_id:
            self.on_paste_track(playlist_id)

    def _on_add_empty_playlist(self):
        """Handle create empty playlist from menu"""
        self.on_add_empty_playlist()

    def _on_add_from_spotify(self):
        """Handle import from Spotify from menu"""
        self.on_add_from_spotify()

    def enable_paste_track(self, enabled: bool):
        """Enable or disable the paste track menu item"""
        if hasattr(self, "menu_button") and self.menu_button.items:
            self.menu_button.items[0].disabled = not enabled
            self.menu_button.update()

    def _on_item_click(self, playlist_id: str, track_id: str):
        print(f"Item clicked in tab area: playlist={playlist_id}, track={track_id}")
        self.on_play(playlist_id, track_id)

    def on_play_button_click(self, e):
        self.on_play(self._active_tab_uuid, None)

    def toggle_play_button(self, is_playing: bool):
        self.play_button.icon = ft.Icons.PAUSE if is_playing else ft.Icons.PLAY_ARROW
        self.play_button.update()

    def toggle_loop_button(self, is_looping: bool):
        self.loop_button.icon_color = (
            ft.Colors.PRIMARY if is_looping else ft.Colors.OUTLINE
        )
        self.loop_button.update()

    def toggle_track_loop(self, track_id: str, is_looping: bool):
        playlist = self.get_active_playlist()
        playlist_item = playlist.get_track_item(track_id) if playlist else None
        if playlist_item:
            playlist_item.toggle_loop_style(is_looping)

    def toggle_body_header(self, visible: bool):
        self.body.controls[1].visible = visible
        self.body.update()

    def is_empty(self) -> bool:
        return len(self.playlist_stack.controls) == 0

    def _show_confirmation_dialog(self, title: str, message: str, on_confirm: Callable):
        """Show a confirmation dialog with the given title and message"""
        if not self.page:
            return

        def confirm_delete(e):
            on_confirm()
            dialog.open = False
            if self.page:
                self.page.update()

        def cancel_delete(e):
            dialog.open = False
            if self.page:
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def confirm_delete_playlist(self, playlist: PlaylistModel, on_confirm: Callable):
        """Show confirmation dialog for deleting a playlist"""
        self._show_confirmation_dialog(
            "Delete Playlist",
            f"Are you sure you want to delete '{playlist.name}'? This will remove all {playlist.size()} tracks from this playlist.",
            on_confirm,
        )

    def confirm_delete_track(self, track: TrackModel, on_confirm: Callable):
        """Show confirmation dialog for deleting a track"""
        self._show_confirmation_dialog(
            "Delete Track",
            f"Are you sure you want to delete '{track.title}' from this playlist?",
            on_confirm,
        )

    def update_ui_on_play(
        self,
        previous_playlist_model: PlaylistModel | None,
        previous_track: TrackModel | None,
        active_playlist_model: PlaylistModel,
        is_playing: bool,
    ):
        if active_playlist_model.id == self._active_tab_uuid:
            self.toggle_play_button(is_playing)

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

            now_playing.toggle_show_hide(True)

        # Update the entire playlist UI once after all highlights are set
        self.playlist_stack.update()

        if now_playing.current_track != new_track:
            self.now_playing.load_track_info(new_track)

        now_playing.play_pause_btn.icon = (
            ft.Icons.PAUSE_CIRCLE_FILLED if is_playing else ft.Icons.PLAY_CIRCLE_FILLED
        )
        now_playing.play_pause_btn.update()
