#%% 匯入套件(包含我們寫好的function檔)

import pandas as pd 
import streamlit as st
import plotly.io as pio
pio.renderers.default='browser'
import math
import numpy as np
import plotly.graph_objects as go
from db_function import *

st.set_page_config(
    page_title='光服務數據中心',
    layout='wide',
    initial_sidebar_state='collapsed'
    )
st.markdown(
    """
    <style>
        .stTextInput > label {
            font-size:105%; 
            font-weight:bold; 
            color:blue;
        }
        .stMultiSelect > label {
            font-size:105%; 
            font-weight:bold; 
            color:blue;
        } 
        .stRadio > label {
            font-size:105%; 
            font-weight:bold; 
            color:blue;
        } 
        .stSlider > label {
            font-size:105%; 
            font-weight:bold; 
            color:blue;
        }
    </style>
    """, 
    unsafe_allow_html=True)

table_style = """
<style>
table {
    font-size: 9px;
}
</style>
"""
expander_style = """
<style>
expander {
    font-size: 9px;
    color:blue;
}
</style>
"""

st.sidebar.markdown(table_style,unsafe_allow_html=True)
st.sidebar.markdown(expander_style,unsafe_allow_html=True)



#%% 包成一整個 backend function: 主要資料處理及視覺化儀表板製

def backend(scan_data:pd.DataFrame, data:dict):
    




    return

