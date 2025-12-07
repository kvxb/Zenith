import flet as ft


class AddTrackForm(ft.AlertDialog):
    """Form dialog for adding a track by name and artist"""

    def __init__(self, on_submit=None):
        self.on_submit_callback = on_submit or (lambda name, artist: None)

        # Input fields
        self.track_name_field = ft.TextField(
            label="Track Name",
            hint_text="Enter track name",
            autofocus=True,
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
        )

        self.artist_field = ft.TextField(
            label="Artist",
            hint_text="Enter artist name",
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
        )

        # Success/Failure message components
        self.message_icon = ft.Icon(name=ft.Icons.CHECK_CIRCLE, size=20)
        self.message_text = ft.Text("", size=14, expand=True)

        # Success/Failure message
        self.message_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self.message_icon,
                    self.message_text,
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.all(10),
            border_radius=5,
            visible=False,
        )

        super().__init__(
            modal=True,
            title=ft.Text("Add Track", weight=ft.FontWeight.BOLD, size=20),
            content=ft.Column(
                controls=[
                    self.message_bar,
                    self.track_name_field,
                    self.artist_field,
                ],
                width=400,
                spacing=15,
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._on_cancel,
                ),
                ft.ElevatedButton(
                    "Add Track",
                    icon=ft.Icons.ADD,
                    on_click=self._on_add_track,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_add_track(self, e):
        """Handle add track button click"""
        track_name = self.track_name_field.value
        artist = self.artist_field.value

        track_name = track_name.strip() if track_name else ""
        artist = artist.strip() if artist else ""
        if not track_name:
            self._show_message("Please enter a track name", success=False)
            return

        if not artist:
            self._show_message("Please enter an artist name", success=False)
            return

        # Call the callback
        try:
            result = self.on_submit_callback(track_name, artist)
            print(f"AddTrackForm: on_submit returned {result}")
            # If callback returns False, show error; otherwise success
            if result is False:
                self._show_message(
                    f"Failed to add '{track_name}' by {artist}. Track not found",
                    success=False,
                )
            else:
                self._show_message(
                    f"Successfully added '{track_name}' by {artist}", success=True
                )
                # Close dialog after brief delay to show success message
                if self.page:
                    self.page.run_task(self._delayed_close)
        except Exception as ex:
            self._show_message(f"Error: {str(ex)}", success=False)

    async def _delayed_close(self):
        """Close the dialog after a brief delay"""
        import asyncio

        await asyncio.sleep(1.5)
        self._close_dialog()

    def _on_cancel(self, e):
        """Handle cancel button click"""
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog and reset form"""
        self.open = False
        self.track_name_field.value = ""
        self.artist_field.value = ""
        self.message_bar.visible = False
        if self.page:
            self.page.update()

    def _show_message(self, message: str, success: bool = True):
        """Show success or failure message"""
        if success:
            self.message_icon.name = ft.Icons.CHECK_CIRCLE
            self.message_icon.color = ft.Colors.PRIMARY
            self.message_bar.bgcolor = ft.Colors.SURFACE
            self.message_bar.border = ft.border.all(1, ft.Colors.PRIMARY)
        else:
            self.message_icon.name = ft.Icons.ERROR
            self.message_icon.color = ft.Colors.ERROR
            self.message_bar.bgcolor = ft.Colors.ERROR_CONTAINER
            self.message_bar.border = ft.border.all(1, ft.Colors.ERROR)

        self.message_text.value = message
        self.message_text.color = ft.Colors.ON_SURFACE
        self.message_bar.visible = True

        if self.page:
            self.page.update()

    def show(self, page):
        """Show the dialog on the page"""
        self.open = True
        page.overlay.append(self)
        page.update()
