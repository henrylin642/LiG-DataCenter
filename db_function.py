
#%% # 情境介紹前處理(1)-匯入套件與資料
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date
import plotly.io as pio
pio.renderers.default = 'browser'
import os
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'data/ga_api.json'

#%% 定義function區


#%% 設定日期範圍
def get_date_data():
    today = date.today()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    this_week_end = this_week_start + timedelta(days=6)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = last_week_start + timedelta(days=6)
    this_month_start = date(today.year, today.month, 1)
    this_month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = date(last_month_end.year, last_month_end.month, 1)
    return today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end

#%% (I) 情境介紹與前處理 - 資料前處理:

# 原資料整理

def get_data(datetime_point):
    date = datetime_point
    url = f"https://codec.tw.ligmarker.com/console/api/decodelog/raw/{date.year}/{date.month}/{date.day}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()  # assuming the response is in json format
        if data:  # check if data is not empty
            df = pd.DataFrame(data, columns=['Timestamp', 'lig_id', 'Tenant ID', 'SDK Instance ID', 'Decoder ID'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            return df
        else:
            return pd.DataFrame()  # return empty DataFrame if no data

def update_data(file_path):
    file_isexisted = os.path.exists(file_path)
    if file_isexisted:
        st.write(file_isexisted)
        try:
            existing_df = pd.read_csv(file_path, parse_dates=['Timestamp'])
        except pd.errors.EmptyDataError:
            st.write('file is not exsited')
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()

    current_date = datetime.now().date()  #2023/7/3
    datetime_point_day = existing_df['Timestamp'].max().date() # 2023/6/30
    # updating_df = existing_df  # 定義 `updating_df` 變量，初始值為 `existing_df`
    
    while datetime_point_day < current_date + timedelta(days=1):   
        df_updated = get_data(datetime_point_day) #get_data(2023/6/30)
         
        if not df_updated.empty:
            datetime_point_df = existing_df[existing_df['Timestamp'].dt.date == datetime_point_day]
            if len(datetime_point_df) != len(df_updated):
                existing_df = existing_df[existing_df['Timestamp'].dt.date < datetime_point_day]
                updating_df = pd.concat([existing_df, df_updated])
                st.write(f"Data downloaded on {datetime_point_day}")
                updating_df.to_csv(file_path, index=False)
                existing_df = updating_df
            else:
                st.write(f"existing_df lens {len(datetime_point_df)}")
                st.write(f"df_updated lens {len(df_updated)}")
                st.write(f"No new data on {datetime_point_day}")
        else:
            st.write(f"No data available on {datetime_point_day}")
        
        datetime_point_day += timedelta(days=1)
    
    return existing_df
        

def userdata_arrange(df):
    a = "<span class=\"translation_missing\" title=\"translation missing: zh-TW.admin.export.csv.default_col_sep\">Default Col Sep</span>"
    rows= []
    column_mapping = {old_column: 'col1' for old_column in df.columns}
    df = df.rename(columns=column_mapping)
    for row in df['col1']:
        row_update = row.replace(a,",")
        row_update = row_update.replace('"','')
        data_list = row_update.split(',')
        rows.append(data_list)
        
    new_df = pd.DataFrame(rows)
    new_df.columns = ['id', 'Email', 'Key', 'Secret', 'Fb_uid', 'Fb_token', 'Apple_uid', 'Apple_token', 'Reset_password', 'Remember_created_at', 'Created_at', 'Updated_at', 'Is_verified', 'Verify_code', 'Verify_time', 'Name', 'Birthday', 'Profile_picture', 'Is_visitor', 'Google_uid', 'Line_uid', 'App_code_number', 'Ref_uid', 'Role']

    # 将 'Created_at' 列转换为日期时间格式
    new_df['Created_at'] = pd.to_datetime(new_df['Created_at'], format='%Y年%m月%d日 %H:%M')

    # 将日期时间格式转换为一般的时间字符串格式
    new_df['Created_at'] = new_df['Created_at'].dt.strftime('%Y-%m-%d %H:%M')

    # 将 'Created_at' 列转换为日期时间格式
    new_df['Updated_at'] = pd.to_datetime(new_df['Updated_at'], format='%Y年%m月%d日 %H:%M')

    # 将日期时间格式转换为一般的时间字符串格式
    new_df['Updated_at'] = new_df['Updated_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    date_string = date.today().strftime('%m%d')
    new_filename = "data/userdata" +"_" + date_string + '.csv'
    new_df.to_csv(new_filename, index=False)
    
    return new_df
    
    
def upload(df,selected_db,uploaded_file):
    filename =  "data/" + df[df['db'] == selected_db]['filename'].values[0]
    if uploaded_file is not None:
        df_upload = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        newfilename = uploaded_file.name
        df.loc[df['db'] == selected_db, 'filename'] = newfilename
        df.to_csv('data/df_file.csv', encoding='utf-8-sig', index = False )
        st.sidebar.success("uploaded succeed")
        return df_upload
    else:
        df_origin = pd.read_csv(filename, encoding="utf-8-sig")
        return df_origin
        
def get_scan_data(df_light,df_coor,df_arobjs):
    # 匯入掃描數據 Timestamp,lig_id,Tenant ID,SDK Instance ID,Decoder ID
    df_scan = pd.read_csv("data/scandata.csv",encoding="utf=8-sig",usecols=['Timestamp','lig_id'])
    df_scan = df_scan.rename(columns={'Timestamp':'scantime'})
    # 剔除不合理數據
    df_scan = df_scan[df_scan['lig_id'] >=100]
    df_scan = df_scan[df_scan['lig_id'] <=10000]
    df_scan['scantime'] = pd.to_datetime(df_scan['scantime'])
    df_scan_lastestday = df_scan['scantime'].max()

    # 匯入light_id數據 Id,Name,Name [Coordinate systems]
    #df_light = pd.read_csv("data/light_2023-06-26_11h36m20.csv",encoding="utf=8-sig",usecols=['Id','Name [Coordinate systems]'])
    df_light = df_light.rename(columns={'Id':'lig_id','Name [Coordinate systems]':'coor_name'})
    df_light = df_light.dropna(subset=['coor_name'])
    df_scan_coor = df_scan.merge(df_light, how = 'left' , on = 'lig_id')

    # 匯入坐標系數據 Id, Name, Created at,  Name[Scenes], Created at[Scenes]
    #df_coor = pd.read_csv("data/coordinate_system_2023-07-06_23h22m11.csv",encoding="utf=8-sig",usecols=['Id','Name','Created at','Name [Scenes]'])
    df_coor = df_coor.rename(columns={'Id':'coor_id','Name':'coor_name','Created at':'coor_createdtime','Name [Scenes]':'scene_name'})
    df_coor['coor_createdtime'] = pd.to_datetime(df_coor['coor_createdtime'], format='%Y年%m月%d日 %H:%M')
    df_coor_lastestday = df_coor['coor_createdtime'].max()
    df_scan_coor_scene = df_scan_coor.merge(df_coor, how = 'left' , on = 'coor_name')

    # 匯入坐標系城市數據
    df_coor_city = pd.read_csv("data/coor_city.csv",encoding="utf=8-sig")
    df_scan_coor_scene_city = df_scan_coor_scene.merge(df_coor_city, how = 'left' , on = 'coor_name')
    df_scan_coor_scene_city = df_scan_coor_scene_city.dropna(subset=['coor_name'])
    df_scan_coor_scene_city.to_csv('data/掃描data.csv', encoding='utf-8-sig', index = False )
    df_arobjs = df_arobjs.rename(columns={"Id":"obj_id","Name":"obj_name","Name [Scene]":"obj_scene"})
    return df_scan_coor_scene_city,df_coor_city,df_coor,df_arobjs

def get_reg_user_data(df_user):
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()
    df_user = df_user.rename(columns={'id':'usr_id','Created_at':'usr_install_time','Updated_at':'usr_update_time'})
    df_user['usr_install_time'] = pd.to_datetime(df_user['usr_install_time'])
    df_user['usr_update_time'] = pd.to_datetime(df_user['usr_update_time'])
    # 設定時間為index
    df_user = df_user.set_index('usr_install_time')
    
    con1 = df_user.index.date == today
    df_user_today = df_user[con1]
    count_user_today = len(df_user_today)

    con2 = df_user.index.date == yesterday
    df_user_yesterday = df_user[con2]
    count_user_yesterday = len(df_user_yesterday)

    conw_1 = df_user.index.date >= last_week_start
    conw_2 = df_user.index.date <= last_week_end
    df_user_lastweek = df_user[conw_1&conw_2]
    count_user_lastweek = len(df_user_lastweek)

    conw_3 = df_user.index.date >= this_week_start
    conw_4 = df_user.index.date <= today
    df_user_thisweek = df_user[conw_3&conw_4]
    count_user_thisweek = len(df_user_thisweek)

    conm_1 = df_user.index.date >= last_month_start
    conm_2 = df_user.index.date <= last_month_end
    df_user_thismonth = df_user[conm_1 & conm_2]
    count_user_thismonth = len(df_user_thismonth)

    conm_3 = df_user.index.date >= this_month_start
    conm_4 = df_user.index.date <= this_month_end
    df_user_lastmonth = df_user[conm_3 & conm_4]
    count_user_lastmonth= len(df_user_lastmonth)
    
    return count_user_today,count_user_yesterday,count_user_thisweek,count_user_lastweek,count_user_thismonth,count_user_lastmonth

def get_coor_list(df): #df_scan_coor_scene_city     
    data = df.dropna(subset=['coor_name'])
    coors_list = data['coor_name'].unique().tolist()
    coors_list.sort()
    coors_df = pd.DataFrame(coors_list,columns=['coor'])   
    return coors_list

def get_ids(df,coors): #df_scan_coor_scene_city
    lig_ids = df[df['coor_name'].isin(coors)]['lig_id'].unique()
    return lig_ids

def get_scenes(df,select_coors): #df_coor
    scenes_list = []
    for i in range(len(select_coors)):
        scenes_list.extend(df[df['coor_name'].isin(select_coors)]['scene_name'].iloc[i].split(","))
    scenes_string = ' '.join(scenes_list)
    return scenes_list

def get_rawdata(df,lig_ids,start_date,end_date): #df_scan_coor_scene_city
    con1 = df['scantime'].dt.date >= start_date
    con2 = df['scantime'].dt.date <= end_date
    con3 = df['lig_id'].isin(lig_ids)
    df_raw = df[con1 & con2 & con3]
    df_raw = df_raw[['scantime','lig_id','coor_name']]
    df_raw = df_raw.set_index('scantime').sort_index(ascending=False)
    return df_raw

def get_cities_data(df,df_coor_city):  ##df_scan_coor_scene_city
    today,yesterday,this_week_start,this_week_end,last_week_start,last_week_end,this_month_start,this_month_end,last_month_start,last_month_end = get_date_data()
    # 建立表格
    df_city_scans = {'city': [], '今日': [], '昨日': [], '本週': [], '上週': [], '本月': [], '上月': []}
    df_coor_cty_filter = df_coor_city.dropna(subset=['city'])
    cities = df_coor_cty_filter['city'].unique().tolist()

    # 統計每個城市的掃描量
    for city in cities:
        con1 = (df['scantime'].dt.date == today) & (df['city'] == city)
        con2 = (df['scantime'].dt.date == yesterday) & (df['city'] == city)
        con3 = (df['scantime'].dt.date >= this_week_start) & (df['scantime'].dt.date <= this_week_end) & (df['city'] == city)
        con4 = (df['scantime'].dt.date >= last_week_start) & (df['scantime'].dt.date <= last_week_end) & (df['city'] == city)
        con5 = (df['scantime'].dt.date >= this_month_start) & (df['scantime'].dt.date <= this_month_end) & (df['city'] == city)
        con6 = (df['scantime'].dt.date >= last_month_start) & (df['scantime'].dt.date <= last_month_end) & (df['city'] == city)

        scans_today = df[con1].shape[0]
        scans_yesterday = df[con2].shape[0]
        scans_this_week = df[con3].shape[0]
        scans_last_week = df[con4].shape[0]
        scans_this_month = df[con5].shape[0]
        scans_last_month = df[con6].shape[0]

        df_city_scans['city'].append(city)
        df_city_scans['今日'].append(scans_today)
        df_city_scans['昨日'].append(scans_yesterday)
        df_city_scans['本週'].append(scans_this_week)
        df_city_scans['上週'].append(scans_last_week)
        df_city_scans['本月'].append(scans_this_month)
        df_city_scans['上月'].append(scans_last_month)
    # 建立統計表格
    table_city_scans = pd.DataFrame(df_city_scans)
    table_city_scans.set_index('city', inplace=True)
    #table_city_scans.loc['總和'] = table_city_scans.sum()
    return table_city_scans

def get_daily_data(df,day1,day2,coors):
    
    dates_range = pd.date_range(start=day1, end=day2, freq='D')

    #建立表格
    df_daily_scans = {'Date':[]} 
    for coor in coors:
        df_daily_scans[coor]=[]
        
    count_days=0
    #填入數據
    for i in range(len(dates_range)):
        day = dates_range[i].date()
        df_daily_scans['Date'].append(day)
        con1= df['scantime'].dt.date==day
        df_daily_filter = df[con1]
        df_daily_filter = df_daily_filter.groupby('coor_name').size()
        for coor in coors:
            count = df_daily_filter.get(coor,0)
            df_daily_scans[coor].append(count)
            count_days += count

    table_daily_scans = pd.DataFrame(df_daily_scans)

    # 剔除 column 全為 0 的數據
    #table_daily_scans_dropzero = table_daily_scans.loc[:, (table_daily_scans != 0).any(axis=0)]
    table_daily_scans['Date'] = pd.to_datetime(table_daily_scans['Date'])
    table_daily_scans['Date'] = table_daily_scans['Date'].dt.strftime('%-m/%-d')

    # 設定時間為index
    table_daily_scans = table_daily_scans.set_index('Date')
    

    # 新增總和列
    table_daily_scans.loc['總和'] = table_daily_scans.sum()
    
    table_daily_scans = table_daily_scans.sort_values(by='總和', axis=1, ascending=False)
    
    
    table_daily_scans_T = table_daily_scans.transpose()
    # 以總和值排序列
    #table_daily_scans_dropzero = table_daily_scans_dropzero.sort_values(by='總和', axis=1, ascending=False)
    return table_daily_scans_T

def get_weekly_date(df,day1,weeknum,coors):  #df_scan_coor_scene_city,2
    # 每週掃描量
    weekly_dates = pd.date_range(end=day1, freq='W-MON',periods=weeknum)
    new_idx = pd.DatetimeIndex([day1]).union(weekly_dates)
    #建立表格
    df_weekly_scans = {'WeekStart':[]} 
    for coor in coors:
        df_weekly_scans[coor]=[]

    count_weeks= 0
    #填入數據
    for i in range(len(new_idx)-1):
        start_week = new_idx[i]
        end_week = new_idx[i+1]
        df_weekly_scans['WeekStart'].append(weekly_dates[i])
        con1 = df['scantime'] >= start_week
        con2 = df['scantime'] < end_week
        df_weekly_filter = df[con1 & con2]
        df_weekly_filter = df_weekly_filter.groupby('coor_name').size()
        for coor in coors:
            count = df_weekly_filter.get(coor,0)
            df_weekly_scans[coor].append(count)
            count_weeks += count
                
    table_weekly_scan = pd.DataFrame(df_weekly_scans)
    # 剔除 column 全為 0 的數據
    #table_weekly_scan_dropzero = table_weekly_scan.loc[:, (table_weekly_scan != 0).any(axis=0)]
    table_weekly_scan['WeekStart'] = pd.to_datetime(table_weekly_scan['WeekStart'])
    table_weekly_scan['WeekStart'] = table_weekly_scan['WeekStart'].dt.strftime('%-m/%-d')


    table_weekly_scan = table_weekly_scan.set_index('WeekStart')
    # 新增總和列
    table_weekly_scan.loc['總和'] = table_weekly_scan.sum()
    table_weekly_scan = table_weekly_scan.sort_values(by='總和', axis=1, ascending=False)
    #table_weekly_scan = table_weekly_scan.sort_values(by='總和', axis=1, ascending=False)


    table_weekly_scan_T = table_weekly_scan.transpose()


    return table_weekly_scan_T

def get_monthly_date(df,day1,monthnum,coors): #df_scan_coor_scene_city
    # 每月掃描量
    monthly_dates = pd.date_range(end=day1, periods = monthnum, freq='MS') 
    #建立表格
    df_monthly_scans = {'MonthStart':[]} 
    for coor in coors:
        df_monthly_scans[coor]=[]

    count_months = 0
    #填入數據
    for i in range(monthnum):
        day = monthly_dates[i]
        df_monthly_scans['MonthStart'].append(day.replace(day=1))
        con1 = df['scantime'].dt.year == day.year
        con2 = df['scantime'].dt.month == day.month
        df_monthly_filter = df[con1 & con2]
        df_monthly_filter = df_monthly_filter.groupby('coor_name').size()
        for coor in coors:
            count = df_monthly_filter.get(coor,0)
            df_monthly_scans[coor].append(count)
            count_months += count
                
    table_monthly_scan = pd.DataFrame(df_monthly_scans)

    # 剔除 column 全為 0 的數據
    table_monthly_scan_dropzero = table_monthly_scan.loc[:, (table_monthly_scan != 0).any(axis=0)]
    # 設定 hour 為索引
    table_monthly_scan_dropzero['MonthStart'] = table_monthly_scan_dropzero['MonthStart'].dt.strftime('%-m/%-d')
    table_monthly_scan_dropzero = table_monthly_scan_dropzero.set_index('MonthStart')
    # 新增總和列
    table_monthly_scan_dropzero.loc['總和'] = table_monthly_scan_dropzero.sum()    
    # 以總和值排序列
    table_monthly_scan_dropzero = table_monthly_scan_dropzero.sort_values(by='總和', axis=1, ascending=False)

    table_monthly_scan_dropzero_T = table_monthly_scan_dropzero.transpose()
    
    return table_monthly_scan_dropzero_T

def get_coor_scan_data(df,select_coors,day1,freq_choice,range_num): #df_scan_coor_scene_city
    if freq_choice == "日":
        date_range = pd.date_range(end=day1, freq="D", periods=range_num)
        new_idx = pd.DatetimeIndex([day1]).union(date_range)      
        #建立表格
        df_scans = {'Date':[]} 
        for coor in select_coors:
            df_scans[coor]=[]
            
        count_days=0
        #填入數據
        for i in range(len(new_idx)):
            day0 = new_idx[i].date()
            df_scans['Date'].append(day0)
            con1= df['scantime'].dt.date==day0
            df_filter = df[con1]
            df_filter = df_filter.groupby('coor_name').size()
            for coor in select_coors:
                count = df_filter.get(coor,0)
                df_scans[coor].append(count)
                count_days += count

        start_date = new_idx[0].date()
        end_date = day1
        table_scans = pd.DataFrame(df_scans)
        table_scans = table_scans.set_index('Date')
        return table_scans,start_date,end_date

    elif freq_choice =="週":
        date_range = pd.date_range(end=day1, freq="W-MON", periods=range_num)
        new_idx = pd.DatetimeIndex([day1]).union(date_range)
        #建立表格
        df_scans = {'Date':[]} 
        for coor in select_coors:
            df_scans[coor]=[]
            
        count_days=0
        #填入數據
        for i in range(len(new_idx)-1):
            start = new_idx[i].date()
            end = new_idx[i+1].date()
            df_scans['Date'].append(start)
            con1= df['scantime'].dt.date>start
            con2= df['scantime'].dt.date<=end
            df_filter = df[con1 & con2]
            df_filter = df_filter.groupby('coor_name').size()
            for coor in select_coors:
                count = df_filter.get(coor,0)
                df_scans[coor].append(count)
                count_days += count
        start_date = new_idx[0].date()
        end_date = day1
        table_scans = pd.DataFrame(df_scans)
        table_scans = table_scans.set_index('Date')
        return table_scans,start_date,end_date
        
    elif freq_choice == "月":
        date_range = pd.date_range(end=day1, freq="MS", periods=range_num)
        new_idx = pd.DatetimeIndex([day1]).union(date_range)
        #建立表格
        df_scans = {'Date':[]} 
        for coor in select_coors:
            df_scans[coor]=[]
            
        count_days=0
        #填入數據
        for i in range(len(new_idx)):
            start = new_idx[i].date()
            df_scans['Date'].append(start)
            con1 = df['scantime'].apply(lambda x: x.strftime('%Y-%m')) == start.strftime('%Y-%m')
            df_filter = df[con1]
            df_filter = df_filter.groupby('coor_name').size()
            for coor in select_coors:
                count = df_filter.get(coor,0)
                df_scans[coor].append(count)
                count_days += count

        start_date = new_idx[0].date()
        end_date = end_date
        table_scans = pd.DataFrame(df_scans)
        table_scans = table_scans.set_index('Date')
        return table_scans,start_date,end_date

def get_GA_data(df_arobjs,start_date,end_date,scenes):
    date_range = {
    'start_date': start_date.strftime('%Y-%m-%d'),
    'end_date': end_date.strftime('%Y-%m-%d')   
    }
    
    def vlookup(key, df, column, return_column):
        try:
            return df.loc[df[column] == key, return_column].iloc[0]
        except IndexError:
            return None

    client = BetaAnalyticsDataClient()
    property_id='270740329'

    request = RunReportRequest(property=f"properties/{property_id}")
    request.date_ranges.append(date_range)
    request.dimensions.append({'name': 'customEvent:ID'})
    request.metrics.append({'name': 'eventCount'})

    response = client.run_report(request)

    obj_id_lst =[]
    obj_name_lst=[]
    obj_scene_lst=[]
    click_count_lst = []

    for row in response.rows:
        obj_id = row.dimension_values[0].value
        click_count = row.metric_values[0].value
        if obj_id and obj_id.isdigit():
            obj_id = int(obj_id)
            obj_name = vlookup(obj_id, df_arobjs, "obj_id", "obj_name")
            obj_scene = vlookup(obj_id, df_arobjs, "obj_id", "obj_scene")
            obj_id_lst.append(obj_id)
            click_count_lst.append(click_count)
            obj_name_lst.append(obj_name)
            obj_scene_lst.append(obj_scene)


    df_obj_click_scene = pd.DataFrame({'物件ID': obj_id_lst,'物件名稱': obj_name_lst,'點擊量': click_count_lst,'物件場景': obj_scene_lst})
    df_obj_click_scene = df_obj_click_scene.dropna(subset=['物件名稱'])
    df_obj_click_scene = df_obj_click_scene[df_obj_click_scene['物件場景'].isin(scenes)]
    return df_obj_click_scene
        
#%% 測試
if __name__ == "__main__":
    print('測試')