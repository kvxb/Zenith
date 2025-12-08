from .track_model import TrackModel


class PlaylistModel:
    def __init__(self, playlist_id: str, name: str, tracks: list[TrackModel] = [], icon: str = ""):
        self.id = playlist_id
        self.name = name
        self.track_dict = {track.id: track for track in tracks}
        self.track_order_list = [track.id for track in tracks]
        self.current_track_id = None
        self.icon = icon
        self.is_looping = False

    def has_track(self, track_id: str) -> bool:
        return track_id in self.track_dict

    def get_track(self, track_id: str) -> TrackModel | None:
        return self.track_dict.get(track_id)

    def add_track(self, track: TrackModel):
        if track.id in self.track_dict:
            return
        self.track_dict[track.id] = track
        self.track_order_list.append(track.id)

    def remove_track(self, track: TrackModel):
        self.track_dict.pop(track.id, None)

        if track.id == self.current_track_id:
            self.current_track_id = None

        if track.id in self.track_order_list:
            self.track_order_list.remove(track.id)

    def tracks(self):
        for track_id in self.track_order_list:
            yield self.track_dict[track_id]

    def total_duration(self) -> int:
        return sum(track.duration for track in self.track_dict.values())

    def size(self) -> int:
        return len(self.track_dict)

    def get_active_track(self) -> TrackModel | None:
        return self.get_track(self.current_track_id) if self.current_track_id else None

    def set_active_track(self, track_id: str | None):
        """Set the active track by ID. Pass None, 'first', or 'last' for special cases"""
        if track_id is None:
            if self.size() == 0:
                self.current_track_id = None
            else:
                self.current_track_id = self.track_order_list[0]
        elif track_id == "first":
            if self.size() == 0:
                self.current_track_id = None
            else:
                self.current_track_id = self.track_order_list[0]
        elif track_id == "last":
            if self.size() == 0:
                self.current_track_id = None
            else:
                self.current_track_id = self.track_order_list[-1]
        elif track_id in self.track_order_list:
            self.current_track_id = track_id
        return self.get_active_track()

    def pause(self, time_played: int):
        track = self.get_active_track()
        if track is not None:
            track.played_time = time_played
            pass

    def resume(self):
        track = self.get_active_track()
        if track is None:
            return self.move_to_next_track()
        elif track.played_time > track.duration * 1000:
            # elif track.played_time >= 1000000:
            print("Track finished, moving to next track")
            return self.move_to_next_track()
        else:
            return track

    def get_list_id_of_active_track(self) -> int | None:
        return (
            self.track_order_list.index(self.current_track_id)
            if self.current_track_id
            else None
        )

    def move_to_next_track(self) -> TrackModel | None:
        index = self.get_list_id_of_active_track()
        if index is None:
            return self.set_active_track("first")

        index += 1

        if index >= self.size():
            return self.set_active_track("first") if self.is_looping else None

        self.current_track_id = self.track_order_list[index]
        return self.get_active_track()

    def move_to_previous_track(self) -> TrackModel | None:
        index = self.get_list_id_of_active_track()
        if index is None:
            return self.set_active_track("first")

        index -= 1

        if index < 0:
            return self.set_active_track("last") if self.is_looping else None

        self.current_track_id = self.track_order_list[index]
        return self.get_active_track()

    def is_inactive(self) -> bool:
        return self.current_track_id is None

    def __repr__(self):
        return f"PlaylistModel(name={self.name}, tracks={self.track_dict})"
