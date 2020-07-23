from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from time import strftime

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    username = Column(String, primary_key=True)
    email = Column(String)
    refresh_token = Column(String)
    last_updated = Column(Integer)
    playlists = relationship("Playlist")

    def __repr__(self):
        return f"<User {self.username} last emailed {self.email} at {self.last_updated} >"


class Playlist(Base):
    __tablename__ = "playlist"

    playlist_id = Column(String, primary_key=True)
    username = Column(String, ForeignKey('user.username', ondelete="CASCADE"))
    owner = Column(Boolean)
    curate = Column(Boolean)
    collab = Column(Boolean)
    data = relationship("Count")


class Count(Base):
    __tablename__ = 'count'

    username = Column(String, ForeignKey('user.username',
                                         ondelete="CASCADE"), primary_key=True)
    song = Column(String, primary_key=True)
    location = Column(String, ForeignKey('playlist.playlist_id',
                                         ondelete="CASCADE"), nullable=True, primary_key=True)
    song_count = Column(Integer)
    song_avg = Column(Float)
    song_duration = Column(Float)
    filtered = Column(Boolean)
