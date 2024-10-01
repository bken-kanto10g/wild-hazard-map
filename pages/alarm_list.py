import os
from pathlib import Path
import pandas as pd
import streamlit as st
import src.utility.const as const
import src.navigate.app2menu as a2m
import src.common as cmn

# 色を決定する関数
def get_color(df, value, color) -> str:
    if value == 0:
        return 'background-color: white;'   # 灰色（ゼロ）
    
    # 色の濃さを計算（最大値に基づいて色の濃淡を表現）
    # 透過度を計算（データの最大値に基づいて透明度を設定）
    alpha = min(1.0, max(0.1, value / df[color].max()))  # 0.1 ~ 1.0の範囲で透過度を設定

    if color == '目撃合計数':
        return f'background-color: rgba(255, 255, 0, {alpha});'  # 黄色
    elif color == '遭遇合計数':
        return f'background-color: rgba(255, 165, 0, {alpha});'  # オレンジ
    elif color == '襲撃合計数':
        return f'background-color: rgba(255, 0, 0, {alpha});'    # 赤色

# パス生成
basepath = Path(os.path.dirname(os.path.abspath(__file__))).parent
datapath = basepath.joinpath('results')

# フォルダ内の期間を取得
date_choice_list = [f.name for f in datapath.glob('*-*')]

# ページ表記
st.set_page_config(
    page_title="警報一覧",
    page_icon="🚨",
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
leftobj3, _ = st.columns([3, 7])

# 都道府県のセレクトボックスを表示
choice_region = leftobj3.selectbox(
    '選択地域', 
    list(cmn.PREF_NAMW_VS_CODE.keys()) + ["全国"]
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
            # データパス存在確認
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
            
            # 画像パス
            image_root = basepath / 'img' / choice_animal
            
            # フォルダパスを作成して警報・注意報情報を取得
            df = pd.read_csv(
                dirpath / '地域別警報注意報一覧.csv',
                encoding='cp932'
            )

            # 地域選択
            if choice_region != "全国":
                df = df[df['都道府県名'] == choice_region]

            # 都道府県名、市区町村名と目撃、遭遇、襲撃のデータを表示
            disable = True
            st.title(f"警報一覧 {signature}")
            for index, row in df.iterrows():
                # 合計数がゼロにならない列名を集約
                enable_kinds = {}
                for kind in ('目撃', '遭遇', '襲撃'):
                    col = f'{kind}合計数'
                    if row[col] != 0:
                        enable_kinds.setdefault(kind, col)

                # 辞書型が空の場合はスキップ
                if len(enable_kinds.keys()) == 0:
                    continue

                # 画像パス生成
                if '目撃' in enable_kinds.keys():
                    imagepath = image_root / '目撃.jpg'

                if '遭遇' in enable_kinds.keys():
                    imagepath = image_root / '遭遇.jpg'

                if '襲撃' in enable_kinds.keys():
                    imagepath = image_root / '襲撃.jpg'

                # 対象の警報を左詰めで表示
                disable = False
                c1, img, c2, c3, c4 = st.columns([3, 1, 2, 2, 2])
                if imagepath.exists():
                    img.image(str(imagepath), use_column_width=True)
                cs = [c2, c3, c4]
                c1.markdown(f"### {row['都道府県名']} {row['市区町村名']}")
                for i, (kind, col) in enumerate(enable_kinds.items()):
                    cs[i].markdown(
                        f"<div style='{get_color(df, row[col], col)}; padding: 10px; margin: 5px;'>"
                        f"{'' if row[col] == 0 else f'{kind}レベル'}</div>",
                        unsafe_allow_html=True
                    )
                
            if disable:
                st.title('警報なし')