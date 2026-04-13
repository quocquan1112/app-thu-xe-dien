import os
import math
import json
import time
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def fetch_data():
    conn = get_connection()
    try:
        df_config = conn.read(worksheet="Config", ttl=0).dropna(how="all")
        conf_scalars = dict(zip(df_config["Key"], df_config["Value"]))
        config = {
            "play_area_name": conf_scalars.get("play_area_name", "Khu Vui Chơi AntiGravity"),
            "price_per_minute": int(float(conf_scalars.get("price_per_minute", 1000))),
            "display_mode": conf_scalars.get("display_mode", "📱 Điện thoại"),
            "mobile_columns": int(float(conf_scalars.get("mobile_columns", 3))),
            "desktop_columns": int(float(conf_scalars.get("desktop_columns", 5))),
            "categories_detail": [],
            "cars": []
        }
    except Exception as e:
        st.error(f"Lỗi đọc Config Cloud: {e}")
        st.stop()
        
    try:
        df_categories = conn.read(worksheet="Categories", ttl=0).dropna(how="all")
        config["categories_detail"] = df_categories.to_dict(orient="records")
    except:
        pass

    try:
        df_cars = conn.read(worksheet="Cars", ttl=0).dropna(how="all")
        df_cars["id"] = df_cars["id"].astype(str).str.zfill(2)
        config["cars"] = df_cars.to_dict(orient="records")
    except:
        pass
        
    try:
        df_active = conn.read(worksheet="Active_Sessions", ttl=0).dropna(how="all")
        active = {}
        for r in df_active.to_dict(orient="records"):
            car_id = str(r["car_id"]).zfill(2)
            row_dict = dict(r)
            del row_dict["car_id"]
            if pd.isna(row_dict.get("merged_into")): row_dict["merged_into"] = None
            if pd.isna(row_dict.get("merged_cost")): row_dict["merged_cost"] = 0
            if pd.isna(row_dict.get("prepaid_amount")): row_dict["prepaid_amount"] = 0
            active[car_id] = row_dict
    except:
        active = {}
        
    try:
        df_history = conn.read(worksheet="History", ttl=0).dropna(how="all")
        hist = df_history.to_dict(orient="records")
    except:
        hist = []
        
    return config, active, hist

if "initialized" not in st.session_state:
    with st.spinner("Đang kết nối & tải dữ liệu từ Google Sheets Cloud..."):
        config, active, hist = fetch_data()
        st.session_state["config"] = config
        st.session_state["active_sessions"] = active
        st.session_state["history"] = hist
        st.session_state["initialized"] = True

def update_config():
    conn = get_connection()
    c = st.session_state["config"]
    s = {"play_area_name": c["play_area_name"], "price_per_minute": c["price_per_minute"], 
         "display_mode": c["display_mode"], "mobile_columns": c["mobile_columns"], "desktop_columns": c["desktop_columns"]}
    df_config = pd.DataFrame(list(s.items()), columns=["Key", "Value"])
    conn.update(worksheet="Config", data=df_config)
    
    if "categories_detail" in c:
        df_cat = pd.DataFrame(c["categories_detail"])
        conn.update(worksheet="Categories", data=df_cat)
        
    if "cars" in c:
        df_cars = pd.DataFrame(c["cars"])
        conn.update(worksheet="Cars", data=df_cars)

def update_active_sessions():
    conn = get_connection()
    act = st.session_state["active_sessions"]
    if act:
        rows = []
        for k, v in act.items():
            r = {"car_id": k}
            r.update(v)
            rows.append(r)
        df_act = pd.DataFrame(rows)
    else:
        df_act = pd.DataFrame(columns=["car_id", "start_time", "type", "billing_type", "prepaid_amount", "max_minutes", "merged_into", "merged_cost", "status"])
    conn.update(worksheet="Active_Sessions", data=df_act)

def update_history():
    conn = get_connection()
    hist = st.session_state["history"]
    if hist:
        df_hist = pd.DataFrame(hist)
    else:
        df_hist = pd.DataFrame(columns=["id", "car_id", "car_name", "start_time", "end_time", "total_minutes", "total_paid", "type", "note"])
    conn.update(worksheet="History", data=df_hist)

st.set_page_config(page_title="Quản Lý Thuê Xe Điện", layout="wide" if st.session_state["config"].get("display_mode", "📱 Điện thoại") == "💻 Máy tính" else "centered")

