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



#%% 包成一整個 backend function: 主要資料處理及視覺化儀表板製 ============================================================================= ##

def backend():
        return 

#%% 頁面呈現 ============================================================================= ##
def main():
    df_file = pd.read_csv("data/df_file.csv",encoding="utf-8-sig")  # 檔案資訊
    df_light,filename_light, upload_date_light = upload(df_file,"light",None)  # id <==> coordinate
    df_coor,filename_coor, upload_date_coor = upload(df_file,"coor",None)  # coordinate <==> scenes
    df_arobjs,filename_arobjs, upload_date_arobjs = upload(df_file,"arobjs",None)
    df_user,filename_user, upload_date_user = upload(df_file,"user",None)
    df_user_converter = userdata_arrange(df_user)
    df_scan_coor_scene_city,df_coor_city,df_coor,df_arobjs = get_scan_data(df_light,df_coor,df_arobjs)
    coors_list = get_coor_list(df_scan_coor_scene_city)
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()

    #%% 【側邊欄】 ============================================================================= ##
    #backed
    

    #front
    st.sidebar.subheader('基礎數據上傳')

    ## ============================================================================= ##
    # 覆蓋github 之scandata 
    #from github import Github
    
    # 取得個人訪問權杖
    #access_token = "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"
    
    # 建立 GitHub 物件
    #g = Github(access_token)
    
    # 取得儲存庫名稱和檔案路徑
    #repository_name = 'henrylin642/LiG-DataCenter'
    file_path = 'data/scandata.csv'
    
    # 讀取上傳的檔案
    #uploaded_file_scandata = st.sidebar.file_uploader("上傳掃描數據", type="csv")
    
    # 檢查是否上傳了檔案
    #if uploaded_file_scandata is not None:
        # 取得檔案內容
        #file_content = uploaded_file_scandata.read()
    
        # 取得要更新的檔案名稱
        #file_name = uploaded_file_scandata.name
    
        # 取得儲存庫
        #repository = g.get_repo(repository_name)
    
        # 取得原有檔案的內容和 SHA 值
        #existing_file = repository.get_contents(file_path)
        #existing_content = existing_file.decoded_content.decode('utf-8')
        #sha = existing_file.sha
    
        # 檢查檔案是否有變更
        #if file_content != existing_content:
            # 更新檔案內容
            #repository.update_file(file_path, 'Commit Message', file_content, sha)
    
            # 提示檔案已成功更新
            #st.sidebar.success('檔案已成功更新')
        #else:
            # 提示檔案無需更新
            #st.sidebar.warning('檔案無需更新')
    #else:
        # 提示尚未上傳檔案
        #st.sidebar.info('請上傳檔案')
    #%%# ============================================================================= ##    
    with st.sidebar.expander("檔案資訊"):
        st.table(df_file)
        
    # 在側邊欄顯示選擇框
    selected_db = st.sidebar.selectbox("選擇資料庫", df_file['db'])
    uploaded_file = st.sidebar.file_uploader(f"上傳數據", type="csv")
    
    #get_scan_data(df_light,df_coor,df_arobjs)

    if selected_db == "light":
        df_light = upload(df_file,selected_db,uploaded_file)
    elif selected_db == "coor":
        df_coor = upload(df_file,selected_db,uploaded_file) 
    elif selected_db == "arobjs":
        df_arobjs = upload(df_file,selected_db,uploaded_file)
    #%%#【主頁面】 ============================================================================= ## 
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>全台基礎數據</h4>", unsafe_allow_html=True)
    
    ## ============================================================================= ##
    #%% 展示資料集-註冊人數  ============================================================================= ##
    ## backend
    count_user_today,count_user_yesterday,count_user_thisweek,count_user_lastweek,count_user_thismonth,count_user_lastmonth = get_reg_user_data(df_user_converter)

    ## fronted: count數據
    
    user_data = {
    '時間': [
        '今日',
        '昨日',
        '本週',
        '上週',
        '本月',
        '上月'
    ],
    '註冊人數': [
        count_user_today,
        count_user_yesterday,
        count_user_thisweek,
        count_user_lastweek,
        count_user_thismonth,
        count_user_lastmonth
    ],  
    }
    
    df_userdata = pd.DataFrame(user_data).set_index('時間')
    
    
    
    # col_u_1,col_u_2,col_u_3 = st.columns(3)

    # with col_u_1:
    #     st.write(f'今日註冊人數：{count_user_today}')
    #     st.write(f'昨日註冊人數：{count_user_yesterday}')
    # with col_u_2:
    #     st.write(f'本週註冊人數：{count_user_thisweek}')
    #     st.write(f'上週註冊人數：{count_user_lastweek}')
    # with col_u_3:    
    #     st.write(f'本月註冊人數：{count_user_thismonth}')
    #     st.write(f'上月註冊人數：{count_user_lastmonth}')

    #%% ============================================================================= ##
    ## backed
    
    day1 = today - timedelta(days=30)
    df_30day = get_daily_data(df_scan_coor_scene_city,day1,today,coors_list)
    # 計算各列的總和
    sum_row = df_30day.sum()
    
    # 將總和新增到 DataFrame 的最後一列
    df_30day.loc['小計'] = sum_row
    ## fronted
    df_30day_trimmed = df_30day.iloc[:, :-1]  # 剔除最後一欄

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_30day_trimmed.tail(1).columns,
        y=df_30day_trimmed.tail(1),
        name= "全台近30日掃描量圖",
    ))
    fig.update_layout(
        title={
        'text': "近30日掃描量",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="日期",
    yaxis_title="掃描量",
    width=800,
    )
    fig.update_layout(xaxis={'type': 'category'})
    
    col_user , col_30day = st.columns([1,4])
    with col_user:
        st.markdown("<h6 style='text-align: left; padding: 10px;color: red'>每日六點更新註冊數據</h6>", unsafe_allow_html=True)
        st.dataframe(df_userdata)
    with col_30day:
        st.plotly_chart(fig)
    #%% 展示資料-近30日掃描數據  ============================================================================= ##
    df_30day = df_30day.reindex(columns=df_30day.columns[::-1])
    # 計算第三欄以後所有數據的平均值
    average_values = df_30day.iloc[:, 1:].mean(axis=1).round(1)
    df_30day.insert(1, '平均值', average_values.round(1))
    
    with st.expander("各專案近30日掃描量"):
        st.dataframe(df_30day)
    
    #%% 展示資料集-By城市數據  ============================================================================= ##
    ## backed
    table_city_scans = get_cities_data(df_scan_coor_scene_city,df_coor_city)
    df_ty = table_city_scans.sort_values(by='昨日',ascending=False).transpose().iloc[:2]
    df_week = table_city_scans.sort_values(by='昨日',ascending=False).transpose().iloc[2:4]
    df_month = table_city_scans.sort_values(by='昨日',ascending=False).transpose().iloc[4:6]
    def fig_draw(df):        
        fig = go.Figure()
        i=0
        for row in df.index:        
            fig.add_trace(go.Bar(
                x=df.columns,
                y=df.iloc[i],
                name= row,
            ))
            i +=1
        fig.update_layout(xaxis={'type': 'category'})
        return fig
    
    fig_ty = fig_draw(df_ty)
    fig_ty.update_layout(
        title={
        'text': "城市掃描量統計-昨日/今日",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="日期",
    yaxis_title="掃描量",
    width=1000,
    )
    fig_week = fig_draw(df_week)
    fig_week.update_layout(
        title={
        'text': "城市掃描量統計-上週/本週",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="日期",
    yaxis_title="掃描量",
    width=1000,
    )
    fig_month = fig_draw(df_month)
    fig_month.update_layout(
        title={
        'text': "城市掃描量統計-上月/本月",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="日期",
    yaxis_title="掃描量",
    width=1000,
    )
    
    ##fronted:
    with st.expander("By 城市"):
        st.plotly_chart(fig_ty)
        #st.divider()
        st.plotly_chart(fig_week)
        #st.divider()
        st.plotly_chart(fig_month)

    #%% 展示資料集-By專案  ============================================================================= ##
    ## backend
    coors_list = get_coor_list(df_scan_coor_scene_city)
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()
    table_daily_scans_dropzero = get_daily_data(df_scan_coor_scene_city,yesterday,today,coors_list)
    table_daily_trim = table_daily_scans_dropzero.iloc[:,:2]
    table_daily_trim.columns = ["昨日", "今日"]
    table_weekly_scan_dropzero = get_weekly_date(df_scan_coor_scene_city,today,2,coors_list)
    table_weekly_trim = table_weekly_scan_dropzero.iloc[:,:2]
    table_weekly_trim.columns = ["上週", "本週"]
    table_monthly_scan_dropzero = get_monthly_date(df_scan_coor_scene_city,today,2,coors_list)
    table_monthly_trim = table_monthly_scan_dropzero.iloc[:,:2]
    table_monthly_trim.columns = ["上月", "本月"]
    # 整合三個表格
    combined_table = pd.concat([table_daily_trim, table_weekly_trim, table_monthly_trim], axis=1)
    combined_table = combined_table.dropna().loc[~(combined_table == 0).all(axis=1)]
    
    ## frontend: download button
    with st.expander("By 專案"):
        st.dataframe(combined_table)
 
    #%% 展示 Raw data  ============================================================================= ##
    ## backed

    ## fronted
    with st.expander("Raw Data"):
        df_scan_coor_scene_city = df_scan_coor_scene_city[['scantime','lig_id','coor_name','city']].sort_values(by='scantime',ascending = False)
        st.dataframe(df_scan_coor_scene_city)

    #%%   ============================================================================= ##  
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>數據查詢平台</h4>", unsafe_allow_html=True)
  
    #%% 資料篩選條件1-選擇坐標系  ============================================================================= ##
    #backed 
    # 找出上週掃描量最高的 coor_name
    lastweek_max = table_weekly_scan_dropzero.loc[table_weekly_scan_dropzero.index, "總和"].idxmax()
    
    #fronted
    select_coors = st.multiselect(
        label="選擇查詢場域(最多4個)",
        options=coors_list,
        default=lastweek_max
        )

    #%% 展示資料-coors包含的lig_id  ============================================================================= ##
    ## backed
    lig_ids = get_ids(df_scan_coor_scene_city,select_coors)
    lig_ids_string = ', '.join(map(str, lig_ids))
    
    ## fronted
    with st.expander("包含light id"):
        st.write(lig_ids_string)

    #%% 展示資料-select coors包含的scenes  ============================================================================= ##
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

    #%% 資料篩選條件1-選擇時間區間  ============================================================================= ##
    # backed
    
    
    # fronted


    #%% 展示資料-坐標系掃描數據  ============================================================================= ##
    #backed
    col_date_1,col_date_2 = st.columns(2)
    freq_choice = col_date_1.radio(
                    label="選擇查詢週期",
                    options=('小時','日','週','月'),
                    horizontal=True
                    ) 
    if freq_choice == '小時':
        selected_date = col_date_2.date_input(label='選擇欲查詢的日期',value = None) 
        df_24hours = H24hour_scans(df_scan_coor_scene_city,selected_date,select_coors)
        fig_24hour = go.Figure()
        for coor in select_coors:
            fig_24hour.add_trace(go.Bar(
                x=df_24hours.index,
                y=df_24hours[coor],
                name= coor,
            ))
        fig_24hour.update_layout(xaxis={'type': 'category'})

        fig_24hour.update_layout(
            title={
            'text': "一日掃描量",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="日期",
        yaxis_title="掃描量",
        width=800,
        )
        start_date = selected_date
        end_date = selected_date
    else:
        range_num = col_date_2.slider(label="選擇欲查詢的日期範圍",max_value=10,min_value =1,step=1,value=7) 
        table_scans,start_date,end_date = get_coor_scan_data(df_scan_coor_scene_city,select_coors,today,freq_choice,range_num)
        fig_scan = go.Figure()
        for coor in select_coors:
            fig_scan.add_trace(
                go.Bar(
                    x=table_scans.index,
                    y=table_scans[coor],
                    name= coor,
                    ))
        
        fig_scan.update_layout(xaxis={'type': 'category'})
        fig_scan.update_layout(
            title={
            'text': f"近{range_num}{freq_choice}掃描量",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="日期",
        yaxis_title="掃描量",
        width=800,
        )
    
   
    #fronted
    st.markdown("<h5 style='text-align: left; padding: 10px;'>場域掃描數據</h5>", unsafe_allow_html=True)
    col_data1 , col_data2  = st.columns([1,2])
    with col_data1:
        if freq_choice == '小時':
            st.dataframe(df_24hours)
        else:
            st.dataframe(table_scans,height=400)
    
    with col_data2:
        if freq_choice == '小時':
            st.plotly_chart(fig_24hour)
        else:
            st.plotly_chart(fig_scan)


    #%% 展示資料-點擊排行榜、raw data  ============================================================================= ##
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
        
    #%% df_light + city 資料維護 ============================================================================= ##
    
    
    #fronted:
    
    
#%% Web App 測試 (檢視成果)  ============================================================================= ##    
if __name__ == "__main__":
    main()
    
