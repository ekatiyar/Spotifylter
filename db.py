from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from os import getenv
import models

# import mock
# mock.set_vars()

engine = create_engine(getenv("DATABASE_URL"))

Session_Factory = sessionmaker(bind=engine)
Scoped_Session = scoped_session(Session_Factory)


def recreate_database() -> None:
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)


def delete_entry(username: str) -> None:
    s = Session_Factory()
    s.query(models.Users).filter_by(
        username=username).delete(synchronize_session=False)
    s.commit()
    s.close()


if __name__ == "__main__":
    recreate_database()
