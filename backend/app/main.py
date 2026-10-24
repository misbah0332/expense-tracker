from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.categories import router as categories_router
from app.api.expenses import router as expenses_router
from app.services.exceptions import (
    ConflictError,
    DateRangeError,
    InvalidCategoryError,
    NotFoundError,
)

app = FastAPI(title="Expense Tracker")
app.include_router(categories_router)
app.include_router(expenses_router)


@app.exception_handler(NotFoundError)
def handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidCategoryError)
def handle_invalid_category(
    _request: Request, exc: InvalidCategoryError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(DateRangeError)
def handle_date_range(_request: Request, exc: DateRangeError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})
