# =======================
# 1. Import 區 (【修改處：依功能分類整理 import】)
# =======================
import os
import glob
import json
import ast
from datetime import datetime, timedelta

# 第三方庫
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import plotly.express as px
import matplotlib.pyplot as plt
import streamlit as st
from streamlit_plotly_events import plotly_events
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pydeck as pdk
from itertools import product
import pytz
import base64
import re
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import random
from collections import Counter
import streamlit.components.v1 as components
from streamlit.components.v1 import html
from io import StringIO
import hashlib
import schedule
import time
import threading
import logging
import shutil


# 自訂函式與變數（依需求調整，請根據實際情況修改此處 import）
from function import (
    data_root,
    today,
    last_scan_time,
    df_scan,
    df_light,
    df_click_lig,
    function_import_error,
)
if function_import_error:
    st.error(f"🚨 {function_import_error}")
    st.stop()

# 設定日誌以便除錯
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)
# =======================
# 2. 基本配置與常數 (【修改處：定義 page config 與常數】)
# =======================
st.set_page_config(page_title="LiG Dashboard",layout="wide",)
TOKEN_FILE = "auth_token.json"  # 本地文件保存 Token 的路徑
taipei_tz = pytz.timezone("Asia/Taipei")    # 設置台北時區
CORE_API_SERVER = "https://api.lig.com.tw"
DASHBOARD_AGENT = "LigDashboard"
project_filepath = os.path.join("data", "projects_new_0306.csv")

today = datetime.now().date()
yesterday = today - timedelta(days=1)
start_of_week = today - timedelta(days=today.weekday())
start_of_last_week = start_of_week - timedelta(days=7)
end_of_last_week = start_of_week - timedelta(days=1)
start_of_month = today.replace(day=1)
if today.month == 1:
    start_of_last_month = today.replace(year=today.year - 1, month=12, day=1)
else:
    start_of_last_month = today.replace(month=today.month - 1, day=1)
end_of_last_month = start_of_month - timedelta(days=1)

#====================================================
# 3. CSS 樣式定義（抽離常數）
#====================================================

BASE_CSS = """
    <style>
    .date-input-row {
    display: inline-block;
    height: 38px;
    width: 100%; /* 根據父容器調整寬度 */
    padding: 5px 10px; /* 垂直方向的內邊距確保文字置中 */
    font-size: 16px;
    line-height: 28px;  /* 調整行高，與框高度匹配 */
    color: #333;
    background-color: #96c5df;
    background-clip: padding-box;
    border: 0px solid #ccc;
    border-radius: 4px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    .date-input-row label {
        margin-right: 10px;
        font-weight: bold;
        white-space: nowrap;
    }
    .date-input-row input {
        flex: 1;
    }
    .page-title {
        background-color: #fff;
        text-align: right;
        box-shadow: none;
        padding: 5px 0;
    }
    .page-title-center {
        background-color: #fff;
        text-align: left;
        box-shadow: none;
        padding: 5px 0;
    }
    </style>
    """
st.markdown(BASE_CSS,unsafe_allow_html=True)

METRIC_CSS = """
    <style>
    .custom-metric {
        background-color: #f0f8ff; /* 淡藍色背景 */
        padding: 10px;
        border-radius: 10px; /* 圓角邊框 */
        text-align: center; /* 置中 */
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); /* 陰影效果 */
        margin-bottom: 5px; /* 與其他元素的距離 */
    }
    .custom-metric h1 {
        margin: 0;
        font-size: 1.5em; /* 調整數字大小 */
        color: #333; /* 數字顏色 */
    }
    .custom-metric p1 {
        margin: 0;
        font-size: 1em; /* 標題大小 */
        color: #666; /* 標題顏色 */
    }
    .custom-metric p2 {
        margin: 0;
        font-size: 1em; /* 標題大小 */
        color: red; /* 標題顏色 */
    }
    </style>
    """
# metric css
st.markdown(METRIC_CSS,unsafe_allow_html=True)

st.markdown("""
    <style>
    div[data-testid="stElementContainer"] .stPlotlyChart {
        transform: scale(0.8) !important;  /* 使用 !important 提高優先級 */
        transform-origin: top left;
        width: 125% !important;  /* 補償縮放 */
        height: auto !important;
    }
    div[data-testid="stElementContainer"] .plot-container {
        transform: scale(0.8) !important;
        transform-origin: top left;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #4f9ac3; 
        color: white; /* 白色文字 */
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        background-color: #CC0000; /* 懸停時變暗的紅色 */
    }
    </style>
    """,
    unsafe_allow_html=True
)
# =======================
# 4. Session 初始化 (【修改處：將預設狀態集中管理】)
# =======================
def initialize():
    default_states = {
        'df_project': lambda: load_data(project_filepath),
        'df_scan': df_scan,
        'df_click_lig': df_click_lig,
        'editing_row_index': None,
        '_lig_token': "",
        'scenes_option': [],
        'light_ids_option': [],
        'coordinates_list_option': [],
        'project_name_new': "",
        'start_date_new': pd.to_datetime("today").date(),
        'end_date_new': pd.to_datetime("today").date(),
        'is_active_new': False,
        'lat_lon_new': "",
        'light_ids_input_new': [],
        'coordinates_list': [],
        'coordinates_input_new': [],
        'scenes_input_new': [],
        'experiment_number': 0,
        'interaction_number': 0,
        'rerun_triggered': False,
        'participants_number': False,
        'merge_data':None,
        'merge_datefilter':None,
        'project_rank':None,
        'email_options':[]
    }

    for key, default in default_states.items():
        if key not in st.session_state:
            value = default() if callable(default) else default
            st.session_state[key] = value

# =======================
# 5. GET Data
# =======================
@st.cache_data
def prepare_project_data(df_prj, df_scan, start_date, end_date):
    # 定義安全解析 Light ID 的函式
    def parse_light_id(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None  # 若解析失敗，返回 None
        return value
    df_prj = df_prj.copy()
    df_prj["Light ID"] = df_prj["Light ID"].apply(parse_light_id)
    df_prj_exploded = df_prj.explode("Light ID").copy()
    df_prj_exploded["Light ID"] = df_prj_exploded["Light ID"].astype(str)
    df_scan_filtered = df_date_filter(df_scan, 'scantime', start_date, end_date)
    
    merge_data = df_scan_filtered.merge(
        df_prj_exploded,
        left_on="lig_id",
        right_on="Light ID",
        how="inner"
    )
    
    return merge_data

def fetch_data_from_server(endpoint, token_key="_lig_token"):
    url = f"{CORE_API_SERVER}/{endpoint}"
    token = st.session_state.get(token_key, "")
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": f"{DASHBOARD_AGENT}/0.1",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from {url}: {e}")
        return {}

def get_coordianate_dict_from_server():
    data = fetch_data_from_server('api/v1/coordinate_systems', token_key="_lig_token").get('coordinate_systems',[])
    return pd.DataFrame(data)

@st.cache_data
def generate_heatmap_data(df):
     # 依據合併後資料產生熱力圖所需的資料
    scan_lonlat = df.copy()
    lat_lon_split = scan_lonlat["Latitude and Longitude"].str.split(",", expand=True)
    scan_lonlat["prj_lat"] = lat_lon_split[0].astype(float)
    scan_lonlat["prj_lon"] = lat_lon_split[1].astype(float)
    df_heatmap = scan_lonlat.groupby("Project Name").agg(
        Scan_Count=("Project Name", "size"),
        prj_lon=("prj_lon", "first"),
        prj_lat=("prj_lat", "first")
    ).reset_index()
    return df_heatmap[['prj_lon', 'prj_lat', 'Scan_Count']].reset_index(drop=True)

@st.cache_data
def fetch_ar_objects(scene_id):
    ar_obj = fetch_data_from_server(f'api/v1/cms_ar_objects_from_scene/{scene_id}', token_key="_lig_token").get('ar_objects',[])
    return ar_obj

@st.cache_data
def get_ar_objects_by_scene_id(scene_id,df_scenelist, token=None):
    url = f"{CORE_API_SERVER}/api/v1/ar_objects_from_scene/{scene_id}"
    headers = {"User-Agent": f"{DASHBOARD_AGENT}/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"取得 light_id {scene_id} 資料錯誤：{e}")
        return []
    
    objects = []
    scene_id_str = str(scene_id)
    # 獲取場景字典
    scene_value = df_scenelist.loc[df_scenelist['Id'] == scene_id_str, 'Name'].iloc[0]
    # data 中 key "scenes" 內部每個 scene 可能包含 "ar_objects"
    for ar_obj in data.get("ar_objects", []):
        objects.append({
            "scene_id": scene_id,
            "scene": f'{scene_id}-{scene_value}',
            "obj_id": ar_obj.get("id"),
            "obj_name": ar_obj.get("name"),
            "location_x": ar_obj.get("location").get("x"),
            "location_y": ar_obj.get("location").get("y"),
            "location_z": ar_obj.get("location").get("z"),
        })
    return objects

def calculate_statistics(click_data, multiplier):
    click_number = int(len(click_data) *multiplier)
    user_number = int(click_data['user_id'].nunique() *multiplier)
    return click_number, user_number

def user_data_fig(df,start_date,end_date):
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    date_range = [d.strftime('%Y-%m-%d') for d in date_range]
    daily_users = (df.groupby(df['clicktime'].dt.strftime('%Y-%m-%d'))['user_id']
            .apply(lambda x: list(x.unique())).reset_index())
    daily_users.columns = ['date', 'user_id']
    # 計算每天的參與人數
    daily_users['daily_active_users'] = daily_users['user_id'].apply(len)
    all_users = set()  # 追蹤所有曾出現的用戶
    new_users_count = []
    returning_users_count = []
    returning_ids_list = []

    for user_list in daily_users['user_id']:
        current_users = set(user_list)
        new_users = current_users - all_users  # 新增用戶
        returning_users = current_users & all_users  # 回購用戶（與之前用戶的交集）
        
        new_users_count.append(len(new_users))
        returning_users_count.append(len(returning_users))
        returning_ids_list.append(list(returning_users))  # 儲存回購用戶的 ID 列表
        
        all_users.update(current_users)  # 更新所有用戶集合

    # 整合數據
    daily_users['daily_active_users'] = daily_users['user_id'].apply(len)
    daily_users['new_users'] = new_users_count
    daily_users['returning_users'] = returning_users_count
    daily_users['returning_ids'] = returning_ids_list
    # 計算累積人數
    daily_users['cumulative_users'] = [len(set(df[df['clicktime'].dt.strftime('%Y-%m-%d') <= date]['user_id'].unique())) 
                                for date in daily_users['date']]

    # 生成完整日期範圍並合併
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    date_range = [d.strftime('%Y-%m-%d') for d in date_range]
    result = pd.DataFrame({'date': date_range})
    result = result.merge(daily_users[['date', 'daily_active_users', 'new_users', 'returning_users', 'returning_ids','cumulative_users']], 
                    on='date', how='left')
    result['daily_active_users'] = result['daily_active_users'].fillna(0).astype(int)
    result['new_users'] = result['new_users'].fillna(0).astype(int)
    result['returning_users'] = result['returning_users'].fillna(0).astype(int)
    result['returning_ids'] = result['returning_ids'].apply(lambda x: x if isinstance(x, list) else [])
    result['cumulative_users'] = result['cumulative_users'].fillna(method='ffill').fillna(0).astype(int)  # 向前填充累積人數

    max_daily = max(result['new_users'] + result['returning_users'])
    max_cumulative = max(result['cumulative_users'])
    scale_factor = max_cumulative / max_daily  # 計算比例因子

    # 統計回購用戶的次數
    returning_ids_flat = [user_id for sublist in result['returning_ids'] for user_id in sublist]  # 展平所有回購 ID
    returning_counts = Counter(returning_ids_flat)  # 計算每個用戶的回購次數

    # 轉為 DataFrame 並排序
    returning_ranking = pd.DataFrame(returning_counts.items(), columns=['user_id', 'return_count'])
    returning_ranking = returning_ranking.sort_values(by='return_count', ascending=False).reset_index(drop=True)

    # 使用 go.Figure 製作圖表
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 添加柱狀圖 - 新增人數（作為參與人數的一部分）
    fig.add_trace(
        go.Bar(
            x=result['date'],
            y=result['new_users'],
            name="新增人數",
            marker_color='skyblue',
            text=result['new_users'],
            textposition='auto'
        ),
        secondary_y=False
    )

    # 添加柱狀圖 - 回購人數（疊加在新增人數上）
    fig.add_trace(
        go.Bar(
            x=result['date'],
            y=result['returning_users'],
            name="回購人數",
            marker_color='salmon',
            text=result['returning_users'],
            textposition='auto'
        ),
        secondary_y=False
    )

    # 添加折線圖 - 累積人數
    fig.add_trace(
        go.Scatter(
            x=result['date'],
            y=result['cumulative_users'],
            name="累積人數",
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=8),
            text=result['cumulative_users'],
            hovertemplate='%{text}'
        ),
        secondary_y=True
    )

    # 更新佈局
    fig.update_layout(
        title=dict(text="每日參與人數與累積人數", x=0.5, xanchor='center'),
        xaxis_title="日期",
        yaxis_title="每日參與人數",
        barmode='stack',  # 柱狀圖疊加
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255, 255, 255, 0.5)', bordercolor='black', borderwidth=1),
        hovermode="x unified",
        template="plotly_white"
    )

    # 更新 Y 軸標籤
    fig.update_yaxes(
        title_text="每日參與人數", 
        secondary_y=False,
        range=[0, max_daily * 1.1],
        dtick=50
    )
    fig.update_yaxes(
        title_text="累積人數", 
        secondary_y=True,
        range=[0, max_daily * scale_factor * 1.1],
        dtick=500
    )
    return daily_users, fig

