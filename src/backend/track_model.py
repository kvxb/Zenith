
class TrackModel:
	def __init__(self, title: str, artist: str, album: str, duration: int, file_path: str):
		self.title = title
		self.artist = artist
		self.album = album
		self.duration = duration  # duration in seconds
		self.file_path = file_path

	def formatted_duration(self) -> str:
		minutes = self.duration // 60
		seconds = self.duration % 60
		return f"{minutes}:{seconds:02}"

	def __repr__(self):
		return f"TrackModel(title={self.title}, artist={self.artist}, album={self.album}, duration={self.duration}, file_path={self.file_path})"
  