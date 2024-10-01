import os
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import src.utility.const as const
import src.navigate.app2menu as a2m

# データ取得
basepath = Path(os.path.dirname(os.path.abspath(__file__))).parent
datapath = basepath.joinpath('data').joinpath('fauna')
df = pd.read_csv(
    datapath.joinpath('全国危険生物出没情報一覧.csv'),
    index_col=0,
    encoding='cp932'
)
df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d')
df.sort_values(
    by=['date'], 
    ascending=[False],
    inplace=True
)

# ページ表記
st.set_page_config(
    page_title="統計情報",
    page_icon="📊",
    layout="wide"
)

# ハンバーガーメニューの削除
st.markdown(
    const.DELETE_HAMBURGER_MENU,
    unsafe_allow_html=True
)

# サイドバー定義
a2m.make_sidebar()

# 初期値の設定：loadingの初期状態をFalseに設定
if 'loading' not in st.session_state:
    st.session_state['loading'] = False

# オブジェクト定義(1)
leftobj1, _ = st.columns([2, 8])

# 対象生物のセレクトボックスを表示
choice_animal = leftobj1.selectbox(
    '対象生物', 
    list(dict().fromkeys(df['animal'].values.tolist()).keys())
)

# オブジェクト定義(2)
leftobj2, _ = st.columns([3, 7])

# 選択地域のセレクトボックスを表示
choice_region = leftobj2.selectbox(
    '選択地域', 
    ['全国'] + list(dict().fromkeys(df['pref_name'].values.tolist()).keys())
)

# 決定ボタン以降のオブジェクトのコンテナ化
with st.container():
    # 決定ボタンを配置
    button_class = "button-disabled" if st.session_state.loading else ""
    st.markdown(f'<div class="right-align {button_class}">', unsafe_allow_html=True)
    if st.button("決定"):
        # 決定ボタン押下後の処理
        st.session_state.loading = True    # 決定ボタン不活性化
        with st.spinner("データを読み込み中..."):
            #########################
            #### データロード待ち ####
            #########################
            # 全国以外は地域を絞る
            if choice_region != '全国':
                df = df[df['pref_name'] == choice_region]
            
            # 対象生物で絞る
            df: pd.DataFrame = df[df['animal'] == choice_animal]

            # 週、月、四半期、年の列を作成
            df['週'] = df['date'].dt.to_period('W-SUN')
            df['月'] = df['date'].dt.to_period('M')
            df['四半期'] = df['date'].dt.to_period('Q')
            df['年'] = df['date'].dt.to_period('Y')

            # 週、月、四半期、年に基づく合計値を算出
            weekly_sum = df.groupby('週')['head'].sum().reset_index()
            monthly_sum = df.groupby('月')['head'].sum().reset_index()
            quarterly_sum = df.groupby('四半期')['head'].sum().reset_index()
            yearly_sum = df.groupby('年')['head'].sum().reset_index()

            # 文字列型へキャスト
            weekly_sum['週'] = weekly_sum['週'].astype(str)
            monthly_sum['月'] = monthly_sum['月'].astype(str)
            quarterly_sum['四半期'] = quarterly_sum['四半期'].astype(str)
            yearly_sum['年'] = yearly_sum['年'].astype(str)

            # 週ごとの頭数の散布図を作成
            fig_weekly = px.scatter(
                weekly_sum, 
                x='週', y='head', 
                title='週ごとの目撃頭数の推移'
            )
            fig_weekly.update_xaxes(rangeslider_visible=True)

            # 月ごとの頭数の棒グラフを作成
            fig_monthly = go.Figure()
            fig_monthly.add_trace(
                go.Bar(
                    x=monthly_sum['月'], 
                    y=monthly_sum['head'], 
                    name='目撃頭数'
                )
            )
            fig_monthly.update_layout(title='月ごとの目撃頭数の推移')
            fig_monthly.update_xaxes(rangeslider_visible=True)

            # 四半期ごとの頭数の棒グラフを作成
            fig_quarterly = go.Figure()
            fig_quarterly.add_trace(
                go.Bar(
                    x=quarterly_sum['四半期'], 
                    y=quarterly_sum['head'], 
                    name='目撃頭数'
                )
            )
            fig_quarterly.update_layout(title='四半期ごとの目撃頭数の推移')
            fig_quarterly.update_xaxes(rangeslider_visible=True)

            # 年ごとの頭数の棒グラフを作成
            fig_yearly = go.Figure()
            fig_yearly.add_trace(
                go.Bar(
                    x=yearly_sum['年'], 
                    y=yearly_sum['head'], 
                    name='目撃頭数'
                )
            )
            fig_yearly.update_layout(title='年ごとの目撃頭数の推移')
            fig_yearly.update_xaxes(rangeslider_visible=True)

            # グラフ表示
            st.plotly_chart(fig_weekly, use_container_width=True)
            st.plotly_chart(fig_monthly, use_container_width=True)
            st.plotly_chart(fig_quarterly, use_container_width=True)
            st.plotly_chart(fig_yearly, use_container_width=True)