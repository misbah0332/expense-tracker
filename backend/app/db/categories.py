from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Category


def list_categories(session: Session) -> list[Category]:
    statement = select(Category).order_by(Category.name, Category.id)
    return list(session.scalars(statement).all())


def get_category(session: Session, category_id: int) -> Category | None:
    return session.get(Category, category_id)


def get_category_by_name(session: Session, name: str) -> Category | None:
    statement = select(Category).where(func.lower(Category.name) == name.lower())
    return session.scalar(statement)
