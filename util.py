import streamlit as st
import pandas as pd
import requests
import urllib.parse
import streamlit as st
import const_category


# --- 2. 外部データの読み込み ---
@st.cache_data
def load_kanagawa_master():
    try:
        df_master = pd.read_csv("kanagawa_towns.csv", encoding="utf-8-sig")
        master_dict = df_master.groupby("市区町村名")["町名"].apply(list).to_dict()
        code_map = {}
        for _, row in df_master.iterrows():
            code_map[(row["市区町村名"], row["町名"])] = {
                "city_code": str(row["市区町村コード"]),
                "town_code": str(row["町域コード"]),
            }
        return master_dict, code_map
    except Exception as e:
        st.error(f"マスターCSVの読み込みに失敗しました: {e}")
        return {}, {}


KANAGAWA_MASTER, CODE_MAP = load_kanagawa_master()


# --- 3. 外部API連携 ---
def get_addr_from_zip(zip_code):
    if not zip_code:
        return None
    res = requests.get(f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zip_code}")
    if res.status_code == 200:
        data = res.json()
        if data["results"]:
            r = data["results"][0]
            return {"pref": r["address1"], "city": r["address2"], "town": r["address3"]}
    return None


def update_address_by_zip(zip_code, prefix="off"):
    """
    prefixによって事業所(off)か法人(corp)を判別し、session_stateのkeyを直接書き換える
    """
    res = get_addr_from_zip(zip_code)
    if res:
        # 直接 key を更新することで text_input に反映させる
        st.session_state[f"{prefix}_pref"] = res["pref"]
        st.session_state[f"{prefix}_city"] = res["city"]
        st.session_state[f"{prefix}_town"] = res["town"]

        # 事業所の場合のみコード検索を実施
        if prefix == "off":
            match = CODE_MAP.get(
                (res["city"], res["town"]), {"city_code": "", "town_code": ""}
            )
            st.session_state["ui_city_code"] = match["city_code"]
            st.session_state["ui_town_code"] = match["town_code"]
    else:
        st.error("住所が見つかりませんでした。")


def get_lat_lon(address):
    if not address:
        return None, None
    s_quote = urllib.parse.quote(address)
    url = f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={s_quote}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0:
                lon, lat = data[0]["geometry"]["coordinates"]
                return lat, lon
    except:
        pass
    return None, None

def reassign_serial_numbers():
    """削除後の連番振り直しロジック"""
    temp_counters = {sub: 0 for sub in st.session_state.category_counters.keys()}
    for entry in st.session_state.data_list:
        s_cat = entry.get("小カテゴリ")
        if s_cat in temp_counters:
            temp_counters[s_cat] += 1
            entry["連番"] = f"{temp_counters[s_cat]:03d}"
    st.session_state.category_counters = temp_counters


# def get_column_order(sub_cat, df_columns):
#     """表示・出力用の列順序を計算"""
#     pattern = (
#         "パターンB"
#         if sub_cat
#         in [
#             "家事支援",
#             "遺品整理",
#             "剪定草むしり",
#             "フードデリバリー",
#             "食料品・日用品配達",
#             "コミュニティバス",
#         ]
#         else "パターンA"
#     )

#     specific_part = const_category.ORDER_PATTERNS[pattern]

#     if sub_cat in [
#         "福祉タクシー",
#         "有料老人ホーム",
#         "サービス付き高齢者向け住宅",
#         "住宅改修",
#     ]:
#         master_order = (
#             const_category.MASTER_ORDER_FRONT + const_category.MASTER_ORDER_END
#         )
#     else:
#         master_order = (
#             const_category.MASTER_ORDER_FRONT
#             + specific_part
#             + const_category.MASTER_ORDER_END
#         )

#     dynamic_cols = [c for c in master_order if c in df_columns]
#     remaining_cols = [c for c in df_columns if c not in master_order]
#     return dynamic_cols + remaining_cols
