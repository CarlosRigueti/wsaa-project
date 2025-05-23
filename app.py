import uuid
from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from marshmallow import Schema, fields, ValidationError
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///spotify.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret')

db = SQLAlchemy(app)

playlist_tracks = db.Table('playlist_tracks',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id')),
    db.Column('track_id', db.String, db.ForeignKey('spotify_tracks.id'))
)

class SpotifyTrack(db.Model):
    __tablename__ = 'spotify_tracks'
    id = db.Column(db.String, primary_key=True)
    track_name = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, nullable=False)
    album = db.Column(db.String)
    release_date = db.Column(db.String)
    popularity = db.Column(db.Integer)
    spotify_url = db.Column(db.String)
    duration_min = db.Column(db.Float)
    genre = db.Column(db.String)
    album_cover_url = db.Column(db.String)

    def to_dict(self):
        return {
            "id": self.id,
            "track_name": self.track_name,
            "artist": self.artist,
            "album": self.album,
            "release_date": self.release_date,
            "popularity": self.popularity,
            "spotify_url": self.spotify_url,
            "duration_min": self.duration_min,
            "genre": self.genre,
            "album_cover_url": self.album_cover_url
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String, nullable=False)
    track_id = db.Column(db.String, db.ForeignKey('spotify_tracks.id'), nullable=False)

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String, nullable=False)
    track_id = db.Column(db.String, db.ForeignKey('spotify_tracks.id'), nullable=False)

class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    user_identifier = db.Column(db.String, nullable=False)
    tracks = db.relationship('SpotifyTrack', secondary=playlist_tracks, backref='playlists')

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String, nullable=False)
    track_id = db.Column(db.String, db.ForeignKey('spotify_tracks.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)

class TrackSchema(Schema):
    id = fields.String()
    track_name = fields.String(required=True)
    artist = fields.String(required=True)
    album = fields.String()
    release_date = fields.String()
    popularity = fields.Integer()
    spotify_url = fields.String()
    duration_min = fields.Float()
    genre = fields.String()
    album_cover_url = fields.String()

track_schema = TrackSchema()

def import_csv_to_db():
    if SpotifyTrack.query.first():
        return
    csv_path = os.path.join(os.getcwd(), 'spotify_top_1000_tracks.csv')
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        track = SpotifyTrack(
            id=row['id'],
            track_name=row['track_name'],
            artist=row['artist'],
            album=row.get('album', ''),
            release_date=str(row.get('release_date', '')),
            popularity=int(row.get('popularity', 0)),
            spotify_url=row.get('spotify_url', ''),
            duration_min=float(row.get('duration_min', 0)),
            genre=row.get('genre', ''),
            album_cover_url=row.get('album_cover_url', '')
        )
        db.session.add(track)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    query = SpotifyTrack.query
    search = request.args.get('search')
    genre = request.args.get('genre')
    popularity = request.args.get('popularity')
    release_year = request.args.get('release_year')
    sort = request.args.get('sort', 'popularity_desc')

    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            func.lower(SpotifyTrack.track_name).like(pattern) |
            func.lower(SpotifyTrack.artist).like(pattern)
        )
    if genre:
        query = query.filter(SpotifyTrack.genre == genre)
    if popularity:
        try:
            pop_val = int(popularity)
            query = query.filter(SpotifyTrack.popularity >= pop_val)
        except ValueError:
            pass
    if release_year:
        query = query.filter(SpotifyTrack.release_date.startswith(str(release_year)))

    if sort == 'popularity_asc':
        query = query.order_by(SpotifyTrack.popularity.asc())
    elif sort == 'release_desc':
        query = query.order_by(SpotifyTrack.release_date.desc())
    elif sort == 'release_asc':
        query = query.order_by(SpotifyTrack.release_date.asc())
    else:
        query = query.order_by(SpotifyTrack.popularity.desc())

    tracks = [t.to_dict() for t in query.all()]

    return jsonify({
        "tracks": tracks,
        "meta": {
            "total": len(tracks),
            "page": 1,
            "pages": 1,
            "per_page": len(tracks),
            "has_next": False,
            "has_prev": False
        }
    })

@app.route('/api/tracks', methods=['POST'])
def create_track():
    try:
        data = track_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    if 'id' not in data or not data['id']:
        data['id'] = str(uuid.uuid4())

    if SpotifyTrack.query.get(data['id']):
        return jsonify({"error": "Track with this ID already exists."}), 400

    new_track = SpotifyTrack(**data)
    db.session.add(new_track)
    db.session.commit()
    return jsonify(new_track.to_dict()), 201

@app.route('/api/tracks/<track_id>', methods=['PUT'])
def update_track(track_id):
    track = SpotifyTrack.query.get_or_404(track_id)
    data = request.json
    for field in ['track_name', 'artist', 'album', 'release_date', 'popularity', 'spotify_url', 'duration_min', 'genre', 'album_cover_url']:
        if field in data:
            setattr(track, field, data[field])
    db.session.commit()
    return jsonify(track.to_dict())

@app.route('/api/tracks/<track_id>', methods=['DELETE'])
def delete_track(track_id):
    track = SpotifyTrack.query.get_or_404(track_id)
    db.session.delete(track)
    db.session.commit()
    return '', 204

# -- Favorites, Likes, and others remain unchanged --

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import_csv_to_db()
    app.run(debug=True)


