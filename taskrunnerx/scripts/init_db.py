
from ..app.db import Base, engine


def init():
    Base.metadata.create_all(bind=engine)
    print("Database initialized")


if __name__ == "__main__":
    init()
