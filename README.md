# Spotify Tracks Project - Flask RESTful API

## Requirements

- Python 3.8+
- pip

## Installation

1. Clone this repository

2. Copy `spotify_top_1000_tracks.csv` to the project root folder

3. Install dependencies:

   pip install -r requirements.txt

4. Run the Flask server:

   python app.py

5. Open in your browser:

   [http://localhost:5000]

---

## Features

- View tracks list
- Create, edit, delete tracks
- Rate tracks with emojis
- Data persisted in SQLite database (`tracks.db`)

---

## Notes

- On first run, CSV is imported into database.
- Edit CSV before first run to change initial data.
- To reset database, delete `tracks.db`.