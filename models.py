from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    playlist_id = Column(String)
    refresh_token = Column(String)
    last_email = Column(Integer)

    def __repr__(self):
        return f"<User {self.username} last emailed {self.email} at {self.last_email} >"