st.markdown("""
<style>
    div[data-testid="stButton"] > button {
        height: 120px !important;
        width: 100% !important;
        white-space: pre-wrap !important;
        word-wrap: break-word;
        font-size: 16px !important;
        line-height: 1.6 !important;
        border-radius: 12px !important;
        padding: 5px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
        border: 1px solid #e0e0e0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    div[data-testid="stButton"] > button:active {
        transform: scale(0.98);
    }
    div[data-testid="stButton"] > button:has(div p:contains("🚨")) {
        background-color: #ffe6e6 !important;
        color: #d32f2f !important;
        border-color: #d32f2f !important;
        animation: flash 1s infinite alternate;
    }
    @keyframes flash {
        from { background-color: #3b0000; }
        to { background-color: #ff3333; }
    }
    @media (max-width: 575px) {
        div[data-testid="column"] {
            flex: 1 1 0% !important;
            width: 100% !important;
            min-width: 0 !important;
            padding: 0px 2px !important;
        }
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            gap: 2px !important;
            overflow-x: hidden !important;
        }
        div[data-testid="stButton"] > button {
            font-size: 13px !important;
            line-height: 1.3 !important;
            height: 95px !important;
            padding: 1px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.dialog("Thao tác xe")
def car_action_dialog(car):
    car_id = car["id"]
    category = car["category"]
    
    cat_info = next((c for c in st.session_state["config"].get("categories_detail", []) if c["name"] == category), None)
    billing_type = cat_info["type"] if cat_info else ("Trả sau" if "sau" in category.lower() else "Trả trước")
    
    price_per_min = st.session_state["config"]["price_per_minute"]
    active = st.session_state["active_sessions"].get(car_id)

    st.write(f"### {car['name']} - {category}")

    if not active:
        if billing_type == "Trả sau":
            if st.button("Bắt đầu thuê (Trả sau)", use_container_width=True, type="primary"):
                st.session_state["active_sessions"][car_id] = {
                    "start_time": int(time.time()),
                    "type": category,
                    "billing_type": billing_type,
                    "merged_into": None,
                    "merged_cost": 0, 
                    "status": "running"
                }
                update_active_sessions()
                st.rerun()
        else: # Trả trước
            amount = st.number_input("Khách đưa bao nhiêu tiền? (VNĐ)", min_value=1000, step=1000, value=10000)
            minutes = amount / price_per_min
            st.write(f"Tương ứng: **{minutes:.1f} phút**")
            if st.button("Bắt đầu thuê (Trả trước)", use_container_width=True, type="primary"):
                st.session_state["active_sessions"][car_id] = {
                    "start_time": int(time.time()),
                    "type": category,
                    "billing_type": billing_type,
                    "prepaid_amount": amount,
                    "max_minutes": minutes,
                    "merged_into": None,
                    "merged_cost": 0,
                    "status": "running"
                }
                update_active_sessions()
                st.rerun()
    else:
        now = int(time.time())
        started_at = active["start_time"]
        elapsed_min = (now - started_at) / 60.0
        b_type = active.get("billing_type", "Trả sau" if "sau" in active["type"].lower() else "Trả trước")
        
        if b_type == "Trả sau":
            billed_mins = max(1, math.ceil(elapsed_min))
            current_cost = billed_mins * price_per_min + active.get("merged_cost", 0)
            st.write(f"- Thời gian đã chạy: **{elapsed_min:.1f} phút** (Tính {billed_mins} phút)")
            st.write(f"- Tiền gộp từ xe khác: **{active.get('merged_cost', 0):,.0f} VNĐ**")
            st.write(f"**Tổng thành tiền: {current_cost:,.0f} VNĐ**")
            
            if st.button("Thanh toán & Kết thúc", type="primary", use_container_width=True):
                record = {
                    "id": str(uuid.uuid4()),
                    "car_id": car_id,
                    "car_name": car["name"],
                    "start_time": started_at,
                    "end_time": now,
                    "total_minutes": round(elapsed_min, 1),
                    "total_paid": round(current_cost, 0),
                    "type": category,
                    "note": ""
                }
                st.session_state["history"].append(record)
                update_history()
                del st.session_state["active_sessions"][car_id]
                update_active_sessions()
                st.rerun()

        else: # Trả trước
            rem_min = active["max_minutes"] - elapsed_min
            if rem_min < 0:
                overdue = abs(rem_min)
                billed_overdue = max(1, math.ceil(overdue))
                st.error(f"Đã quá giờ {overdue:.1f} phút!")
                extra_cost = billed_overdue * price_per_min + active.get("merged_cost", 0)
                st.write(f"Cần thu thêm quá giờ ({billed_overdue} phút) + phí gộp: **{extra_cost:,.0f} VNĐ**")
                
                if st.button("Thanh toán & Kết thúc", type="primary", use_container_width=True):
                    record = {
                        "id": str(uuid.uuid4()),
                        "car_id": car_id,
                        "car_name": car["name"],
                        "start_time": started_at,
                        "end_time": now,
                        "total_minutes": round(elapsed_min, 1),
                        "total_paid": active["prepaid_amount"] + round(extra_cost, 0),
                        "type": category,
                        "note": ""
                    }
                    st.session_state["history"].append(record)
                    update_history()
                    del st.session_state["active_sessions"][car_id]
                    update_active_sessions()
                    st.rerun()
            else:
                st.write(f"- Còn lại: **{rem_min:.1f} phút**")
                if st.button("Kết thúc sớm", type="primary", use_container_width=True):
                    record = {
                        "id": str(uuid.uuid4()),
                        "car_id": car_id,
                        "car_name": car["name"],
                        "start_time": started_at,
                        "end_time": now,
                        "total_minutes": round(elapsed_min, 1),
                        "total_paid": active["prepaid_amount"],
                        "type": category,
                        "note": ""
                    }
                    st.session_state["history"].append(record)
                    update_history()
                    del st.session_state["active_sessions"][car_id]
                    update_active_sessions()
                    st.rerun()

        st.divider()
        st.write("### Gộp đơn vào xe khác")
        other_running = [c for c, state in st.session_state["active_sessions"].items() if c != car_id]
        if other_running:
            target_car = st.selectbox("Chọn xe đích", options=other_running, format_func=lambda x: [cx['name'] for cx in st.session_state["config"]["cars"] if cx['id'] == x][0])
            if st.button("Xác nhận gộp đơn", use_container_width=True):
                cost_to_transfer = 0
                if b_type == "Trả sau":
                    billed_mins = max(1, math.ceil(elapsed_min))
                    cost_to_transfer = billed_mins * price_per_min + active.get("merged_cost", 0)
                else: 
                    if rem_min < 0:
                        billed_overdue = max(1, math.ceil(abs(rem_min)))
                        cost_to_transfer = billed_overdue * price_per_min + active.get("merged_cost", 0)
                
                st.session_state["active_sessions"][target_car]["merged_cost"] = st.session_state["active_sessions"][target_car].get("merged_cost", 0) + cost_to_transfer
                
                record = {
                        "id": str(uuid.uuid4()),
                        "car_id": car_id,
                        "car_name": car["name"],
                        "start_time": started_at,
                        "end_time": now,
                        "total_minutes": round(elapsed_min, 1),
                        "total_paid": active.get("prepaid_amount", 0), 
                        "note": f"Gộp nợ {round(cost_to_transfer, 0)} qua xe {target_car}",
                        "type": category
                }
                st.session_state["history"].append(record)
                update_history()
                del st.session_state["active_sessions"][car_id]
                update_active_sessions()
                st.success("Đã gộp thành công!")
                st.rerun()
        else:
            st.info("Không có xe nào khác đang chạy.")

@st.fragment(run_every="5s")
def render_car_cards():
    price_per_min = st.session_state["config"]["price_per_minute"]
    cars = st.session_state["config"]["cars"]
    
    is_mobile = st.session_state["config"].get("display_mode", "📱 Điện thoại") == "📱 Điện thoại"
    cols_per_row = st.session_state["config"].get("mobile_columns", 3) if is_mobile else st.session_state["config"].get("desktop_columns", 5)
    
    now_ts = int(time.time())
    total_active = len(st.session_state["active_sessions"])
    total_money = 0
    for cid, state in st.session_state["active_sessions"].items():
        elapsed = (now_ts - state["start_time"]) / 60.0
        b_type = state.get("billing_type", "Trả sau" if "sau" in state["type"].lower() else "Trả trước")
        if b_type == "Trả sau":
            billed_mins = max(1, math.ceil(elapsed))
            total_money += billed_mins * price_per_min + state.get("merged_cost", 0)
        else:
            total_money += state.get("prepaid_amount", 0) + state.get("merged_cost", 0)
            rem = state["max_minutes"] - elapsed
            if rem < 0:
                 billed_overdue = max(1, math.ceil(abs(rem)))
                 total_money += billed_overdue * price_per_min
    
    st.info(f"💰 Tạm tính: **{total_money:,.0f} đ** &nbsp;|&nbsp; ☕ Đang dùng: **{total_active}/{len(cars)}**")
    
    categories_detail = st.session_state["config"].get("categories_detail", [])
    postpaid_names = [c["name"] for c in categories_detail if c["type"] == "Trả sau"]
    prepaid_names = [c["name"] for c in categories_detail if c["type"] == "Trả trước"]
    
    postpaid_cars = [c for c in cars if c["category"] in postpaid_names or (c["category"] not in prepaid_names and "sau" in c["category"].lower())]
    prepaid_cars = [c for c in cars if c["category"] in prepaid_names or (c["category"] not in postpaid_names and "trước" in c["category"].lower())]

    def render_grid(car_list):
        cols = st.columns(cols_per_row)
        for i, car in enumerate(car_list):
            with cols[i % cols_per_row]:
                active = st.session_state["active_sessions"].get(car["id"])
                if active:
                    elapsed = (now_ts - active["start_time"]) / 60.0
                    b_type = active.get("billing_type", "Trả sau" if "sau" in active["type"].lower() else "Trả trước")
                    if b_type == "Trả sau":
                        billed_mins = max(1, math.ceil(elapsed))
                        cost = billed_mins * price_per_min + active.get("merged_cost", 0)
                        label = f"{car['name']}\n⏱ {int(elapsed)}p\n💵 {cost:,.0f}"
                        btn_type = "primary"
                    else:
                        rem = active["max_minutes"] - elapsed
                        if rem < 0:
                            billed_overdue = max(1, math.ceil(abs(rem)))
                            extra_cost = billed_overdue * price_per_min + active.get("merged_cost", 0)
                            label = f"🚨 {car['name']}\nQuá {abs(rem):.1f}p\n💵 +{extra_cost:,.0f}"
                            btn_type = "secondary"
                        else:
                            label = f"{car['name']}\n⏱ {rem:.1f}p\n💵 {active['prepaid_amount']:,}"
                            btn_type = "primary"
                else:
                    label = f"{car['name']}\n✅ Sẵn sàng"
                    btn_type = "secondary"
                
                if st.button(label, key=f"btn_{car['id']}", type=btn_type, use_container_width=True):
                    car_action_dialog(car)

    if postpaid_cars:
        st.subheader("🚙 Xe Trả Sau")
        render_grid(postpaid_cars)
        
    if prepaid_cars:
        st.subheader("⚡ Xe Trả Trước")
        render_grid(prepaid_cars)

st.title(st.session_state["config"]["play_area_name"])
tab_dashboard, tab_settings, tab_stats = st.tabs(["🚀 Dashboard", "⚙️ Cấu Hình", "📊 Thống Kê"])

with tab_dashboard:
    render_car_cards()

with tab_settings:
    st.header("Cài Đặt Hệ Thống")
    
    with st.expander("Thông tin chung", expanded=True):
        new_name = st.text_input("Tên khu vui chơi", value=st.session_state["config"]["play_area_name"])
        new_price = st.number_input("Giá thuê 1 phút (VNĐ)", value=st.session_state["config"]["price_per_minute"])
        
        st.divider()
        st.write("##### Giao diện hiển thị")
        new_display_mode = st.radio("Chế độ xem mặc định", ["📱 Điện thoại", "💻 Máy tính"], index=0 if st.session_state["config"].get("display_mode", "📱 Điện thoại") == "📱 Điện thoại" else 1, horizontal=True)
        c_m, c_d = st.columns(2)
        new_m_cols = c_m.number_input("Số xe/dòng (Điện thoại)", min_value=1, max_value=8, value=st.session_state["config"].get("mobile_columns", 3))
        new_d_cols = c_d.number_input("Số xe/dòng (Máy tính)", min_value=1, max_value=12, value=st.session_state["config"].get("desktop_columns", 5))
        
        if st.button("Lưu thay đổi"):
            st.session_state["config"]["play_area_name"] = new_name
            st.session_state["config"]["price_per_minute"] = new_price
            st.session_state["config"]["display_mode"] = new_display_mode
            st.session_state["config"]["mobile_columns"] = new_m_cols
            st.session_state["config"]["desktop_columns"] = new_d_cols
            update_config()
            st.success("Đã cập nhật!")
            st.rerun()

    with st.expander("Quản lý danh mục", expanded=False):
        st.write("Quản lý các danh mục xe. 'Kiểu tính tiền' quyết định xe thuộc loại Bấm giờ (Trả sau) hay Nạp tiền (Trả trước).")
        df_cats = pd.DataFrame(st.session_state["config"].get("categories_detail", []))
        edited_cats = st.data_editor(
            df_cats,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Tên Danh Mục", required=True),
                "type": st.column_config.SelectboxColumn("Kiểu tính tiền", options=["Trả sau", "Trả trước"], required=True)
            },
            key="cat_editor"
        )
        if st.button("Lưu danh mục"):
            st.session_state["config"]["categories_detail"] = edited_cats.dropna(subset=["name"]).to_dict(orient="records")
            update_config()
            st.success("Đã lưu cấu hình danh mục!")
            st.rerun()
            
    with st.expander("Quản lý danh sách xe", expanded=False):
        cat_names = [c["name"] for c in st.session_state["config"].get("categories_detail", [])]
        if not cat_names:
            cat_names = ["Trả sau", "Trả trước"]
            
        c1, c2, c3 = st.columns([1, 2, 1])
        new_car_id = c1.text_input("ID Xe mới (Ví dụ: 21)")
        new_car_name = c2.text_input("Tên xe mới")
        new_car_cat = c3.selectbox("Danh mục", options=cat_names, key="new_cat")
        
        if st.button("Thêm xe"):
            if new_car_id and new_car_name:
                car_ids = [c["id"] for c in st.session_state["config"]["cars"]]
                if new_car_id not in car_ids:
                    st.session_state["config"]["cars"].append({
                        "id": new_car_id, "name": new_car_name, "category": new_car_cat
                    })
                    update_config()
                    st.success("Thêm thành công! Xin hãy làm mới trang để thấy trên Dashboard.")
                else:
                    st.error("ID xe đã tồn tại!")

        st.divider()
        st.write("### Danh sách hiện tại")
        df_cars = pd.DataFrame(st.session_state["config"]["cars"])
        edited_df = st.data_editor(
            df_cars, 
            num_rows="dynamic", 
            key="car_editor",
            column_config={
                "id": st.column_config.TextColumn("ID", required=True),
                "name": st.column_config.TextColumn("Tên xe", required=True),
                "category": st.column_config.SelectboxColumn("Danh mục", options=cat_names, required=True),
            },
            use_container_width=True
        )
        if st.button("Lưu danh sách xe"):
            st.session_state["config"]["cars"] = edited_df.dropna(subset=["id", "name"]).to_dict(orient="records")
            update_config()
            st.success("Đã lưu danh sách xe mới!")
            st.rerun()

with tab_stats:
    st.header("Thống Kê Doanh Thu & Lịch Sử")
    history_data = st.session_state["history"]
    if len(history_data) == 0:
        st.info("Chưa có dữ liệu lịch sử.")
    else:
        df_hist = pd.DataFrame(history_data)
        df_hist["start_time_str"] = pd.to_datetime(df_hist["start_time"], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        df_hist["end_time_str"] = pd.to_datetime(df_hist["end_time"], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        df_hist["ngày"] = pd.to_datetime(df_hist["start_time"], unit='s').dt.strftime('%Y-%m-%d')
        
        total_rev = df_hist["total_paid"].sum()
        total_runs = len(df_hist)
        
        c1, c2 = st.columns(2)
        c1.metric("Tổng doanh thu", f"{total_rev:,.0f} VNĐ")
        c2.metric("Tổng số lượt thuê", f"{total_runs} lượt")
        
        st.subheader("Doanh thu theo ngày")
        daily_rev = df_hist.groupby("ngày")["total_paid"].sum().reset_index()
        st.bar_chart(daily_rev.set_index("ngày"))
        
        st.subheader("Chi tiết lịch sử")
        if "note" not in df_hist.columns:
            df_hist["note"] = ""
        st.dataframe(df_hist[["id", "car_name", "type", "start_time_str", "end_time_str", "total_minutes", "total_paid", "note"]].fillna(""))
