from datetime import date
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import Expense

_MAX_AMOUNT = Decimal("9999999999.99")
_CENTS = Decimal("0.01")


def _parse_amount(value: object) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError("Amount must be greater than 0")
    try:
        if isinstance(value, float):
            amount = Decimal(str(value))
        elif isinstance(value, Decimal):
            amount = value
        else:
            amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Amount must be a number") from exc

    if amount != amount.quantize(_CENTS):
        raise ValueError("Amount must have at most 2 decimal places")
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if amount > _MAX_AMOUNT:
        raise ValueError("Amount must be at most 9999999999.99")
    return amount.quantize(_CENTS)


class ExpenseWrite(BaseModel):
    amount: Decimal
    expense_date: date
    category_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        return _parse_amount(value)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        stripped = value.strip()
        return stripped or None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    expense_date: date
    description: str | None
    category_id: int
    category_name: str

    @classmethod
    def from_expense(cls, expense: Expense) -> "ExpenseRead":
        return cls(
            id=expense.id,
            amount=expense.amount,
            expense_date=expense.expense_date,
            description=expense.description,
            category_id=expense.category_id,
            category_name=expense.category.name,
        )


class CategoryTotal(BaseModel):
    category_id: int
    category_name: str
    total: Decimal


class ExpenseSummary(BaseModel):
    total: Decimal
    categories: list[CategoryTotal]
