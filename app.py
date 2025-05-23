from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///spotify.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret')

db = SQLAlchemy(app)

# Models
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
            "genre": self.genre
        }

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String, nullable=False)
    track_id = db.Column(db.String, db.ForeignKey('spotify_tracks.id'), nullable=False)

# CSV import helper
def import_csv_to_db():
    if SpotifyTrack.query.first():
        print("Data already imported.")
        return
    csv_path = os.path.join(os.getcwd(), 'spotify_top_1000_tracks.csv')
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
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
            genre=row.get('genre', '')
        )
        db.session.add(track)
    db.session.commit()
    print("CSV data import completed.")

# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    query = SpotifyTrack.query

    search = request.args.get('search')
    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            func.lower(SpotifyTrack.track_name).like(pattern) |
            func.lower(SpotifyTrack.artist).like(pattern)
        )

    sort = request.args.get('sort', 'popularity_desc')
    if sort == 'popularity_asc':
        query = query.order_by(SpotifyTrack.popularity.asc())
    elif sort == 'release_desc':
        query = query.order_by(SpotifyTrack.release_date.desc())
    elif sort == 'release_asc':
        query = query.order_by(SpotifyTrack.release_date.asc())
    else:
        query = query.order_by(SpotifyTrack.popularity.desc())

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    tracks = [t.to_dict() for t in paginated.items]

    return jsonify({
        "tracks": tracks,
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages
    })

@app.route('/api/tracks', methods=['POST'])
def create_track():
    data = request.json
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
    for field in ['track_name', 'artist', 'album', 'release_date', 'popularity', 'spotify_url', 'duration_min', 'genre']:
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

@app.route('/api/top-artists', methods=['GET'])
def get_top_artists():
    results = (
        db.session.query(
            SpotifyTrack.artist,
            func.sum(SpotifyTrack.popularity).label('total_popularity')
        )
        .group_by(SpotifyTrack.artist)
        .order_by(func.sum(SpotifyTrack.popularity).desc())
        .limit(10)
        .all()
    )
    data = [{"artist": r.artist, "total_popularity": r.total_popularity} for r in results]
    return jsonify(data)

@app.route('/api/genres', methods=['GET'])
def get_genres():
    results = (
        db.session.query(
            SpotifyTrack.genre,
            func.count(SpotifyTrack.id).label('count')
        )
        .group_by(SpotifyTrack.genre)
        .order_by(func.count(SpotifyTrack.id).desc())
        .all()
    )
    data = [{"genre": r.genre, "count": r.count} for r in results if r.genre]
    return jsonify(data)

@app.route('/api/spotify-sync', methods=['POST'])
def spotify_sync():
    return jsonify({"message": "Spotify sync feature coming soon"}), 200

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

# Create DB tables and import CSV before first request
with app.app_context():
    db.create_all()
    import_csv_to_db()

if __name__ == '__main__':
    app.run(debug=True)


