from decimal import Decimal

import streamlit as st

from client import ApiClient


def render(client: ApiClient) -> None:
    st.header("Summary")
    from_col, to_col = st.columns(2)
    from_date = from_col.date_input("From", value=None, key="summary_from")
    to_date = to_col.date_input("To", value=None, key="summary_to")
    if from_date and to_date and from_date > to_date:
        st.error("From date must be on or before to date.")
        return

    summary = client.summarize(from_date=from_date, to_date=to_date)
    st.metric("Total", f"{Decimal(summary['total']):.2f}")
    rows = summary["categories"]
    if not rows:
        st.info("No expenses in this date range.")
        return
    table = [
        {
            "Category": row["category_name"],
            "Total": f"{Decimal(row['total']):.2f}",
        }
        for row in rows
    ]
    st.dataframe(table, hide_index=True, width="stretch")
    st.bar_chart(
        {
            "Category": [row["category_name"] for row in rows],
            "Total": [float(row["total"]) for row in rows],
        },
        x="Category",
        y="Total",
        horizontal=True,
    )
