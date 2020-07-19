from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableDict, MutableList
from time import strftime

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    username = Column(String, primary_key=True)
    email = Column(String)
    playlist_id = Column(String)
    refresh_token = Column(String)
    last_email = Column(Integer)

    def __repr__(self):
        return f"<User {self.username} last emailed {self.email} at {self.last_email} >"


class Counts(Base):
    __tablename__ = 'counts'

    username = Column(String, ForeignKey('users.username',
                                         ondelete="CASCADE"), primary_key=True)
    # Heroku DB Row Limits for free users necessitate using dictionaries rather than db rows
    playlist = Column(MutableDict.as_mutable(JSON))
    library = Column(MutableDict.as_mutable(JSON))
    other = Column(MutableDict.as_mutable(JSON))
    filtered = Column(MutableList.as_mutable(ARRAY(String)))
