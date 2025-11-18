import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import flet as ft
import uuid
from flet_audio import Audio
from src.ui import PlaylistManager
from src.backend import TrackModel, PlaylistModel

random_tracks = [
	TrackModel(track_id=str(uuid.uuid4()), title="One Piece", artist="Eiichiro Oda", album="Shonen Jump", duration=234, file_path="Saika.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Gorosei Theme", artist="Kohei Tanaka", album="One Piece OST", duration=198, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Luffy's Awakening", artist="Kohei Tanaka", album="Wano Arc", duration=312, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Zoro vs King", artist="Shiro Hamaguchi", album="One Piece Film Red", duration=276, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Gear 5", artist="Kohei Tanaka", album="Egghead Arc", duration=189, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Nika Drums", artist="Shiro Hamaguchi", album="One Piece OST", duration=245, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Shanks Arrival", artist="Kohei Tanaka", album="Film Red", duration=167, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Going Merry", artist="Kohei Tanaka", album="Water 7 Arc", duration=298, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Overtaken", artist="Kohei Tanaka", album="Enies Lobby", duration=223, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="The Very Strongest", artist="Shiro Hamaguchi", album="Marineford", duration=267, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="Binks Sake", artist="Brook", album="Thriller Bark", duration=178, file_path="gorosei.mp3"),
	TrackModel(track_id=str(uuid.uuid4()), title="We Are!", artist="Hiroshi Kitadani", album="Opening 1", duration=142, file_path="gorosei.mp3"),
]

# Create test playlists
playlist1 = PlaylistModel(
	playlist_id=str(uuid.uuid4()),
	name="Straw Hat Crew",
	tracks=[
		random_tracks[0],  # One Piece
		random_tracks[4],  # Gear 5
		random_tracks[10], # Binks Sake
		random_tracks[11], # We Are!
	]
)

playlist2 = PlaylistModel(
	playlist_id=str(uuid.uuid4()),
	name="Epic Battles",
	tracks=[
		random_tracks[1],  # Gorosei Theme
		random_tracks[2],  # Luffy's Awakening
		random_tracks[3],  # Zoro vs King
		random_tracks[5],  # Nika Drums
		random_tracks[9],  # The Very Strongest
	]
)

playlist3 = PlaylistModel(
	playlist_id=str(uuid.uuid4()),
	name="Emotional Moments",
	tracks=[
		random_tracks[6],  # Shanks Arrival
		random_tracks[7],  # Going Merry
		random_tracks[8],  # Overtaken
	]
)

test_playlists = [playlist1, playlist2, playlist3]


def main(page: ft.Page):
	page.title = "Zenith"
	
	playlist_manager = PlaylistManager(test_playlists)
	playlist_manager.add_to_page(page)
	
	# playlist_manager.audio_manager.play_track("Saika.mp3")
	# # Create PlaylistTabArea with test playlists
	# tab_area = UiMapper.playlist_tab_area_from_models(test_playlists)
	
	# page.add(
	#     ft.Container(
	#         content=tab_area,
	#         expand=True,
	#     )
	# )


if __name__ == "__main__":
	ft.app(main, assets_dir="assets", port=8550)