def generate_user_id_ranking(df):
    # 按 user_id 統計點擊次數
    user_click_counts = df.groupby('user_id').size().reset_index(name='Click Count')
    # 按點擊次數降序排序
    user_click_counts = user_click_counts.sort_values(by='Click Count', ascending=False)
    return user_click_counts

def clickobjdist_with_userpath(fig,user_data, multiplier=1.0):    
    fig_ranking = fig
    user_data['clicktime'] = pd.to_datetime(user_data['clicktime'])
    user_data = user_data.sort_values('clicktime')
    selected_user = user_data['user_id'].iloc[0]  # 預設第一個 user_id
    if not user_data.empty:
        user_data['sequence'] = range(1, len(user_data) + 1)
        fig_ranking.add_trace(
            go.Scatter(
                x=user_data['location_x'],
                y=user_data['location_z'],
                mode='markers+lines+text',  # 添加文字顯示順序
                marker=dict(
                    size=10,
                    color=user_data['sequence'],  # 根據順序漸變顏色
                    colorscale='Blues',
                    showscale=True,
                    symbol='circle',
                    line=dict(width=1, color='black')  # 只保留一個 line 定義
                ),
                line=dict(width=2, color='gray', dash='dash'),  # 虛線表示路徑
                text=user_data['sequence'],  # 在點上顯示順序號
                textposition='top center',
                textfont=dict(size=20, color='red'),
                hovertemplate=(
                    'Time: %{customdata[0]}<br>'
                    'Obj: %{customdata[1]}<br>'
                    'Sequence: %{text}<extra></extra>'
                ),
                customdata=user_data[['clicktime', 'obj_name']].values,
                name=f"Path of {selected_user}"
            )
        )
# 更新圖表標題並啟用圖例
    fig_ranking.update_layout(
        title=f"Click Distribution with User Path for {selected_user or 'None'}",
        showlegend=True,
        xaxis=dict(
            range=[-10, 10],
            scaleanchor="y",
            scaleratio=1,
            tickangle=45
        ),
        yaxis=dict(
            range=[10, -10]
        ),
        width=600,
        height=600,
    )
    user_data['clicktime'] = user_data['clicktime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return fig_ranking, user_data

def generate_project_rank(merge_data, df_prj,merge_data_yesterday,merge_data_today):
    yesterday_scan_counts = merge_data_yesterday.groupby("Project Name").size().reset_index(name="Yesterday Scans")
    today_scan_counts = merge_data_today.groupby("Project Name").size().reset_index(name="Today Scans")
    scan_counts = merge_data.groupby("Project Name").size().reset_index(name="Scan Count")
    # 將總掃描次數與昨天掃描次數 merge 到 df_prj 中，缺失的部分填 0
    df_prj = (
        df_prj.merge(scan_counts, on="Project Name", how="left")
              .merge(yesterday_scan_counts, on="Project Name", how="left")
              .merge(today_scan_counts, on="Project Name", how="left")
              .fillna({"Scan Count": 0, "Yesterday Scans": 0, "Today Scans": 0})
    )
    # 回傳排序後的結果，依據總掃描次數排序
    return df_prj[["Project Name", "Scan Count", "Yesterday Scans","Today Scans"]].sort_values(by="Scan Count", ascending=False)

def get_id_list_from_file():
    all_lights_list = df_light.apply(lambda row: int(row['lig_id']), axis=1).tolist()
    all_ids = [id_ for id_ in all_lights_list]
    return all_ids

def get_coordinates_list_from_server():
    data = fetch_data_from_server('api/v1/coordinate_systems', token_key="_lig_token").get('coordinate_systems',[])    
    return [f'{item['id']}-{item['name']}' for item in data]

#儲存 project_rank 資料的函數
def save_project_rank():
    if 'project_rank_data' in st.session_state:
        # 確保資料夾存在
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        
        # 產生檔案名稱，使用當前日期時間
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_rank_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        try:
            st.session_state.project_rank.to_csv(filepath, index=False)
            logger.info(f"Project rank saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save project rank: {e}")
        
    else:
        logger.warning("No project_rank_data found in session state")


# =======================
# 6. Figure 製圖
# =======================

def plot_heatmpy(df):    
    # 定義熱力圖層
    layer = pdk.Layer(
        "HeatmapLayer",  # 使用熱力圖層
        df,  # 數據源 df_scan_lat_long_datefilter_zvalue_merged
        get_position=["prj_lon", "prj_lat"],  # 指定經緯度列
        get_weight="Scan_Count",  # 指定熱力圖的權重列
        radius_pixels=50,  # 設置熱點的半徑
        colorRange=[  # 自定義顏色範圍
            [33, 102, 172],  # 低強度顏色
            [103, 169, 207],  # ...
            [209, 229, 240],  # ...
            [253, 219, 199],  # ...
            [239, 138, 98],  # ...
            [178, 24, 43],  # 高強度顏色
        ],
        opacity=0.6,  # 設置不透明度
    )
    # 設置地圖初始視圖位置
    view_state = pdk.ViewState(latitude=31.65627693618275, longitude=107.65665580285913, zoom=1.5)
    # 使用pydeck渲染地圖
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            # 啟用地圖控件
            map_style="mapbox://styles/mapbox/light-v9",
        )
    )

def display_metric(title, value, height="100px"):
    st.markdown(f"""
        <div class="custom-metric" style="height: {height};">
            <p1>{title}</p1>
            <h1>{value}</h1>
        </div>
    """, unsafe_allow_html=True)

@st.cache_data
def plot_stacked_histogram_with_dual_y_axis(data, start_date, end_date,timecol, col_name, multiplier):
    data['time_normalized'] = data[timecol].dt.normalize()  # 轉成 00:00 的 Timestamp
    date_index = pd.date_range(start_date, end_date, tz='Asia/Taipei')
    size_result = data.groupby(['time_normalized', col_name]).size()
    daily_counts = (size_result * multiplier).unstack(fill_value=0).reindex(date_index, fill_value=0)
    # 計算累計 count
    daily_counts['cumulative'] = daily_counts.sum(axis=1).cumsum()

    # daily_counts = daily_counts.reset_index().rename(columns={'index': 'date'})
    dates = daily_counts.index
    ticktext = [
        f"<b style='color:red;'>{date.strftime('%b %d')}</b>" if date.weekday() >= 5 else date.strftime('%b %d')
        for date in dates
    ]
    tickvals = dates

    # 使用 Plotly Express 的預設顏色序列
    color_sequence = px.colors.qualitative.Plotly

    # 創建圖表
    fig = go.Figure()

    # 添加堆疊直方圖，每個 trace 明確指定顏色
    for i, col_name in enumerate(daily_counts.columns[:-1]):  # 忽略 'cumulative'
        fig.add_trace(
            go.Bar(
                x=daily_counts.index,
                y=daily_counts[col_name],
                name=f"{col_name}",
                marker=dict(color=color_sequence[i % len(color_sequence)]),
                hovertemplate=f'{col_name}: ' + "%{y}<extra></extra>"
            )
        )

    # # 添加累計折線圖
    fig.add_trace(
        go.Scatter(
            x=daily_counts.index,
            y=daily_counts['cumulative'],
            name="Cumulative Count",
            mode="lines+markers",
            line=dict(color="red"),
            hovertemplate="Date: %{x}<br>Cumulative: %{y}<extra></extra>",
            yaxis='y2',
        )
    )

    # 設置雙 Y 軸
    fig.update_layout(
        # title="Interactive Stacked Histogram with Dual Y-Axis",
        xaxis=dict(
            title="Date",
            tickvals=tickvals,  # 確保每一天都有字
            ticktext=ticktext,  # 自定義文字，週末顯示為紅色
            tickangle=45,  # 旋轉 X 軸標籤
        ),
        yaxis=dict(
            title="Daily Counts",
            range=[0, daily_counts.iloc[:, :-1].values.max() * 1.2],  # Y1範圍從0開始
            showgrid=True,  # 主 Y 軸顯示 Grid
        ),
        yaxis2=dict(
            title="Cumulative Count",
            overlaying="y",  # 與主 Y 軸重疊
            side="right",
            range=[0, daily_counts['cumulative'].max() * 1.2],  # Y2範圍從0開始
            showgrid=False  # 禁用次 Y 軸的 Grid
        ),
        barmode="stack",  # 堆疊模式
        legend=dict(title="Legend", orientation="h", x=0.5, xanchor="center", y=-0.2),
        hovermode="x unified"  # 統一 hover
    )
    daily_counts_csv = daily_counts.reset_index().rename(columns={'index': 'date'})
    daily_counts_csv['date'] = daily_counts_csv['date'].dt.strftime('%Y-%m-%d')
    return daily_counts_csv, fig

