from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import categories as category_repository
from app.db.models import Category
from app.schemas.category import CategoryCreate
from app.services.exceptions import ConflictError


def list_categories(session: Session) -> list[Category]:
    return category_repository.list_categories(session)


def create_category(session: Session, payload: CategoryCreate) -> Category:
    if category_repository.get_category_by_name(session, payload.name):
        raise ConflictError("Category name already exists")

    category = Category(name=payload.name, is_predefined=False)
    session.add(category)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("Category name already exists") from None
    session.refresh(category)
    return category
