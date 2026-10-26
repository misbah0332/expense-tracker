import streamlit as st

from categories import render as render_categories
from client import ApiClient, ApiError, get_base_url
from expenses import render as render_expenses
from summary import render as render_summary

st.set_page_config(page_title="Expense Tracker", layout="wide")


def main() -> None:
    if not st.session_state.get("access_token"):
        _login()
        return

    st.sidebar.title("Expense Tracker")
    page = st.sidebar.radio("Go to", ["Expenses", "Summary", "Categories"])
    if st.sidebar.button("Log out"):
        st.session_state.pop("access_token", None)
        st.rerun()

    client = ApiClient(get_base_url(), st.session_state.get("access_token"))
    try:
        if page == "Expenses":
            render_expenses(client)
        elif page == "Summary":
            render_summary(client)
        else:
            render_categories(client)
    except ApiError as exc:
        if exc.status_code == 401:
            st.session_state.pop("access_token", None)
            st.session_state["login_error"] = "Your session has ended. Log in again."
            st.rerun()
        st.error(exc.detail)


def _login() -> None:
    st.title("Expense Tracker")
    st.caption("Log in to manage expenses.")
    error = st.session_state.pop("login_error", None)
    if error:
        st.error(error)
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if not submitted:
        return
    try:
        token = ApiClient(get_base_url()).login(username, password)
    except ApiError as exc:
        st.error(exc.detail)
        return
    st.session_state["access_token"] = token
    st.rerun()


main()