def week_pie_fig(df):
    weekday_counts = df['weekday'].value_counts().sort_index()
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_counts = weekday_counts.reindex(range(7), fill_value=0)
    weekday_counts.index = [weekday_names[i] for i in weekday_counts.index]
    total_scans = weekday_counts.sum()
    weekday_proportions = (weekday_counts / total_scans * 100).round(2)  # 轉換為百分比，四捨五入到小數點後兩位
    week_pie_fig = go.Figure(data=[go.Pie(
        labels=weekday_proportions.index,
        values=weekday_proportions.values,
        hole=0.3,  # 設置中空圓形（甜甜圈圖）
        textinfo='label+percent',  # 顯示標籤和百分比
        textposition='auto',  # 文字位置自動調整
        hoverinfo='label+percent+value',  # 懸停顯示標籤、百分比和數值
        marker=dict(colors=px.colors.qualitative.Plotly)  # 使用 Plotly 的預設顏色
    )])

    week_pie_fig.update_layout(
        title={
            "text": "Weekly Scan",
            "x": 0.5,
            "xanchor": "center"
        }
    )
    return week_pie_fig

def time_distribution(df,start_date,end_date):
    # 取得掃描日期 (將時間部分歸零)
    df["scan_date"] = df["scantime"].dt.normalize()

    # 取得掃描時間部分：只取時間，並轉換成固定日期（預設為 1900-01-01）的 datetime 物件
    # df["scan_time_only"] = pd.to_datetime(df["scantime"].dt.strftime('%H:%M:%S'))
    # 修正 scan_time_only：只提取時間部分，轉為一天中的秒數或 datetime.time
    df["scan_time_only"] = df["scantime"].dt.time  # 提取時間部分 (datetime.time 對象)

    # 為了 Plotly 的 Y 軸（需要數值），將時間轉換為一天中的秒數
    df["scan_time_seconds"] = df["scantime"].dt.hour * 3600 + \
                             df["scantime"].dt.minute * 60 + \
                             df["scantime"].dt.second

    date_index = pd.date_range(start_date, end_date, tz='Asia/Taipei', freq='D')
    ticktext = [
    f"<b style='color:red;'>{date.strftime('%b %d')}</b>" if date.weekday() >= 5 else date.strftime('%b %d')
    for date in date_index
    ]
    tickvals = date_index 

    # 繪製散點圖：x 軸用掃描日期，y 軸用當天掃描時間
    fig_time_distribution = go.Figure(data=go.Scatter(
        x=df["scan_date"],
        y=df["scan_time_seconds"],
        mode='markers',
        marker=dict(color='green', opacity=0.6)
    ))
    # 計算整個期間的最高值和最低值（基於秒數）
    overall_max_seconds = df["scan_time_seconds"].max()
    overall_min_seconds = df["scan_time_seconds"].min()

    # 添加最高值的水平線
    fig_time_distribution.add_hline(
        y=overall_max_seconds,
        line_width=3,
        line_color="red",
        opacity=0.8,
        layer="below",
        annotation_text="Max Time",
        annotation_position="right",
        annotation_font=dict(color="red")
    )

    # 添加最低值的水平線
    fig_time_distribution.add_hline(
        y=overall_min_seconds,
        line_width=3,
        line_color="blue",
        opacity=0.8,
        layer="below",
        annotation_text="Min Time",
        annotation_position="right",
        annotation_font=dict(color="blue")
    )
    # 定義 Y 軸每兩小時的刻度
    y_tickvals = list(range(0, 24*3600 + 1, 2*3600))  # 從 0 到 24 小時，每 2 小時
    y_ticktext = [f"{hour:02d}:00" for hour in range(0, 25, 2)]

    # 更新佈局
    fig_time_distribution.update_layout(
        xaxis=dict(
            title="Scan Date",
            type="date",
            range=[start_date - pd.Timedelta(days=2), end_date + pd.Timedelta(days=1)],
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=45,
            tickformat="%b-%d",
            showgrid=True,
            gridcolor="lightgray"
        ),
        yaxis=dict(
            title="Scan Time",
            tickvals=y_tickvals,
            ticktext=y_ticktext,
            range=[0, 24*3600],
            showgrid=True,
            gridcolor="lightgray"
        ),
        height=500
    )
    return fig_time_distribution

def h24_distribution(df,col_name):
    # 計算每 6 小時區間的掃描次數分佈
    df['hour'] = df[col_name].dt.hour  # 提取小時（0-23）

    # 將小時分為 4 個 6 小時區間
    def categorize_hour(hour):
        if 1 <= hour <= 6:
            return "1-6 AM"
        elif 7 <= hour <= 12:
            return "7-12 AM"
        elif 13 <= hour <= 18:
            return "1-6 PM"
        else:  # 19 <= hour <= 24
            return "7-12 PM"

    df['hour_interval'] = df['hour'].apply(categorize_hour)
    hour_interval_counts = df['hour_interval'].value_counts()

    # 定義時間段名稱（確保所有區間都包含）
    hour_intervals = ['1-6 AM', '7-12 AM', '1-6 PM', '7-12 PM']
    
    # 確保所有時間段都有數據（填補缺失的時間段為 0）
    hour_interval_counts = hour_interval_counts.reindex(hour_intervals, fill_value=0)

    # 計算總掃描次數
    total_scans = hour_interval_counts.sum()
    
    # 計算每個時間段的比例
    hour_interval_proportions = (hour_interval_counts / total_scans * 100).round(2)  # 轉換為百分比，四捨五入到小數點後兩位

    # 創建時間區間分佈圓形圖
    fig_h24_distribution = go.Figure(data=[go.Pie(
        labels=hour_interval_proportions.index,
        values=hour_interval_proportions.values,
        hole=0.3,  # 設置中空圓形（甜甜圈圖）
        textinfo='label+percent',  # 顯示標籤和百分比
        textposition='auto',  # 文字位置自動調整
        hoverinfo='label+percent+value',  # 懸停顯示標籤、百分比和數值
        marker=dict(colors=px.colors.qualitative.Plotly)  # 使用 Plotly 的預設顏色
    )])

    fig_h24_distribution.update_layout(
        title={
            "text": f"Hourly Scan Distribution",
            "x": 0.5,
            "xanchor": "center"
        }
    )
    return fig_h24_distribution

def clickobjdist(df,multiplier):
    objclick_size_result = df.groupby(['ar_obj','location_x','location_z']).size().reset_index(name='click_count')
    ranking = objclick_size_result.copy()
    ranking['click_count'] = (ranking['click_count'] * multiplier).astype(int)
    ranking = ranking.sort_values('click_count', ascending=False)
    ranking_top20 = ranking.head(20)
    # 動態計算氣泡大小縮放因子
    min_size = 5   # 最小氣泡大小（可調整）
    max_size = 50  # 最大氣泡大小（可調整）
    click_min = ranking_top20["click_count"].min()  # click_count 最小值
    click_max = ranking_top20["click_count"].max()  # click_count 最大值

    # 如果 click_max == click_min，避免除以零
    if click_max == click_min:
        scale_factor = 0.5  # 若所有值相同，使用固定縮放
    else:
        # 計算縮放因子，使 click_count 映射到 [min_size, max_size]
        scale_factor = (max_size - min_size) / (click_max - click_min)
    # 計算氣泡大小
    bubble_sizes = min_size + (ranking_top20["click_count"] - click_min) * scale_factor

    # 繪製泡泡圖
    fig_ranking = go.Figure()

    fig_ranking.add_trace(
        go.Scatter(
            x=ranking_top20["location_x"],
            y=ranking_top20["location_z"],
            mode='markers',  # 只顯示氣泡
            marker=dict(
                size=bubble_sizes,  # 氣泡大小與點擊次數成正比（調整倍數 0.5）
                color=ranking_top20["click_count"],      # 根據點擊次數著色
                colorscale='blues',                    # 使用橙色漸變（與原 Bar 的 orange 一致）
                opacity=0.85,
                showscale=True,                          # 顯示顏色條
                line=dict(width=0.1, color='black')        # 氣泡邊框
            ),
            text=ranking_top20.apply(lambda row: f"物件: {row['ar_obj']}<br>點擊次數: {row['click_count']}", axis=1),
            hovertemplate='%{text}'  # 懸停時顯示物件名稱和點擊次數
        )
    )
    # 更新佈局
    fig_ranking.update_layout(
        xaxis_title="Location X(m)",
        yaxis_title="Location Y(m)",
        xaxis=dict(
            range=[-10, 10],  # 固定 X 軸範圍
            dtick = 1,
            tickangle=45,      # 傾斜 X 軸標籤，避免重疊
            showgrid=True,
            gridcolor='lightgray',
            gridwidth = 1,
            zeroline=True,    # 顯示 x=0 線
            zerolinecolor='black',  # x=0 線顏色
            zerolinewidth=3
        ),
        yaxis=dict(
            range=[10, -10],   # 固定 Y 軸範圍
            dtick = 1,
            scaleanchor="x",
            scaleratio=1,      # 保證 X 和 Y 軸比例 1:1
            showgrid=True,    # 顯示網格線
            gridcolor='lightgray',
            gridwidth=1,
            zeroline=True,    # 顯示 x=0 線
            zerolinecolor='black',  # x=0 線顏色
            zerolinewidth=3
        ),
        width=600,
        height =600,
        autosize = False,
        template="plotly_white",   # 使用白色主題
        showlegend=False           # 無需圖例
    )
    return fig_ranking,ranking

def plot_user_experience_bar(experience_df, selected_scene):
    df = experience_df[experience_df['scene'] == selected_scene]
    df['label'] = df['user_id'].astype(str)
    fig = go.Figure(data=[
        go.Bar(
            x=df['label'],
            y=df['duration_sec'],
            text=df['duration_sec'],
            textposition='outside',
            marker_color='lightblue'
        )
    ])
    fig.update_layout(
        title=f"{selected_scene} 使用者每段體驗時間（秒）",
        xaxis_title="使用者/日期/段落",
        yaxis_title="體驗時間（秒）",
        xaxis_tickangle=45,
        height=500,
        template="plotly_white"
    )
    return fig

def plot_experience_box(experience_df, selected_scene):
    df = experience_df[experience_df['scene'] == selected_scene]
    fig = px.box(
        df,
        y="duration_sec",
        points="all",
        title=f"{selected_scene} 體驗時間分布",
        labels={"duration_sec": "體驗時間（秒）"},
        template="plotly_white"
    )
    return fig


def plot_experience_box(experience_df, selected_scene):
    df = experience_df[experience_df['scene'] == selected_scene]
    fig = px.box(
        df,
        y="duration_sec",
        points="all",  # 顯示所有數據點
        title=f"{selected_scene} 體驗時間分布",
        labels={"duration_sec": "體驗時間（秒）"},
        template="plotly_white"
    )
    return fig

# =======================
# 7. Table 製表
# =======================

