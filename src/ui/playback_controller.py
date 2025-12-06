from ui import AudioManager
from backend import TrackModel, PlaylistModel


class PlaybackController:
    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
        self.is_playing = False

    def play(self, track: TrackModel, seek: int = 0):
        """Start playing a track"""
        self.is_playing = True
        self.audio_manager.play_track(track.file_path, seek)

    def pause(self, current_position: int = 0) -> int:
        """Pause playback and return current position"""
        self.is_playing = False
        self.audio_manager.pause()
        return current_position

    def stop(self):
        """Stop playback completely"""
        if self.is_playing:
            self.pause()
        self.audio_manager.should_play = False

    def seek(self, position: int):
        """Seek to a position in the current track"""
        self.audio_manager.audio.seek(int(position))
