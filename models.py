from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_name = db.Column(db.String(255), nullable=False)
    artist_name = db.Column(db.String(255), nullable=False)
    album_name = db.Column(db.String(255))
    rating = db.Column(db.String(10))
    preview_url = db.Column(db.String(500))  # 30-second preview audio URL

    def to_dict(self):
        return {
            'id': self.id,
            'track_name': self.track_name,
            'artist_name': self.artist_name,
            'album_name': self.album_name or '',
            'rating': self.rating or '',
            'preview_url': self.preview_url or ''
        }
