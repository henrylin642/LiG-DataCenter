import io
import streamlit as st
import pandas as pd
from pandas import Timestamp, Timedelta
import requests
from datetime import datetime, timedelta, date
import plotly.io as pio
import os
import pytz


pio.renderers.default = "browser"

Now = datetime.today()
taipei_timezone = pytz.timezone("Asia/Taipei")
datetime_taipei = datetime.now(taipei_timezone)
today = datetime_taipei.date()

data_root = os.getenv("DATA_ROOT", "data")
api_host = os.getenv("API_HOST", "http://localhost:3000")
function_import_error = None

df_file = pd.read_csv(f"{data_root}/file.csv", encoding="utf-8-sig", dtype=str)
df_field = pd.read_csv(f"{data_root}/coor_city.csv", encoding="utf-8-sig", dtype=str)
df_field_id = pd.read_csv(f"{data_root}/field.csv", encoding="utf-8-sig", dtype=str)

scan_data_from = os.getenv("SCAN_DATA_FROM", "from_file")
click_data_from = os.getenv("CLICK_DATA_FROM", "from_file")

def upload(df, selected_db, usecols, url=None):
    if selected_db not in df["db"].values:
        st.error(f"{selected_db} 沒有資料")
        return pd.DataFrame()

    filename = None
    if url:
        filename = url
    else:
        filename = f"{data_root}/" + df[df["db"] == selected_db]["filename"].values[0]

    print(f"load {filename}..")
    df_origin = pd.read_csv(filename, encoding="utf-8-sig", usecols=usecols, dtype=str)
    print(f"load {filename}..done")
    return df_origin


def df_scan_from_api(debug=None):
    """
    replace `df_scan`

    call api 取代 從檔案讀取
    """
    token = os.getenv("LIG_SA", None)
    st.write(scan_data_from,click_data_from,data_root,api_host, token)
    if (token := os.getenv("LIG_SA", None)) is None:
        st.toast("沒有適當的權限，請聯絡管理員", icon="🚨")
        return pd.DataFrame()

    url = None
    if debug:
        print(datetime.now(), "load local scan data")
        url = "http://localhost:3000/logs/scan_records"
    else:
        print(datetime.now(), "load scan data from api")
        url = f"{api_host}/logs/scan_records"
    res = requests.get(url, headers={"Authorization": "Bearer " + token})
    if res.ok:
        return pd.read_json(io.StringIO(res.text), dtype=str)
    else:
        raise RuntimeError(f"API Error: {res.status_code}")


def df_click_lig_from_api(debug=None):
    """
    replace `df_click_lig`

    call api 取代 從檔案讀取
    """
    if (token := os.getenv("LIG_SA", None)) is None:
        st.toast("沒有適當的權限，請聯絡管理員", icon="🚨")
        return pd.DataFrame()

    url = None
    if debug:
        print(datetime.now(), "load local click data")
        url = "http://localhost:3000/logs/obj_click_logs.csv?scope=all"
    else:
        print(datetime.now(), "load click data from api")
        url = f"{api_host}/logs/obj_click_logs.csv?scope=all"
    res = requests.get(url, headers={"Authorization": "Bearer " + token})
    if res.ok:
        return pd.read_csv(io.StringIO(res.text), dtype=str)
    else:
        raise RuntimeError(f"API Error: {res.status_code}")


def scan_data_frame(option: str = "from_api") -> pd.DataFrame:

    if option == "from_api":
        return df_scan_from_api()
    elif option == "from_file":
        return upload(
            df_file,
            "scan_statistic",
            [
                "time",
                "ligtag_id",
                "client_id",
                "coordinate_system_id",
            ],
        )
    else:
        raise ValueError("invalid option")


def click_data_frame(option: str = "from_api"):
    if option == "from_api":
        return df_click_lig_from_api()
    elif option == "from_file":
        return upload(
            df_file,
            "obj_click_log",
            [
                "time",
                "code_name",
                "obj_id",
            ],
        )
    else:
        raise ValueError("invalid option")


last_scan_time = None
down_sacn_data_date = None


df_scan = scan_data_frame(scan_data_from)
# df_scan = scan_data_frame(scan_data_from)
# print("df_scan", df_scan)
# LOGGER.debug(f"df_scan: {df_scan}")
# os.write(1, f"df_scan: {df_scan}\n".encode())
# if len(df_scan) == 0:
#     function_import_error = "scan data is empty"


