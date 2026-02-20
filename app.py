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
st.set_page_config(page_title="事業所情報入力", layout="centered")
st.title("csvアップロード編集フォーム")

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

if "df" not in st.session_state:
    st.session_state.df = None
if "category_counters" not in st.session_state:
    st.session_state.category_counters = {}
if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False
if "search_result" not in st.session_state:
    st.session_state.search_result = {
        "pref": "",
        "city": "",
        "town": "",
        "banchi": "",
        "build": "",
        "city_code": "",
        "town_code": "",
        "lat": "",
        "lon": "",
    }

# st.title("csvアップロード編集フォーム")

# --- (A) CSVアップロード ---
st.header("1. CSVデータ編集")
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

# 初回アップロード時の処理
if uploaded_file is not None and st.session_state.df is None:
    # 1. まず文字列として読み込む（型崩れを防ぐため）
    temp_df = pd.read_csv(uploaded_file, dtype=object)

    if "連番" in temp_df.columns:
        # 全角を半角に直したい場合はここで処理（任意）
        # temp_df["連番"] = temp_df["連番"].str.translate(str.maketrans('０１２３４５６７８９', '0123456789'))

        # 2. 数値に変換できるものだけ変換して最大値を取得（変換できないものはNaNになる）
        numeric_series = pd.to_numeric(temp_df["連番"], errors="coerce")

        # 3. 既存の値を活かしつつ、空（NaN）の部分だけ "000" で埋める
        # これにより、全角文字が入っていてもそのまま保持されます
        temp_df["連番"] = temp_df["連番"].fillna("000")

    st.session_state.df = temp_df
    st.rerun()


# 編集エリア
if st.session_state.df is not None:
    # 常に最新の session_state.df をエディタに渡す
    # keyを変更せずに運用するため、編集結果を直接受け取る
    st.subheader("編集エディタ")
    st.info("特定の列はプルダウンから選択できます。")

    # 1. プルダウンの選択肢を定義
    status_options = ["新規", "更新", "休止", "廃止", "非表示"]
    possibility_options = ["可", "非"]

    # 2. st.data_editor の設定
    edited_df = st.data_editor(
        st.session_state.df,
        # use_container_width=True,
        key="main_editor",
        # ここで列ごとに設定を行います
        column_config={
            "ステータス": st.column_config.SelectboxColumn(
                "ステータス",
                help="現在の状態を選択してください",
                options=status_options,
                required=True,
            ),
            "事業所住所掲載可否": st.column_config.SelectboxColumn(
                "事業所住所掲載可否",
                help="住所の掲載可否を選択してください",
                options=possibility_options,
                required=True,
            ),
        },
        num_rows="dynamic",  # 行の追加・削除を許可する場合
    )
    col_c1, col_c2 = st.columns(2)

    if col_c1.button("編集内容を確定して連番を振る"):
        new_df = edited_df.copy()

        if "連番" in new_df.columns:
            # 1. 数値として解釈できるものから最大値を取得
            numeric_values = pd.to_numeric(new_df["連番"], errors="coerce").dropna()
            max_num = int(numeric_values.max()) if not numeric_values.empty else 0

            # 2. 各行の値をチェック
            for i in range(len(new_df)):
                # 判定用に値を加工（文字列化 + 前後の空白削除）
                raw_val = str(new_df.iloc[i]["連番"]).strip()

                # 【重要】採番を実行する条件を広げる
                # 以下のいずれかに当てはまれば「未入力」とみなして連番を振る
                if raw_val in ["", "nan", "NaN", "None", "0", "000"]:
                    max_num += 1
                    # 3桁ゼロ埋めで上書き
                    new_df.iloc[i, new_df.columns.get_loc("連番")] = f"{max_num:03d}"
                else:
                    # 全角文字や、既に 001 以外の具体的な番号がある場合はそのまま
                    pass

            st.session_state.df = new_df
            st.success(f"処理が完了しました（現在の最大連番: {max_num}）")
            st.rerun()

        # ダウンロードは常に session_state.df (確定済みの最新データ) を参照する
    csv_out = st.session_state.df.to_csv(index=False).encode("utf_8_sig")
    col_c2.download_button(
        "💾 編集済みCSVを保存", csv_out, "updated_data.csv", "text/csv"
    )
st.divider()

# --- (B) 住所・コード検索 ---
st.header("2. 住所・コード検索 (コピー用)")

# 1. 郵便番号入力
zip_query = st.text_input(
    "郵便番号を入力", placeholder="例: 2310021", key="zip_search_input"
)

