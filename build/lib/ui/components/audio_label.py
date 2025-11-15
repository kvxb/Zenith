import flet as ft
from flet_audio import Audio


class MusicListItem(ft.Container):
    """Music list item with number, name, author, album and timestamp"""
    def __init__(
        self, 
        number: int, 
        name: str, 
        author: str, 
        album: str, 
        duration: str,
        audio_src: str
    ):
        super().__init__()
        self.number = number
        self.name = name
        self.author = author
        self.album = album
        self.duration = duration
        self.audio_src = audio_src
        self.audio_player = None
        self.state = "stopped"
        
        # Container styling
        self.padding = 10
        self.border = ft.border.all(1, ft.Colors.GREY_400)
        self.border_radius = 5
        
        # Layout: [Number] [Play Button] [Name - Author] [Album] [Duration]
        self.content = ft.GestureDetector(
            content=ft.Row([
                self._number_text(),
                self._play_button(),
                self._name_author_column(),
                self._album_text(),
                self._duration_text(),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            on_tap=self.handle_play_click,
        )
    
    def _play_button(self):
        return ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.handle_play_click,
            tooltip="Play",
            icon_size=30,
        )
    
    def _number_text(self):
        return ft.Text(str(self.number), size=18, width=40, color=ft.Colors.GREY_600)
    
    def _name_author_column(self):
        return ft.Column([
            ft.Text(self.name, size=20, weight=ft.FontWeight.BOLD),
            ft.Text(self.author, size=20, color=ft.Colors.GREY_600),
        ], spacing=1, expand=True)
    
    def _album_text(self):
        return ft.Text(self.album, size=18, color=ft.Colors.GREY_700, width=150)
    
    def _duration_text(self):
        return ft.Text(self.duration, size=18, color=ft.Colors.GREY_600, width=60)
    
    def handle_play_click(self, e):
        if not self.audio_player:
            raise RuntimeError("Audio player is not initialized yet!")
        
        # Stop event propagation when clicking the button specifically
        if hasattr(e.control, 'icon'):
            e.stop_propagation = True
        
        match self.state:
            case "stopped" | "completed":
                self.audio_player.release()
                self.audio_player.resume()
            case "paused":
                self.audio_player.resume()
            case "playing":
                self.audio_player.pause()
    
    def did_mount(self):
        # Store reference to play button after content is created
        self.play_button = self.content.content.controls[1]
        
        self.audio_player = Audio(
            src=self.audio_src,
            autoplay=False,
            volume=1,
            release_mode="stop",
            on_state_changed=self.on_sound_change,
        )
        self.page.overlay.append(self.audio_player)
        self.page.update()
    
    def on_sound_change(self, e):
        state = e.data
        self.state = state
        
        if state == "playing":
            self.play_button.icon = ft.Icons.PAUSE
            self.play_button.tooltip = "Pause"
        elif state == "paused":
            self.play_button.icon = ft.Icons.PLAY_ARROW
            self.play_button.tooltip = "Play"
        elif state == "completed":
            self.play_button.icon = ft.Icons.REPLAY
            self.play_button.tooltip = "Replay"
        
        self.play_button.update()


class AudioLabel(ft.Container):
    """Reusable audio label component"""
    def __init__(self, label: str, audio_src: str):
        super().__init__()
        self.label = label
        self.audio_src = audio_src
        self.audio_player = None
        self.state = "stopped"  # Track state: "playing", "paused", "stopped", "completed"
        
        # Set container properties
        self.padding = 10
        self.border = ft.border.all(1, ft.Colors.GREY_400)
        self.border_radius = 1
        
        self.play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.handle_play_click,
            tooltip="Play",
            icon_size=30,
        )
        
        # Set container content immediately
        self.content = ft.GestureDetector(
            content=ft.Row([
                ft.Text(self.label, size=16),
                self.play_button,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
            on_tap=self.handle_play_click,
        )
    
    # Handle play button click
    def handle_play_click(self, e):
        if not self.audio_player:        
            raise RuntimeError("Audio player is not initialized yet!")
        
        # Stop event propagation when clicking the button specifically
        if hasattr(e.control, 'icon'):  # This is the IconButton
            e.stop_propagation = True
        
        match self.state:
            case "stopped" | "completed":
                print("Audio is stopped or completed - will play")
                self.audio_player.release()
                self.audio_player.resume()
            case "paused":
                print("Audio is paused - will resume")
                self.audio_player.resume()
            case "playing":
                print("Audio is playing - will pause")
                self.audio_player.pause()
    
    def toggle_button_state(self, playing: bool):
        if playing:
            self.play_button.icon = ft.Icons.PAUSE
            self.play_button.tooltip = "Pause"
        else:
            self.play_button.icon = ft.Icons.PLAY_ARROW
            self.play_button.tooltip = "Play"
        self.page.update()
    
    # Called when the component is added to the page
    def did_mount(self):
        print(f"AudioLabel mounted, creating audio player for: {self.audio_src}")
        
        self.audio_player = Audio(
            src=self.audio_src,
            autoplay=False,
            volume=1,
            release_mode="stop",
            on_state_changed=self.on_sound_change,
            on_loaded=lambda e: print(f"Audio loaded: {self.audio_src}"),
        )
        
        self.page.overlay.append(self.audio_player)
        self.page.update()
        print("Audio player added to overlay")
        
    def on_sound_change(self, e):
        """Called when audio state changes"""
        state = e.data
        self.state = state  # Store the state
        print(f"Audio state: {state}")
        
        if state == "playing":
            self.play_button.icon = ft.Icons.PAUSE
            self.play_button.tooltip = "Pause"
        elif state == "paused":
            self.play_button.icon = ft.Icons.PLAY_ARROW
            self.play_button.tooltip = "Play"
        elif state == "completed":
            print("Audio finished playing!")
            self.play_button.icon = ft.Icons.REPLAY
            self.play_button.tooltip = "Replay"
        
        self.play_button.update()
