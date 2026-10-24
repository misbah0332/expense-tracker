from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Category, Expense


def list_expenses(
    session: Session,
    *,
    category_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[Expense]:
    statement = select(Expense).options(joinedload(Expense.category))
    if category_id is not None:
        statement = statement.where(Expense.category_id == category_id)
    if from_date is not None:
        statement = statement.where(Expense.expense_date >= from_date)
    if to_date is not None:
        statement = statement.where(Expense.expense_date <= to_date)
    statement = statement.order_by(Expense.expense_date.desc(), Expense.id.desc())
    return list(session.scalars(statement).unique().all())


def get_expense(session: Session, expense_id: int) -> Expense | None:
    statement = (
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.id == expense_id)
        .execution_options(populate_existing=True)
    )
    return session.scalars(statement).unique().one_or_none()


def summarize_expenses(
    session: Session,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
) -> tuple[Decimal, list[tuple[int, str, Decimal]]]:
    filters = []
    if from_date is not None:
        filters.append(Expense.expense_date >= from_date)
    if to_date is not None:
        filters.append(Expense.expense_date <= to_date)

    total = session.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(*filters)
    )
    rows = session.execute(
        select(Category.id, Category.name, func.sum(Expense.amount))
        .join(Category, Category.id == Expense.category_id)
        .where(*filters)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    ).all()
    breakdown = [
        (category_id, category_name, amount)
        for category_id, category_name, amount in rows
    ]
    return Decimal(total), breakdown
