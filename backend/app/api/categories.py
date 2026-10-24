from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.services import categories as category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_db)) -> list[CategoryRead]:
    return category_service.list_categories(session)


@router.post("", response_model=CategoryRead, status_code=201)
def create_category(
    payload: CategoryCreate, session: Session = Depends(get_db)
) -> CategoryRead:
    return category_service.create_category(session, payload)