#%% 頁面呈現
def main():
    
    
    #%% 【側邊欄】
    #backed
    df_file = pd.read_csv("data/df_file.csv",encoding="utf-8-sig")

    #front
    st.sidebar.subheader('基礎數據上傳')
    
    # 覆蓋github 之scandata ==============================================
    from github import Github
    
    # 取得個人訪問權杖
    access_token = "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"
    
    # 建立 GitHub 物件
    g = Github(access_token)
    
    # 取得儲存庫名稱和檔案路徑
    repository_name = 'henrylin642/LiG-DataCenter'
    file_path = 'data/scandata.csv'
    
    # 讀取上傳的檔案
    uploaded_file_scandata = st.sidebar.file_uploader("上傳掃描數據", type="csv")
    
    # 檢查是否上傳了檔案
    if uploaded_file_scandata is not None:
        # 取得檔案內容
        file_content = uploaded_file_scandata.read()
    
        # 取得要更新的檔案名稱
        file_name = uploaded_file_scandata.name
    
        # 取得儲存庫
        repository = g.get_repo(repository_name)
    
        # 取得原有檔案的內容和 SHA 值
        existing_file = repository.get_contents(file_path)
        existing_content = existing_file.decoded_content.decode('utf-8')
        sha = existing_file.sha
    
        # 檢查檔案是否有變更
        if file_content != existing_content:
            # 更新檔案內容
            repository.update_file(file_path, 'Commit Message', file_content, sha)
    
            # 提示檔案已成功更新
            st.sidebar.success('檔案已成功更新')
        else:
            # 提示檔案無需更新
            st.sidebar.warning('檔案無需更新')
    else:
        # 提示尚未上傳檔案
        st.sidebar.info('請上傳檔案')
        
    with st.sidebar.expander("檔案資訊"):
        st.table(df_file)
        
    # 在側邊欄顯示選擇框
    selected_db = st.sidebar.selectbox("選擇資料庫", df_file['db'])
    uploaded_file = st.sidebar.file_uploader(f"上傳數據", type="csv")
    df_light,filename_light, upload_date_light = upload(df_file,"light",uploaded_file)
    df_coor,filename_coor, upload_date_coor = upload(df_file,"coor",uploaded_file)
    df_arobjs,filename_arobjs, upload_date_arobjs = upload(df_file,"arobjs",uploaded_file)
    df_user,filename_user, upload_date_user = upload(df_file,"user",uploaded_file)
    df_user_converter = userdata_arrange(df_user)
    #get_scan_data(df_light,df_coor,df_arobjs)

    if selected_db == "light":
        df_light = upload(df_file,selected_db,uploaded_file)
    elif selected_db == "coor":
        df_coor = upload(df_file,selected_db,uploaded_file) 
    elif selected_db == "arobjs":
        df_arobjs = upload(df_file,selected_db,uploaded_file)
     
    #%% 【主頁面】
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>全台基礎數據</h4>", unsafe_allow_html=True)
    
    
    #%% 展示資料集-註冊人數
    ## backend
    count_user_today,count_user_yesterday,count_user_thisweek,count_user_lastweek,count_user_thismonth,count_user_lastmonth = get_reg_user_data(df_user_converter)

    ## fronted: count數據
    st.markdown("<h6 style='text-align: left; padding: 10px;color: red'>每日六點更新註冊數據</h6>", unsafe_allow_html=True)
    col_u_1,col_u_2,col_u_3 = st.columns(3)

    with col_u_1:
        st.write(f'今日註冊人數：{count_user_today}')
        st.write(f'昨日註冊人數：{count_user_yesterday}')
    with col_u_2:
        st.write(f'本週註冊人數：{count_user_thisweek}')
        st.write(f'上週註冊人數：{count_user_lastweek}')
    with col_u_3:    
        st.write(f'本月註冊人數：{count_user_thismonth}')
        st.write(f'上月註冊人數：{count_user_lastmonth}')
    
    #%% 展示資料集-By城市數據
    ## backed
    df_scan_coor_scene_city,df_coor_city,df_coor,df_arobjs = get_scan_data(df_light,df_coor,df_arobjs)
    table_city_scans = get_cities_data(df_scan_coor_scene_city,df_coor_city)
    
    ##fronted:
    with st.expander("By 城市"):
        st.dataframe(table_city_scans.sort_values(by='昨日',ascending=False).transpose().iloc[:2].style.highlight_max(axis=1))
        st.dataframe(table_city_scans.sort_values(by='上週',ascending=False).transpose().iloc[2:4].style.highlight_max(axis=1))
        st.dataframe(table_city_scans.sort_values(by='上月',ascending=False).transpose().iloc[4:6].style.highlight_max(axis=1))
    #%% 展示資料集-By專案
    ## backend
    coors_list = get_coor_list(df_scan_coor_scene_city)
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()
    table_daily_scans_dropzero = get_daily_data(df_scan_coor_scene_city,yesterday,today,coors_list)
    table_weekly_scan_dropzero = get_weekly_date(df_scan_coor_scene_city,today,2,coors_list)
    table_monthly_scan_dropzero = get_monthly_date(df_scan_coor_scene_city,today,2,coors_list)

    ## frontend: download button
    with st.expander("By 專案"):
        col1,col2,col3 = st.columns(3)
        with col1:
            st.write("今日昨日")
            st.dataframe(table_daily_scans_dropzero.style.highlight_max(axis=0))
            #col1.write(table_daily_scans_dropzero.iloc[:2].transpose().sort_values(by='昨天',ascending=False))

        with col2:
            st.write("本週上週")
            st.dataframe(table_weekly_scan_dropzero.style.highlight_max(axis=0))
            #col2.write(table_weekly_scan_dropzero.iloc[:2].transpose().sort_values(by='上週',ascending=False))

        with col3:
            st.write("本月上月")
            st.dataframe(table_monthly_scan_dropzero.style.highlight_max(axis=0))
    
    #%% 展示 Raw data
    ## backed

    ## fronted
    with st.expander("Raw Data"):
        df_scan_coor_scene_city = df_scan_coor_scene_city[['scantime','lig_id','coor_name','city']].sort_values(by='scantime',ascending = False)
        st.dataframe(df_scan_coor_scene_city)
    
    #%%     
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>數據查詢平台</h4>", unsafe_allow_html=True)
        
    #%% 資料篩選條件1-選擇坐標系
    #backed 
    # 找出上週掃描量最高的 coor_name
    lastweek_max = table_weekly_scan_dropzero.loc[table_weekly_scan_dropzero.index, "總和"].idxmax()
    
    #fronted
    select_coors = st.multiselect(
        label="選擇查詢場域(最多4個)",
        options=coors_list,
        default=lastweek_max
        )
    
    #%% 展示資料-coors包含的lig_id
    ## backed
    lig_ids = get_ids(df_scan_coor_scene_city,select_coors)
    lig_ids_string = ', '.join(map(str, lig_ids))
    
    ## fronted
    with st.expander("包含light id"):
        st.write(lig_ids_string)
    
    #%% 展示資料-select coors包含的scenes
    ## backed
    scenes_list = get_scenes(df_coor,select_coors)
    scenes_list_sorted = sorted(scenes_list)
    # 計算需要幾個columns
    num_columns = 5
    num_rows = math.ceil(len(scenes_list_sorted) / num_columns)
    # 補足列表，使其元素數量為 num_columns 的倍數
    padding = num_columns - (len(scenes_list_sorted) % num_columns)
    scenes_list_sorted += [''] * padding
    # 將列表轉換為2D列表
    scenes_list_sorted_2d = np.array(scenes_list_sorted).reshape(num_rows, num_columns).tolist()
    # 建立表格
    scene_list = pd.DataFrame(scenes_list_sorted_2d)
    
    ## fronted
    with st.expander("包含場景Scenes"):
        st.table(scene_list)
    
    #%% 資料篩選條件1-選擇時間區間
    # backed
    
    
    # fronted
    col_date_1,col_date_2 = st.columns([1,3])
    freq_choice = col_date_1.radio(label="選擇查詢週期",options=['日','週','月'],horizontal=True)         
    range_num = col_date_2.slider(label="選擇欲查詢的日期範圍",max_value=10,min_value =1,step=1,value=7) 
    
    #%% 展示資料-坐標系掃描數據
    #backed
    table_scans,start_date,end_date = get_coor_scan_data(df_scan_coor_scene_city,select_coors,today,freq_choice,range_num)
    st.success(f"您選擇了【近{range_num}{freq_choice}】【{start_date}~{end_date}】的區間查詢") 
    #fronted
    st.markdown("<h5 style='text-align: left; padding: 10px;'>場域掃描數據</h5>", unsafe_allow_html=True)
    col_data1 , col_data2  = st.columns([1,2])
    with col_data1:
        st.dataframe(table_scans,height=400)

    with col_data2:
        fig = go.Figure()
        for coor in select_coors:
            fig.add_trace(go.Bar(
                x=table_scans.index,
                y=table_scans[coor],
                name= coor,
            ))
        
        fig.update_layout(xaxis={'type': 'category'})
        
        st.plotly_chart(fig)


    #%% 展示資料-點擊排行榜、raw data
    #backed
    scenes_list = get_scenes(df_coor,select_coors)
    df_obj_click_scene = get_GA_data(df_arobjs,start_date,end_date,scenes_list)
    df_obj_click_scene = df_obj_click_scene.set_index('物件ID')
    df_raw = get_rawdata(df_scan_coor_scene_city,lig_ids,start_date,end_date)
    
    #fronted
    col_click , col_raw = st.columns(2)
    with col_click:
        st.markdown("<h5 style='text-align: left; padding: 10px;'>物件點擊排行榜</h5>", unsafe_allow_html=True)
        st.dataframe(df_obj_click_scene)
    with col_raw:
        st.markdown("<h5 style='text-align: left; padding: 10px;'>Raw Data</h5>", unsafe_allow_html=True)
        st.dataframe(df_raw)
#%% Web App 測試 (檢視成果)      
if __name__ == "__main__":
    main()
    
