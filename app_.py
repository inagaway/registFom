import streamlit as st
import pandas as pd
import requests
import urllib.parse
import datetime
import streamlit as st
import const_category
import util

ORDER_PATTERNS = {
    "パターンA": ["概要", "料金", "サービス提供地域", "営業時間", "定休日"],
    "パターンB": ["概要", "サービス提供地域", "料金", "営業時間", "定休日"],
}

# --- 4. 初期化処理 (UI表示前に必須) ---
st.set_page_config(page_title="事業所入力")
# util.initialize_session()

# セッションステートに必要なキーをすべて登録
initial_keys = {
    "data_list": [],
    "off_pref": "",
    "off_city": "",
    "off_town": "",
    "corp_pref": "",
    "corp_city": "",
    "corp_town": "",
    "ui_city_code": "",
    "ui_town_code": "",
}
for k, v in initial_keys.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 4. 初期化処理 (UI表示前に必須) ---
if "category_counters" not in st.session_state:
    # 全ての小カテゴリに対して 0 で初期化
    counters = {}
    for main in const_category.CATEGORY_STRUCTURE:
        for mid in const_category.CATEGORY_STRUCTURE[main]:
            for sub in const_category.CATEGORY_STRUCTURE[main][mid]:
                counters[sub] = 0
    st.session_state.category_counters = counters

# --- リスト表示・削除用の初期化 ---
# if "delete_targets" not in st.session_state:
#     st.session_state.delete_targets = set()


# --- 4. UI設定 ---
st.set_page_config(page_title="事業所入力", layout="centered")
st.title("事業所情報入力フォーム")

# セッション状態の初期化（一箇所にまとめます）
if "data_list" not in st.session_state:
    st.session_state.data_list = []

# 事業所用
if "addr_input" not in st.session_state:
    st.session_state.addr_input = {
        "pref": "",
        "city": "",
        "town": "",
        "city_code": "",
        "town_code": "",
    }

# 法人用
if "corp_input" not in st.session_state:
    st.session_state.corp_input = {"pref": "", "city": "", "town": ""}

if "data_list" not in st.session_state:
    st.session_state.data_list = []
if "addr_input" not in st.session_state:
    st.session_state.addr_input = {"city": "", "town": ""}

# --- 5. カテゴリ選択エリア ---
st.subheader("【1】カテゴリ選択")
col_cat1, col_cat2, col_cat3 = st.columns(3)

with col_cat1:
    main_cat = st.selectbox(
        "大カテゴリ", list(const_category.CATEGORY_STRUCTURE.keys())
    )

with col_cat2:
    mid_options = list(const_category.CATEGORY_STRUCTURE[main_cat].keys())
    mid_cat = st.selectbox("中カテゴリ", mid_options)

with col_cat3:
    sub_options = const_category.CATEGORY_STRUCTURE[main_cat][mid_cat]
    sub_cat = st.selectbox("小カテゴリ", sub_options)

st.info(f"選択中: {main_cat} ＞ {mid_cat} ＞ {sub_cat}")

