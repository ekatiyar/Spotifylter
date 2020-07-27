from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

Base = declarative_base()

association_table = Table(
    "association",
    Base.metadata,
    Column("username", Text, ForeignKey("user.username", ondelete="CASCADE")),
    Column("playlist_id", Text, ForeignKey("playlist.playlist_id", ondelete="CASCADE")),
)


class User(Base):
    __tablename__ = "user"

    username = Column(String(30), primary_key=True)
    email = Column(Text)
    refresh_token = Column(Text)
    last_updated = Column(Integer)
    playlists = relationship(
        "Playlist",
        secondary=association_table,
        back_populates="users",
        collection_class=attribute_mapped_collection("playlist_id"),
    )
    data = relationship(
        "Count", collection_class=attribute_mapped_collection("count_key")
    )

    def __repr__(self):
        return (
            f"<User {self.username} last emailed {self.email} at {self.last_updated} >"
        )


class Playlist(Base):
    __tablename__ = "playlist"

    playlist_id = Column(String(22), primary_key=True)
    owner = Column(Text, ForeignKey("user.username", ondelete="CASCADE"))
    candidate = Column(Boolean)
    users = relationship(
        "User",
        secondary=association_table,
        back_populates="playlists",
        collection_class=attribute_mapped_collection("username"),
    )


class Count(Base):
    __tablename__ = "count"

    username = Column(
        String(30), ForeignKey("user.username", ondelete="CASCADE"), primary_key=True
    )
    candidate = Column(Boolean, primary_key=True)
    song = Column(String(22), primary_key=True)
    song_count = Column(Integer)
    song_avg = Column(Float)
    song_duration = Column(Float)
    filtered = Column(Boolean)

    @property
    def count_key(self):
        return (self.candidate, self.song)
