import os
import subprocess
import sys


# Configuration
APP_NAME = "zenith"
PACKAGE_DIR = "debian_package"
APP_SHARE_PATH = os.path.join(PACKAGE_DIR, "usr/share/zenith")
APP_BIN_PATH = os.path.join(PACKAGE_DIR, "usr/bin/zenith")
DESKTOP_FILE_PATH = os.path.join(PACKAGE_DIR, "usr/share/applications/zenith.desktop")
DEBIAN_DIR = os.path.join(PACKAGE_DIR, "DEBIAN")
CONTROL_FILE_PATH = os.path.join(DEBIAN_DIR, "control")
POSTINST_FILE_PATH = os.path.join(DEBIAN_DIR, "postinst")
EXEC_LOCATION = "/usr/bin/zenith"

DESCRIPTION = (
    "Zenith Music Player is a portable music player built using the Flet framework."
)

DEPENDENCIES = [
    "ffmpeg",
    "mpv",
    "libmpv1",
    "libgtk-3-0",
    "libgstreamer1.0-0",
    "libgstreamer-plugins-base1.0-0",
    "gstreamer1.0-plugins-good",
    "gstreamer1.0-plugins-ugly",
    "gstreamer1.0-libav",
    "gstreamer1.0-pulseaudio",
]

FLET_DEPENDENCIES = [
    "flet==0.28.3",
    "flet-audio==0.1.0",
    "spotipy",
    "yt-dlp",
    "mutagen",
]

DEVELOPERS = [
    {"name": "Curca Mihai Mihnea", "email": ""},
    {"name": "Tudor Biciusca", "email": ""},
]


# Ensure directory structure
os.makedirs(APP_SHARE_PATH, exist_ok=True)
os.makedirs(os.path.dirname(APP_BIN_PATH), exist_ok=True)
os.makedirs(os.path.dirname(DESKTOP_FILE_PATH), exist_ok=True)
os.makedirs(DEBIAN_DIR, exist_ok=True)


def get_authors():
    return ", ".join([f"{dev['name']} <{dev['email']}>" for dev in DEVELOPERS])


# Example: Write a minimal control file
def write_control(version, installed_size):
    maintainer = ", ".join([f"{dev['name']} <{dev['email']}>" for dev in DEVELOPERS])
    depends = ", ".join(DEPENDENCIES)
    with open(CONTROL_FILE_PATH, "w") as f:
        f.write(
            f"""Package: {APP_NAME}
Version: {version}
Section: multimedia
Priority: optional
Architecture: amd64
Maintainer: {maintainer}
Installed-Size: {installed_size}
Depends: {depends}
Description: {DESCRIPTION}
"""
        )


# Example: Write a minimal desktop file
def write_desktop():
    with open(DESKTOP_FILE_PATH, "w") as f:
        f.write(
            f"""[Desktop Entry]
Name={APP_NAME.capitalize()} Music Player
Comment={DESCRIPTION}
Exec={APP_BIN_PATH.replace(PACKAGE_DIR, '')}
Terminal=false
Type=Application
Icon={APP_NAME}
Categories=AudioVideo;Player;
"""
        )


def write_startup_script():
    startup_script_path = os.path.join(PACKAGE_DIR, "usr/bin", APP_NAME)
    with open(startup_script_path, "w") as f:
        f.write(
            f"""#!/bin/sh
cd {EXEC_LOCATION}
exec ./{APP_NAME} "$@"
"""
        )
    os.chmod(startup_script_path, 0o755)


# Example: Write a minimal postinst script
def write_postinst():
    with open(POSTINST_FILE_PATH, "w") as f:
        f.write(
            """#!/bin/sh
update-desktop-database /usr/share/applications/
gtk-update-icon-cache -f /usr/share/icons/hicolor || true
"""
        )
    os.chmod(POSTINST_FILE_PATH, 0o755)


# Example: Write a minimal pyproject.toml file
def write_project_toml(version):
    authors = ",\n     ".join(
        [f'"{dev["name"]} <{dev["email"]}>"' for dev in DEVELOPERS]
    )
    dependencies = ",\n    ".join([f'"{dep}"' for dep in FLET_DEPENDENCIES])

    with open("pyproject.toml", "w") as f:
        f.write(
            f"""[project]
name = "{APP_NAME}-music-player"
version = "{version}"
description = "{DESCRIPTION}"
readme = "README.md"
requires-python = ">=3.9"
authors = [
    {authors}
]
dependencies = [
  {dependencies}
]

[tool.flet]
org = "com.zenith"
product = "Zenith"
company = "Zenith"
copyright = "Copyright (C) 2025 by Zenith"

[tool.flet.app]
path = "src"
module = "main"
icon = "src/assets/logo.png"
assets = ["src/assets"]

[tool.poetry]
package-mode = false

[tool.poetry.group.dev.dependencies]
flet = {{extras = ["all"], version = "0.28.3"}}
"""
        )


if __name__ == "__main__":
    argc = len(sys.argv)
    if argc > 3:
        print("Usage: python setup_deb.py <part> <data>")
        sys.exit(1)

    part = sys.argv[1]
    data = sys.argv[2] if argc == 3 else ""

    if part == "flet-config":
        write_project_toml(data)
        print("pyproject.toml generated.")
        sys.exit(0)

    if part == "deb-config":

        write_control(
            data,
            subprocess.getoutput(f"du -s {os.path.join(PACKAGE_DIR, 'usr')} | cut -f1"),
        )
        write_desktop()
        write_postinst()
        write_startup_script()
        print("Debian package config files generated.")
        sys.exit(0)

    if part == "package-file-name":
        package_file_name = f"{APP_NAME}_{data}_amd64.deb"
        print(package_file_name)
        sys.exit(0)

    if part == "target-path":
        print(APP_BIN_PATH)
        sys.exit(0)

    if part == "package-dir":
        print(PACKAGE_DIR)
        sys.exit(0)

    if part == "app-name":
        print(APP_NAME)
        sys.exit(0)
