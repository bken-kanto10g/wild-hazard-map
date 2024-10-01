import contextlib
from pathlib import Path
from datetime import datetime as dt
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

#==================================================================================================#
# 定数
#--------------------------------------------------------------------------------------------------#
ANIMAL = "ツキノワグマ"
BASEDATE = dt.strptime('2024/06/29', '%Y/%m/%d')    # 基準日 2024/6/29 (土)
WEEK_INTERVAL = 104    # インターバル週数
MONTH_INTERVAL = 3    # インターバル月数
EPSILON = 0.000001
PREDICT_MAX_WEEK = 8
MAX_CLUSTER_NUM = 4
PREF_NAMW_VS_CODE = {
    "青森県": "02",
    "岩手県": "03",
    "宮城県": "04",
    "秋田県": "05",
    "山形県": "06",
    "福島県": "07"
}
PREF_NAME_VS_GRID1ST_LIST = {
    "青森県": [6240, 6241, 6139, 6140, 6141, 6039, 6040, 6041],
    "岩手県": [6040, 6041, 5940, 5941, 5942, 5840, 5841],
    "宮城県": [5840, 5841, 5740, 5741, 5640],
    "秋田県": [6039, 6040, 5939, 5940, 5839, 5840],
    "山形県": [5839, 5840, 5739, 5740, 5639, 5640],
    "福島県": [5639, 5640, 5641, 5539, 5540, 5541]
}
RISK_CATEGORIES = ['目撃', '食害', '物的被害', '人的被害']
LAND_CATEGORIES = ['田', '他農用地', '森林', '荒地', '建物用地', '道路', '鉄道', '他用地', '海浜', 'ゴルフ場']
OCEAN_CATEGORIES = ['河川湖沼', '海水域']
WEATHER_ITEMS = ('平均気温', '最高気温', '最低気温', '降水量', '日照時間', '平均湿度')
CATEGORY_VS_COLOR = {
    '－': 'grey',
    '安全': 'cyan',
    '目撃': 'yellow',
    '遭遇': 'orange',
    '襲撃': 'red'
}
EXTRACT_ALERT_COLUMNS = {
    '警報・注意報(前期)': '警報・注意報(前期)',
    '警報・注意報': '警報・注意報(今期)',
    'prefcode': '都道府県コード',
    'citycode': '市区町村コード',
    'minlat': '緯度',
    'minlon': '経度',
    'grid3rd': '3次メッシュコード'
}

#==================================================================================================#
# 関数
#--------------------------------------------------------------------------------------------------#
def calc_grid1st(lon: float, lat: float) -> int:
    """1次メッシュ計算関数

    1次メッシュの定義は以下
        1次メッシュ = (緯度 × 1.5)の整数部 × 100.0 + (経度 - 100)の整数部

    Args:
        lon (float): 経度
        lat (float): 緯度

    Returns:
        int: 1次メッシュ(4桁)

    """
    return int(lat * 1.5) * 100 + int(lon - 100.0)

def calc_grid2nd(lon: float, lat: float) -> int:
    """2次メッシュ計算関数

    2次メッシュの定義は以下
        2次メッシュ = 1次メッシュ × 100 + X * 10 + Y
        X = 緯度 * 12.0 mod 8
        Y = (経度 - 100.0) * 8.0 mod 8
        ※8等分のため8の剰余を取っている

    Args:
        lon (float): 経度
        lat (float): 緯度

    Returns:
        int: 2次メッシュ(6桁)

    """
    grid1st = calc_grid1st(lon, lat) * 100
    return grid1st + int(lat * 12.0 % 8) * 10 + int((lon - 100.0) * 8.0) % 8

def calc_grid3rd(lon: float, lat: float) -> int:
    """3次メッシュ計算関数

    3次メッシュの定義は以下
        3次メッシュ = 2次メッシュ × 100 + X * 10 + Y
        X = 緯度 * 120.0 mod 10
        Y = (経度 - 100.0) * 80.0 mod 10
        ※10等分のため10の剰余を取っている

    Args:
        lon (float): 経度
        lat (float): 緯度

    Returns:
        int: 3次メッシュ(6桁)

    """
    grid2nd = calc_grid2nd(lon, lat) * 100
    return grid2nd + int(lat * 120 % 10) * 10 + int((lon - 100) * 80) % 10

def calc_grid2lonlat(mesh: int) -> tuple:
    """メッシュ緯度経度変換処理

    1～3次メッシュの基準となる緯度経度を算出する

    Args:
        mesh (int): 1～3次メッシュ

    Returns:
        tuple: 緯度経度情報
            float: 経度
            float: 緯度

    """
    # どんな桁が来ても6桁に置換する処理
    strmesh = str(mesh)
    strmesh = strmesh + '0' * (8 - len(strmesh))

    # 上4桁の処理(1次メッシュ)
    lat = float(strmesh[:2]) / 1.5
    lon = float(strmesh[2:4]) + 100.0

    # 上5～6桁の処理(2次メッシュ)
    lat += float(strmesh[4]) / 12.0
    lon += float(strmesh[5]) / 8.0

    # 下2桁の処理(3次メッシュ)
    lat += float(strmesh[6]) / 120.0
    lon += float(strmesh[7]) / 80.0

    return (lon, lat)

