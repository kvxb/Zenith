from .track_model import TrackModel

class PlaylistModel:
	def __init__(self, name: str, tracks: list[TrackModel] = []):
		self.name = name
		self.tracks = tracks

	def add_track(self, track: TrackModel):
		self.tracks.append(track)

	def remove_track(self, track: TrackModel):
		self.tracks.remove(track)

	def total_duration(self) -> int:
		return sum(track.duration for track in self.tracks)

	def size(self) -> int:
		return len(self.tracks)

	def __repr__(self):
		return f"PlaylistModel(name={self.name}, tracks={self.tracks})"
