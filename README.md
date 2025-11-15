# Zenith

## Introduction

A Python application that enables users to download their Spotify
playlists as local MP3 files and provides an ad-free offline music
player. The system bridges Spotify's streaming service with local music
ownership, giving users permanent access to their favorite playlists
without subscription dependencies.

### Target Users:

-   Music enthusiasts wanting offline access to Spotify playlists
-   Users in areas with poor internet connectivity
-   Privacy-conscious individuals avoiding cloud streaming
-   People who oppose the monthly subscription model

## System Overview

### Frontend

The Flet framework is used to create a fast and reactive interface that
runs on desktop or the web. The interface displays the downloaded
playlists and songs and manages the playback controls.

### Backend

Implemented in Python, this component manages:

**Downloading:** It interacts with external sources (via specific APIs
or scraping libraries, not declared here for legal reasons) to retrieve
playlist information and, subsequently, the audio files.\
**Database:** A simple SQLite or JSON/YAML file is used to store the
metadata (title, artist, duration, cover art) of the downloaded songs
and playlists, as well as the local path to the audio file.\
**Audio Playback:** The Flet Audio library (or an auxiliary Python
library like pygame or pydub if Flet Audio is insufficient) is used to
play the locally stored MP3 files.

## Detailed Component Design

### 1. User Interface

The Frontend is built using the Flet framework, providing a fast,
reactive, and cross-platform user interface (desktop and web). This
component is responsible for all visual elements and user interactions.
It is composed of separate UI controls for displaying the available
playlists, presenting the list of tracks within a selected playlist, and
offering persistent playback controls (Play/Pause/Skip). The UI controls
act as ViewModels in an MVVM pattern, managing local state and
triggering requests to the backend for data retrieval (e.g., getting the
track list from the database) or initiating audio playback. User
selections (e.g., clicking a track) interface with the Playback module
to start playing the selected file.

### 2. External Data Management

This backend component manages all secure interactions with the Spotify
Web API. It's primarily responsible for authentication (handling the
necessary OAuth 2.0 flow to acquire and manage access tokens) and
metadata extraction. Upon receiving a valid Spotify playlist URL, this
component makes secure HTTPS requests to the Spotify API, retrieves
structured data (title, artist, duration, cover art URL) for all tracks
in the playlist, and passes this metadata forward to the Database and
Download components for persistence and processing. It uses standard
Python HTTP libraries for communication.

### 3. Database Management

The Database Management component provides the application's data
persistence layer, utilizing a local SQLite file. This module is
implemented as a central service responsible for all CRUD (Create, Read,
Update, Delete) operations. It stores the metadata received from the
Spotify component, crucially linking it with the local file path
provided by the Download component. It exposes methods for other parts
of the application to retrieve lists of playlists, fetch all tracks
associated with a given playlist, and query individual track details.
This component serves as the single source of truth for the
application's music library.

### 4. Download and File Management

This component's core function is to coordinate the safe acquisition and
storage of the audio files. It receives track metadata (title, artist)
from the Spotify API component and manages the external communication
(via HTTPS to external sources, specific details omitted) to locate and
download the audio file. After successfully saving the audio file to the
local disk using the yt-dlp API, this module communicates with the
Database Management component to register the file's local storage path,
completing the track record. It also handles local directory management
for organizing the downloaded content.

### 5. Audio Playback Subsystem

This component handles the actual playing of music and is built around
the core Flet Audio control, instantiated and added to the application's
page overlay. It receives the local file path from the Frontend when a
user selects a song. Its primary responsibilities include loading the
file, executing playback commands (Play, Pause), and tracking playback
progress. Crucially, it must expose event handlers to notify the
Frontend's Playback Controls when a track finishes, allowing the
application to seamlessly transition and load the next song in the
playlist.

## Deployment and Testing

Deployment requirements are split by target. For desktop distribution,
Flet natively handles packaging into self-contained executables. For web
deployment (PWA), Docker can be used to containerize the Python backend,
Flet runner, ensuring a consistent and reliable environment for cloud
hosting or local sharing.

For the testing phase we will first manually test our product during the
development process and after finishing it we will conduct a performance
test using huge playlists to measure the time cost of the downloading
process.

## Conclusion

In conclusion, our project is built for users who want to leave the
monthly payment scheme of audio streaming apps such as Spotify. By
making the process as friendly as possible, the user is required to have
a working Spotify account with playlists containing the songs they want
to listen to, and we'll handle the rest using the APIs provided by
Spotify and yt-dlp.
