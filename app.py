import os
from flask import Flask, request, jsonify, render_template
from models import db, Track
from flask_migrate import Migrate
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)  # Flask-Migrate setup

CSV_PATH = 'spotify_top_1000_tracks.csv'

def import_csv():
    with app.app_context():
        if Track.query.first() is None:  # Import only if table empty
            print('Importing CSV into SQLite database...')
            df = pd.read_csv(CSV_PATH)
            for _, row in df.iterrows():
                track = Track(
                    track_name=row.get('track_name', 'Unknown'),
                    artist_name=row.get('artist_name', 'Unknown'),
                    album_name=row.get('album_name', '') if 'album_name' in row else '',
                    preview_url=''  # Empty now, can be updated later
                )
                db.session.add(track)
            db.session.commit()
            print('CSV import completed.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = Track.query.paginate(page=page, per_page=per_page, error_out=False)
    tracks = [t.to_dict() for t in pagination.items]
    return jsonify({
        'tracks': tracks,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@app.route('/api/tracks', methods=['POST'])
def add_track():
    data = request.json
    track = Track(
        track_name=data.get('track_name', 'Unknown'),
        artist_name=data.get('artist_name', 'Unknown'),
        album_name=data.get('album_name', ''),
        preview_url=data.get('preview_url', '')
    )
    db.session.add(track)
    db.session.commit()
    return jsonify({'message': 'Track added', 'id': track.id})

@app.route('/api/tracks/<int:track_id>', methods=['PUT'])
def update_track(track_id):
    data = request.json
    track = Track.query.get_or_404(track_id)
    if 'track_name' in data:
        track.track_name = data['track_name']
    if 'artist_name' in data:
        track.artist_name = data['artist_name']
    if 'album_name' in data:
        track.album_name = data['album_name']
    if 'preview_url' in data:
        track.preview_url = data['preview_url']
    db.session.commit()
    return jsonify({'message': 'Track updated'})

@app.route('/api/tracks/<int:track_id>', methods=['DELETE'])
def delete_track(track_id):
    track = Track.query.get_or_404(track_id)
    db.session.delete(track)
    db.session.commit()
    return jsonify({'message': 'Track deleted'})

@app.route('/api/tracks/<int:track_id>/rating', methods=['POST'])
def rate_track(track_id):
    data = request.json
    emoji = data.get('emoji', '')
    track = Track.query.get_or_404(track_id)
    track.rating = emoji
    db.session.commit()
    return jsonify({'message': 'Rating updated'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import_csv()
    app.run(debug=True)
