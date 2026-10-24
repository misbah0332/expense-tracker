from datetime import date
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import categories as category_repository
from app.db import expenses as expense_repository
from app.db.models import Expense
from app.schemas.expense import CategoryTotal, ExpenseSummary, ExpenseWrite
from app.services.exceptions import DateRangeError, InvalidCategoryError, NotFoundError


def _validate_date_range(from_date: date | None, to_date: date | None) -> None:
    if from_date is not None and to_date is not None and from_date > to_date:
        raise DateRangeError("from_date must be on or before to_date")


def _require_category(session: Session, category_id: int) -> None:
    if category_repository.get_category(session, category_id) is None:
        raise InvalidCategoryError("Category not found")


def list_expenses(
    session: Session,
    *,
    category_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[Expense]:
    _validate_date_range(from_date, to_date)
    return expense_repository.list_expenses(
        session,
        category_id=category_id,
        from_date=from_date,
        to_date=to_date,
    )


def get_expense(session: Session, expense_id: int) -> Expense:
    expense = expense_repository.get_expense(session, expense_id)
    if expense is None:
        raise NotFoundError("Expense not found")
    return expense


def create_expense(session: Session, payload: ExpenseWrite) -> Expense:
    _require_category(session, payload.category_id)
    expense = Expense(
        amount=payload.amount,
        expense_date=payload.expense_date,
        description=payload.description,
        category_id=payload.category_id,
    )
    session.add(expense)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise InvalidCategoryError("Category not found") from None
    return get_expense(session, expense.id)


def update_expense(
    session: Session, expense_id: int, payload: ExpenseWrite
) -> Expense:
    expense = get_expense(session, expense_id)
    _require_category(session, payload.category_id)
    expense.amount = payload.amount
    expense.expense_date = payload.expense_date
    expense.description = payload.description
    expense.category_id = payload.category_id
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise InvalidCategoryError("Category not found") from None
    return get_expense(session, expense.id)


def delete_expense(session: Session, expense_id: int) -> None:
    expense = get_expense(session, expense_id)
    session.delete(expense)
    session.commit()


def summarize_expenses(
    session: Session,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
) -> ExpenseSummary:
    _validate_date_range(from_date, to_date)
    total, rows = expense_repository.summarize_expenses(
        session, from_date=from_date, to_date=to_date
    )
    categories = [
        CategoryTotal(
            category_id=category_id,
            category_name=category_name,
            total=Decimal(amount).quantize(Decimal("0.01")),
        )
        for category_id, category_name, amount in rows
    ]
    return ExpenseSummary(total=total.quantize(Decimal("0.01")), categories=categories)
