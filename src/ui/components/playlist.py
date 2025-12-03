import flet as ft
import uuid
import random
from .playlist_item import PlaylistItem


class Playlist(ft.ReorderableListView):
    def __init__(self, playlist_id: str = "", **kwargs):
        super().__init__(**kwargs)
        self.id = playlist_id if playlist_id else str(uuid.uuid4())
        self.visible = True
        self.padding = ft.padding.only(right=10)

        self.on_card_click = lambda id: print(f"ERROR Clicked on item with id: {id}")
        self.on_reorder_callback = lambda id, old_idx, new_idx: print(
            f"ERROR Reorder from {old_idx} to {new_idx}"
        )

        self.on_reorder = self._on_reorder

    def append(self, item: PlaylistItem):
        self.controls.append(item)
        item.on_card_click = lambda id: self.on_card_click(id)

    def shuffle(self):
        random.shuffle(self.controls)
        self.update()

        print("Playlist shuffled")
        self.on_reorder_callback(self.id, None, None)

    def get_uuid_list(self) -> list[str]:
        uuid_list = []
        for item in self.controls:
            if isinstance(item, PlaylistItem):
                uuid_list.append(item.id)

        return uuid_list

    def _on_reorder(self, e: ft.OnReorderEvent):
        old_index = e.old_index or 0
        new_index = e.new_index or 0
        print(f"Reordering from {old_index} to {new_index}")
        element_to_move = self.controls[old_index]
        self.controls.insert(new_index, self.controls.pop(old_index))

        if isinstance(element_to_move, PlaylistItem):
            # Use a property that belongs to the PlaylistItem control itself
            element_to_move.on_card_click = lambda id: self.on_card_click(id)

        self.on_reorder_callback(self.id, old_index, new_index)
        # self.update()

    def get_track_item(self, track_id: str) -> PlaylistItem | None:
        for item in self.controls:
            if isinstance(item, PlaylistItem) and item.id == track_id:
                return item
        return None
