import os
import urllib
import requests
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import geopandas as gpd
import plotly.express as px
from shapely.geometry import Polygon
import src.common as cmn
import src.utility.const as const
import src.navigate.app2menu as a2m

# 国土地理院API
GSI_API = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="

# パス生成
basepath = Path(os.path.dirname(os.path.abspath(__file__))).parent
datapath = basepath.joinpath('results')

# フォルダ内の期間を取得
date_choice_list = [f.name for f in datapath.glob('*-*')]

# ページ表記
st.set_page_config(
    page_title="ミクロワイルドハザードマップ",
    page_icon="🔎",
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
leftobj1, _, rightobj1 = st.columns([5, 2, 3])

# 期間のセレクトボックスを表示
choice_date = leftobj1.selectbox(
    '基準期間', 
    date_choice_list[1:]
)

# 予測のセレクトボックスを表示
choice_predict = rightobj1.selectbox(
    '予測選択', 
    ['予測しない'] + [f'{i}週間先' for i in range(1, 10)]
)

# オブジェクト定義(2)
leftobj2, _ = st.columns([2, 8])

# 対象生物のセレクトボックスを表示
choice_animal = leftobj2.selectbox(
    '対象生物', 
    const.ANIMALS
)

# オブジェクト定義(3)
leftobj3, _, rightobj3 = st.columns([7, 1, 2])

# 住所入力を表示
input_address = leftobj3.text_input(
    '調査対象の所在地を教えて下さい',
    max_chars=40
)

# 範囲選択欄を表示
choice_range = rightobj3.selectbox(
    '範囲選択',
    [f'{(i + 1) * 5}km' for i in range(10)]
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
            # チャート表示エリアの定義
            title, _ = st.columns([7, 3])
            mapchart, listchart = st.columns([7, 3])
            nowlist, comblist = st.columns([5, 5])

            # 範囲選択から値を取り出す
            radius_km = float(choice_range.replace('km', ''))

            # パス存在確認
            if choice_predict == '予測しない':
                # 予測しない場合
                dirpath = datapath / choice_date / choice_animal
                signature = choice_date
            else:
                # 予測する場合
                dirpath = datapath / choice_date / choice_animal / 'predicted' / choice_predict
                signature = f'{choice_date}({choice_predict})' 
                if not dirpath.exists():
                    # パスが存在しない場合は予測しないを選択する
                    dirpath = datapath / choice_date / choice_animal
                    signature = choice_date

            # フォルダパスを作成して警報・注意報情報を取得
            df = pd.read_csv(
                dirpath / '警報注意情報.csv',
                encoding='cp932'
            )
            diff = pd.read_csv(
                dirpath / 'diff.csv',
                encoding='cp932'
            )
            diff.rename(
                columns={
                    '警報注意報(前回)': '警報注意報(前期)',
                    '警報注意報(今回)': '警報注意報(今期)',
                },
                inplace=True
            )

            # 国土地理院APIを使って緯度経度を求める
            s_quote = urllib.parse.quote(input_address)
            response = requests.get(GSI_API + s_quote)
            if len(address := response.json()) != 0:
                # 住所における緯度経度取得
                (ownlon, ownlat) = address[0]['geometry']['coordinates']

                # ハーバーサイン法を使って二点間の距離を算出
                df['距離'] = df.apply(
                    lambda row: cmn.haversine(
                        x1=ownlat, 
                        x2=row['minlat'], 
                        y1=ownlon, 
                        y2=row['minlon']
                    ), 
                    axis=1
                )

                # 算出した距離以下になるデータを抽出
                df = df[df['距離'] <= radius_km]
                diff = diff[diff['grid3rd'].isin(df['grid3rd'])]

                # 各種ポリゴン用の座標情報へ変換
                df['geometry'] = df.apply(
                    lambda x: Polygon(
                        [
                            (x['minlon'], x['minlat']),
                            (x['minlon'], x['maxlat']),
                            (x['maxlon'], x['maxlat']),
                            (x['maxlon'], x['minlat'])
                        ]
                    ), 
                    axis=1
                )

                # mapboxによる可視化
                df.rename(
                    columns={
                        # 'prefcode': '都道府県コード',
                        # 'citycode': '市区町村コード', 
                        'minlon': '経度', 
                        'minlat': '緯度', 
                        'maxlon': '最大経度', 
                        'maxlat': '最大緯度', 
                        'grid3rd': '1kmメッシュ'
                    },
                    inplace=True
                )
                geometry = px.choropleth_mapbox(
                    df, 
                    geojson=gpd.GeoSeries(df['geometry']).__geo_interface__, 
                    locations=df.index, 
                    color='警報注意報',
                    color_discrete_map=cmn.CATEGORY_VS_COLOR,
                    center=dict(
                        lat=np.mean(df[['緯度', '最大緯度']].mean(axis=0)),
                        lon=np.mean(df[['経度', '最大経度']].mean(axis=0))
                    ),
                    hover_data=['警報注意報', '都道府県名', '市区町村名', '緯度', '経度', '1kmメッシュ'],
                    mapbox_style='open-street-map',
                    opacity=0.5,
                    zoom=10 - int(radius_km / 15.0), 
                    height=700
                )

                # 前期と今期を左結合する
                _diff = diff[diff['警報注意報(今期)'] != '安全']
                _diff['警報注意報(前期)'] = pd.Categorical(
                    _diff['警報注意報(前期)'], 
                    categories=list(cmn.CATEGORY_VS_COLOR.keys())[1:], 
                    ordered=True
                )
                _diff['警報注意報(今期)'] = pd.Categorical(
                    _diff['警報注意報(今期)'], 
                    categories=list(cmn.CATEGORY_VS_COLOR.keys())[1:], 
                    ordered=True
                )
                _diff.sort_values(
                    by=['警報注意報(前期)', '警報注意報(今期)'], 
                    ascending=True,
                    inplace=True
                )
                df_color = _diff.style.applymap(
                    lambda s: f'background-color: {cmn.CATEGORY_VS_COLOR[s]}; color: black;',
                    subset=['警報注意報(前期)', '警報注意報(今期)']
                )

                # 統計情報の作成
                count_now = df.groupby('警報注意報').size().reset_index(name='合計')
                count_now['警報注意報'] = pd.Categorical(
                    count_now['警報注意報'], 
                    categories=list(cmn.CATEGORY_VS_COLOR.keys())[1:], 
                    ordered=True
                )
                count_now.sort_values(
                    by=['警報注意報'], 
                    ascending=True,
                    inplace=True
                )
                count_now.columns = ['警報・注意報(今期)', '地点数']
                count_now.reset_index(inplace=True)
                count_now = count_now.style.applymap(
                    lambda s: f'background-color: {cmn.CATEGORY_VS_COLOR[s]}; color: black;',
                    subset=['警報・注意報(今期)']
                )

                # 統計情報の作成
                count_combinations = diff.groupby(
                    ['警報注意報(前期)', '警報注意報(今期)']
                ).size().reset_index(name='地点数')
                count_combinations['警報注意報(前期)'] = pd.Categorical(
                    count_combinations['警報注意報(前期)'], 
                    categories=list(cmn.CATEGORY_VS_COLOR.keys())[1:], 
                    ordered=True
                )
                count_combinations['警報注意報(今期)'] = pd.Categorical(
                    count_combinations['警報注意報(今期)'], 
                    categories=list(cmn.CATEGORY_VS_COLOR.keys())[1:], 
                    ordered=True
                )
                count_combinations.sort_values(
                    by=['警報注意報(前期)', '警報注意報(今期)'], 
                    ascending=True,
                    inplace=True
                )
                count_combinations.reset_index(inplace=True)
                count_combinations = count_combinations.style.applymap(
                    lambda s: f'background-color: {cmn.CATEGORY_VS_COLOR[s]}; color: black;',
                    subset=['警報注意報(前期)', '警報注意報(今期)']
                )

                # 表示
                title.title(f'表示期間：{signature}')
                mapchart.title('ハザードマップ')
                mapchart.plotly_chart(geometry, use_container_width=True)
                listchart.title('ハザードリスト')
                listchart.dataframe(df_color, height=700, use_container_width=True)
                nowlist.title('今期の合計数')
                nowlist.dataframe(count_now, height=200, use_container_width=True)
                comblist.title('前期今期の組み合わせ合計数')
                comblist.dataframe(count_combinations, height=200, use_container_width=True)

            else:
                # 存在しない住所が入力された場合
                st.error(f'入力された住所(={input_address})は存在しません')

            #########################
            #### データロード待ち ####
            #########################
        
        st.session_state.loading = False    # 決定ボタン活性化

    st.markdown('</div>', unsafe_allow_html=True)