# --- 6. 基本情報（共通項目） ---
st.divider()
st.subheader("【2】基本情報（共通）")
with st.container(border=True):

    status = st.selectbox("ステータス", ["新規", "更新", "休止", "廃止", "非表示"])
    name = st.text_input("名称")
    if sub_cat in ["サロン・通いの場", "趣味・交流の場"]:
        publish_poss = st.selectbox("事業所住所掲載可否", ["可", "不可"])

    if sub_cat in ["移動販売"]:
        st.write("営業エリア(市区町村)※〇〇市〇〇区〇〇町まで")
        s_cities = st.multiselect("対象市区町村", list(util.KANAGAWA_MASTER.keys()))
        areas = []
        sales_area = {}
        for ct in s_cities:
            t_opts = util.KANAGAWA_MASTER.get(ct, [])
            s_towns = st.multiselect(
                f"📍 {ct} の町名", t_opts, default=t_opts, key=f"t_{ct}"
            )
            areas.extend([f"{ct}{t}" for t in s_towns])
            sales_area["サービス提供地域"] = " / ".join(areas)
    else:
        zip_office = st.text_input("事業所郵便番号", key="ui_zip_off")
        if st.button("事業所住所を検索"):
            util.update_address_by_zip(zip_office, prefix="off")
            st.rerun()

        c1, c2, c3 = st.columns(3)
        off_pref = c1.text_input("都道府県", key="off_pref")
        off_city = c2.text_input("市区町村", key="off_city")
        off_town = c3.text_input("町名", key="off_town")

        off_banchi = st.text_input("番地", key="off_banchi")
        off_build = st.text_input("建物名", key="off_build")

        # 市区町村と町名が選択されたら、コードを自動表示
        match = util.CODE_MAP.get(
            (off_city, off_town), {"city_code": "", "town_code": ""}
        )
        st.session_state["ui_city_code"] = match["city_code"]
        st.session_state["ui_town_code"] = match["town_code"]
        current_codes = util.CODE_MAP.get(
            (off_city, off_town), {"city_code": "", "town_code": ""}
        )

        col_code1, col_code2 = st.columns(2)
        city_code = col_code1.text_input(
            "市区町村コード", value=current_codes["city_code"], disabled=True
        )
        town_code = col_code2.text_input(
            "町域コード", value=current_codes["town_code"], disabled=True
        )

    hp = st.text_input("ホームページ")
    tel = st.text_input("電話番号")
    fax = st.text_input("Fax番号")
    mail = st.text_input("問合せメールアドレス")
    contact_dept = st.text_input("問合せ部署名")
    contact_tel = st.text_input("問合せ連絡先")
    remarks = st.text_area("備考")
    min_date = datetime.date(1900, 1, 1)
    max_date = datetime.date(2100, 12, 31)
    accept_date = st.date_input("受理日", min_value=min_date, max_value=max_date)
# --- 7. 小カテゴリに応じた動的入力項目 ---
st.divider()
specific_data = {}
with st.container(border=True):
    st.subheader("【3】法人情報")
    cop_name = st.text_input("法人名/屋号")
    zip_corp = st.text_input("法人郵便番号", key="ui_zip_corp")
    if st.button("法人住所を検索"):
        util.update_address_by_zip(zip_corp, prefix="corp")
        st.rerun()

    c4, c5, c6 = st.columns(3)
    corp_pref = c4.text_input("都道府県", key="corp_pref")
    corp_city = c5.text_input("市区町村", key="corp_city")
    corp_town = c6.text_input("町名", key="corp_town")

    corp_banchi = st.text_input("番地", key="corp_banchi")
    corp_build = st.text_input("建物名", key="corp_build")

    corp_tel = st.text_input("法人電話番号")

if sub_cat in [
    "サロン・通いの場",
    "趣味・交流の場",
    "市民団体",
    "自治体",
    "フレイル予防教室",
    "介護予防教室",
]:
    st.subheader(f"📋 {sub_cat} 専用項目")
    sc1, sc2 = st.columns(2)
    with sc1:
        held_place = st.text_input("開催場所")
        held_date = st.text_input("開催日時")
    with sc2:
        over_view = st.text_area("概要")

elif sub_cat in [
    "家事支援",
    "遺品整理",
    "剪定草むしり",
    "高齢者向け配食サービス",
    "フードデリバリー",
    "食料品・日用品配達",
    "外出支援",
    "見守り・安否確認",
    "スポーツジム・フィットネスクラブ",
]:
    st.subheader(f"📋 {sub_cat} 専用項目")
    over_view = st.text_area("概要")
    price = st.text_area("料金")
    sales_time = st.text_area("営業時間")
    holiday = st.text_area("定休日")
    st.write("サービス提供地域")
    s_cities = st.multiselect("対象市区町村", list(util.KANAGAWA_MASTER.keys()))
    areas = []
    for ct in s_cities:
        t_opts = util.KANAGAWA_MASTER.get(ct, [])
        s_towns = st.multiselect(
            f"📍 {ct} の町名", t_opts, default=t_opts, key=f"t_{ct}"
        )
        areas.extend([f"{ct}{t}" for t in s_towns])
    specific_data["サービス提供地域"] = " , ".join(areas)

elif sub_cat in ["住宅改修"]:
    sales_time = st.text_area("営業時間")
    holiday = st.text_area("定休日")
    regiornot = st.selectbox("介護保険登録事業者の有無", ("あり", "なし"))