def AgGridTable(df):
    # 配置表格選項
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="single", use_checkbox=False)  # 單選模式，使用勾選框
    gb.configure_grid_options(domLayout="normal")  # 設置表格布局
    gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=8)  # 可選，添加分頁功能
    grid_options = gb.build()
    # 渲染 Ag-Grid
    response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,  # 監控選擇變化
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=400,
        width = '100%',
        use_container_width=True,
        enable_enterprise_modules=False,
    )
    return response
    
# =======================
# 8. Fuction 功能
# =======================
def download_csv_button(df, filename, label):
    csv_buffer = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=label,
        data=csv_buffer,
        file_name=filename,
        mime="text/csv",
        key=f"download_{filename}"
    )

def split_project_name(df): # 拆分地區、客戶名、活動名的函式
    # 拆分成地區、客戶名、活動名
    df[['region', 'client', 'campaign']] = df['Project Name'].str.split('-', expand=True)
    return df

def extract_coordinate_name(row):
    try:
        # 先將 coordinate_system_id 轉成字串並去除空白
        coordinate_id = str(row['coordinate_system_id']).strip()
        # 將 Coordinates 先 strip，再用 literal_eval
        coordinates_str = row['Coordinates'].strip()

        coordinates = ast.literal_eval(coordinates_str)  # 將字串轉為列表

        # 遍歷 Coordinates，找到對應的名稱
        for coord in coordinates:
            if coord.strip().startswith(coordinate_id + "-"):
                return coord.split("-", 1)[1].strip()  # 返回 ID 之後的名稱部分
    except (ValueError, SyntaxError, KeyError, TypeError):
        return None  # 如果解析失敗或格式錯誤，返回 None
    return None

def calculate_scan_count(df, start_date, end_date):
    # 轉換 scantime 並處理時區
    df['scantime'] = pd.to_datetime(df['scantime'], errors="coerce")
    invalid_times = df['scantime'].isna().sum()
    if invalid_times > 0:
        st.warning(f"⚠️ 發現 {invalid_times} 筆無效的 scantime 數據，已忽略這些記錄。")
    if invalid_times == len(df):
        st.error("🚨 所有 scantime 數據均無效，無法計算掃描量！")
        return 0
    if df['scantime'].dt.tz is None:  # 若無時區，設定台北時區
        df['scantime'] = df['scantime'].dt.tz_localize("Asia/Taipei")
    else:  # 若已有時區，轉換到台北時區
        df['scantime'] = df['scantime'].dt.tz_convert("Asia/Taipei")
    
    # 將 scantime normalize (只保留日期)
    df['scantime_normalized'] = df['scantime'].dt.normalize()
    
    # 確保 start_date 和 end_date 也 normalize
    start_date = pd.Timestamp(start_date).replace(hour=0, minute=0).tz_localize("Asia/Taipei")
    end_date = pd.Timestamp(end_date).replace(hour=23, minute=59).tz_localize("Asia/Taipei")
            
    # 過濾數據
    mask = (df['scantime_normalized'] >= start_date) & (df['scantime_normalized'] <= end_date)
    return df[mask].shape[0]

def ensure_date_format(value, timezone="Asia/Taipei"):
    # 確保傳入值轉為 pandas.Timestamp 並設置時區
    if not isinstance(value, pd.Timestamp):
        value = pd.to_datetime(value, errors="coerce")
    if timezone:  # 如果指定了時區，轉換到該時區
        if value.tzinfo is None:
            value = value.tz_localize(timezone)
        else:
            value = value.tz_convert(timezone)
    return value

def df_date_filter(df, col_name, start_day, end_day):
    df[col_name] = pd.to_datetime(df[col_name], errors="coerce").apply(lambda x: ensure_date_format(x))
    df['scantime_normalized'] = df[col_name].dt.normalize()
    start_day = ensure_date_format(start_day)
    end_day = ensure_date_format(end_day)
    start_day = pd.Timestamp(start_day).replace(hour=0, minute=0)
    end_day = pd.Timestamp(end_day).replace(hour=23, minute=59)
    
    return df[(df['scantime_normalized'] >= start_day) & (df['scantime_normalized'] <= end_day)]

def load_data(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        df = pd.read_csv(filepath,encoding="utf-8-sig",dtype={'Owner Email': str})
        df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d', errors='coerce')
        df['End Date'] = pd.to_datetime(df['End Date'], format='%Y-%m-%d', errors='coerce')
        # if 'Owner Email' not in df.columns:
        #     df['Owner Email'] = '[]'
        def safe_parse_json(x):
            if pd.notna(x):
                if isinstance(x, str):
                    try:
                        parsed = json.loads(x)
                        if isinstance(parsed, list):
                            return parsed
                        return [parsed] if parsed else []
                    except json.JSONDecodeError:
                        return [x]  # 如果不是 JSON，作為單一字串處理
                elif isinstance(x, list):
                    return x
            return []
        df['Owner Email'] = df['Owner Email'].apply(safe_parse_json)
        return df
    except FileNotFoundError:
        st.error(f"File not found: {filepath}")
        cols = ['ProjectID', 'Project Name', 'Start Date', 'End Date', 'Coordinates', 'Light ID', 'Scenes', 'Is Active', 'Latitude and Longitude', 'Owner Email']
        return pd.DataFrame(columns=cols)
    except Exception as e:
        st.error(f"Error loading file {filepath}: {e}")
        cols = ['ProjectID', 'Project Name', 'Start Date', 'End Date', 'Coordinates', 'Light ID', 'Scenes', 'Is Active', 'Latitude and Longitude', 'Owner Email']
        return pd.DataFrame(columns=cols)

def check_dataframe(df, name, required_columns):
    if df is None or df.empty:
        st.error(f"🚨 {name} 數據為空，請檢查數據來源！")
        st.stop()
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"🚨 {name} 缺少必要欄位：{', '.join(missing_cols)}")
        st.stop()

def get_data_hash(df):
    return hashlib.md5(df.to_string().encode()).hexdigest()

# 排程任務
def schedule_tasks():
    # 每天早上 6:00 儲存
    schedule.every().day.at("08:17").do(save_project_rank)
    logger.info("Scheduled tasks set for 08:05 daily")
    # 每天下午 5:00 儲存
    schedule.every().day.at("17:00").do(save_project_rank)

# 在背景執行排程的函數
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次
        logger.debug("Scheduler checked pending tasks")

def compute_multi_experiences(df_click_obj, gap_threshold_sec=600):
    df = df_click_obj.copy()
    df['clicktime'] = pd.to_datetime(df['clicktime'])
    df['click_date'] = df['clicktime'].dt.date

    df = df.sort_values(by=['user_id', 'scene', 'click_date', 'clicktime'])
    df['prev_time'] = df.groupby(['user_id', 'scene', 'click_date'])['clicktime'].shift()
    df['delta_sec'] = (df['clicktime'] - df['prev_time']).dt.total_seconds().fillna(0)

    df['new_experience_flag'] = df['delta_sec'] > gap_threshold_sec
    df['experience_id'] = df.groupby(['user_id', 'scene', 'click_date'])['new_experience_flag'].cumsum()

    grouped = df.groupby(['user_id', 'scene', 'click_date', 'experience_id'])
    experience_df = grouped.agg(
        start_time=('clicktime', 'min'),
        end_time=('clicktime', 'max')
    ).reset_index()

    experience_df['duration_sec'] = (experience_df['end_time'] - experience_df['start_time']).dt.total_seconds()

    return experience_df



# =======================
# 9. 定義日期區段及計算區段掃描量
# =======================
# 計算各時間範圍的掃描量
today_scan = calculate_scan_count(df_scan, today, today)
yesterday_scan = calculate_scan_count(df_scan, yesterday, yesterday)
this_week_scan = calculate_scan_count(df_scan, start_of_week, today)
last_week_scan = calculate_scan_count(df_scan, start_of_last_week, end_of_last_week)
this_month_scan = calculate_scan_count(df_scan, start_of_month, today)
last_month_scan = calculate_scan_count(df_scan, start_of_last_month, end_of_last_month)  
default_start_date = datetime.date(last_scan_time) - timedelta(days=30)


