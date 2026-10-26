from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import require_user
from app.db.session import get_db
from app.schemas.expense import ExpenseRead, ExpenseSummary, ExpenseWrite
from app.services import expenses as expense_service

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=list[ExpenseRead])
def list_expenses(
    category_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    session: Session = Depends(get_db),
) -> list[ExpenseRead]:
    expenses = expense_service.list_expenses(
        session,
        category_id=category_id,
        from_date=from_date,
        to_date=to_date,
    )
    return [ExpenseRead.from_expense(expense) for expense in expenses]


@router.get("/summary", response_model=ExpenseSummary)
def summarize_expenses(
    from_date: date | None = None,
    to_date: date | None = None,
    session: Session = Depends(get_db),
) -> ExpenseSummary:
    return expense_service.summarize_expenses(
        session, from_date=from_date, to_date=to_date
    )


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(
    expense_id: int, session: Session = Depends(get_db)
) -> ExpenseRead:
    return ExpenseRead.from_expense(expense_service.get_expense(session, expense_id))


@router.post("", response_model=ExpenseRead, status_code=201)
def create_expense(
    payload: ExpenseWrite, session: Session = Depends(get_db)
) -> ExpenseRead:
    expense = expense_service.create_expense(session, payload)
    return ExpenseRead.from_expense(expense)


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int, payload: ExpenseWrite, session: Session = Depends(get_db)
) -> ExpenseRead:
    expense = expense_service.update_expense(session, expense_id, payload)
    return ExpenseRead.from_expense(expense)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, session: Session = Depends(get_db)) -> Response:
    expense_service.delete_expense(session, expense_id)
    return Response(status_code=204)