def normalize_scan(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "time": "scantime",
            "ligtag_id": "lig_id",
        }
    )
    if "scantime" not in df.columns:
        print("沒有時間欄位(scantime)")

    else:
        df["scantime"] = pd.to_datetime(
            df["scantime"],
            format="ISO8601",
            errors="coerce",
        )
    return df


df_scan = normalize_scan(df_scan)

if len(df_scan) > 0:
    last_scan_time = df_scan["scantime"].max()
    down_sacn_data_time = last_scan_time - Timedelta(days=1)
    down_sacn_data_date = down_sacn_data_time.date()


df_light = upload(
    df_file,
    "light",
    [
        "Id",
        "Updated at",
        "Latitude",
        "Longitude",
        "Group",
        "Id [Coordinate systems]",
        "Name [Coordinate systems]",
        "Created at [Coordinate systems]",
        "Updated at [Coordinate systems]",
    ],
).rename(
    columns={
        "Id": "lig_id",
        "Updated at": "light_uploadtime",
        "Latitude": "lig_latitude",
        "Longitude": "lig_longitude",
        "Group": "field_id",
        "Id [Coordinate systems]": "coor_id",
        "Name [Coordinate systems]": "coor_name",
        "Created at [Coordinate systems]": "coor_createtime",
        "Updated at [Coordinate systems]": "coor_updatetime",
    }
)





if len(df_light) == 0:
    st.warning("skipped light")