# =======================
# 10. 頁面範例：All Projects 頁面 (【修改處：簡化頁面邏輯，分離各區塊】)
# =======================
def all_projects():    
    user_email = st.session_state.get("logged_in_user", "")
    # st.write(user_email)
    # st.write(st.session_state.df_project)
    # if not user_email:
    #     st.error("請先登入以查看專案數據")
    #     return
    # 過濾專案數據，只顯示當前使用者有權限的專案
    filter_result = st.session_state.df_project['Owner Email'].apply(lambda owners: user_email in owners)
    filtered_df_project = st.session_state.df_project[filter_result]
    # st.session_state.df_project = filtered_df_project  # 更新 session state
    # st.write(filtered_df_project)
    # =======================
    # 7-2. 輸入查詢日期
    # =======================
    with st.container():
        col1, col2, col3, col4 = st.columns([1,2,1,2])
        with col1:
            st.markdown('<div class="date-input-row"><label>⏱️ Enquiry Start Date：</label></div>', unsafe_allow_html=True)
        with col2:
            start_date = st.date_input("⏱️ Select Star Date", label_visibility = "collapsed",value=default_start_date, max_value=last_scan_time)
            start_date = pd.Timestamp(start_date).replace(hour=0, minute=0).tz_localize("Asia/Taipei")
        with col3:
            st.markdown('<div class="date-input-row"><label>⏱️ Enquiry End Date：</label></div>', unsafe_allow_html=True)
        with col4:
            end_date = st.date_input("⏱️ Select End Date", label_visibility = "collapsed",value=last_scan_time, max_value=last_scan_time)
            end_date = pd.Timestamp(end_date).replace(hour=23, minute=59).tz_localize("Asia/Taipei")

        if start_date > end_date:
            st.error("Error: 結束日期必須大於等於開始日期")
            st.stop()
        
        scan_hash = get_data_hash(df_scan)
        project_hash = get_data_hash(filtered_df_project)
        # 檢查是否需要重新計算 merge_data 和 project_rank
        if ('scan_hash' not in st.session_state or
            'project_hash' not in st.session_state or
            st.session_state.scan_hash != scan_hash or
            st.session_state.project_hash != project_hash or 
            st.session_state.merge_datefilter is None or 
            st.session_state.project_rank is None or 
            st.session_state.start_date != start_date or 
            st.session_state.end_date != end_date):
            st.session_state.merge_datefilter = prepare_project_data(filtered_df_project, df_scan, start_date, end_date)
            st.session_state.merge_data_yesterday = prepare_project_data(filtered_df_project, df_scan, yesterday, yesterday)
            st.session_state.merge_data_today = prepare_project_data(filtered_df_project, df_scan, today, today)
            st.session_state.project_rank = generate_project_rank(st.session_state.merge_datefilter, filtered_df_project,st.session_state.merge_data_yesterday,st.session_state.merge_data_today)
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.scan_hash = scan_hash
            st.session_state.project_hash = project_hash
        
    # =======================
    # 7-2. 數據整理
    # =======================
    merge_datefilter = st.session_state.merge_datefilter
    merge_datefilter = split_project_name(merge_datefilter)
    merge_datefilter['coordinate_system_name'] = merge_datefilter.apply(extract_coordinate_name, axis=1)
    merge_datefilter['weekday'] = merge_datefilter['scantime'].dt.weekday  # 0 = Monday, 6 = Sunday
    df_scenelist = pd.read_csv(
        os.path.join(data_root, "scene.csv"),
        encoding="utf-8-sig",
    )
    df_scenelist['Id'] = df_scenelist['Id'].astype(str)
    df_coordinates = get_coordianate_dict_from_server().assign(id=lambda df: df['id'].astype(int))
    df_heatmap = generate_heatmap_data(merge_datefilter)
    df_click_data = st.session_state.df_click_lig
    df_click_data['obj_id'] = df_click_data['obj_id'].astype(int)
    df_click_data['weekday'] = df_click_data['clicktime'].dt.weekday  # 0 = Monday, 6 = Sunday
    
    
    # =======================
    # 7-3. 熱力圖、排行榜、統計數據
    # =======================
    with st.expander('all data',expanded=True):
        col_map,col_table = st.columns([6,4])
        with col_map:
            st.markdown('<div class="date-input-row"><label>Scanning HeatMap</label></div>', unsafe_allow_html=True)           
            plot_heatmpy(df_heatmap)
        with col_table:
            st.markdown('<div class="date-input-row"><label>Data Statistics</label></div>', unsafe_allow_html=True)     
            with st.container():
                col2_1, col2_2, col2_3 = st.columns(3)
                # 今日、昨日、本週
                with col2_1:   
                    display_metric('Today Scans',today_scan)      
                    display_metric('Yesterday Scans',yesterday_scan)      
                # 上週、本月、上月
                with col2_2:
                    display_metric('This Week Scans',this_week_scan)  
                    display_metric('Last Week Scans',last_week_scan)  
            
                # 其他數據（根據需要添加）
                with col2_3:
                    display_metric('This Month Scans',this_month_scan)  
                    display_metric('Last Month Scans',last_month_scan)  

            # 顯示掃描排行        
            st.markdown('<div class="date-input-row"><label>Project Scan (Click "Project Name" to see the detail)</label></div>', unsafe_allow_html=True)
            project_rank = AgGridTable(
                st.session_state.project_rank.sort_values(by="Today Scans", ascending=False)
            )

            # 只在程式啟動時啟動排程
            if 'scheduler_started' not in st.session_state:
                st.session_state.scheduler_started = True
                schedule_tasks()
                # 在背景執行緒中運行排程
                scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
                scheduler_thread.start()
                logger.info("Scheduler initialized and started")
            download_csv_button(st.session_state.project_rank,filename='project_rank.csv',label='Download Project Rank')
            selected_row = project_rank["selected_rows"]
            if selected_row is None:
                st.write("Select a project to see detail")            
            else:
                selected_project = selected_row['Project Name']

    col_1,col_2 = st.columns([10,1])
    with col_1.expander("Scan Raw data"):                
        raw_arrange_data = merge_datefilter[['scantime','region','campaign','coordinate_system_name','Light ID']]
        AgGridTable(raw_arrange_data)
    with col_2.expander(''):
        multiplier = st.number_input("Multiplier for charts", min_value=0.1, max_value=10.0, value=1.0, step=0.1)

    # =======================
    # 7-3. 專案參數及統計數據
    # =======================
    if selected_row is not None:
        selected_project_name = selected_project.iloc[0]
        with st.container():
            st.markdown(
            f"<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>{selected_project_name} Information</h4>",
            unsafe_allow_html=True,
            )
            col1,col2 = st.columns(2)
            with col1:
                col_prj_head, col_prj_sel = st.columns([1,6])
                with col_prj_head:
                    st.markdown('<div class="date-input-row page-title"><label>Project: </label></div>', unsafe_allow_html=True)            
                with col_prj_sel:
                    selected_project = st.selectbox('Select Project', options=selected_project,label_visibility='collapsed')
                prj_filtered_df=merge_datefilter[merge_datefilter['Project Name']==selected_project]
                df_project = st.session_state.df_project

                filtered_ids_list = (
                    prj_filtered_df['Light ID']
                    .dropna()  # 去除空值
                    .apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)  # 安全解析字符串
                    .explode()  # 展平嵌套列表
                    .drop_duplicates()  # 去重（僅適用於 Series）
                    .tolist()  # 轉換為 Python 列表
                )
                col_id_head, col_id_sel = st.columns([1,6]) 
                with col_id_head:
                    st.markdown('<div class="date-input-row page-title"><label>lig id: </label></div>', unsafe_allow_html=True)
                with col_id_sel:
                    # 多選框選擇
                    st.multiselect('Select ID', options=filtered_ids_list,default=filtered_ids_list,label_visibility='collapsed')

                col_scene_head, col_scene_sel = st.columns([1,6]) 
                with col_scene_head:
                    st.markdown('<div class="date-input-row page-title"><label>Scenes: </label></div>', unsafe_allow_html=True)
                with col_scene_sel:
                    #獲取AR對象數據                
                    prjfiltered_scenes_list = (
                        df_project[df_project['Project Name']==selected_project]['Scenes']
                        .dropna()
                        .apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
                        .sum()
                    )
                    select_scenes = st.multiselect(
                        'Select Scene',
                        options=prjfiltered_scenes_list,
                        default=prjfiltered_scenes_list,
                        label_visibility='collapsed',
                        help="Scroll to view all options",
                        max_selections=None,
                    )
                prjfilter_scene_id_list = [int(item.split("-")[0]) for item in prjfiltered_scenes_list]
                extract_arobj_id = [
                    ar_obj['id'] 
                    for scene_id in select_scenes 
                    for ar_obj in fetch_ar_objects(scene_id.split('-')[0])
                ]

                extract_arobj_id = sorted(set(extract_arobj_id))
                
                filtered_df_click_data = df_click_data[df_click_data['obj_id'].isin(extract_arobj_id)].reset_index()
                filtered_df_click_data = df_date_filter(filtered_df_click_data, "clicktime", start_date, end_date)
                #計算統計數據
                experiment_number = int(len(prj_filtered_df)*multiplier)
                interaction_number, participants_number = calculate_statistics(filtered_df_click_data,multiplier)
                arobj_number = len(extract_arobj_id)
                      
            with col2:
                #更新頁面數據
                cola,colb,colc = st.columns(3)
                with cola:
                    display_metric('Experiment',experiment_number)
                    display_metric('Number of AR objects',arobj_number)

                with colb:
                    display_metric('Interaction',interaction_number)
                with colc:
                    display_metric('Participants',participants_number)      
            
    # =======================
    # 7-4. 統計圖表（by day & by hour）
    # =======================
            st.markdown(
                "<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>Project Scan Diagram</h4>",
                unsafe_allow_html=True,
            )    
            col_daily_fig, col_daily_table = st.columns([3,1])            
            with col_daily_fig:
                st.markdown(f'<div class="date-input-row"><label>{selected_project} Daily Scans</label></div>', unsafe_allow_html=True)
                dimenssion = st.selectbox('Choose the sampling by', ['lig_id','coordinate_system_name'])  
                # st.write(prj_filtered_df)
                dailyscan_counts,fig_dailyscan_counts = plot_stacked_histogram_with_dual_y_axis(data=prj_filtered_df, start_date=start_date, end_date=end_date,timecol ='scantime',col_name=dimenssion,multiplier=multiplier)
                st.plotly_chart(fig_dailyscan_counts, use_container_width=True)
                download_csv_button(dailyscan_counts,filename=f'{selected_project}_dailyscan_counts.csv',label='Download Daily Scan Counts')

            with col_daily_table:
                st.markdown(f'<div class="date-input-row"><label>Weekly Statistics</label></div>', unsafe_allow_html=True)               
                fig_week_pie = week_pie_fig(prj_filtered_df)

                st.plotly_chart(fig_week_pie, use_container_width=True)

        # =======================
        # 7-4-2. 時間分佈圖
        # =======================  
        col_time_dist_fig,col_weekday_dist = st.columns([3,1])
        with col_time_dist_fig:
            st.markdown(f'<div class="date-input-row"><label>{selected_project} Daily 24-hour Scan Event Distribution</label></div>', unsafe_allow_html=True)
            fig_time_distribution = time_distribution(prj_filtered_df,start_date, end_date)
            st.plotly_chart(fig_time_distribution, use_container_width=True)

        with col_weekday_dist:
            st.markdown('<div class="date-input-row"><label>Day Distribution</label></div>', unsafe_allow_html=True)
            fig_h24_distribution = h24_distribution(merge_datefilter,col_name='scantime')
            st.plotly_chart(fig_h24_distribution, use_container_width=True)

        # 檢查 select_scenes 是否為空
        if not select_scenes:  # 如果是空列表
            st.warning("請選取一個場景")  # 顯示警告訊息
            st.stop()  # 中止後續代碼執行
        st.markdown(
            "<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>Scenes Interaction Diagram</h4>",
            unsafe_allow_html=True,
        )
        # =======================
        # 7-5. 專案物件及互動數據
        # ======================= 
        col_ckick_fig , col_click_data = st.columns([3,1])
        # 主流程：依據 ids_list 依序取得所有 ar_objects 資料
        all_objects = []
        token = st.session_state.get("_lig_token")
        for scene_id in prjfilter_scene_id_list:
            objs = get_ar_objects_by_scene_id(scene_id,df_scenelist, token=token)
            all_objects.extend(objs)

        # 建立 DataFrame df_selected_obj，若無資料則建立空 DataFrame
        df_selected_obj = pd.DataFrame(all_objects, columns=["scene_id","scene", "obj_id", "obj_name","location_x","location_y","location_z"])
        
        # 接下來，與點擊記錄 filtered_df_click_lig 依據 'obj_id' 融合，新增 'obj_name' 欄位
        filtered_df_click_obj = pd.merge(filtered_df_click_data, df_selected_obj, on="obj_id", how="left")
        filtered_df_click_obj["click_date_only"] = filtered_df_click_obj["clicktime"].dt.normalize()
        filtered_df_click_obj["ar_obj"] = filtered_df_click_obj["obj_id"].astype(str) + " - " + filtered_df_click_obj["obj_name"].astype(str)
        
        click_daily_counts, fig_dailyclick = plot_stacked_histogram_with_dual_y_axis(filtered_df_click_obj, start_date, end_date, timecol ='clicktime',col_name='scene', multiplier=multiplier)


        with col_ckick_fig:            
            st.markdown(f'<div class="date-input-row"><label>{selected_project} Daily Click Histogram</label></div>', unsafe_allow_html=True)
            st.plotly_chart(fig_dailyclick, use_container_width=True)
            download_csv_button(df=click_daily_counts, filename=f'{selected_project}_dailyclick.csv', label='Download Daily Click CSV')
            with st.expander("click raw data"):
                st.write(filtered_df_click_obj)
        with col_click_data:
            with st.container():            
                st.markdown(f'<div class="date-input-row"><label>Weekly Statistics</label></div>', unsafe_allow_html=True)
                st.markdown('<div class="plotly-chart-container">', unsafe_allow_html=True)
                fig_click_week_pie = week_pie_fig(filtered_df_click_obj)
                st.plotly_chart(fig_click_week_pie, use_container_width=True)            
                st.markdown('</div>', unsafe_allow_html=True)
            
        # ----------------------------
        # (2) 製作物件點擊排行榜
        # ----------------------------        
        click_scene_list = filtered_df_click_obj['scene'].unique()
        if click_scene_list is None:
            st.warning("⚠️ 沒有可用的場景數據，請檢查 click_scene_list!")
        else:    
            st.markdown(
                "<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>Scenes Interaction Diagram</h4>",
                unsafe_allow_html=True,
            )                
            sc = st.selectbox('Choose a Scene',options=click_scene_list)
            col_f,col_t = st.columns([3,1])
            with col_f:
                st.markdown(f'<div class="date-input-row"><label>{sc} Object Location Click Distribution </label></div>', unsafe_allow_html=True)
                filtered_click_obj_sc = filtered_df_click_obj[filtered_df_click_obj['scene'] == sc]
                fig_clcikobjdist,ranking = clickobjdist(filtered_click_obj_sc,multiplier)

                word_freq = dict(zip(ranking["ar_obj"], ranking["click_count"]))
                
                # 生成橢圓形遮罩
                mask = np.zeros((400, 800), dtype=np.uint8)
                image = Image.new("L", (800, 400))
                draw = ImageDraw.Draw(image)
                draw.ellipse((10, 10, 790, 390), fill=255)  # 畫一個橢圓形
                mask = np.array(image)

                # 反轉遮罩：白色變為黑色，黑色變為白色
                mask = 255 - mask  # 橢圓形內變為 0（允許放置文字），橢圓形外變為 255（不允許放置文字）
                
                # 自訂隨機顏色函數
                def random_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                    if font_size > 100:  # 假設字體大小大於100的詞彙是中心詞，設為綠色
                        return "hsl(120, 60%, 40%)"  # 綠色
                    else:
                        # 隨機生成其他顏色
                        h = random.randint(0, 360)  # 色相
                        s = random.randint(50, 100)  # 飽和度
                        l = random.randint(30, 70)  # 亮度
                        return f"hsl({h}, {s}%, {l}%)"
                
                # 生成文字雲
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    background_color="white",
                    mask=mask,  # 使用橢圓形遮罩
                    contour_width=0,  # 不顯示遮罩邊框
                    font_path="font/msjh.ttc",  # 指定中文字體（根據你的系統路徑調整）
                    color_func=random_color_func,  # 使用自訂顏色函數
                    min_font_size=10, 
                    max_font_size=100,
                    relative_scaling=0.15,  # 降低縮放比例，讓文字分佈更均勻
                    prefer_horizontal=50,  # 降低水平排列比例，讓文字更靈活
                    max_words=100,  # 確保所有詞彙都能顯示
                    scale=5,  # 增加密度，讓文字更展開
                    random_state=100,  # 固定隨機種子，嘗試讓大字更接近中間
                ).generate_from_frequencies(word_freq)
                
                # 使用 matplotlib 顯示
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation="bilinear")
                plt.axis("off")
                
                # 在 Streamlit 上顯示
                st.pyplot(plt)


                # st.write(ranking)
                if fig_clcikobjdist is None:
                    st.error(f"🚨 無法生成場景 {sc} 的點擊分佈圖，請檢查數據！")
                else:
                    st.plotly_chart(fig_clcikobjdist, use_container_width=True)

            with col_t:
                st.markdown(f'<div class="date-input-row"><label>Click Object Ranks</label></div>', unsafe_allow_html=True)    
                ranking = ranking[['ar_obj', 'click_count']]
                if ranking is None:
                    st.warning(f"⚠️ 場景 {sc} 的排行榜數據為空！")
                else:
                    st.dataframe(ranking,use_container_width=True,height=300, hide_index=True)
                fig_h24_clickdistribution = h24_distribution(filtered_click_obj_sc,col_name='clicktime')

                st.plotly_chart(fig_h24_clickdistribution, use_container_width=True)

        st.markdown(
            f"<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>{selected_project} User Data</h4>",
            unsafe_allow_html=True,
        )
        # ----------------------------
        # (2) 每日參與人數統計
        # ----------------------------    

        daily_users, fig_user_counts = user_data_fig(filtered_click_obj_sc,start_date,end_date)
        # 顯示圖表
        st.plotly_chart(fig_user_counts, use_container_width=True)

        # =======================
        st.markdown(
            f"<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>{selected_project} 體驗時間分析</h4>",
            unsafe_allow_html=True,
        )

        experience_df = compute_multi_experiences(filtered_df_click_obj)

        col_ex1, col_ex2 = st.columns([2, 1])
        with col_ex1:
            st.markdown(f'<div class="date-input-row"><label>{sc} 體驗段落長條圖</label></div>', unsafe_allow_html=True)
            fig_bar = plot_user_experience_bar(experience_df, selected_scene=sc)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_ex2:
            st.markdown(f'<div class="date-input-row"><label>{sc} 體驗時間分布 Box Plot</label></div>', unsafe_allow_html=True)
            fig_box = plot_experience_box(experience_df, selected_scene=sc)
            st.plotly_chart(fig_box, use_container_width=True)
        # =======================


        st.markdown(f'<div class="date-input-row"><label>{sc} User Interaction Path</label></div>', unsafe_allow_html=True)
 


        col_userrank, col_path_log = st.columns([1,2])
        with col_userrank:
            user_ranking = generate_user_id_ranking(filtered_click_obj_sc)
            user_ranking_table = AgGridTable(user_ranking)
        with col_path_log:
            selected_row = user_ranking_table["selected_rows"]          
            if selected_row is None:
                selected_user = filtered_click_obj_sc['user_id'].iloc[0]
                st.write("Select a project to see detail")            
            else:
                selected_user = str(selected_row['user_id'].iloc[0])
            fig_clcikobjdist,merge_ranking = clickobjdist(filtered_df_click_obj,multiplier)
            user_data = filtered_df_click_obj[filtered_df_click_obj['user_id']==selected_user]
            fig_with_path, user_data = clickobjdist_with_userpath(fig_clcikobjdist,user_data, multiplier=1.0)

            user_data['click_date'] = pd.to_datetime(user_data['clicktime']).dt.date
            available_dates = sorted(user_data['click_date'].unique())
            date_options = [date.strftime('%Y-%m-%d') for date in available_dates]
            st.write(f'{selected_user} click path')
            selected_dates = st.multiselect(
                "Select Dates to Display",
                options=date_options,
                default=date_options,  # 預設全選
                key=f"date_select_{selected_user}"  # 確保每個用戶的選擇獨立
            )
          # 根據選擇的日期過濾 user_data
            if selected_dates:
                filtered_user_data = user_data[user_data['click_date'].isin(
                    [pd.to_datetime(date).date() for date in selected_dates]
                )]
            else:
                filtered_user_data = user_data  # 如果未選擇日期，顯示所有數據            
            st.dataframe(
                filtered_user_data[['clicktime','ar_obj']],
                use_container_width=True,
                height=300, 
                hide_index=True
            )

        st.plotly_chart(fig_with_path, use_container_width=True)
        
        with st.expander("user information raw ddata"):
            st.write(daily_users)

        # =======================
        # 7-5. 選擇物件看點擊排行
        # ======================= 
        with st.expander("Custom Object Clicks"):
            st.markdown(f'<div class="date-input-row"><label>{selected_project} Custom Object Clicks</label></div>', unsafe_allow_html=True)         
            col_obj, col_rank = st.columns(2)
            with col_obj:
                def extract_obj_name(ar_obj):
                    return ar_obj.split(' - ')[-1]
                # Add scene selection
                scene_options = sorted(filtered_df_click_obj['scene'].unique())  # Assuming there's a 'scene' column
                selected_scenes = st.multiselect('Choose Scenes', options=scene_options)
                
                # Filter dataframe based on selected scenes
                if selected_scenes:
                    scene_filtered_df = filtered_df_click_obj[filtered_df_click_obj['scene'].isin(selected_scenes)]
                else:
                    scene_filtered_df = filtered_df_click_obj

                ar_obj_options = sorted(scene_filtered_df['ar_obj'].unique(), key=lambda x: extract_obj_name(x))
                # ar_obj_options = sorted(filtered_df_click_obj['ar_obj'].unique(), key=lambda x: extract_obj_name(x))
                
                # ar_obj_options = merged_clicks['ar_obj'].unique()
                st.markdown("""
                <style>
                .stMultiSelect .select-multi-item div {
                    white-space: normal !important;
                    font-size: 8px;
                    word-wrap: break-word;
                    max-width: 100%;
                }
                </style>
                """, unsafe_allow_html=True)

                # st.write(filtered_df_click_obj)
                selected_ar_objs = st.multiselect('Choose AR Objects', options=ar_obj_options)
                # 過濾選擇的ar_obj
                if selected_ar_objs:
                    filtered_clicks = filtered_df_click_obj[filtered_df_click_obj['ar_obj'].isin(selected_ar_objs)]
                else:
                    filtered_clicks = filtered_df_click_obj        
                filtered_ranking = (
                    filtered_clicks.groupby(["ar_obj"])
                    .size()
                    .reset_index(name="click_count")        
                    .sort_values("click_count", ascending=False)
                )

            with col_rank:
                if not selected_ar_objs:
                    st.write("Choose AR Objects to check the click counts")
                else:
                    st.dataframe(filtered_ranking, use_container_width=True)
                download_csv_button(filtered_ranking,filename=f'{selected_project}_custmon_clickcount.csv',label='Download Custmon ClickCounts')