elif sub_cat in ["コミュニティバス"]:
    over_view = st.text_area("概要")
    price = st.text_area("料金")
    st.write("サービス提供地域")
    s_cities = st.multiselect("対象市区町村", list(util.KANAGAWA_MASTER.keys()))
    areas = []
    for ct in s_cities:
        t_opts = util.KANAGAWA_MASTER.get(ct, [])
        s_towns = st.multiselect(
            f"📍 {ct} の町名", t_opts, default=t_opts, key=f"t_{ct}"
        )
        areas.extend([f"{ct}{t}" for t in s_towns])
    specific_data["サービス提供地域"] = " , ".join(areas)

elif sub_cat in ["移動販売"]:
    over_view = st.text_area("概要")
    price = st.text_area("料金")
    open_place = st.text_input("出店場所 ※出店所在地を入力してください")

elif sub_cat in ["福祉タクシー"]:
    sales_time = st.text_area("営業時間")
    holiday = st.text_area("定休日")
    st.write("営業エリア")
    s_cities = st.multiselect("対象市区町村", list(util.KANAGAWA_MASTER.keys()))
    areas = []
    sales_area = {}
    for ct in s_cities:
        t_opts = util.KANAGAWA_MASTER.get(ct, [])
        s_towns = st.multiselect(
            f"📍 {ct} の町名", t_opts, default=t_opts, key=f"t_{ct}"
        )
        areas.extend([f"{ct}{t}" for t in s_towns])
    sales_area["営業エリア"] = " , ".join(areas)
    riding_capacity = st.text_area("乗車定員")
    retention = st.text_area("保有台数")
    passenger_capacity = st.text_area("乗客定員")
    func = st.text_area("機能")
    price_plan_distance = st.selectbox("料金体系(距離制運賃)", ["", "〇"])
    price_plan_time = st.selectbox("料金体系(時間制運賃)", ["", "〇"])
    price_plan_distime = st.selectbox("料金体系(時間距離併用)", ["", "〇"])
    price_plan_other = st.selectbox("料金体系(その他)", ["", "〇"])
    price_transfer_distance = st.text_input("(距離制運賃)送迎運賃")
    price_first_distance = st.text_input("(距離制運賃)初乗運賃")
    price_addition_distance = st.text_input("(距離制運賃)加算運賃")
    price_transfer_time = st.text_input("(時間制運賃)送迎運賃")
    price_first_time = st.text_input("(時間制運賃)初乗運賃")
    price_addition_time = st.text_input("(時間制運賃)加算運賃")
    discount = st.text_area("割引き")
    other_common = st.text_area("(共通)その他")
    basic_price = st.text_area("(介助料金)基本介助料")
    other_common_assistance = st.text_area("(介助料金)その他")
    arrange = st.selectbox("当日手配", ["なし", "あり"])
    wheelchair = st.selectbox("車いすの貸出", ["なし", "あり"])
    stretcher = st.selectbox("ストレッチャーの貸出", ["なし", "あり"])
    employee_training = st.selectbox("定期的な従業員の研修", ["なし", "あり"])
    original_brochure = st.selectbox("独自のパンフレット", ["なし", "あり"])

elif sub_cat in ["住宅型有料老人ホーム", "サービス付き高齢者向け住宅"]:
    sales_time = st.text_area("営業時間")
    holiday = st.text_area("定休日")
    access = st.text_area("アクセス")
    availability = st.selectbox("空き情報", ["あり", "なし"])
    requestment = st.text_input("入居時の要件")
    requestment_plus = st.text_input("入居時の要件(補足)")
    use_need_price = st.text_input("(利用料金)入居時必要額")
    use_month_price = st.text_input("(利用料金)月額")


elif sub_cat == "ボランティアポイント制度受入れ施設":
    st.subheader(f"📋 {sub_cat} 専用項目")
    detail = st.text_area("活動内容")
    ivent = st.text_area("イベント等")
    feature = st.text_area("施設の特徴")


