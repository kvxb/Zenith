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

        self.on_card_click = lambda track_id: print(
            f"ERROR Clicked on item with id: {track_id}"
        )
        self.on_reorder_callback = lambda id, old_idx, new_idx: print(
            f"ERROR Reorder from {old_idx} to {new_idx}"
        )
        self.on_delete_track = lambda track_id: print(f"ERROR Delete track {track_id}")
        self.on_copy_track = lambda track_id: print(f"ERROR Copy track {track_id}")
        self.on_loop_track = lambda track_id: print(f"ERROR Loop track {track_id}")

        self.on_reorder = self._on_reorder

    def append(self, item: PlaylistItem):
        self.controls.append(item)
        item.on_card_click = lambda track_id: self.on_card_click(track_id)
        item.on_delete = lambda track_id: self.on_delete_track(track_id)
        item.on_copy = lambda track_id: self.on_copy_track(track_id)
        item.on_loop = lambda track_id: self.on_loop_track(track_id)

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

        if e.old_index is None or e.new_index is None:
            return

        element_to_move = self.controls.pop(old_index)
        self.update()
        self.controls.insert(new_index, element_to_move)
        self.update()

        self.on_reorder_callback(self.id, old_index, new_index)

    def get_track_item(self, track_id: str) -> PlaylistItem | None:
        for item in self.controls:
            if isinstance(item, PlaylistItem) and item.id == track_id:
                return item
        return None

    def get_track_items(self):
        for item in self.controls:
            if isinstance(item, PlaylistItem):
                yield item

    def remove_track_item(self, track_id: str):
        """Remove a track item and renumber all remaining items"""
        control: PlaylistItem
        for i, item in enumerate(self.get_track_items()):
            if item.id == track_id:
                self.controls.pop(i)
                break

        # Renumber all items
        self.renumber_all_items()
        self.update()

    def add_track_item(self, item: PlaylistItem):
        """Add a track item and renumber all items"""
        self.append(item)
        self.renumber_all_items()
        self.update()

    def renumber_all_items(self):
        """Update the number on all PlaylistItems"""
        for i, control in enumerate(self.controls):
            if isinstance(control, PlaylistItem):
                control.number = i + 1
                control.number_text_control.value = str(i + 1)
