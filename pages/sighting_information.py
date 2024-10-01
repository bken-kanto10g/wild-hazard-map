import os
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
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
df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
df.sort_values(
    by=['date'], 
    ascending=[False],
    inplace=True
)
df = df[
    [
        'pref_code', 'pref_name', 'city_code', 'city_name', 
        'animal', 'date', 'year', 'month', 'lat', 'lon', 'head', 'category'
    ]
]
df.rename(
    columns={
        'pref_code': '都道府県コード', 
        'pref_name': '都道府県名', 
        'city_code': '市区町村コード', 
        'city_name': '市区町村名', 
        'animal': '動物名', 
        'date': '出没日', 
        'year': '出没年',
        'month': '出没月',
        'lat': '緯度', 
        'lon': '経度', 
        'head': '出没数'
    },
    inplace=True
)

# ページ表記
st.set_page_config(
    page_title="目撃情報",
    page_icon="📍",
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
    list(dict().fromkeys(df['動物名'].values.tolist()).keys())
)

# オブジェクト定義(2)
leftobj2, _ = st.columns([3, 7])

# 選択地域のセレクトボックスを表示
choice_region = leftobj2.selectbox(
    '選択地域', 
    ['全国'] + list(dict().fromkeys(df['都道府県名'].values.tolist()).keys())
)

# 表示期間スライダーを表示
min_date = df['出没日'].min()
max_date = df['出没日'].max()
choice_range = st.slider(
    '表示期間を指定してください',
    value=(min_date,  max_date),
    format='YYYY/MM/DD',
    min_value=min_date, 
    max_value=max_date
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
                df = df[df['都道府県名'] == choice_region]
            
            # 対象生物及び表示期間で絞る
            df: pd.DataFrame = df[
                (df['動物名'] == choice_animal) &
                (df['出没日'] >= choice_range[0]) &
                (df['出没日'] <= choice_range[1])
            ]

            # 出没年、出没月でソート
            df.sort_values(
                by=['出没年', '出没月'], 
                ascending=[False, False],
                inplace=True
            )

            # 出没年、出没月を組み合わせた列の作成
            df['出没年月'] = df['出没年'] * 100 + df['出没月']

            # 出没年、出没月を組み合わせたカスタムラベルを作成
            df['出没年月ラベル'] = df['出没年'].astype(str) + '-' + df['出没月'].astype(str).str.zfill(2)

            # データ長チェック
            if df.shape[0] != 0:
                # データを地図上にプロット
                fig = px.scatter_mapbox(
                    df,
                    lat='緯度',
                    lon='経度',
                    color='出没年',
                    text="動物名",  # ピンに表示されるテキスト
                    hover_name="動物名",  # ホバー時に表示される名前
                    hover_data=[
                        '都道府県コード', 
                        '都道府県名', 
                        '市区町村コード', 
                        '市区町村名', 
                        '出没日',
                        '出没数'
                    ],
                    color_discrete_sequence=["fuchsia"],  # ピンの色
                    zoom=8,  # ズームレベル
                    height=800
                )

                # カスタムラベルを適用するためにカラーバーを更新
                # fig.update_layout(coloraxis_colorbar=dict(
                #     title="出没年月",
                #     tickvals=df['出没年月'],  # 数値化した値
                #     ticktext=df['出没年月ラベル']  # カスタムラベル
                # ))

                # マップボックスのスタイルとトークンを設定
                fig.update_layout(
                    mapbox_style="open-street-map", 
                    mapbox_accesstoken='your_mapbox_access_token'
                )

                # 地図の中心を設定 (日本の中央付近に設定)
                fig.update_layout(
                    mapbox_center={
                        "lat": df['緯度'].mean(), 
                        "lon": df['経度'].mean()
                    }
                )

                # グラフ表示
                st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.error('該当するデータはゼロ件です')