from backend.track_model import TrackModel
import flet as ft
import time

# asyncio is no longer needed since we removed the async loop


class NowPlaying(ft.Container):
    def __init__(self):
        super().__init__()

        self.current_track: TrackModel | None = None
        self.on_play_pause_click = lambda state: None
        self.on_next_click = lambda: None
        self.on_previous_click = lambda: None
        self.on_slider_end = lambda position: None

        self.is_dragging_slider = (
            False  # Still used to ignore external updates during drag
        )

        # Removed all synchronization properties (_last_position_ms, _last_update_time, _is_running)

        # --- UI Initialization (Controls) ---
        self.title_text = ft.Text(
            "No Track Loaded",
            weight=ft.FontWeight.BOLD,
            size=14,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.artist_text = ft.Text(
            "N/A", size=10, color=ft.Colors.GREY_500, overflow=ft.TextOverflow.ELLIPSIS
        )
        self.track_info_col = ft.Column(
            controls=[self.title_text, self.artist_text],
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
        self.current_time_text = ft.Text("0:00", size=10)
        self.duration_time_text = ft.Text("0:00", size=10, color=ft.Colors.GREY_500)

        self.position_slider = ft.Slider(
            min=0,
            max=180000,
            value=0,
            active_color=ft.Colors.CYAN_400,
            inactive_color=ft.Colors.GREY_700,
            on_change=self._on_change,
            on_change_end=self._slider_scrub_end,
            on_change_start=lambda e: self._on_slider_start(e),
            expand=True,
        )
        self.previous_btn = ft.IconButton(
            icon=ft.Icons.SKIP_PREVIOUS_ROUNDED,
            icon_size=24,
            on_click=lambda e: (
                self.on_previous_click() if self.on_previous_click else None
            ),
        )
        self.play_pause_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED,
            icon_size=36,
            on_click=lambda e: (
                self.on_play_pause_click("playing")
                if self.on_play_pause_click
                else None
            ),
        )
        self.next_btn = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT_ROUNDED,
            icon_size=24,
            on_click=lambda e: self.on_next_click() if self.on_next_click else None,
        )

        self.controls_row = ft.Row(
            controls=[self.previous_btn, self.play_pause_btn, self.next_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )
        self.main_content_row = ft.Row(
            controls=[self.track_info_col, self.controls_row],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        self.time_slider_row = ft.Row(
            controls=[
                self.current_time_text,
                self.position_slider,
                self.duration_time_text,
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
            height=25,
        )

        self.content = ft.Column(
            controls=[self.time_slider_row, self.main_content_row],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

        self.padding = ft.padding.only(left=15, right=15, top=5, bottom=5)
        self.bgcolor = ft.Colors.BLUE_GREY_900
        self.visible = True
        self.height = 0
        self.animate_size = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        # --- End of UI Initialization ---

    def toggle_show_hide(self, show: bool):
        self.height = 90 if show else 0
        self.update()

    def _format_time(self, milliseconds: float) -> str:
        """Converts total milliseconds to a minutes:seconds string."""
        total_seconds = int(milliseconds // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def _on_change(self, e: ft.ControlEvent):
        self.update_playback_position(int(e.control.value))
        self.is_dragging_slider = False
        self.on_slider_end(int(e.control.value))

    def _slider_scrub_end(self, e: ft.ControlEvent):
        value = int(e.control.value)

        self.is_dragging_slider = False
        self.update_playback_position(value)

    def _on_slider_start(self, e: ft.ControlEvent):
        self.is_dragging_slider = True

    def seek_complete(self):
        self.is_dragging_slider = False

    def update_playback_position(self, current_time_miliseconds: int):
        if self.current_track is None or self.is_dragging_slider:
            return

        # Prevent updates if page is no longer available
        if not self.page:
            return

        self.current_time_text.value = self._format_time(current_time_miliseconds)
        self.position_slider.value = float(current_time_miliseconds)

        try:
            self.current_time_text.update()
            self.position_slider.update()
        except:
            # Ignore errors if page is shutting down
            pass

    def load_track_info(self, track: TrackModel):
        self.current_track = track

        self.title_text.value = track.title
        self.artist_text.value = track.artist
        self.position_slider.max = track.duration * 1000
        self.duration_time_text.value = track.formatted_duration()
        self.position_slider.value = 0
        self.current_time_text.value = "0:00"
        self.play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED

        self.toggle_show_hide(True)
        self.update()
