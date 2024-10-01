from time import sleep
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages

USER_INFO: dict = {}

def set_user_info(user_info: dict):
    global USER_INFO
    USER_INFO = user_info


def get_user_info() -> dict:
    return USER_INFO


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context!")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]


def make_sidebar():
    with st.sidebar:
        st.title("")

        if st.session_state.get("logged_in", False):

            if st.button("ログアウト"):
                logout()

        elif get_current_page_name() != "app":
            st.switch_page('app.py')


def logout():
    global USER_INFO
    st.session_state.logged_in = False
    USER_INFO = {}
    st.info("ログアウトしました.")
    sleep(0.5)
    st.switch_page('app.py')