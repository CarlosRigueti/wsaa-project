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
    album_cover_url = db.Column(db.String)  # New column

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

# Marshmallow Schema
class TrackSchema(Schema):
    id = fields.String(required=True)
    track_name = fields.String(required=True)
    artist = fields.String(required=True)
    album = fields.String()
    release_date = fields.String()
    popularity = fields.Integer()
    spotify_url = fields.String()
    duration_min = fields.Float()
    genre = fields.String()
    album_cover_url = fields.String()  # New field

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
            album_cover_url=row.get('album_cover_url', '')  # New field
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

@app.route('/api/suggest')
def suggest():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])

    suggestions = (
        db.session.query(SpotifyTrack.track_name)
        .filter(SpotifyTrack.track_name.ilike(f'%{q}%'))
        .distinct()
        .limit(10)
        .all()
    )
    return jsonify([s[0] for s in suggestions])

@app.route('/api/tracks', methods=['POST'])
def create_track():
    try:
        data = track_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

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

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    data = request.json
    user_id = data.get('user_identifier', 'anonymous')
    track_id = data.get('track_id')
    if not track_id or not SpotifyTrack.query.get(track_id):
        return jsonify({"error": "Invalid track ID"}), 400
    fav = Favorite.query.filter_by(user_identifier=user_id, track_id=track_id).first()
    if fav:
        return jsonify({"message": "Already favorited"}), 200
    new_fav = Favorite(user_identifier=user_id, track_id=track_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"message": "Added to favorites"}), 201

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    user_id = request.args.get('user_identifier', 'anonymous')
    favs = Favorite.query.filter_by(user_identifier=user_id).all()
    track_ids = [f.track_id for f in favs]
    tracks = SpotifyTrack.query.filter(SpotifyTrack.id.in_(track_ids)).all()
    return jsonify([t.to_dict() for t in tracks])

@app.route('/api/likes', methods=['POST'])
def toggle_like():
    data = request.get_json()
    user_id = data.get('user_identifier', 'anonymous')
    track_id = data.get('track_id')

    if not track_id:
        return jsonify({"error": "Track ID missing"}), 400

    like = Like.query.filter_by(user_identifier=user_id, track_id=track_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({"liked": False})
    else:
        new_like = Like(user_identifier=user_id, track_id=track_id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({"liked": True})

@app.route('/favorites/dashboard')
def favorites_dashboard():
    user_id = request.args.get('user_identifier', 'anonymous')
    favs = Favorite.query.filter_by(user_identifier=user_id).all()
    track_ids = [f.track_id for f in favs]

    genre_results = (
        db.session.query(SpotifyTrack.genre, func.count(SpotifyTrack.id))
        .filter(SpotifyTrack.id.in_(track_ids))
        .group_by(SpotifyTrack.genre)
        .all()
    )
    genre_data = [{"genre": g or "Unknown", "count": c} for g, c in genre_results]

    artist_results = (
        db.session.query(SpotifyTrack.artist, func.sum(SpotifyTrack.popularity))
        .filter(SpotifyTrack.id.in_(track_ids))
        .group_by(SpotifyTrack.artist)
        .order_by(func.sum(SpotifyTrack.popularity).desc())
        .all()
    )
    artist_data = [{"artist": a, "total_popularity": p} for a, p in artist_results]

    return render_template("favorites_dashboard.html", genre_data=genre_data, artist_data=artist_data)

@app.route('/artist/<name>')
def artist_page(name):
    tracks = SpotifyTrack.query.filter(SpotifyTrack.artist == name).all()
    total_popularity = sum([t.popularity or 0 for t in tracks])
    return render_template('artist_page.html', artist_name=name, tracks=tracks, total_popularity=total_popularity)

@app.route('/playlists')
def view_playlists():
    user_id = 'anonymous'
    playlists = Playlist.query.filter_by(user_identifier=user_id).all()
    return render_template('playlist_manager.html', playlists=playlists)

@app.route('/playlists/create', methods=['POST'])
def create_playlist():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    playlist = Playlist(name=name, user_identifier='anonymous')
    db.session.add(playlist)
    db.session.commit()
    return jsonify({'message': 'Playlist created'}), 201

@app.route('/playlists/delete/<int:playlist_id>', methods=['POST'])
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    db.session.delete(playlist)
    db.session.commit()
    return redirect('/playlists')

@app.route('/playlists/<int:playlist_id>/remove/<track_id>', methods=['POST'])
def remove_track_from_playlist(playlist_id, track_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    playlist.tracks = [t for t in playlist.tracks if t.id != track_id]
    db.session.commit()
    return redirect('/playlists')

@app.route('/track/<track_id>/feedback', methods=['GET', 'POST'])
def track_feedback(track_id):
    track = SpotifyTrack.query.get_or_404(track_id)
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        user_id = 'anonymous'
        feedback = Feedback(user_identifier=user_id, track_id=track.id, rating=rating, comment=comment)
        db.session.add(feedback)
        db.session.commit()
        return redirect(f'/track/{track.id}/feedback')
    feedbacks = Feedback.query.filter_by(track_id=track.id).all()
    return render_template('track_feedback.html', track=track, feedbacks=feedbacks)

with app.app_context():
    # Drop all tables and recreate to avoid old schema conflicts (only for dev)
    db.drop_all()
    db.create_all()
    import_csv_to_db()

if __name__ == '__main__':
    app.run(debug=True)


