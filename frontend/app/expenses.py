from datetime import date
from decimal import Decimal

import streamlit as st

from client import ApiClient, ApiError


def render(client: ApiClient) -> None:
    _show_notice()
    st.header("Expenses")
    categories = client.list_categories()
    if not categories:
        st.error("No categories are available.")
        return
    category_ids = {item["name"]: item["id"] for item in categories}

    filter_col, from_col, to_col = st.columns(3)
    selected_category = filter_col.selectbox(
        "Category", ["All", *category_ids.keys()], key="expense_filter_category"
    )
    from_date = from_col.date_input("From", value=None, key="expense_filter_from")
    to_date = to_col.date_input("To", value=None, key="expense_filter_to")
    if from_date and to_date and from_date > to_date:
        st.error("From date must be on or before to date.")
        return

    category_id = None if selected_category == "All" else category_ids[selected_category]
    expenses = client.list_expenses(
        category_id=category_id, from_date=from_date, to_date=to_date
    )
    if expenses:
        st.dataframe(
            [
                {
                    "Date": item["expense_date"],
                    "Category": item["category_name"],
                    "Amount": f"{Decimal(item['amount']):.2f}",
                    "Description": item["description"] or "",
                }
                for item in expenses
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No expenses match these filters.")

    st.subheader("Add expense")
    _expense_form(client, categories, form_key="add-expense", submit_label="Add expense")

    st.subheader("Edit expense")
    if not expenses:
        st.caption("Add an expense before editing.")
        return
    labels = {
        item["id"]: (
            f"{item['expense_date']} · {item['category_name']} · "
            f"{Decimal(item['amount']):.2f}"
        )
        for item in expenses
    }
    selected_id = st.selectbox(
        "Expense",
        list(labels),
        format_func=lambda expense_id: labels[expense_id],
        key="expense_edit_choice",
    )
    selected = next(item for item in expenses if item["id"] == selected_id)
    _expense_form(
        client,
        categories,
        form_key=f"edit-expense-{selected_id}",
        submit_label="Save changes",
        expense=selected,
    )
    if st.checkbox("Confirm delete", key=f"confirm-delete-{selected_id}"):
        if st.button("Delete expense", key=f"delete-expense-{selected_id}"):
            client.delete_expense(selected_id)
            _notice("Expense deleted.")
            st.rerun()


def _expense_form(
    client: ApiClient,
    categories: list[dict],
    *,
    form_key: str,
    submit_label: str,
    expense: dict | None = None,
) -> None:
    names = [item["name"] for item in categories]
    default_name = expense["category_name"] if expense else names[0]
    with st.form(form_key):
        amount = st.number_input(
            "Amount",
            min_value=0.01,
            step=0.01,
            format="%.2f",
            value=float(expense["amount"]) if expense else 0.01,
            key=f"{form_key}-amount",
        )
        expense_date = st.date_input(
            "Date",
            value=date.fromisoformat(expense["expense_date"]) if expense else date.today(),
            key=f"{form_key}-date",
        )
        category_name = st.selectbox(
            "Category",
            names,
            index=names.index(default_name) if default_name in names else 0,
            key=f"{form_key}-category",
        )
        description = st.text_input(
            "Description",
            value=expense["description"] or "" if expense else "",
            max_chars=500,
            key=f"{form_key}-description",
        )
        submitted = st.form_submit_button(submit_label)
    if not submitted:
        return
    category_id = next(item["id"] for item in categories if item["name"] == category_name)
    payload = {
        "amount": Decimal(f"{amount:.2f}"),
        "expense_date": expense_date,
        "category_id": category_id,
        "description": description,
    }
    try:
        if expense is None:
            client.create_expense(**payload)
            _notice("Expense added.")
        else:
            client.update_expense(expense["id"], **payload)
            _notice("Expense updated.")
    except ApiError as exc:
        if exc.status_code == 401:
            raise
        st.error(exc.detail)
        return
    st.rerun()


def _notice(message: str) -> None:
    st.session_state["notice"] = message


def _show_notice() -> None:
    message = st.session_state.pop("notice", None)
    if message:
        st.success(message)
