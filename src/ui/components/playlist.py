import flet as ft
import uuid
import random
from .playlist_item import PlaylistItem

class Playlist(ft.ReorderableListView):
	def __init__(self, playlist_id: str = "", **kwargs):
		super().__init__(**kwargs)
		self.id = playlist_id if playlist_id else str(uuid.uuid4())
		self.on_reorder = self._on_reorder
		self.visible = True
		self.padding = ft.padding.only(right=10)
  
		self.on_card_click = lambda id: print(f"Clicked on item with id: {id}")

	def append(self, item: PlaylistItem):
		self.controls.append(item)
		# Make item's callback forward to the Playlist's callback
		item.on_card_click = lambda id: self.on_card_click(id)

	def shuffle(self):
		random.shuffle(self.controls)
		self.update()
	
	def get_uuid_list(self) -> list[str]:
		uuid_list = []
		for item in self.controls:
			if isinstance(item, PlaylistItem):
				uuid_list.append(item.id)

		return uuid_list
		
	def _on_reorder(self, e: ft.OnReorderEvent):
		old_index = e.old_index
		new_index = e.new_index
  
		print(f"Reorder from {e.old_index} to {e.new_index}")
		if old_index is None or new_index is None:
			return

		element_to_move = self.controls.pop(old_index)
		self.controls.insert(new_index, element_to_move)
		self.update()

