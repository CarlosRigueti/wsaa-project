from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spotify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class SpotifyTrack(db.Model):
    id = db.Column(db.String, primary_key=True)
    track_name = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, nullable=False)
    album = db.Column(db.String)
    release_date = db.Column(db.String)
    popularity = db.Column(db.Integer)
    spotify_url = db.Column(db.String)
    duration_min = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id,
            "track_name": self.track_name,
            "artist": self.artist,
            "album": self.album,
            "release_date": self.release_date,
            "popularity": self.popularity,
            "spotify_url": self.spotify_url,
            "duration_min": self.duration_min
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    tracks = SpotifyTrack.query.all()
    return jsonify([t.to_dict() for t in tracks])

@app.route('/api/tracks', methods=['POST'])
def create_track():
    data = request.json
    if SpotifyTrack.query.get(data['id']):
        return jsonify({"error": "Track with this ID already exists."}), 400
    new_track = SpotifyTrack(
        id=data['id'],
        track_name=data['track_name'],
        artist=data['artist'],
        album=data.get('album'),
        release_date=data.get('release_date'),
        popularity=data.get('popularity'),
        spotify_url=data.get('spotify_url'),
        duration_min=data.get('duration_min')
    )
    db.session.add(new_track)
    db.session.commit()
    return jsonify(new_track.to_dict()), 201

@app.route('/api/tracks/<track_id>', methods=['PUT'])
def update_track(track_id):
    track = SpotifyTrack.query.get_or_404(track_id)
    data = request.json
    track.track_name = data.get('track_name', track.track_name)
    track.artist = data.get('artist', track.artist)
    track.album = data.get('album', track.album)
    track.release_date = data.get('release_date', track.release_date)
    track.popularity = data.get('popularity', track.popularity)
    track.spotify_url = data.get('spotify_url', track.spotify_url)
    track.duration_min = data.get('duration_min', track.duration_min)
    db.session.commit()
    return jsonify(track.to_dict())

@app.route('/api/tracks/<track_id>', methods=['DELETE'])
def delete_track(track_id):
    track = SpotifyTrack.query.get_or_404(track_id)
    db.session.delete(track)
    db.session.commit()
    return '', 204

def import_csv_to_db():
    if SpotifyTrack.query.first():
        print("Data already imported.")
        return
    if not os.path.exists('spotify_top_1000_tracks.csv'):
        print("CSV file not found.")
        return
    df = pd.read_csv('spotify_top_1000_tracks.csv')
    for _, row in df.iterrows():
        track = SpotifyTrack(
            id=row['id'],
            track_name=row['track_name'],
            artist=row['artist'],
            album=row.get('album', ''),
            release_date=str(row.get('release_date', '')),
            popularity=int(row.get('popularity', 0)),
            spotify_url=row.get('spotify_url', ''),
            duration_min=float(row.get('duration_min', 0))
        )
        db.session.add(track)
    db.session.commit()
    print("Import completed.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import_csv_to_db()
    app.run(debug=True)
