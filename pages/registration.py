from datetime import datetime as dt
import streamlit as st
import src.utility.const as const
import src.navigate.app2menu as a2m

# ページ表記
st.set_page_config(
    page_title="目撃情報登録",
    page_icon="📋",
    layout="wide"
)

# ハンバーガーメニューの削除
st.markdown(
    const.DELETE_HAMBURGER_MENU,
    unsafe_allow_html=True
)

# サイドバー定義
a2m.make_sidebar()

# タイトル
st.title('危険な動物目撃情報入力')

# 住所or緯度経度の入力選択をフォーム外で設定
location_type = st.radio("住所または緯度経度を入力してください（どちらか一方必須）", ('住所', '緯度経度'))

# フォームの入力項目
with st.form("sighting_form"):
    # 必須項目
    sighting_date = st.date_input("目撃年月日", value=dt.now(), help="目撃された日付を選択してください。")
    animal_name = st.text_input("目撃動物名", max_chars=50, help="目撃した動物の名前を入力してください。")
    sighting_count = st.number_input("目撃頭数", min_value=1, help="目撃した頭数を入力してください。")
    
    # 住所or緯度経度
    if location_type == '住所':
        address = st.text_input("住所", help="目撃された場所の住所を入力してください。")
        latitude, longitude = None, None  # 緯度経度をクリア
    else:
        latitude = st.text_input("緯度", help="緯度を入力してください。")
        longitude = st.text_input("経度", help="経度を入力してください。")
        address = None  # 住所をクリア

    # 任意項目
    photo = st.file_uploader("目撃写真（任意）", type=["jpg", "jpeg", "png"])
    situation = st.text_area("状況説明（任意）", help="目撃時の状況を詳しく記入してください。")
    remarks = st.text_area("備考（任意）", help="その他備考を記入してください。")
    
    # フォームの送信ボタン
    submitted = st.form_submit_button("確定")

# 確認画面表示
if submitted:
    # 必須項目のバリデーション
    if not animal_name or sighting_count < 1 or not sighting_date:
        st.error("目撃年月日、目撃頭数、目撃動物名は必須項目です。")
    elif location_type == '住所' and not address:
        st.error("住所を入力してください。")
    elif location_type == '緯度経度' and (not latitude or not longitude):
        st.error("緯度と経度を入力してください。")
    else:
        # 入力内容の確認画面
        st.write("以下の内容で登録しますか？")
        st.write(f"目撃年月日: {sighting_date}")
        st.write(f"目撃動物名: {animal_name}")
        st.write(f"目撃頭数: {sighting_count}")
        
        if location_type == '住所':
            st.write(f"住所: {address}")
        else:
            st.write(f"緯度: {latitude}, 経度: {longitude}")
        
        if photo:
            st.write("目撃写真: アップロード済み")
        else:
            st.write("目撃写真: なし")
        
        st.write(f"状況説明: {situation if situation else 'なし'}")
        st.write(f"備考: {remarks if remarks else 'なし'}")

        # 再度確認用の確定ボタン
        confirm = st.button("登録を確定")
        if confirm:
            st.success("目撃情報が登録されました！")
