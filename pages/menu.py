from time import sleep
import streamlit as st
import src.utility.const as const
import src.navigate.app2menu as a2m

# ページ表記
st.set_page_config(
    page_title=f"{const.APP_NAME} メニュー",
    page_icon=const.APP_ICON,
    layout="wide"
)

# ハンバーガーメニューの削除
st.markdown(
    const.DELETE_HAMBURGER_MENU,
    unsafe_allow_html=True
)

# サイドバー定義
a2m.make_sidebar()

with st.sidebar:
    st.title("")
    if st.button('目撃情報登録'):
        st.switch_page("pages/registration.py")

# タイトル定義
st.title('メニュー')

buttonColMacroWildHazardMap, textAreaMacroWildHazardMap = st.columns([1, 4])
with buttonColMacroWildHazardMap:
    if st.button("マクロマップ"):
        sleep(0.5)
        st.switch_page("pages/macro_wild_hazard_map.py")

with textAreaMacroWildHazardMap:
    st.text("地域単位で警報・注意報を参照するハザードマップです")

buttonColMicroWildHazardMap, textAreaMicroWildHazardMap = st.columns([1, 4])
with buttonColMicroWildHazardMap:
    if st.button("ミクロマップ"):
        sleep(0.5)
        st.switch_page("pages/micro_wild_hazard_map.py")

with textAreaMicroWildHazardMap:
    st.text("周辺で警報・注意報を参照するハザードマップです")

buttonColAlarmList, textAreaAlarmList = st.columns([1, 4])
with buttonColAlarmList:
    if st.button("警報一覧　　"):
        sleep(0.5)
        st.switch_page("pages/alarm_list.py")

with textAreaAlarmList:
    st.text("現在発表されている警報・注意報を一覧化しました")

buttonColStatsInfo, textAreaStatsInfo = st.columns([1, 4])
with buttonColStatsInfo:
    if st.button("統計情報　　"):
        sleep(0.5)
        st.switch_page("pages/statistics_information.py")

with textAreaStatsInfo:
    st.text("危険生物の目撃件数などの統計情報を扱います")

buttonColSightInfo, textAreaSightInfo = st.columns([1, 4])
with buttonColSightInfo:
    if st.button("目撃情報参照"):
        sleep(0.5)
        st.switch_page("pages/sighting_information.py")

with textAreaSightInfo:
    st.text("登録された生物の目撃情報を参照します")