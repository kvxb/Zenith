import flet as ft


class PlaylistCard(ft.Card):
	def __init__(self, playlist_id: str, name: str, count: int, duration: int, **kwargs):
		super().__init__(**kwargs)
		self.id = playlist_id
		self.name = name
		self.count = count
		self.duration = duration
		self.on_click = lambda id: print(id)
  
		self.inner_row = ft.Row(
				controls=[
					ft.Column(
						[
							ft.Text(self.name, size=20, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
							ft.Text(f"{self.count} tracks • {self.format_duration()}", size=14, color=ft.Colors.GREY_600, overflow=ft.TextOverflow.ELLIPSIS),
						],
						alignment=ft.MainAxisAlignment.START,
						expand=True,
						spacing=5,
					)
				],
				spacing=10,
				vertical_alignment=ft.CrossAxisAlignment.CENTER,
			)
  
		self.content = ft.Container(
			content=self.inner_row,
			padding=ft.padding.all(10),
			on_click=lambda e: self.on_click(self.id),
		)

	def format_duration(self) -> str:
		minutes, seconds = divmod(self.duration, 60)
		hours, minutes = divmod(minutes, 60)
		if hours > 0:
			return f"{hours}h {minutes}m {seconds}s"
		else:
			return f"{minutes}m {seconds}s"

	def __repr__(self):
		return f"PlaylistCard(id={self.id}, name={self.name}, count={self.count}, duration={self.duration})"