# 2. 検索実行（ここで値を更新する）
if st.button("事業所の住所を検索", key="btn_zip_search"):
    if zip_query:
        # util側で addr = get_addr(zip_query) などを実行する想定
        res = util.get_addr_from_zip(zip_query)
        if res:
            # ウィジェットの key と同じ session_state を「表示前」に更新
            st.session_state.res_upp_pref = res.get("pref", "")
            st.session_state.res_upp_city = res.get("city", "")
            st.session_state.res_upp_town = res.get("town", "")

            # コード類も更新
            match = util.CODE_MAP.get(
                (res["city"], res["town"]), {"city_code": "", "town_code": ""}
            )
            st.session_state.tab2_search_city_code = match.get("city_code", "")
            st.session_state.tab2_search_town_code = match.get("town_code", "")

            # 成功したら rerun して、下のウィジェットに反映させる
            st.rerun()

# 3. 入力エリア（ここが「表示」のタイミング）
t1, t2, t3 = st.columns(3)

# keyを指定するだけで、session_state の値が自動的に value として表示されます
upp_pref = t1.text_input("都道府県", key="res_upp_pref")
upp_city = t2.text_input("市区町村", key="res_upp_city")
upp_town = t3.text_input("町名", key="res_upp_town")

upp_banchi = st.text_input("番地", key="upp_banchi")
upp_build = st.text_input("建物名", key="upp_build")

col_t1, col_t2 = st.columns(2)
# コード類も key を指定
city_code_2 = col_t1.text_input(
    "市区町村コード", disabled=True, key="tab2_search_city_code"
)
town_code_2 = col_t2.text_input(
    "町域コード", disabled=True, key="tab2_search_town_code"
)

# 4. 反映ボタン
if st.button("👉 コピーテキスト欄に反映", key="btn_apply_copy"):
    full_address = f"{upp_pref}{upp_city}{upp_town}{upp_banchi}{upp_build}"
    new_lat, new_lon = util.get_lat_lon(full_address)

    st.session_state.search_result["lat"] = new_lat
    st.session_state.search_result["lon"] = new_lon
    st.session_state.search_result["banchi"] = upp_banchi
    st.session_state.search_result["build"] = upp_build
    st.session_state.show_copy_area = True
    st.rerun()

# 5. 分割されたコピー用エリア
if st.session_state.get("show_copy_area", False):
    st.success("各項目右のアイコンでコピーして、貼り付けてください。")

    col_copy1, col_copy2, col_copy3 = st.columns(3)

    with col_copy1:
        st.markdown("#####  住所")
        # 都道府県 / 市区町村 / 町名 / 番地 / 建物名
        addr_text = f"{upp_pref}\t{upp_city}\t{upp_town}\t{upp_banchi}\t{upp_build}"
        st.code(addr_text, language=None)
        st.caption("都道府県～建物名 (タブ区切り)")

    with col_copy2:
        st.markdown("##### コード")
        # 市区町村コード / 町域コード
        code_text = f"{city_code_2}\t{town_code_2}"
        st.code(code_text, language=None)
        st.caption("市区町村・町域コード (タブ区切り)")

    with col_copy3:
        st.markdown("##### 座標")
        # 緯度 / 経度
        lat_val = st.session_state.search_result["lat"]
        lon_val = st.session_state.search_result["lon"]
        geo_text = f"{lat_val}\t{lon_val}"
        st.code(geo_text, language=None)
        st.caption("緯度・経度 (タブ区切り)")

    if st.button("閉じる"):
        st.session_state.show_copy_area = False
        st.rerun()

st.divider()


# --- (C) サービス提供地域コピー セクションの修正 ---
st.header("3. サービス提供地域等検索 (コピー用)")

if util.KANAGAWA_MASTER:
    # 1. まずは「市区町村」だけを選択（ここが親カテゴリになる）
    selected_cities = st.multiselect(
        "① 対象の市区町村を選択してください",
        list(util.KANAGAWA_MASTER.keys()),
        key="city_selector_improved",
    )

    # 選択された市区町村がある場合のみ、町名選択を表示
    if selected_cities:
        area_names = []

        st.write("② 各市区町村の町名を選択してください（デフォルトは全選択）")

        # 市区町村ごとにカード形式（expander）でまとめると画面がスッキリします
        for ct in selected_cities:
            with st.expander(f"📍 {ct} の町名設定", expanded=True):
                t_opts = util.KANAGAWA_MASTER.get(ct, [])

                # その市区町村に属する町名だけを表示
                s_towns = st.multiselect(
                    f"{ct} 内の町名を選択",
                    t_opts,
                    default=t_opts,
                    key=f"town_select_{ct}",
                )

                # 選択された町名をリストに追加
                for t in s_towns:
                    area_names.append(f"{ct}{t}")

        # --- 結果表示 ---
        if area_names:
            st.divider()
            st.subheader("📋 生成された地域リスト(コピー用)")
            display_text = "、".join(area_names)

            # プレビュー
            st.write(f"現在の選択件数: **{len(area_names)}** 件")
            st.code(display_text, language=None)
    else:
        st.info("市区町村を選択すると、詳細な町名の選択肢が表示されます。")
