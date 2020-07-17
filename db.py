from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from os import getenv
import models

# import mock
# mock.set_vars()

engine = create_engine(getenv("DATABASE_URL"))

Session_Factory: sessionmaker = sessionmaker(bind=engine)
Scoped_Session = scoped_session(Session_Factory)


def recreate_database() -> None:
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)


if __name__ == "__main__":
    recreate_database()
