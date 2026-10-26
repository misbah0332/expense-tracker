import streamlit as st

from client import ApiClient, ApiError


def render(client: ApiClient) -> None:
    message = st.session_state.pop("notice", None)
    if message:
        st.success(message)
    st.header("Categories")
    categories = client.list_categories()
    st.dataframe(
        [
            {
                "Name": item["name"],
                "Type": "Predefined" if item["is_predefined"] else "Custom",
            }
            for item in categories
        ],
        hide_index=True,
        width="stretch",
    )
    with st.form("add-category"):
        name = st.text_input("New category", max_chars=50)
        submitted = st.form_submit_button("Add category")
    if not submitted:
        return
    try:
        client.create_category(name)
    except ApiError as exc:
        if exc.status_code == 401:
            raise
        st.error(exc.detail)
        return
    st.session_state["notice"] = "Category added."
    st.rerun()
