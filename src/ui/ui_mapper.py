from src.backend import TrackModel, PlaylistModel
from src.ui.components import Playlist, PlaylistItem, PlaylistTabArea, PlaylistCard


class UiMapper:
    @staticmethod
    def play_list_item_from_track_model(track: TrackModel, number: int) -> PlaylistItem:
        return PlaylistItem(
            number=number,
            name=track.title,
            author=track.artist,
            album=track.album,
            duration=track.formatted_duration(),
        )

    @staticmethod
    def playlist_card_from_model(playlist_model: PlaylistModel) -> PlaylistCard:
        return PlaylistCard(
            name=playlist_model.name,
            count=playlist_model.size(),
            duration=playlist_model.total_duration(),
        )

    @staticmethod
    def playlist_from_model(playlist_model: PlaylistModel) -> Playlist:
        playlist = Playlist()
        for index, track in enumerate(playlist_model.tracks):
            item = UiMapper.play_list_item_from_track_model(track, index + 1)
            playlist.controls.append(item)
        return playlist

    @staticmethod
    def playlist_tab_area_from_models(playlists: list[PlaylistModel]) -> PlaylistTabArea:
        tab_area = PlaylistTabArea()
        for playlist_model in playlists:
            card = UiMapper.playlist_card_from_model(playlist_model)
            playlist = UiMapper.playlist_from_model(playlist_model)
            tab_area.add_playlist(card, playlist)
            
        print(tab_area.playlist_card_list.controls)
        return tab_area
