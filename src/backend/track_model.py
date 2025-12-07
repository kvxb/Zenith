from __future__ import annotations

class TrackModel:
    def __init__(
        self,
        track_id: str,
        title: str,
        artist: str,
        album: str,
        duration: int,
        file_path: str,
        image_path: str = "",
        is_copy: bool = False,
        position: int = 0,
    ):
        self.id = track_id
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration  # duration in seconds
        self.file_path = file_path
        self.image_path = image_path
        self.position = position
        self.copy_of = None

        self.is_looping = False
        self.played_time = 0
    
    def formatted_duration(self) -> str:
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02}"


    def clone(self, source: TrackModel) -> TrackModel:
        new_track = TrackModel(
            track_id=self.id,
            title=self.title,
            artist=self.artist,
            album=self.album,
            duration=self.duration,
            file_path=self.file_path,
            image_path=self.image_path,
            is_copy=True,
            position=self.position,
        )
        new_track.copy_of = source

        return new_track

    def __repr__(self):
        return f"TrackModel(title={self.title}, artist={self.artist}, album={self.album}, duration={self.duration}, file_path={self.file_path}, position={self.position})"