def parameters():
    """View: 更新 Dashboard 設定"""
    project_filepath = os.path.join("data", "projects_new_0306.csv")
    df_project_edit = load_data(project_filepath)
    st.info("Projects Table")
    st.session_state.coordinates_list_option = get_coordinates_list_from_server()
    st.session_state.light_ids_option = get_id_list_from_file()
    df_scenelist = pd.read_csv(
        os.path.join(data_root, "scene.csv"),
        encoding="utf-8-sig",
    )
    scanlist_option  = df_scenelist.apply(lambda row: f"{row['Id']}-{row['Name']}", axis=1).tolist()
    st.session_state.scenes_option = scanlist_option
    user_login_email = st.session_state.get("logged_in_user", "")

    # 如果 email_options 未包含當前使用者，動態添加
    if user_login_email:
        if user_login_email not in st.session_state.email_options:
            st.session_state.email_options.append(user_login_email)


    def save_uploaded_file(uploaded_file, path):
        """保存上傳的檔案"""
        try:
            # 確保目錄存在
            os.makedirs(path, exist_ok=True)
            
            # 建立完整路徑
            file_path = os.path.join(path, uploaded_file.name)
            
            # 寫入檔案
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"檔案已保存至：{file_path}")
        except PermissionError:
            st.error("權限錯誤：請檢查目錄寫入權限")
        except OSError as e:
            st.error(f"存儲失敗：{e}（可能是磁碟空間不足）")
        except Exception as e:
            st.error(f"未知錯誤：{e}")

    def save_data(df,filepath):
        max_backups = 5
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        bakcup_filepath  = os.path.join("data", f"projects.csv.backup_{timestamp}")
        df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d', errors='coerce')        
        df['End Date'] = pd.to_datetime(df['End Date'], format='%Y-%m-%d', errors='coerce')        
        df['Start Date'] = df['Start Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
        df['End Date'] = df['End Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
        df['Owner Email'] = df['Owner Email'].apply(json.dumps)
        try:
            df.to_csv(filepath, encoding="utf-8-sig", index=False)   # /data/projects.csv
            df.to_csv(bakcup_filepath, encoding="utf-8-sig", index=False) #/data/projects.csv.backup_20250102234210
            backup_files = sorted(glob.glob(f'data/projects.csv.backup_*'))
            st.write(backup_files)
            while len(backup_files) > max_backups:
                oldest_backup = backup_files.pop(0)
                os.remove(oldest_backup)
            st.success("Saved successfully!")
        except Exception as e:
            print(f"Failed to save the file: {e}")
        df['Owner Email'] = df['Owner Email'].apply(json.loads)

    def fetch_coordinates_from_server(light_id):
        url = f"{CORE_API_SERVER}/api/v1/lightids/{light_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            cs_list = data.get("cs_list", [])
            return [f'{cs["id"]}-{cs["name"]}' for cs in cs_list]
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch coordinates for Light ID {light_id}: {e}")
            return []

    def add_project(df_project_edit):
        st.subheader("Add New Project")
        user_login_email = st.session_state.get("logged_in_user", "")

        # 使用輔助變數控制 new_email 的顯示值
        if "new_email_input" not in st.session_state:
            st.session_state.new_email_input = ""

        with st.container():
            st.text_input("Project Name", value="", key="project_name_new")
            st.date_input("Start Date", value=datetime.now().date(), key="start_date_new")
            st.date_input("End Date", value=datetime.now().date(), key="end_date_new")
            st.checkbox("Active", value=False, key="is_active_new")
            st.text_input("Latitude and Longitude", value="", key="lat_lon_new")
            st.multiselect(
                "Light IDs",
                options=st.session_state.light_ids_option,
                default=[],
                key="light_ids_input_new",
            )
            coordinates_list = []
            for light_id in st.session_state.light_ids_input_new:
                new_coordinates = fetch_coordinates_from_server(light_id)
                coordinates_list.extend(new_coordinates)
                coordinates_list = list(set(coordinates_list))
            st.multiselect(
                "Coordinates",
                options=st.session_state.coordinates_list_option,
                default=coordinates_list,
                key="coordinates_input_new",
            )
            st.multiselect(
                "Scenes",
                options=st.session_state.scenes_option,
                default=[],
                key="scenes_input_new",
            )

            #使用表單處理新電子郵件輸入
            with st.form(key="email_form", clear_on_submit=True):
                new_email = st.text_input("Add New Owner Email", value="", key="new_owner_email")
                submit_email = st.form_submit_button("Add Email")
                if submit_email and new_email and new_email not in st.session_state.email_options:
                    st.session_state.email_options.append(new_email)  # 添加完整字串
                    st.rerun()


            default_emails = [user_login_email] if user_login_email else []

            st.multiselect(
                "Owner Emails",
                options=st.session_state.email_options,
                default=default_emails,
                key="owner_emails_new"
            )
            st.write(f"Selected owner_emails_new: {st.session_state.owner_emails_new}")
            add_button = st.button(label="Add Project",use_container_width=True)

            if add_button:
                if not st.session_state.project_name_new.strip():
                    st.error("Project Name cannot be empty.")
                elif pd.notnull(st.session_state.start_date_new) and st.session_state.end_date_new < st.session_state.start_date_new:
                    st.error("End Date cannot be earlier than Start Date.")
                else:

                    # 檢查 df_project_edit 是否有效
                    if df_project_edit is None or df_project_edit.empty:
                        st.error("無法載入專案數據，請檢查資料來源！")
                        return

                    new_project_id = (
                        df_project_edit['ProjectID'].astype(int).max() + 1
                        if not df_project_edit.empty
                        else 1
                    )
                    new_project = {
                        'ProjectID': new_project_id,
                        'Project Name': st.session_state.project_name_new,
                        'Start Date': st.session_state.start_date_new,
                        'End Date': st.session_state.end_date_new,
                        'Coordinates': json.dumps(st.session_state.coordinates_input_new, ensure_ascii=False),
                        'Light ID': json.dumps(st.session_state.light_ids_input_new, ensure_ascii=False),
                        'Scenes': json.dumps(st.session_state.scenes_input_new, ensure_ascii=False),
                        'Is Active': st.session_state.is_active_new,
                        'Latitude and Longitude': st.session_state.lat_lon_new,
                        'Owner Email': st.session_state.owner_emails_new,
                    }
                    df_new_project = pd.DataFrame([new_project])
                    df_new_project['Start Date'] = pd.to_datetime(df_new_project['Start Date'], format='%Y-%m-%d', errors='coerce')
                    df_new_project['End Date'] = pd.to_datetime(df_new_project['End Date'], format='%Y-%m-%d', errors='coerce')
                    df_new_project['Start Date'] = df_new_project['Start Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                    df_new_project['End Date'] = df_new_project['End Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                    df_project_edit['Start Date'] = pd.to_datetime(df_project_edit['Start Date'], format='%Y-%m-%d', errors='coerce')
                    df_project_edit['End Date'] = pd.to_datetime(df_project_edit['End Date'], format='%Y-%m-%d', errors='coerce')
                    df_project_edit['Start Date'] = df_project_edit['Start Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                    df_project_edit['End Date'] = df_project_edit['End Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                    df_concat = pd.concat([df_project_edit, df_new_project], ignore_index=True)
                    df_project_edit = df_concat
                    st.session_state.editing_row_index = None
                    save_data(df_concat, project_filepath)
                    del st.session_state.project_name_new
                    del st.session_state.start_date_new
                    del st.session_state.end_date_new
                    del st.session_state.coordinates_input_new
                    del st.session_state.light_ids_input_new
                    del st.session_state.scenes_input_new
                    del st.session_state.is_active_new
                    del st.session_state.lat_lon_new
                    st.rerun()

    def edit_project(selected): # 编辑项目
        project_info = process_selected_row(pd.DataFrame(selected))
        project_id_default = project_info['ProjectID']
        project_name_default = project_info['Project Name']
        project_start_date_default = project_info['Start Date'] if pd.notnull(project_info['Start Date']) else datetime.now().date()  # 提供一個預設值
        project_end_date_default = project_info['End Date'] if pd.notnull(project_info['End Date']) else datetime.now().date()
        project_coordinates_default = project_info['Coordinates']
        project_light_id_default = project_info['Light ID']
        project_scenes_default = project_info['Scenes']
        project_is_active_default = project_info['Is Active']
        project_lat_lon_default = project_info['Latitude and Longitude']
        project_owner_emails_default = project_info.get('Owner Email')
        project_is_active_default = str(project_is_active_default).upper() == 'TRUE'
        # 確保 project_owner_emails_default 是列表
        if isinstance(project_owner_emails_default, str):
            try:
                project_owner_emails_default = json.loads(project_owner_emails_default)  # 解析 JSON 字串
            except json.JSONDecodeError:
                project_owner_emails_default = [project_owner_emails_default]  # 如果不是 JSON，作為單一字串處理
        elif not isinstance(project_owner_emails_default, list):
            project_owner_emails_default = []
        # 動態更新 email_options，包含 project_owner_emails_default 中的所有值
        for email in project_owner_emails_default:
            if email and email not in st.session_state.email_options:
                st.session_state.email_options.append(email)

        st.subheader(f"Edit Project Id: {project_id_default}")
        with st.container():
            st.text_input('Project Name', value=project_name_default, key="project_name_new")
            st.date_input("Start Date", value=project_start_date_default, key="start_date_new")
            st.date_input("End Date", value=project_end_date_default, key="end_date_new")
            st.checkbox("Active", value=project_is_active_default, key="is_active_new")
            st.text_input("Latitude and Longitude", value=project_lat_lon_default, key="lat_lon_new")

            if isinstance(project_light_id_default,list):
                st.multiselect(
                    "Light IDs",
                    options=st.session_state.light_ids_option,
                    default=project_light_id_default,
                    key="light_ids_input_new",
                )
            if isinstance(project_light_id_default,str):                
                st.multiselect(
                    "Light IDs",
                    options=st.session_state.light_ids_option,
                    default=json.loads(project_light_id_default),
                    key="light_ids_input_new",
                )
            coordinates_list = []
            for light_id in st.session_state.light_ids_input_new:
                new_coordinates = fetch_coordinates_from_server(light_id)
                coordinates_list.extend(new_coordinates)
                coordinates_list = list(set(coordinates_list))
            
            default_coords = json.loads(project_coordinates_default)
            valid_coords = [c for c in default_coords if c in st.session_state.coordinates_list_option]
            invalid_coords = [c for c in default_coords if c not in st.session_state.coordinates_list_option]
            if invalid_coords:
                st.warning(f"以下座標不存在於目前選項中：{invalid_coords}")

            st.multiselect(
                "Coordinates",
                options=st.session_state.coordinates_list_option,
                default=valid_coords,
                key='coordinates_input_new'
            )
            st.multiselect(
                "Scenes",
                options=st.session_state.scenes_option,
                default=json.loads(project_scenes_default),
                key="scenes_input_new",
            )
            with st.form(key="email_form_edit", clear_on_submit=True):
                new_email = st.text_input("Add New Owner Email", value="", key="new_owner_email_edit")
                submit_email = st.form_submit_button("Add Email")
                if submit_email and new_email and new_email not in st.session_state.email_options:
                    st.session_state.email_options.append(new_email)
                    st.rerun()

            st.multiselect(
                "Owner Emails",
                options=st.session_state.email_options,
                default=project_owner_emails_default,
                key="owner_emails_new"
            )
            update_button = st.button(label="Update Project",use_container_width=True)
            # submit_button = st.form_submit_button(label='Update Project')

        if update_button:
            if not st.session_state.project_name_new.strip():
                st.error("Project Name cannot be empty.")
            elif pd.notnull(st.session_state.end_date_new) and st.session_state.end_date_new < st.session_state.start_date_new:
                st.error("End Date cannot be earlier than Start Date.")
            elif not st.session_state.owner_emails_new:
                st.error("At least one Owner Email is required.")
            else:
                st.session_state.coordinates_list = []
                df_project_edit.at[int(st.session_state.editing_row_index), "Project Name"] = st.session_state.project_name_new
                df_project_edit.at[int(st.session_state.editing_row_index), "Start Date"] = st.session_state.start_date_new
                df_project_edit.at[int(st.session_state.editing_row_index), "End Date"] = st.session_state.end_date_new
                df_project_edit.at[int(st.session_state.editing_row_index), "Is Active"] = st.session_state.is_active_new
                df_project_edit.at[int(st.session_state.editing_row_index), "Latitude and Longitude"] = st.session_state.lat_lon_new
                df_project_edit.at[int(st.session_state.editing_row_index), "Coordinates"] = json.dumps(
                    st.session_state.coordinates_input_new, ensure_ascii=False
                )
                df_project_edit.at[int(st.session_state.editing_row_index), "Light ID"] = json.dumps(
                    st.session_state.light_ids_input_new, ensure_ascii=False
                )
                df_project_edit.at[int(st.session_state.editing_row_index), "Scenes"] = json.dumps(
                    st.session_state.scenes_input_new, ensure_ascii=False
                )
                df_project_edit.at[int(st.session_state.editing_row_index), "Owner Email"] = st.session_state.owner_emails_new
                save_data(df_project_edit, project_filepath)
                st.success("Project updated successfully!")
                st.session_state.editing_row_index = None
                st.rerun()

    def process_selected_row(selected):

        if not selected.empty:
            selected_row = selected.iloc[0]           
            try:
                project_id = int(selected_row.get('ProjectID', None))
            except (ValueError, TypeError):
                project_id = None

            project_data = {
                "ProjectID": project_id,
                "Project Name": selected_row.get('Project Name', None),
                "Start Date": pd.to_datetime(selected_row.get('Start Date', None), errors='coerce'),
                "End Date": pd.to_datetime(selected_row.get('End Date', None), errors='coerce'),
                "Coordinates": selected_row.get('Coordinates', None),
                "Light ID": selected_row.get('Light ID', None),
                "Scenes": selected_row.get('Scenes', None),
                "Is Active": selected_row.get('Is Active', None),  
                "Latitude and Longitude": selected_row.get('Latitude and Longitude', None),
                "Owner Email": selected_row.get('Owner Email', []),                    
                "Row Index": selected.index.values[0],
            }

            # 更新 session_state 中的编辑索引
            select_row_index = project_data["Row Index"]
            st.session_state.editing_row_index = select_row_index

            return project_data
        else:
            # st.write("No row selected.")
            st.session_state.editing_row_index = None
            return None

    def display_aggrid(df):        
        # 准备显示的 DataFrame，将日期和列表转换为字符串
        # df_reorder = df[::-1].copy()
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('single', use_checkbox=True, groupSelectsChildren=False)
        gb.configure_default_column(editable=True, sortable=True, filter=True)
        gb.configure_column("ProjectID", editable=False)
        gb.configure_column("Coordinates", editable=False)
        gb.configure_column("Light ID", editable=False)
        gb.configure_column("Scenes", editable=False)
        gb.configure_column("Is Active", editable=False)
        gb.configure_column("Latitude and Longitude", editable=False)
        gb.configure_column("Owner Email", editable=False)
        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            height=500,
            theme='streamlit',
            # return_mode='AS_INPUT',
            fit_columns_on_grid_load=True,
            ColumnsAutoSizeMode="FIT_ALL_COLUMNS_TO_VIEW",
            reload_data = True,
            # data_return_mode='AS_INPUT'  # 确保返回的是编辑后的 DataFrame
        )    
        return grid_response

    grid_response = display_aggrid(df_project_edit)

    st.divider()

    selected = pd.DataFrame(grid_response.get('selected_rows', []))

    if not selected.empty:
        st.session_state.editing_row_index = selected.index.values[0]
    else:
        st.session_state.editing_row_index = None

    #如果有選中行的話，顯示編輯表單
    if st.session_state.editing_row_index is not None:
        edit_project(selected)
    else:
        add_project(df_project_edit)
        

    st.divider()
        # 添加 Logout 按鈕
    if st.button("Logout"):
        logout()  # 調用 logout 函數

    with st.expander("Clear st.session_status.df_project"):
        st.markdown(
            "<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>File Management</h4>",
            unsafe_allow_html=True,
        )

        data_folder = "data"
        file_options = [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))]

        # 選擇要下載的檔案
        selected_file = st.selectbox('Choose a File', file_options)

        # 創建下載按鈕
        if st.button('Download'):
            file_path = os.path.join(data_folder, selected_file)
            with open(file_path, "rb") as file:
                file_bytes = file.read()
                b64_file = base64.b64encode(file_bytes).decode()
                href = f'<a href="data:file/txt;base64,{b64_file}" download="{selected_file}">點擊此處下載 {selected_file}</a>'
                st.markdown(href, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Choose Upload File", type=["csv", "txt"])

        # 上傳按鈕
        if st.button("Upload Files"):
            if uploaded_file is not None:
                data_folder = "data"
                # 檢查 data 資料夾是否存在，如果不存在則創建
                if not os.path.exists(data_folder):
                    os.makedirs(data_folder)
                
                # 保存上傳的檔案
                file_path = os.path.join(data_folder, uploaded_file.name)
                save_uploaded_file(uploaded_file, data_folder)
                st.success(f"Upload Sucessfully {file_path}")
            else:
                st.error("請先選擇一個檔案")



        # 添加清除按鈕
        if st.button("清除 df_project"):
            st.session_state.df_project = None  # 清除數據
            st.success("df_project 已成功清除！")

        # 顯示當前 df_project 狀態（可選）
        if st.session_state.df_project is not None:
            st.write("當前 df_project：")
            st.dataframe(st.session_state.df_project)
        else:
            st.write("df_project 已被清除。")

def extract_main_view():
    col_today,col_page_title ,col_page = st.columns([9,1,2])
    with col_today:
        # 使用 JavaScript 顯示即時時間
        js_code = """
        <div id="datetime" style="font-size: 16px;"></div>
        <script>
            function updateTime() {
                const now = new Date();
                const datetimeStr = now.toLocaleString('zh-TW', { 
                    year: 'numeric', 
                    month: '2-digit', 
                    day: '2-digit', 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit', 
                    hour12: false 
                });
                document.getElementById('datetime').innerText = 'Today: ' + datetimeStr;
            }
            updateTime();  // 初次執行
            setInterval(updateTime, 1000);  // 每秒更新
        </script>
        """
        components.html(js_code, height=30)  # 嵌入 HTML 和 JS
    with col_page_title:
        st.markdown('<div class="date-input-row page-title"><label>🌐</label></div>', unsafe_allow_html=True)
    with col_page:
        page_select = st.selectbox(
                        "🌐",
                        ("All","Setting"),
                        label_visibility = "collapsed"
                        )
    st.markdown(
        "<h4 style='text-align: center; background-color: #4f9ac3; padding: 10px;'>LiG Taiwan Dashboard</h4>",
        unsafe_allow_html=True,
    )

    if "page" not in st.session_state:
        st.session_state.page = "All"

    if page_select == "All":
        st.session_state.page = "All"
    elif page_select == "Setting":
        st.session_state.page = "parameters"

    # Load the content based on current page
    if st.session_state.page == "All":
        all_projects()
    elif st.session_state.page == "parameters":
        parameters()
#====================================================
# 1) 用戶登錄函式
#====================================================
def login_api(username, password): # 模擬的 API 登錄函數
    """模擬 API 登錄請求"""
    response = requests.post(
        f"{CORE_API_SERVER}/api/v1/login",
        data={
            "user[email]": username,
            "user[password]": password,
        },
        headers={"User-Agent": f"{DASHBOARD_AGENT}/0.1"},
    )
    if response.status_code == 200:
        token = response.json().get("token")
        expires_in = 28800  # 8 hour
        return token, expires_in  
    return None, None

def is_token_valid(token,expires_at):  # 檢查 Token 的有效性
    """檢查 Token 是否仍有效"""
    response = requests.get(
        f"{CORE_API_SERVER}/logs/echo",
        headers = {'Authorization': 'Bearer ' + token, 
        'User-Agent': 'DashboardAgent/1.0'}
    )
    expired_check = datetime.now() < datetime.fromisoformat(expires_at)

    if not response.ok or not expired_check:
        return False
    return True

def save_token_to_file(token, expires_at, logged_in_user):
    """將 Token 和過期時間保存到本地文件"""
    token_filepath = os.path.join("data", TOKEN_FILE)
    try:
        # 確保 data 目錄存在
        os.makedirs("data", exist_ok=True)
        with open(token_filepath, "w") as f:
            json.dump({"token": token, "expires_at": expires_at, "logged_in_user": logged_in_user}, f)
        print(f"Saved token to {token_filepath}")
    except OSError as e:
        print(f"Failed to save token to {token_filepath}: {e}")
        st.error(f"無法保存 token 文件：{e}（可能是磁盤空間不足）")
        # 可選：返回 False 表示保存失敗
        return False
    return True

def load_token_from_file():  # 從本地文件加載 Token
    """從本地文件加載 Token 和過期時間"""
    token_filepath = os.path.join("data", TOKEN_FILE)
    if os.path.exists(token_filepath):
        with open(token_filepath, "r") as f:
            data = json.load(f)
        return data.get("token"), data.get("expires_at"), data.get("logged_in_user", "")
    return None, None, None

def clear_token_file():  # 清除本地文件中的 Token
    token_filepath = os.path.join("data", TOKEN_FILE)
    """清除本地文件中的 Token"""
    if os.path.exists(token_filepath):
        os.remove(token_filepath)

def login(): # 登錄函數
    """用戶登錄處理"""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            token, expires_in = login_api(username, password)
            # 呼叫API 獲取 Token跟過期時間
            st.write(f'token: {token}')
            st.write(f'expires_in: {expires_in}')

            if token:
                #加密 token
                expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                st.session_state["auth_token"] = token
                st.session_state["expires_at"] = expires_at
                st.session_state["logged_in_user"] = username
                save_token_to_file(token, expires_at, username)  # 保存到本地文件
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

def logout(): # 登出函數
    """處理用戶登出"""
    st.session_state["auth_token"] = ""
    st.session_state["expires_at"] = (datetime.now()).isoformat()
    st.session_state["logged_in_user"] = ""
    save_token_to_file("", (datetime.now()).isoformat(),"")
    st.success("Logged out!")
    st.rerun()

def check_login_status(): # 檢查登入狀態
    """檢查用戶是否已登入"""
    # 如果 session 中沒有 Token，嘗試從文件加載
    if "auth_token" not in st.session_state or "logged_in_user" not in st.session_state:
        token, expires_at, logged_in_user = load_token_from_file()
        st.session_state["auth_token"] = token
        st.session_state["expires_at"] = expires_at
        st.session_state["logged_in_user"] = logged_in_user

    # 如果 Token 無效，要求重新登入
    if not is_token_valid(st.session_state.get("auth_token"), st.session_state.get("expires_at")):
        st.session_state["auth_token"] = ""
        st.session_state["expires_at"] = (datetime.now()).isoformat()
        st.session_state["logged_in_user"] = ""
        login()
        st.stop()  # 停止執行後續代碼

#====================================================
# 2) Main()
#====================================================
def main():
    # print("your api host url is: ", os.getenv("API_HOST", None))
    # bypass the login page if the API_HOST is not set
    # if os.getenv("API_HOST", None):   

    initialize()
    check_dataframe(df_scan, "掃描數據 (df_scan)", ["scantime"])
    # check_dataframe(st.session_state.df_project, "專案數據 (df_project)", ["Project Name"])   
    token, expires_at, logged_in_user = load_token_from_file()

    if is_token_valid(token,expires_at):
        st.session_state._lig_token = token
        st.session_state["logged_in_user"] = logged_in_user

    check_login_status()
    extract_main_view()

# %% Web App 測試 (檢視成果)  ============================================================================= ##
if __name__ == "__main__":
    main()
