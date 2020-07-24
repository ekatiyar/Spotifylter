from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.orm.collections import attribute_mapped_collection
from time import strftime
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    username = Column(String, primary_key=True)
    email = Column(String)
    refresh_token = Column(String)
    last_updated = Column(Integer)
    counttypes = relationship(
        "CountType", collection_class=attribute_mapped_collection('location'))

    def __repr__(self):
        return f"<User {self.username} last emailed {self.email} at {self.last_updated} >"


class CountType(Base):
    __tablename__ = "counttype"
    username = Column(String, ForeignKey(
        "user.username", ondelete="CASCADE"), primary_key=True)
    location = Column(String, primary_key=True)
    playlists = relationship(
        "Playlist", collection_class=attribute_mapped_collection('playlist_id'))  # This is equal to playlist_id for candidate playlist
    data = relationship(
        "Count", collection_class=attribute_mapped_collection('song'))


class Playlist(Base):
    __tablename__ = "playlist"

    playlist_id = Column(String, primary_key=True)
    username = Column(String, primary_key=True)
    location = Column(String)
    owner = Column(Boolean)
    __table_args__ = (
        ForeignKeyConstraint(["username", "location"], [
                             "counttype.username", "counttype.location"], ondelete="CASCADE"),
    )


class Count(Base):
    __tablename__ = 'count'

    username = Column(String, primary_key=True)
    location = Column(String, primary_key=True)
    song = Column(String, primary_key=True)
    song_count = Column(Integer)
    song_avg = Column(Float)
    song_duration = Column(Float)
    filtered = Column(Boolean)
    __table_args__ = (
        ForeignKeyConstraint(["username", "location"], [
                             "counttype.username", "counttype.location"], ondelete="CASCADE"),
    )