# --- 8. 登録・CSV出力 ---
st.divider()
if st.button("➕ この内容でリストに追加", type="primary"):
    if name == "":
        st.error("名称を入力してください")
    else:
        # 現在のカウントを取得
        st.session_state.category_counters[sub_cat] += 1
        current_number = st.session_state.category_counters[sub_cat]

        # 連番を含めたIDの作成
        unique_id = f"{current_number:03d}"

        # 緯度経度取得
        if sub_cat not in ["移動販売"]:
            if (off_city == "") or (off_town == ""):
                lat, lon = None, None
            else:
                lat, lon = util.get_lat_lon(
                    f"神奈川県{off_city}{off_town}{off_banchi}{off_build}"
                )
            # データの統合
            new_entry = {
                "小カテゴリ": sub_cat,
                "ステータス": status,
                "名称": name,
                "郵便番号": zip_office,
                "都道府県": off_pref,
                "市区町村": off_city,
                "町名": off_town,
                "番地": off_banchi,
                "建物名": off_build,
                "市区町村コード": city_code,
                "町域コード": town_code,
                "連番": unique_id,
                "電話番号": tel,
                "FAX番号": fax,
                "ホームページ": hp,
                "問い合わせメールアドレス": mail,
                "緯度": lat,
                "経度": lon,
                "備考": remarks,
                "問合せ先部署名": contact_dept,
                "問合せ先連絡先": contact_tel,
                "受理日": accept_date,
            }
            if sub_cat in ["サロン・通いの場", "趣味・交流の場"]:
                new_entry.update(
                    {
                        "事業所住所掲載可否": publish_poss,
                        "概要": over_view,
                        "開催場所": held_place,
                        "開催日時": held_date,
                    }
                )

            if sub_cat in [
                "家事支援",
                "遺品整理",
                "剪定草むしり",
                "高齢者向け配食サービス",
                "フードデリバリー",
                "食料品・日用品配達",
                "外出支援",
                "見守り・安否確認",
                "スポーツジム・フィットネスクラブ",
            ]:
                new_entry.update(
                    {
                        "法人名/屋号": cop_name,
                        "法人郵便番号": zip_corp,
                        "法人都道府県": corp_pref,
                        "法人市区町村名": corp_city,
                        "法人番地": corp_banchi,
                        "法人建物名": corp_build,
                        "法人電話番号": corp_tel,
                        "概要": over_view,
                        "料金": price,
                        "営業時間": sales_time,
                        "定休日": holiday,
                    }
                )
                new_entry.update(specific_data)
            elif sub_cat in ["住宅改修"]:
                new_entry.update(
                    {
                        "法人名/屋号": cop_name,
                        "法人郵便番号": zip_corp,
                        "法人都道府県": corp_pref,
                        "法人市区町村名": corp_city,
                        "法人番地": corp_banchi,
                        "法人建物名": corp_build,
                        "法人電話番号": corp_tel,
                        "営業時間": sales_time,
                        "定休日": holiday,
                        "介護保険登録事業者の有無": regiornot,
                    }
                )
            elif sub_cat in ["コミュニティバス"]:
                new_entry.update({"概要": over_view, "料金": price})
                new_entry.update(specific_data)
            elif sub_cat in ["福祉タクシー"]:
                new_entry.update(
                    {
                        "法人名/屋号": cop_name,
                        "法人郵便番号": zip_corp,
                        "法人都道府県": corp_pref,
                        "法人市区町村名": corp_city,
                        "法人番地": corp_banchi,
                        "法人建物名": corp_build,
                        "法人電話番号": corp_tel,
                        "営業時間": sales_time,
                        "定休日": holiday,
                        "乗車定員": riding_capacity,
                        "保有台数": retention,
                        "乗客定員": passenger_capacity,
                        "機能": func,
                        "料金体系(距離制運賃)": price_plan_distance,
                        "料金体系(時間制運賃)": price_plan_time,
                        "料金体系(時間距離併用)": price_plan_distime,
                        "料金体系(その他)": price_plan_other,
                        "(距離制運賃)送迎運賃": price_transfer_distance,
                        "(距離制運賃)初乗運賃": price_first_distance,
                        "(距離制運賃)加算運賃": price_addition_distance,
                        "(時間制運賃)送迎運賃": price_transfer_time,
                        "(時間制運賃)初乗運賃": price_first_time,
                        "(時間制運賃)加算運賃": price_addition_time,
                        "(共通)割引き": discount,
                        "(共通)その他": other_common,
                        "(介助料金)基本介助料": basic_price,
                        "(介助料金)その他": other_common_assistance,
                        "当日手配": arrange,
                        "車いすの貸出": wheelchair,
                        "ストレッチャーの貸出": stretcher,
                        "定期な従業員の研修": employee_training,
                        "独自のパンフレット": original_brochure,
                    }
                )
                new_entry.update(sales_area)
            elif sub_cat in ["有料老人ホーム"]:
                new_entry.update(
                    {
                        "法人名/屋号": cop_name,
                        "法人郵便番号": zip_corp,
                        "法人都道府県": corp_pref,
                        "法人市区町村名": corp_city,
                        "法人番地": corp_banchi,
                        "法人建物名": corp_build,
                        "法人電話番号": corp_tel,
                        "営業時間": sales_time,
                        "定休日": holiday,
                        "アクセス": access,
                        "空き情報": availability,
                        "入居時の要件": requestment,
                        "入居時の要件(補足)": requestment_plus,
                        "(利用料金)入居時必要額": use_need_price,
                        "(利用料金)月額": use_month_price,
                    }
                )
        else:
            # データの統合
            new_entry = {
                "小カテゴリ": sub_cat,
                "ステータス": status,
                "名称": name,
                "営業エリア": sales_area,
                "出店場所": open_place,
                "電話番号": tel,
                "FAX番号": fax,
                "ホームページ": hp,
                "問い合わせメールアドレス": mail,
                "備考": remarks,
                "問合せ先市町村部署名": contact_dept,
                "問合せ先市町村連絡先": contact_tel,
                "受理日": accept_date,
            }
        st.session_state.data_list.append(new_entry)
        st.success("リストに追加しました。")

    if st.session_state.data_list:
        df = pd.DataFrame(st.session_state.data_list)
        # final_cols = util.get_column_order(sub_cat, df.columns)
        # df_display = df[final_cols]

        # --- ヘッダー（列）を動的に整理するロジック ---
        # 1. マスター
        master_order_front = [
            "小カテゴリ",
            "ステータス",
            "名称",
            "事業所住所掲載可否",
            "郵便番号",
            "都道府県",
            "市区町村",
            "町名",
            "番地",
            "建物名",
            "市区町村コード",
            "町域コード",
            "連番",
            "電話番号",
            "FAX番号",
            "ホームページ",
            "問い合わせメールアドレス",
            "法人名/屋号",
            "法人郵便番号",
            "法人都道府県",
            "法人市区町村名",
            "法人番地",
            "法人建物名",
            "法人電話番号",
            "出店場所",
            "介護保険登録事業者の有無",
            "アクセス",
            "空き情報",
            "(入居時の要件・状況)入居時の要件",
            "(入居時の要件・状況)入居時の要件(補足)",
            "(利用料金)入居時必要額",
            "(利用料金)月額",
            "営業エリア",
            "乗車定員",
            "保有台数",
            "乗客定員",
            "機能",
            "料金体系(距離制運賃)",
            "料金体系(時間制運賃)",
            "料金体系(時間距離併用)",
            "料金体系(その他)",
            "(距離制運賃)送迎運賃",
            "(距離制運賃)初乗運賃",
            "(距離制運賃)加算運賃",
            "(時間制運賃)送迎運賃",
            "(時間制運賃)初乗運賃",
            "(時間制運賃)加算運賃",
            "(共通)割引き",
            "(共通)その他",
            "(介助料金)基本介助料",
            "(介助料金)その他",
            "当日手配",
            "車いすの貸出",
            "ストレッチャーの貸出",
            "定期な従業員の研修",
            "独自のパンフレット",
            "開催場所",
            "開催日時",
        ]

        master_order_end = [
            "緯度",
            "経度",
            "備考",
            "問合せ先部署名",
            "問合せ先連絡先",
            "受理日",
        ]

        specific_part = (
            ORDER_PATTERNS["パターンA"]
            if sub_cat
            in [
                "家事支援",
                "遺品整理",
                "剪定草むしり",
                "フードデリバリー",
                "食料品・日用品配達",
                "コミュニティバス",
            ]
            else ORDER_PATTERNS["パターンB"]
        )
        if sub_cat in [
            "福祉タクシー",
            "有料老人ホーム",
            "サービス付き高齢者向け住宅",
            "住宅改修",
        ]:
            master_order = master_order_front + master_order_end
        else:
            master_order = master_order_front + specific_part + master_order_end

        # 2. 現在のDataFrameに存在する列だけを、マスターの順序で抽出
        dynamic_cols = [c for c in master_order if c in df.columns]

        # 3. もしマスターにない新しいキーがあれば最後に追加
        remaining_cols = [c for c in df.columns if c not in master_order]
        final_cols = dynamic_cols + remaining_cols

        # 列の並び替え実行（存在しない列は作成されない）
        df_display = df[final_cols]
        st.subheader("📋 登録済みリスト")
        st.dataframe(df_display)

    # --- 削除処理の追加 ---
        st.write("---")
        st.subheader("🗑️ データの削除操作")
        
        with st.form("delete_form"):
            st.write("削除したい項目にチェックを入れてください（複数選択可）")
            
            check_results = []
            for i, entry in enumerate(st.session_state.data_list):
                # チェックボックスを生成
                label = f"No.{entry.get('連番')} : [{entry.get('小カテゴリ')}] {entry.get('名称')}"
                is_checked = st.checkbox(label, key=f"del_cb_{i}")
                check_results.append((i, is_checked))
                
            submit_delete = st.form_submit_button("選択した項目を一括削除する", type="primary")

            if submit_delete:
                indices_to_delete = [idx for idx, checked in check_results if checked]
                
                if not indices_to_delete:
                    st.warning("削除するデータが選択されていません。")
                else:
                    # 削除（逆順にpop）
                    for idx in sorted(indices_to_delete, reverse=True):
                        st.session_state.data_list.pop(idx)
                    
                    # util内の関数で連番振り直し
                    util.reassign_serial_numbers()
                    
                    st.success(f"{len(indices_to_delete)} 件のデータを削除しました。")
                    st.rerun()
    # with st.form("delete_form"):

    #     # 削除対象を選択するためのセレクトボックス
    #     # 名称と小カテゴリを表示して選びやすくします
    #     delete_options = [
    #         f"{i}: [{d.get('小カテゴリ')}] {d.get('名称')}"
    #         for i, d in enumerate(st.session_state.data_list)
    #     ]
    #     target_idx_str = st.selectbox(
    #         "削除するデータを選択してください", delete_options
    #     )
    #     submit_delete = st.form_submit_button("選択したデータを削除する", type="primary")
    #     if submit_delete:
    #     # if st.button("選択したデータを削除する"):
    #         target_idx = int(target_idx_str.split(":")[0])
    #         st.session_state.data_list.pop(target_idx)
    #         util.reassign_serial_numbers()
    #         # データの削除
    #         removed_item = df.drop()
    #         removed_sub_cat = removed_item.get("小カテゴリ")

    #         # --- 連番の振り直しロジック ---
    #         # 同じ小カテゴリのデータだけを抽出して番号を付け直す
    #         # category_countersも更新する
    #         temp_counters = {
    #             sub: 0 for sub in st.session_state.category_counters.keys()
    #         }

    #         for entry in st.session_state.data_list:
    #             s_cat = entry.get("小カテゴリ")
    #             if s_cat in temp_counters:
    #                 temp_counters[s_cat] += 1
    #                 # 3桁の連番を更新
    #                 entry["連番"] = f"{temp_counters[s_cat]:03d}"

    #         # セッション状態のカウンターも現在の最大値に同期させる
    #         st.session_state.category_counters = temp_counters

    #         st.warning(
    #             f"「{removed_item.get('名称')}」を削除し、連番を振り直しました。"
    #         )
    #         st.rerun()

    # ダウンロード用
    csv = df_display.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "📥 CSVダウンロード",
        data=csv,
        file_name="facility_list.csv",
        mime="text/csv",
    )

    # リストをリセットするボタン（運用上あると便利です）
    # if st.button("全リストをクリア"):
    #     st.session_state.data_list = []
    #     st.rerun()
