from sqlmodel import Session, select

from app.db import engine
from app.models import Topic, User, utcnow
from app.services.discover import default_surfaces

EXAMPLE = {
    "name": "Unofficial game ports",
    "seed": "unofficial game ports",
    "notes": "Example topic: fan ports, community ports, Steam Deck / Switch / Android.",
}


def seed_example_topic() -> None:
    with Session(engine) as session:
        if session.exec(select(User).limit(1)).first():
            return
        if session.exec(select(Topic).limit(1)).first():
            return
        topic = Topic(
            name=EXAMPLE["name"],
            seed=EXAMPLE["seed"],
            notes=EXAMPLE["notes"],
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        session.add(topic)
        session.commit()
        session.refresh(topic)
        for surface in default_surfaces(topic.id, topic.seed):  # type: ignore[arg-type]
            session.add(surface)
        session.commit()
