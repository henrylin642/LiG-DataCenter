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
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()
    df_file = pd.read_csv("data/df_file.csv",encoding="utf-8-sig")  # 檔案資訊
    df_light,filename_light, upload_date_light = upload(df_file,"light",None)  # id <==> coordinate
    df_coor,filename_coor, upload_date_coor = upload(df_file,"coor",None)  # coordinate <==> scenes
    df_arobjs,filename_arobjs, upload_date_arobjs = upload(df_file,"arobjs",None)
    df_user,filename_user, upload_date_user = upload(df_file,"user",None)
    df_user_converter,domain_df = userdata_arrange(df_user)
    df_scan_coor_scene_city,df_coor_city,df_coor,df_arobjs = get_scan_data(df_light,df_coor,df_arobjs)
    coors_list = get_coor_list(df_scan_coor_scene_city)    
    #%% 【側邊欄】 ============================================================================= ##
    #backed
    
    #front
    st.sidebar.subheader('基礎數據上傳')

    #%%# ============================================================================= ##    
    with st.sidebar.expander("檔案資訊"):
        st.table(df_file)
        
    # 在側邊欄顯示選擇框
    # selected_db = st.sidebar.selectbox("選擇資料庫", df_file['db'])
    # uploaded_file = st.sidebar.file_uploader(f"上傳數據", type="csv")
    
    # #get_scan_data(df_light,df_coor,df_arobjs)

    # if selected_db == "light":
    #     df_light = upload(df_file,selected_db,uploaded_file)
    # elif selected_db == "coor":
    #     df_coor = upload(df_file,selected_db,uploaded_file) 
    # elif selected_db == "arobjs":
    #     df_arobjs = upload(df_file,selected_db,uploaded_file)
    #%%#【主頁面】 ============================================================================= ## 
    st.write(f"今天日期：{today}")
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>全台基礎數據</h4>", unsafe_allow_html=True)
    ## ============================================================================= ##
    #%% 展示資料集-註冊人數  ============================================================================= ##
    ## backend
    count_user_today,count_user_yesterday,count_user_thisweek,count_user_lastweek,count_user_thismonth,count_user_lastmonth = get_reg_user_data(df_user_converter)    
    user_data = {
    '時間': ['今日','昨日','本週','上週','本月','上月'],
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
    
    day1 = today - timedelta(days=30)
    
    if 'df_360day' not in st.session_state:
        df_30day = get_daily_data(df_scan_coor_scene_city,day1,today,coors_list)        
        # 計算各列的總和
        sum_row = df_30day.sum()        
        # 將總和新增到 DataFrame 的最後一列
        df_30day.loc['小計'] = sum_row    
        st.session_state['df_360day'] = df_30day
    df_30day = st.session_state['df_360day']    
    df_30day_trimmed = df_30day.iloc[:, :-1]  # 剔除最後一欄

    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_30day_trimmed.columns,
        y=df_30day_trimmed.iloc[-1],
        text=df_30day_trimmed.iloc[-1],
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
    # frontend
    col_30day ,col_user = st.columns([5,1])
    with col_user:
        st.markdown("<h6 style='text-align: left'>安裝人數統計：</h6>", unsafe_allow_html=True)
        st.dataframe(
            data = df_userdata,
            width = 400
            )
        st.markdown("<h12 style='text-align: left;color: red'>每日六點更新註冊數據</h12>", unsafe_allow_html=True)
        with st.expander("user_domain"):
            st.dataframe(domain_df)
    with col_30day:
        st.plotly_chart(fig)
    
    #%% 展示資料-近30日掃描數據  ============================================================================= ##
    df_30day = df_30day.reindex(columns=df_30day.columns[::-1])
    # 計算第三欄以後所有數據的平均值
    average_values = df_30day.iloc[:, 1:].mean(axis=1).apply(lambda x: round(x, 1))
    df_30day.insert(1, '平均值', average_values)
    
    with st.expander("各專案近30日掃描量"):
        st.dataframe(
            data = df_30day,
            width = 1000
            )
    
    #%% 展示資料集-By城市數據  ============================================================================= ##
    ## backed
    if 'table_city_scans' not in st.session_state:        
        table_city_scans = get_cities_data(df_scan_coor_scene_city,df_coor_city)
        st.session_state['table_city_scans'] = table_city_scans
    table_city_scans = st.session_state['table_city_scans']
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
    height = 400
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
    height = 400
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
    height = 400
    )
    
    ##fronted:
    with st.expander("By 城市 (點擊欄位可排序)"):
        periond_status = st.radio(label="選擇週期",options=["昨日今日","上週本週","上月本月"],horizontal=True)
        if periond_status =="昨日今日":
            st.plotly_chart(fig_ty)
        elif periond_status == "上週本週":
            st.plotly_chart(fig_week)
        else:
            st.plotly_chart(fig_month)

    #%% 展示資料集-By專案  ============================================================================= ##
    ## backend
    if 'coors_list' not in st.session_state:
        coors_list = get_coor_list(df_scan_coor_scene_city)
        st.session_state['coors_list'] =coors_list
    coors_list = st.session_state['coors_list']    
    
    
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()

    if 'df_project_sumary' not in st.session_state:        
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
        df_project_sumary = pd.concat([table_daily_trim, table_weekly_trim, table_monthly_trim], axis=1)
        df_project_sumary = df_project_sumary.dropna().loc[~(df_project_sumary == 0).all(axis=1)]
        
        st.session_state['df_project_sumary'] = df_project_sumary
        
    df_project_sumary = st.session_state['df_project_sumary']
    
    ## frontend: download button
    with st.expander("By 專案 (點擊欄位可排序)"):
        st.dataframe(
            data = df_project_sumary,
            width = 1000           
            )
 
    #%% 展示 Raw data  ============================================================================= ##
    ## backed

    ## fronted
    with st.expander("Raw Data"):
        df_scan_coor_scene_city = df_scan_coor_scene_city[['scantime','lig_id','coor_name','city']].sort_values(by='scantime',ascending = False)
        st.dataframe(
            data = df_scan_coor_scene_city,
            width = 1000           
            )

    #%%   ============================================================================= ##  
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>數據查詢平台</h4>", unsafe_allow_html=True)
  
    #%% 資料篩選條件1-選擇坐標系  ============================================================================= ##
    #backed 
    # 找出上週掃描量最高的 coor_name
    lastweek_max = df_project_sumary.loc[df_project_sumary.index, "上週"].idxmax()
    
    #fronted
    select_coors = st.multiselect(
        label="選擇查詢場域 (最多可同時查詢4個)",
        options=coors_list,
        default=lastweek_max
        )
    select_coors_string = ', '.join(map(str, select_coors))
    #%% 展示資料-coors包含的lig_id  ============================================================================= ##
    ## backed
    lig_ids = get_ids(df_scan_coor_scene_city,select_coors)
    lig_ids_string = ', '.join(map(str, lig_ids))
    
    ## fronted
    with st.expander("包含light id"):
        st.write(lig_ids_string)

    #%% 展示資料-select coors包含的scenes  ============================================================================= ##
    ## backed
    if len(select_coors) > 0:
        scenes_list = get_scenes(df_coor,select_coors)
        scenes_list_sorted = sorted(scenes_list)
        # 計算需要幾個columns
        num_columns = 5
        num_rows = math.ceil(len(scenes_list_sorted) / num_columns)
        remainder = len(scenes_list_sorted) % num_columns
        # 補足列表，使其元素數量為 num_columns 的倍數
        if remainder == 0:
            padding = 0
        else:
            padding = num_columns - (len(scenes_list_sorted) % num_columns)
        scenes_list_sorted += [''] * padding
        # 將列表轉換為2D列表
        scenes_list_sorted_2d = np.array(scenes_list_sorted).reshape(num_rows, num_columns).tolist()
        # 建立表格
        scene_list = pd.DataFrame(scenes_list_sorted_2d)
    else:
        scene_list = pd.DataFrame()
    
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
                    options=('日','週','月','小時'),
                    horizontal=True
                    ) 
    if freq_choice == '小時':
        #selected_date = col_date_2.date_input(label='選擇欲查詢的日期',value = None) 
        selected_date = col_date_2.date_input(label='選擇欲查詢的日期',value = yesterday) 
        df_24hours,df_rawfilter = H24hour_scans(df_scan_coor_scene_city,selected_date,select_coors)
        fig_24hour = go.Figure()
        for coor in select_coors:
            fig_24hour.add_trace(go.Bar(
                x=df_24hours.index,
                y=df_24hours[coor],
                text=df_24hours[coor],
                name= coor,
            ))
        fig_24hour.update_layout(xaxis={'type': 'category'})

        fig_24hour.update_layout(
            title={
            'text': f"「{select_coors_string}」{selected_date}當日掃描量",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="時間",
        yaxis_title="掃描量",
        width=1000,
        height=400
        )
        start_date = selected_date
        end_date = selected_date
        csv_24hour = csv_download(df_24hours)
    else:
        range_num = col_date_2.slider(label="選擇欲查詢的日期範圍",max_value=30,min_value =1,step=1,value=30) 
        table_scans,start_date,end_date,df_filter = get_coor_scan_data(df_scan_coor_scene_city,select_coors,today,freq_choice,range_num)
        table_scans.index = pd.to_datetime(table_scans.index)
        table_scans.index = table_scans.index.strftime('%m/%d')
        fig_scan = go.Figure()
        for coor in select_coors:
            fig_scan.add_trace(
                go.Bar(
                    x=table_scans.index,
                    y=table_scans[coor],
                    text=table_scans[coor],
                    name= coor,
                    ))
        fig_scan.update_layout(xaxis={'type': 'category'})
        fig_scan.update_layout(
            title={
            'text': f"「{select_coors_string}」從{start_date}至{end_date}掃描量",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="日期",
        yaxis_title="掃描量",
        width=1000,
        height=400
        )
    
    #fronted
    st.markdown("<h5 style='text-align: left; padding: 10px;'>場域掃描數據</h5>", unsafe_allow_html=True)

    if freq_choice == '小時':
        st.plotly_chart(fig_24hour)
        
        st.download_button(
         label = "下載圖表數據csv檔",
         data = csv_24hour,
         file_name='點擊排行榜.csv',
         mime='text/csv',
         )
    
    else:
        st.plotly_chart(fig_scan)


    #%% 展示資料-點擊排行榜、raw data  ============================================================================= ##
    #backed
    scenes_list = get_scenes(df_coor,select_coors)
    df_obj_click_scene = get_GA_data(df_arobjs,start_date,end_date,scenes_list)
    df_obj_click_scene = df_obj_click_scene.set_index('物件ID')
    df_raw = get_rawdata(df_scan_coor_scene_city,lig_ids,start_date,end_date)
    csv_scan_coor_scene_city = csv_download(df_obj_click_scene)
    
    #fronted
    #col_click , col_raw = st.columns(2)
    with st.expander('點擊排行榜'):
        #with col_click:
        #st.markdown("<h5 style='text-align: left; padding: 10px;'>物件點擊排行榜</h5>", unsafe_allow_html=True)
        st.download_button(
         label = "下載物件點擊排行榜csv檔",
         data = csv_scan_coor_scene_city,
         file_name='點擊排行榜.csv',
         mime='text/csv',
         )
        st.table(
            data = df_obj_click_scene,
            )

    with st.expander("場景掃描raw data"):
        st.markdown("<h5 style='text-align: left; padding: 10px;'>Raw Data</h5>", unsafe_allow_html=True)
        st.table(
            data = df_raw
            )
    
 #%%   ============================================================================= ##  
    st.markdown("<h4 style='text-align: center; background-color: #e6f2ff; padding: 10px;'>註冊用戶查詢平台</h4>", unsafe_allow_html=True)
        
    #%% 展示資料-坐標系掃描數據  ============================================================================= ##
    #backed
    col_userdate_1,col_userdate_2 = st.columns(2)
    user_freq_choice = col_userdate_1.radio(
                    label="選擇user查詢週期",
                    options=('小時','日','週','月'),
                    horizontal=True
                    ) 
    if user_freq_choice == '小時':
        selected_date = col_userdate_2.date_input(label='選擇用戶註冊欲查詢的日期',value = yesterday) 
        df_24hours,df_user_filter = H24hour_users(df_user_converter,selected_date)
        fig_24hour = go.Figure()
        fig_24hour.add_trace(go.Bar(
            x=df_24hours.index,
            y=df_24hours['註冊訪客'],
            text=df_24hours['註冊訪客'],
        ))
        fig_24hour.update_layout(xaxis={'type': 'category'})
    
        fig_24hour.update_layout(
            title={
            'text': f"{selected_date}當日訪客註冊數統計",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="時間",
        yaxis_title="註冊（訪客）數",
        width=1000,
        height=400
        )
        start_date = selected_date
        end_date = selected_date
        csv_24hour = csv_download(df_24hours)
    else:
        range_num = col_userdate_2.slider(label="選擇日期範圍",max_value=10,min_value =1,step=1,value=7) 
        table_scans,start_date,end_date,df_user_filter = get_user_data(df_user_converter,today,user_freq_choice,range_num)
        fig_scan = go.Figure()
        fig_scan.add_trace(
            go.Bar(
                x=table_scans.index,
                y=table_scans['用戶數'],
                text=table_scans['用戶數'],
                ))
    
        fig_scan.update_layout(xaxis={'type': 'category'})
        fig_scan.update_layout(
            title={
            'text': f"從{start_date}到{end_date}訪客用戶註冊數",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="日期",
        yaxis_title="訪客註冊數",
        width=1000,
        height=400
        )
        
        
        
    #fronted
    st.markdown("<h5 style='text-align: left; padding: 10px;'>用戶(訪客)註冊數據</h5>", unsafe_allow_html=True)
    
    if user_freq_choice == '小時':
        st.plotly_chart(fig_24hour)
        
        st.download_button(
         label = "下載用戶註冊圖表數據csv檔",
         data = csv_24hour,
         file_name='點擊排行榜.csv',
         mime='text/csv',
         )
    
    else:
        st.plotly_chart(fig_scan)
    
    
    #%% 展示資料-點擊排行榜、raw data  ============================================================================= ##
    #backed
    df_raw = get_rawdata(df_scan_coor_scene_city,lig_ids,start_date,end_date)
    
    #fronted
    #col_click , col_raw = st.columns(2)
    
    with st.expander("場景掃描raw data"):
        st.markdown("<h5 style='text-align: left; padding: 10px;'>Raw Data</h5>", unsafe_allow_html=True)
        st.table(
            data = df_user_filter
            )
    
    
#%% Web App 測試 (檢視成果)  ============================================================================= ##    
if __name__ == "__main__":
    main()
    