def calc_next2point(
    mesh: int, 
    left: bool=False, 
    right: bool=False, 
    up: bool=False, 
    down: bool=False
) -> int:
    """隣接メッシュ算出

    原点のメッシュコードに隣接するメッシュコードを算出する

    Args:
        mesh (int): 原点メッシュコード
        left (bool): Trueのとき左へ進む
        right (bool): Trueのとき右へ進む
        up (bool): Trueのとき上へ進む
        down (bool): Trueのとき下へ進む

    Returns:
        int: 隣接するメッシュコード

    """
    # 原点の緯度経度
    (lon, lat) = calc_grid2lonlat(mesh)

    if left:
        # 経度に関して原点-1/80.0
        lon -= (1.0 / 80.0)

    if right:
        # 経度に関して原点+1/80.0
        lon += (1.0 / 80.0)

    if left:
        # 経度に関して原点-1/80.0
        lon -= (1.0 / 80.0)

    if up:
        # 緯度に関して原点+1/120.0
        lat += (1.0 / 120.0)

    if down:
        # 緯度に関して原点-1/120.0
        lat -= (1.0 / 120.0)

    return calc_grid3rd(lon, lat)

def haversine(x1: float, x2: float, y1: float, y2: float) -> float:
    """ハーバーサイン法による距離算出処理

    ハーバーサイン法を用いた球面上の任意の二点の距離を計算する関数

    Args:
        x1 (float): 緯度1
        x2 (float): 緯度2
        y1 (float): 経度1
        y2 (float): 経度2

    Returns:
        float: 二点間の距離[km]

    """
    lat1, lon1, lat2, lon2 = map(np.radians, [x2, y2, x1, y1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    # return 6378.137 * np.acos(
    #     np.sin(y1) * np.sin(y2) + np.cos(y1) * np.cos(y2) * np.cos(x2 - x1)
    # )
    return 6378 * c

def abc_categorizer(cumsum_ratio: float) -> str:
    """ABC分析に基づくカテゴライズ関数

    累積割合をABC分析に基づく範囲で警報・注意報をカテゴライズする処理

    Args:
        cumsum_ratio (float): 累積割合

    Returns:
        str: 警報・注意報

    """
    if cumsum_ratio < 0.71:
        category = 'CAUTION'

    elif 0.71 <= cumsum_ratio < 0.91:
        category = 'WARNING'

    else:
        category = 'DANGER'
    
    return category

@contextlib.contextmanager
def WIP(target_root: Path, filename: str):
    finishpath = target_root.joinpath(f'.finish_{filename}')
    if not finishpath.exists():
        wippath = target_root.joinpath(f'.{filename}')
        if not wippath.exists():
            with open(wippath, 'w'):
                pass
        try:
            yield
            # 正常時の場合のみ削除
            wippath.unlink(missing_ok=False)
            with open(finishpath, 'w'):
                pass
            print(filename, '実行完了')
        except Exception as e:
            print(e)
            print(filename, '実行失敗')
    
    else:
        print(filename, '実行済み')

def data_combin_b2w_2p_in_latlon(
    src: pd.DataFrame,
    dst: pd.DataFrame,
    columns_in_dst2add2src: list,
    src_latlon_columns: list = ["lat", "lon"],
    dst_latlon_columns: list = ["lat", "lon"],
) -> pd.DataFrame:
    """緯度経度の二点間におけるsrcとdstの結合処理

    緯度経度を持っているsrc, dstの二つのデータに関して
    srcの任意の行と緯度経度が一番近いdstのある行と左結合させるための関数

    Args:
        src (DataFrame): 結合元データ
        dst (DataFrame): 結合先データ
        columns_in_dst2add2src (list): srcに結合したいdstの列名
        src_latlon_columns (list): src側の緯度経度の列名
        dst_latlon_columns (list): dst側の緯度経度の列名

    Returns:
        DataFrame: 結合後のデータ

    """
    copy = src.copy()
    src_coords = np.radians(src[src_latlon_columns])
    dst_coords = np.radians(dst[dst_latlon_columns])
    tree = BallTree(
        dst_coords, 
        leaf_size=15, 
        metric='haversine'
    )
    _, indices = tree.query(
        src_coords, 
        k=1
    )
    copy[columns_in_dst2add2src] = dst.loc[
        dst_coords.iloc[indices.flatten()].index, 
        columns_in_dst2add2src
    ].values

    return copy