from .track_model import TrackModel

class PlaylistModel:
	def __init__(self, playlist_id: str, name: str, tracks: list[TrackModel] = []):
		self.id = playlist_id
		self.name = name
		self.tracks = tracks
		self.current_track_index = 0

		self.is_looping = False

	def get_track(self, track_id: str) -> TrackModel | None:
		for track in self.tracks:
			if track.id == track_id:
				return track
		return None

	def add_track(self, track: TrackModel):
		self.tracks.append(track)

	def remove_track(self, track: TrackModel):
		self.tracks.remove(track)

	def total_duration(self) -> int:
		return sum(track.duration for track in self.tracks)

	def size(self) -> int:
		return len(self.tracks)

	def get_active_track(self) -> TrackModel | None:
		if not self.tracks:
			return None
		return self.tracks[self.current_track_index]

	def set_active_track(self, index: int):
		if 0 <= index < len(self.tracks):
			self.current_track_index = index
 
	def move_to_next_track(self) -> TrackModel | None:
		if not self.tracks:
			return None
		
		current_track = self.get_active_track()
		if current_track is None:
			self.set_active_track(0)
			return self.get_active_track()
		
		next_index = self.current_track_index + 1
		if next_index >= self.size():
			if self.is_looping:
				self.set_active_track(0)
			else:
				return None
		else:
			self.set_active_track(next_index)
   
		return self.get_active_track()

	def move_to_previous_track(self) -> TrackModel | None:
		if not self.tracks:
			return None
		
		current_track = self.get_active_track()
		if current_track is None:
			self.set_active_track(0)
			return self.get_active_track()
		
		prev_index = self.current_track_index - 1
		if prev_index < 0:
			if self.is_looping:
				self.current_track_index = self.size() - 1
			else:
				return None
		else:
			self.set_active_track(prev_index)
   
		return self.get_active_track()
	def __repr__(self):
		return f"PlaylistModel(name={self.name}, tracks={self.tracks})"
