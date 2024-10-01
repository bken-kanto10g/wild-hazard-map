import hashlib
import warnings
from time import sleep
import streamlit as st

import src.utility.const as const
import src.navigate.app2menu as a2m

warnings.simplefilter('ignore')

USER_INFO = {
    # keyはユーザID、valueはユーザ情報
    "bken-kanto10g-001": {
        "username": "佐々木悠",
        "phone": "",
        "email": "y-sasaki@nandis.jp",
        # パスワードは前もってハッシュ化されている
        "password": hashlib.sha256("p@ssword1234".encode('utf-8')).hexdigest()
    }
}

# ページ設定
st.set_page_config(
    page_title=const.APP_NAME,
    page_icon=const.APP_ICON,
    layout="wide"
)

# ハンバーガーメニューの削除
st.markdown(
    const.DELETE_HAMBURGER_MENU,
    unsafe_allow_html=True
)

def login():
    """ログイン関数

    ログイン画面を構成する処理系

    Args:
        None

    Returns:
        None

    """
    _, midobj, _ = st.columns([0.3, 0.4, 0.3])
    midobj.subheader("ログインセクション")
    midobj.markdown("")
    userid = midobj.text_input("ユーザーID")
    midobj.markdown("")
    password = midobj.text_input("パスワード", type='password')

    midobj.markdown("")
    if not midobj.button("ログイン"):
        return

    # パスワードのハッシュ化
    hashed_password = hashlib.sha256(
        password.encode('utf-8')
    ).hexdigest()
    
    if not userid or not password:
        # 未入力
        st.warning(f"ユーザID、パスワードに未入力項目があります.")
        return

    if userid not in USER_INFO.keys():
        # ユーザIDの誤り
        st.warning(f"ユーザID{userid}が誤っています.")
        return
    
    ture_user_info = USER_INFO[userid]
    
    if hashed_password != ture_user_info["password"]:
        # パスワードの誤り
        st.warning(f"パスワードが間違っています.")
        return

    st.session_state.logged_in = True
    a2m.set_user_info(
        user_info=ture_user_info
    )
    sleep(0.5)
    st.switch_page("pages/menu.py")

def change_password():
    """パスワード変更関数

    パスワード変更画面を構成する処理系

    Args:
        None

    Returns:
        None

    """
    global USER_INFO

    _, midobj, _ = st.columns([0.3, 0.4, 0.3])
    midobj.subheader("パスワード変更")
    midobj.markdown("")
    userid = midobj.text_input("ユーザーID")
    midobj.markdown("")
    before_password = midobj.text_input("変更前のパスワード", type='password')
    midobj.markdown("")
    after_password1 = midobj.text_input("変更後のパスワード", type='password')
    midobj.markdown("")
    after_password2 = midobj.text_input("変更後のパスワード(確認)", type='password')

    if not midobj.button("変更"):
        return

    if userid or not before_password or \
        not after_password1 or not after_password2:
        # 未入力
        st.warning("ユーザID、パスワードに未入力項目があります.")
        return
    
    if before_password == after_password1 or \
        before_password == after_password2:
        # パスワードが変更前と変わらない
        st.warning("変更前と同じパスワードは入力できません.")
        return

    # 変更前の情報の正しさチェック
    hashed_before_password = hashlib.sha256(
        before_password.encode('utf-8')
    ).hexdigest()
    
    if userid not in USER_INFO.keys():
        # ユーザIDの誤り
        st.warning(f"ユーザID{userid}が誤っています.")
        return
    
    ture_user_info = USER_INFO[userid]

    if hashed_before_password != ture_user_info["password"]:
        # パスワードの誤り
        st.warning("変更前のパスワードが間違っています.")
        return

    # パスワード変更処理
    if after_password1 != after_password2:
        # 確認項目の誤り
        st.warning("変更後及び変更後(確認)には同じパスワード入力してください.")
        return

    USER_INFO[userid]["password"] = hashlib.sha256(
        after_password2.encode('utf-8')
    ).hexdigest()

    st.success("パスワードの変更が正常に行われました.")

# サインアップ
def sign_up():
    _, midobj, _ = st.columns([0.3, 0.4, 0.3])
    midobj.subheader("サインアップ")
    midobj.markdown("")
    username = midobj.text_input('ユーザ名(半角英数)')
    midobj.markdown("")
    email = midobj.text_input('e-mailアドレス')

# ホーム関数
def home():
    a2m.make_sidebar()
    choice = st.sidebar.selectbox(
        "メニュー",
        const.MENU_LIST
    )
    match choice:
        case "ログイン":
            login()
        case "サインアップ":
            sign_up()
        case "パスワード変更":
            change_password()

if __name__ == "__main__":
    home()