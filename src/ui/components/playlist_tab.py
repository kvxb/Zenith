import flet as ft
from typing import Optional
from .playlist_card import PlaylistCard
from .playlist import Playlist


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
			expand=True,
		)

	def _library_label(self):
		return ft.Row(
			controls=[
				ft.TextField(
					value="My Library",
					expand=True),
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
		old_index = e.old_index
		new_index = e.new_index
		target = self.playlist_card_list
  
		if old_index is None or new_index is None:
			return

		element_to_move = target.controls.pop(old_index)
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
        	on_click=lambda e: self.on_play(None)
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
		self.body = ft.Column(
			controls=[
				self._body_header(),
				self._playlist_stack(),
			]
		)
		return self.body

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self._active_tab_uuid = ""
		self.on_play = lambda id: None
		self.on_shuffle = lambda new_uuids: None
		self.on_loop = lambda: None

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
		"""Add a card and playlist with matching UUID"""

		playlist_card.on_click = self._on_card_click
		playlist.on_card_click = self._on_item_click

		# Add to controls
		self.playlist_card_list.controls.append(playlist_card)
		self.playlist_stack.controls.append(playlist)

		# Hide playlist by default (show only when card is clicked)
		playlist.visible = False

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
		self._active_tab_uuid = playlist_id
		self.show_playlist(playlist_id)

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
		print(playlist)
		if playlist is None:
			return
		playlist.shuffle()
		self.on_shuffle(playlist.get_uuid_list())
  
	def _on_loop(self, e):
		self.on_loop()
  
	def _on_item_click(self, id: str):
		print(f"Item clicked in tab area: {id}")
		self.on_play(id)