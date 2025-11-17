import flet as ft
import uuid
from .playlist_item import PlaylistItem

class Playlist(ft.ReorderableListView):
	def __init__(self, playlist_id: str = "", **kwargs):
		super().__init__(**kwargs)
		self.id = playlist_id if playlist_id else str(uuid.uuid4())
		self.on_reorder = self._on_reorder
		self.visible = True
		self.padding = ft.padding.only(right=10)

	def append(self, item: PlaylistItem):
		self.controls.append(item)

	def _on_reorder(self, e: ft.OnReorderEvent):
		return

