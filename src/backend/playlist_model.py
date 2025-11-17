from .track_model import TrackModel

class PlaylistModel:
	def __init__(self, playlist_id: str, name: str, tracks: list[TrackModel] = []):
		self.id = playlist_id
		self.name = name
		self.track_dict = {track.id: track for track in tracks}
		self.track_order_list = [track.id for track in tracks]
		self.current_track_index = 0

		self.is_looping = False

	def get_track(self, track_id: str) -> TrackModel | None:
		return self.track_dict.get(track_id)

	def add_track(self, track: TrackModel):
		self.track_dict[track.id] = track
		self.track_order_list.append(track.id)

	def remove_track(self, track: TrackModel):
		self.track_dict.pop(track.id, None)

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
		return self.get_track(self.track_order_list[self.current_track_index])

	def pause(self, time_played: int):
		track = self.get_active_track()
		if track is not None:
			track.played_time = time_played
			pass
	
	def resume(self):
		track = self.get_active_track()
		if track is None:
			self.current_track_index = 0
			return self.get_active_track()
		elif track.played_time > track.duration:
			return self.move_to_next_track()

	def move_to_next_track(self) -> TrackModel | None:
		index = self.current_track_index + 1
		if index >= self.size():
			self.current_track_index = 0
			if not self.is_looping:
				return None
		else:
			self.current_track_index = index
   
		return self.get_active_track()

	def move_to_previous_track(self) -> TrackModel | None:
		index = self.current_track_index - 1
		if index < 0:
			self.current_track_index = self.size() - 1
			if not self.is_looping:
				return None
		else:
			self.current_track_index = index
   
		return self.get_active_track()

	def __repr__(self):
		return f"PlaylistModel(name={self.name}, tracks={self.track_dict})"