else:
    df_light["light_uploadtime"] = pd.to_datetime(
        df_light["light_uploadtime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    df_light["coor_createtime"] = pd.to_datetime(
        df_light["coor_createtime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    df_light["coor_updatetime"] = pd.to_datetime(
        df_light["coor_updatetime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    last_light_time = df_light["light_uploadtime"].max()
    down_light_data_time = last_light_time - Timedelta(days=1)
    down_light_data_date = down_light_data_time.date()


df_coor = upload(
    df_file,
    "coordinate_system",
    [
        "Id",
        "Name",
        "Created at",
        "Updated at",
        "Id [Scenes]",
        "Name [Scenes]",
        "Created at [Scenes]",
        "Updated at [Scenes]",
    ],
).rename(
    columns={
        "Id": "coor_id",
        "Name": "coor_name",
        "Created at": "coor_createtime",
        "Updated at": "coor_updatetime",
        "Id [Scenes]": "scene_id",
        "Name [Scenes]": "scene_name",
        "Created at [Scenes]": "scene_createtime",
        "Updated at [Scenes]": "scene_updatetime",
    }
)

if len(df_coor) == 0:
    st.warning("skipped coordinate_system")
else:
    df_coor["coor_createtime"] = pd.to_datetime(
        df_coor["coor_createtime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    df_coor["coor_updatetime"] = pd.to_datetime(
        df_coor["coor_updatetime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    df_coor["scene_createtime"] = pd.to_datetime(
        df_coor["scene_createtime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    df_coor["scene_updatetime"] = pd.to_datetime(
        df_coor["scene_updatetime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    last_coor_time = df_coor["coor_updatetime"].max()


df_arobjs = upload(
    df_file,
    "ar_object",
    [
        "Id",
        "Name",
        "Created at",
        "Id [Scene]",
        "Name [Scene]",
    ],
).rename(
    columns={
        "Id": "obj_id",
        "Name": "obj_name",
        "Created at": "obj_createtime",
        "Id [Scene]": "scene_id",
        "Name [Scene]": "scene_name",
    }
)

if len(df_arobjs) == 0:
    st.warning("skipped ar_object")
else:
    df_arobjs["obj_scene_name"] = df_arobjs["scene_name"] + "-" + df_arobjs["obj_name"]
    df_arobjs["obj_createtime"] = pd.to_datetime(
        df_arobjs["obj_createtime"],
        # TODO: can change if data from api
        infer_datetime_format=True,
        errors="coerce",
    )
    last_obj_time = df_arobjs["obj_createtime"].max()


# df_click_lig = click_data_from().rename(
#     columns={
#         "時間(time)": "clicktime",
#         "使用者(code_name)": "codename",
#         "物件id(obj_id)": "obj_id",
#     }
# )

df_click_lig = click_data_frame(click_data_from)


def normalize_click_lig(df: pd.DataFrame) -> pd.DataFrame:
    # incoming columns: clicktime, codename, obj_id
    df = df.rename(
        columns={
            "time": "clicktime",
            "code_name": "codename",
        }
    )

    os.write(1, f"df: {df}\n".encode())
    if "clicktime" not in df.columns:
        print("沒有時間欄位(clicktime)")

    else:
        df["clicktime"] = pd.to_datetime(
            df["clicktime"],
            format="ISO8601",
            errors="coerce",
        )

        os.write(1, f"codenames: {df['codename']}\n".encode())

        # last_click_time = df_click_lig["clicktime"].max()
        df["pj_code"] = df["codename"].astype(str).str[:2]
        df["user_id"] = df["codename"].astype(str).str[2:]
    return df


df_click_lig = normalize_click_lig(df_click_lig)
last_click_time = None
if len(df_click_lig) > 0:
    last_click_time = df_click_lig["clicktime"].max()
else:
    st.warning("skipped obj_click_log")
# if len(df_click_lig) == 0:
#     st.warning("skipped obj_click_log")
# else:
#     df_click_lig["clicktime"] = pd.to_datetime(
#         df_click_lig["clicktime"],
#         format="ISO8601",
#         errors="coerce",
#     )
#     last_click_time = df_click_lig["clicktime"].max()
#     df_click_lig["pj_code"] = df_click_lig["codename"].astype(str).str[:2]
#     df_click_lig["user_id"] = df_click_lig["codename"].astype(str).str[2:]


def click_data_update_time():
    """
    replace `last_click_time`

    call api 取代 從檔案讀取
    """
    return last_click_time


df_pj_code = upload(df_file, "pj", ["pj_id", "pj_name", "pj_code"])
if len(df_pj_code) == 0:
    st.warning("skipped pj")
elif len(df_click_lig) > 0:
    df_click_lig = df_click_lig.merge(df_pj_code, on="pj_code")

df_scene = upload(
    df_file,
    "scene",
    [
        "Id",
        "Name",
        "Created at",
        "Updated at",
    ],
    # url=f"data/mock/scene_2024-06-03_00h10m12.csv",
).rename(
    columns={
        "Id": "scene_id",
        "Name": "scene_name",
        "Created at": "scene_createtime",
        "Updated at": "scene_updatetime",
    }
)

if len(df_scene) == 0:
    st.warning("skipped scene")
else:
    df_scene["scene_createtime"] = pd.to_datetime(
        df_scene["scene_createtime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    df_scene["scene_updatetime"] = pd.to_datetime(
        df_scene["scene_updatetime"], format="%Y年%m月%d日 %H:%M", errors="coerce"
    )
    last_scene_time = df_scene["scene_updatetime"].max()


df_deploy = upload(
    df_file,
    "deployment",
    [
        "Id",
        "Id [Coordinate system]",
        "Id [Scene]",
    ],
).rename(
    columns={
        "Id": "deploy_id",
        "Id [Coordinate system]": "coor_id",
        "Id [Scene]": "scene_id",
    }
)


def get_coor_list(df):  # df_scan_coor_scene_city
    data = df.dropna(subset=["coor_name"])
    coors_list = data["coor_name"].unique().tolist()
    coors_list.sort()
    coors_df = pd.DataFrame(coors_list, columns=["coor"])
    return coors_list


def get_ids(df, field):  # df_scan_coor_scene_city
    lig_ids = df[df["field"] == field]["lig_id"].unique()
    return lig_ids


def get_scenes(df, field):  # scenes_list = get_scenes(filtered_date_df,'大稻埕')
    coor_scenes = df[df["field_name"] == field][["lig_id", "coor_name", "scene_name"]]
    unique_coor_scenes = coor_scenes.drop_duplicates(
        subset=["lig_id"], keep="first"
    )  # 去除重复的 lig_id，保留第一个出现的
    unique_coor_scenes = unique_coor_scenes.reset_index(drop=True)
    return unique_coor_scenes


def get_rawdata(df, lig_ids, start_date, end_date):  # df_scan_coor_scene_city
    con1 = df["scantime"].dt.date >= start_date
    con2 = df["scantime"].dt.date <= end_date
    con3 = df["lig_id"].isin(lig_ids)
    df_raw = df[con1 & con2 & con3]
    df_raw = df_raw[["scantime", "lig_id", "coor_name"]]
    df_raw = df_raw.set_index("scantime").sort_index(ascending=False)
    return df_raw


def csv_download(df):
    csv_download = df.to_csv().encode("utf-8-sig")
    return csv_download


def date_filter(df, colname, start_date, end_date):
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    con1 = df[colname].dt.date >= start_date.date()
    con2 = df[colname].dt.date <= end_date.date()
    filtered_df = df[con1 & con2]
    return filtered_df


# %% 測試
if __name__ == "__main__":
    print("測試")
