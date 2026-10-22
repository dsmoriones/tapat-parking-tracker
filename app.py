from datetime import datetime, timedelta
import io
import os
import pandas as pd
from PIL import Image
import streamlit as st

# Import Turso / libSQL driver
try:
  import libsql

  HAS_TURSO = True
  TURSO_IMPORT_ERROR = None
except Exception as e:
  HAS_TURSO = False
  TURSO_IMPORT_ERROR = str(e)

# --- TURSO CREDENTIALS & DB SETUP ---
TURSO_DB_URL = "https://tapatparkingdb-dsmoriones.aws-ap-northeast-1.turso.io"
TURSO_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTI2Nzk5MDgsImlkIjoiMDFhMTY0MGMtMTAwMS03YmRkLWE3ZTktODE4ZWZhYjhhYjIxIiwia2lkIjoiWk00cjVhRGMxMFYxY2Z4amJGa2YtRjZHR2VmeW9ybEt5eHVJMEpXS0tYdyIsInJpZCI6IjFiZGE2MDI0LWM1M2MtNDQzNy1iNjAxLTBiNjdmM2NjNTAyOSJ9.PuJBbsZyEt1IE-zKBZ16QPOjv185qScPfWJv_-4QbyXG-ASioALW2u54hqm3VTiLf44om3po5BRl2lzKtiAZDQ"

FILENAME = "tapat_parking_logs.csv"
IMAGE_DIR = "uploaded_photos"
HEADER_BANNER_PATH = "tapat_banner.png"

# Capacity estimates per parking area (for visual capacity bars)
AREA_CAPACITIES = {
    "Parking 1": 50,
    "Parking 2": 40,
    "Parking 3": 35,
    "Parking 4": 30,
    "Parking 5": 25,
    "Parking 6": 25,
    "Parking 7": 20,
    "Parking 8": 20,
    "Parking 9": 15,
    "Parking 10": 15,
    "Basement": 60,
    "Open Parking": 100,
    "Main Parking": 80,
    "BIR": 40,
}

# Ensure local storage directory exists
if not os.path.exists(IMAGE_DIR):
  os.makedirs(IMAGE_DIR)


def get_turso_db():
  if not HAS_TURSO:
    return None, f"libsql library not loaded: {TURSO_IMPORT_ERROR}"
  try:
    conn = libsql.connect(database=TURSO_DB_URL, auth_token=TURSO_AUTH_TOKEN)
    return conn, None
  except Exception as e:
    return None, str(e)


def init_turso_db():
  conn, err = get_turso_db()
  if conn:
    try:
      conn.execute("""
                CREATE TABLE IF NOT EXISTS parking_logs (
                    Timestamp TEXT,
                    Date TEXT,
                    Week_Number INTEGER,
                    Location TEXT,
                    Service TEXT,
                    Parking_Area TEXT,
                    Car_Count INTEGER,
                    Motorcycle_Count INTEGER,
                    Photo_Path TEXT
                )
            """)
      conn.commit()
    except Exception:
      pass


if HAS_TURSO:
  init_turso_db()

# Location configuration
LOCATION_CONFIG = {
    "COG Dasma - Main": {
        "areas": [
            "Parking 1",
            "Parking 2",
            "Parking 3",
            "Parking 4",
            "Parking 5",
            "Parking 6",
            "Parking 7",
            "Parking 8",
            "Parking 9",
            "Parking 10",
            "Basement",
        ],
        "services": [
            "1st Service",
            "2nd Service",
            "3rd Service",
            "4th Service",
            "5th Service",
            "6th Service",
            "7th Service",
            "8th Service",
            "Tuesday Worship Service",
            "Salvation Night",
            "Empowered Night",
        ],
    },
    "COG Jabez": {
        "areas": ["Open Parking"],
        "services": [
            "1st Service",
            "2nd Service",
            "3rd Service",
            "4th Service",
            "5th Service",
        ],
    },
    "COG Trece": {
        "areas": ["Main Parking", "BIR"],
        "services": [
            "1st Service",
            "2nd Service",
            "3rd Service",
            "4th Service",
            "5th Service",
            "6th Service",
            "7th Service",
        ],
    },
    "COG Silang": {
        "areas": ["Main Parking"],
        "services": [
            "1st Service",
            "2nd Service",
            "3rd Service",
            "4th Service",
            "5th Service",
            "6th Service",
        ],
    },
    "Palmas Resort": {
        "areas": ["Main Parking"],
        "services": ["Whole Day"],
    },
}


@st.cache_data(ttl=5)
def load_data():
  conn, _ = get_turso_db()
  if conn is not None:
    try:
      res = conn.execute("SELECT * FROM parking_logs")
      rows = res.fetchall()
      cols = [
          "Timestamp",
          "Date",
          "Week_Number",
          "Location",
          "Service",
          "Parking_Area",
          "Car_Count",
          "Motorcycle_Count",
          "Photo_Path",
      ]
      df_turso = pd.DataFrame(rows, columns=cols)
      if not df_turso.empty:
        return df_turso
    except Exception:
      pass

  try:
    return pd.read_csv(FILENAME)
  except FileNotFoundError:
    return pd.DataFrame(columns=[
        "Timestamp",
        "Date",
        "Week_Number",
        "Location",
        "Service",
        "Parking_Area",
        "Car_Count",
        "Motorcycle_Count",
        "Photo_Path",
    ])


def save_data(new_entries_df):
  conn, _ = get_turso_db()
  if conn is not None:
    try:
      for _, entry in new_entries_df.iterrows():
        conn.execute(
            """
                    INSERT INTO parking_logs (Timestamp, Date, Week_Number, Location, Service, Parking_Area, Car_Count, Motorcycle_Count, Photo_Path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                str(entry["Timestamp"]),
                str(entry["Date"]),
                int(entry["Week_Number"]),
                str(entry["Location"]),
                str(entry["Service"]),
                str(entry["Parking_Area"]),
                int(entry["Car_Count"]),
                int(entry["Motorcycle_Count"]),
                str(entry["Photo_Path"]),
            ),
        )
      conn.commit()
    except Exception as e:
      st.warning(f"Turso cloud sync warning: {e}")

  try:
    if os.path.exists(FILENAME):
      df = pd.read_csv(FILENAME)
      df = pd.concat([df, new_entries_df], ignore_index=True)
    else:
      df = new_entries_df
    df.to_csv(FILENAME, index=False)
  except Exception as e:
    st.error(f"Error saving to local CSV: {e}")


# --- UI HELPER COMPONENTS ---
def kpi_card(title, value, icon, accent_color="#2563eb"):
  return f"""
    <div style="
        background-color: var(--background-secondary-color, #1e293b);
        padding: 16px;
        border-radius: 12px;
        border-top: 4px solid {accent_color};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 12px;
    ">
        <p style="margin: 0; font-size: 0.85rem; opacity: 0.8; font-weight: 500;">{icon} {title}</p>
        <h2 style="margin: 4px 0 0 0; font-size: 1.8rem; font-weight: 700;">{value:,}</h2>
    </div>
    """


def status_badge(is_online=True):
  color = "#10b981" if is_online else "#f59e0b"
  label = "TURSO CLOUD ONLINE" if is_online else "LOCAL CSV BACKUP MODE"
  return f"""
    <div style="display: inline-flex; align-items: center; gap: 6px; background-color: #1e293b; border: 1px solid #334155; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin-bottom: 15px;">
        <span style="height: 8px; width: 8px; background-color: {color}; border-radius: 50%; display: inline-block;"></span>
        <span style="color: #f8fafc;">{label}</span>
    </div>
    """


def empty_state_card(message="No parking logs recorded for this selection."):
  st.markdown(
      f"""
    <div style="text-align: center; padding: 30px; background-color: #1e293b; border-radius: 12px; border: 2px dashed #334155; margin: 15px 0;">
        <p style="font-size: 2.2rem; margin-bottom: 8px;">📋</p>
        <h4 style="margin: 0; opacity: 0.9; color: #f8fafc;">{message}</h4>
        <p style="font-size: 0.85rem; opacity: 0.6; margin-top: 6px; color: #94a3b8;">Select another week/location or switch to "Log Parking Counts" to insert data.</p>
    </div>
    """,
      unsafe_allow_html=True,
  )


def capacity_progress_bar(area_name, current_count, capacity):
  percentage = min(int((current_count / max(1, capacity)) * 100), 100)
  color = (
      "#10b981" if percentage < 70 else "#f59e0b" if percentage < 90 else "#ef4444"
  )
  st.markdown(
      f"""
    <div style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;">
            <span>🅿️ {area_name}</span>
            <span>{current_count} / {capacity} vehicles ({percentage}%)</span>
        </div>
        <div style="background-color: #334155; border-radius: 8px; height: 10px; width: 100%;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 8px; transition: width 0.4s ease;"></div>
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )


st.set_page_config(
    page_title="TAPAT Parking Tracker", page_icon="🚗", layout="centered"
)

# --- MODERN ENHANCED UI STYLING & POLISHED CARDS ---
st.markdown(
    """
    <style>
        [data-testid="stMetric"] {
            background-color: var(--background-secondary-color, #1e293b);
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color, #334155);
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
        }
        div[data-testid="stVerticalBlock"] > div[style*="border"] {
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Detection for URL view options
try:
  query_params = st.query_params
  is_leadership_view = query_params.get("view") in ["leadership", "summary"]
except Exception:
  query_params = st.experimental_get_query_params()
  is_leadership_view = (
      query_params.get("view", [""])[0] in ["leadership", "summary"]
  )

if is_leadership_view:
  st.markdown(
      """
        <style>
            [data-testid="stSidebar"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
        </style>
    """,
      unsafe_allow_html=True,
  )
  menu = "Summary Dashboard"
else:
  ADMIN_PASSWORD = "tapat_admin_2026"

  if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

  st.sidebar.title("📌 Main Menu")

  nav_options = [
      "Log Parking Counts",
      "View Weekly Report",
      "Summary Dashboard",
  ]
  if st.session_state.is_admin:
    nav_options.append("Data Verification")

  menu = st.sidebar.radio("Navigate to:", nav_options)

  st.sidebar.markdown("---")
  if not st.session_state.is_admin:
    with st.sidebar.expander("🔑 Admin Access"):
      entered_pass = st.text_input(
          "Password", type="password", key="admin_pass_input"
      )
      if st.button("Unlock Admin", use_container_width=True):
        if entered_pass == ADMIN_PASSWORD:
          st.session_state.is_admin = True
          st.success("Admin unlocked!")
          st.rerun()
        else:
          st.error("Incorrect password.")
  else:
    with st.sidebar.expander("⚙️ System Admin Controls", expanded=True):
      st.markdown("#### ☁️ Cloud Database Health")
      if st.button("🔌 Test Connection", use_container_width=True):
        conn, err = get_turso_db()
        if conn is not None:
          try:
            res = conn.execute("SELECT COUNT(*) FROM parking_logs")
            total_rows = res.fetchone()[0]
            st.success(
                f"🟢 Connected to Turso!\nTotal saved entries: {total_rows}"
            )
          except Exception as e:
            st.warning(f"🟡 Connected, but table query failed: {e}")
        else:
          st.error(f"🔴 Connection failed:\n`{err}`")

      st.markdown("---")
      custom_banner = st.file_uploader(
          "Upload Header Banner", type=["png", "jpg", "jpeg"]
      )
      if custom_banner is not None:
        banner_img = Image.open(custom_banner)
        banner_img.save(HEADER_BANNER_PATH)
        st.success("Header banner updated!")

      st.markdown("---")
      if st.button("🗑️ Clear Local Backup CSV", use_container_width=True):
        if os.path.exists(FILENAME):
          os.remove(FILENAME)
          st.cache_data.clear()
          st.success("Backup logs cleared!")
          st.rerun()

      st.markdown("---")
      if st.button("🔒 Lock Admin Access", use_container_width=True):
        st.session_state.is_admin = False
        st.rerun()

# --- HEADER SECTION ---
if os.path.exists(HEADER_BANNER_PATH):
  st.image(HEADER_BANNER_PATH, use_container_width=True)
else:
  st.title("🚗 TAPAT PARKING MANAGEMENT SYSTEM")

st.markdown(status_badge(HAS_TURSO), unsafe_allow_html=True)

# --- TAB 1: LOG PARKING COUNTS ---
if menu == "Log Parking Counts":
  st.header("📝 Log Parking Counts")

  if "success_message" in st.session_state:
    st.success(st.session_state["success_message"])
    del st.session_state["success_message"]

  # Location selection header card
  with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
      selected_location = st.selectbox(
          "📍 Church Location:", list(LOCATION_CONFIG.keys())
      )
      active_services = LOCATION_CONFIG[selected_location]["services"]
      active_parking_areas = LOCATION_CONFIG[selected_location]["areas"]
    with c2:
      selected_service = st.selectbox("⛪ Worship Service:", active_services)
      log_date = st.date_input("📅 Date", datetime.now())

  st.markdown("### 🚘 Area Count Inputs")

  with st.form("table_entry_form", clear_on_submit=True):
    counts_data = {}

    for area in active_parking_areas:
      with st.container(border=True):
        st.markdown(f"#### 🅿️ {area}")
        col1, col2 = st.columns(2)
        with col1:
          cars = st.number_input(
              f"🚘 Cars", min_value=0, step=1, value=0, key=f"car_{area}"
          )
        with col2:
          motors = st.number_input(
              f"🛵 Motorcycles",
              min_value=0,
              step=1,
              value=0,
              key=f"motor_{area}",
          )
        counts_data[area] = {"cars": cars, "motors": motors}

    st.markdown("### 📷 Photo Verification (Optional)")
    uploaded_file = st.file_uploader(
        "Upload photos of full parking lots or traffic incidents",
        type=["png", "jpg", "jpeg"],
    )

    submit_button = st.form_submit_button(
        label="💾 Submit All Counts", use_container_width=True, type="primary"
    )

    if submit_button:
      now = datetime.now()

      if log_date.weekday() == 6:
        calc_date = log_date - timedelta(days=1)
      else:
        calc_date = log_date

      week_num = calc_date.isocalendar()[1]
      saved_image_path = ""

      if uploaded_file is not None:
        img_filename = f"{log_date.strftime('%Y%m%d')}_{selected_service.split()[0]}_{uploaded_file.name}"
        saved_image_path = os.path.join(IMAGE_DIR, img_filename)
        image = Image.open(uploaded_file)
        image.save(saved_image_path)

      new_entries = []
      for area, vals in counts_data.items():
        new_entries.append({
            "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Date": log_date.strftime("%Y-%m-%d"),
            "Week_Number": int(week_num),
            "Location": selected_location,
            "Service": selected_service,
            "Parking_Area": area,
            "Car_Count": int(vals["cars"]),
            "Motorcycle_Count": int(vals["motors"]),
            "Photo_Path": saved_image_path,
        })

      new_df = pd.DataFrame(new_entries)

      try:
        save_data(new_df)
        st.cache_data.clear()
        st.session_state["success_message"] = (
            f"✅ Saved counts for {selected_location} - {selected_service}"
            f" (Week {week_num})!"
        )
        st.rerun()
      except Exception as e:
        st.error(f"Error saving data: {e}")

# --- TAB 2: VIEW WEEKLY REPORT ---
elif menu == "View Weekly Report":
  st.header("📊 Weekly Summary Report")

  df = load_data()

  if df.empty:
    empty_state_card("No parking logs found yet.")
  else:
    today = datetime.now()
    if today.weekday() == 6:
      curr_calc_date = today - timedelta(days=1)
    else:
      curr_calc_date = today

    current_week = curr_calc_date.isocalendar()[1]

    r_col1, r_col2 = st.columns(2)
    with r_col1:
      selected_week = st.number_input(
          "Select Week Number:",
          min_value=1,
          max_value=53,
          value=int(current_week),
      )
    with r_col2:
      report_location = st.selectbox(
          "Filter by Location:",
          ["All Locations"] + list(LOCATION_CONFIG.keys()),
      )

    filtered_df = df[df["Week_Number"] == selected_week]

    if report_location != "All Locations":
      filtered_df = filtered_df[filtered_df["Location"] == report_location]

    if filtered_df.empty:
      empty_state_card(
          f"No records found for Week {selected_week} ({report_location})."
      )
    else:
      filtered_df["Total_Vehicles"] = (
          filtered_df["Car_Count"] + filtered_df["Motorcycle_Count"]
      )

      summary_table = (
          filtered_df.groupby(["Location", "Parking_Area"])[
              ["Car_Count", "Motorcycle_Count", "Total_Vehicles"]
          ]
          .sum()
          .reset_index()
      )

      if report_location != "All Locations":
        custom_order = LOCATION_CONFIG[report_location]["areas"]
        summary_table["Parking_Area"] = pd.Categorical(
            summary_table["Parking_Area"], categories=custom_order, ordered=True
        )
        summary_table = summary_table.sort_values("Parking_Area")

      summary_table.columns = [
          "Location",
          "Parking Area",
          "Cars",
          "Motorcycles",
          "Total Vehicles",
      ]

      st.dataframe(summary_table, use_container_width=True)

      total_cars = filtered_df["Car_Count"].sum()
      total_motors = filtered_df["Motorcycle_Count"].sum()
      grand_total = filtered_df["Total_Vehicles"].sum()

      col1, col2, col3 = st.columns(3)
      with col1:
        st.markdown(
            kpi_card("Total Cars", total_cars, "🚘", "#3b82f6"),
            unsafe_allow_html=True,
        )
      with col2:
        st.markdown(
            kpi_card("Total Motorcycles", total_motors, "🛵", "#10b981"),
            unsafe_allow_html=True,
        )
      with col3:
        st.markdown(
            kpi_card("Grand Total", grand_total, "📊", "#8b5cf6"),
            unsafe_allow_html=True,
        )

      st.markdown("### 📊 Area Occupancy Progress")
      for _, row in summary_table.iterrows():
        area = row["Parking Area"]
        tot = row["Total Vehicles"]
        cap = AREA_CAPACITIES.get(area, 50)
        capacity_progress_bar(area, tot, cap)

      st.markdown("### 📈 Vehicle Breakdown Chart")
      chart_data = summary_table.set_index("Parking Area")[
          ["Cars", "Motorcycles"]
      ]
      st.bar_chart(chart_data, color=["#3b82f6", "#10b981"], height=280)

      st.markdown("---")

      # Export format dataset
      export_df = summary_table.copy()
      export_df.insert(0, "Week Number", int(selected_week))
      export_df = export_df[[
          "Week Number",
          "Location",
          "Parking Area",
          "Total Vehicles",
      ]]
      export_df.columns = [
          "Week Number",
          "Church Location",
          "Parking Location",
          "Vehicle Count",
      ]

      dl_col1, dl_col2 = st.columns(2)

      with dl_col1:
        csv_data = summary_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export CSV Report",
            data=csv_data,
            file_name=(
                f"tapat_report_week_{selected_week}_{report_location.replace(' ', '_')}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

      with dl_col2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
          export_df.to_excel(writer, index=False, sheet_name="Weekly Report")
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📥 Export Excel Report (.xlsx)",
            data=excel_data,
            file_name=(
                f"tapat_report_week_{selected_week}_{report_location.replace(' ', '_')}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
            type="primary",
        )

# --- TAB 3: SUMMARY DASHBOARD ---
elif menu == "Summary Dashboard":
  st.header("📈 Leadership Executive Dashboard")

  if not is_leadership_view:
    with st.expander("🔗 Share Clean Executive Link"):
      st.code(
          "https://tapat-parking-tracker.streamlit.app/?view=leadership",
          language="text",
      )

  df = load_data()

  if df.empty:
    empty_state_card("No parking logs recorded yet.")
  else:
    col_week, col_loc = st.columns(2)

    today = datetime.now()
    if today.weekday() == 6:
      curr_calc_date = today - timedelta(days=1)
    else:
      curr_calc_date = today

    current_week = curr_calc_date.isocalendar()[1]

    with col_week:
      selected_week = st.number_input(
          "Select Week Number:",
          min_value=1,
          max_value=53,
          value=int(current_week),
          key="dash_week",
      )

    with col_loc:
      selected_dash_loc = st.selectbox(
          "Filter Location:",
          ["All Locations"] + list(LOCATION_CONFIG.keys()),
          key="dash_loc_filter",
      )

    week_df = df[df["Week_Number"] == selected_week]

    if week_df.empty:
      empty_state_card(f"No records found for Week {selected_week}.")
    else:
      if selected_dash_loc != "All Locations":
        filtered_dash_df = week_df[week_df["Location"] == selected_dash_loc]
      else:
        filtered_dash_df = week_df

      if filtered_dash_df.empty:
        empty_state_card(
            f"No records logged for {selected_dash_loc} in Week {selected_week}."
        )
      else:
        total_cars_all = filtered_dash_df["Car_Count"].sum()
        total_motors_all = filtered_dash_df["Motorcycle_Count"].sum()
        grand_total_vehicles = total_cars_all + total_motors_all

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
          st.markdown(
              kpi_card("Total Cars", total_cars_all, "🚘", "#3b82f6"),
              unsafe_allow_html=True,
          )
        with c2:
          st.markdown(
              kpi_card("Total Motorcycles", total_motors_all, "🛵", "#10b981"),
              unsafe_allow_html=True,
          )
        with c3:
          st.markdown(
              kpi_card(
                  "Grand Total Vehicles", grand_total_vehicles, "📊", "#8b5cf6"
              ),
              unsafe_allow_html=True,
          )

        st.markdown("---")

        target_locations = (
            list(LOCATION_CONFIG.keys())
            if selected_dash_loc == "All Locations"
            else [selected_dash_loc]
        )

        for loc in target_locations:
          loc_df = week_df[week_df["Location"] == loc]

          if not loc_df.empty:
            with st.container(border=True):
              st.markdown(f"### 📍 {loc}")

              service_grouped = (
                  loc_df.groupby("Service")[["Car_Count", "Motorcycle_Count"]]
                  .sum()
                  .reset_index()
              )

              config_services = LOCATION_CONFIG[loc]["services"]
              service_grouped["Service"] = pd.Categorical(
                  service_grouped["Service"],
                  categories=config_services,
                  ordered=True,
              )
              service_grouped = service_grouped.sort_values("Service")

              loc_cars = 0
              loc_motors = 0

              for _, row in service_grouped.iterrows():
                svc = row["Service"]
                c = int(row["Car_Count"])
                m = int(row["Motorcycle_Count"])
                tot = c + m
                loc_cars += c
                loc_motors += m

                st.write(
                    f"• **{svc}:** {c:,} Cars | {m:,} Motorcycles *(Total:"
                    f" {tot:,})*"
                )

              loc_combined = loc_cars + loc_motors
              st.success(
                  f"**{loc} Subtotal:** {loc_cars:,} Cars + {loc_motors:,}"
                  f" Motorcycles = **{loc_combined:,} Total Vehicles**"
              )

# --- SECRET TAB 4: DATA VERIFICATION (ADMIN ONLY) ---
elif menu == "Data Verification" and getattr(
    st.session_state, "is_admin", False
):
  st.header("🔒 Admin Data Verification Log")

  df_verify = load_data()

  if df_verify.empty:
    empty_state_card("No parking log entries found.")
  else:
    st.markdown("---")

    grouped_entries = (
        df_verify.groupby(["Timestamp", "Date", "Location", "Service"])[
            ["Car_Count", "Motorcycle_Count"]
        ]
        .sum()
        .reset_index()
    )

    for idx, row in grouped_entries.iloc[::-1].iterrows():
      ts = row["Timestamp"]
      dt = row["Date"]
      loc = row["Location"]
      svc = row["Service"]
      cars = int(row["Car_Count"])
      motors = int(row["Motorcycle_Count"])
      tot = cars + motors

      with st.container(border=True):
        col_text, col_btn = st.columns([5, 1])

        with col_text:
          st.markdown(
              f"🕒 **`{ts}`** | 📍 **{loc}** ({svc}) — Date: `{dt}` | 🚘"
              f" `{cars}` | 🛵 `{motors}` | **Total: {tot}**"
          )

        with col_btn:
          if st.button("🗑️ Delete", key=f"del_submission_{idx}"):
            conn, _ = get_turso_db()
            if conn is not None:
              try:
                conn.execute(
                    "DELETE FROM parking_logs WHERE Timestamp = ?", (ts,)
                )
                conn.commit()
              except Exception:
                pass

            if os.path.exists(FILENAME):
              df_csv = pd.read_csv(FILENAME)
              df_csv = df_csv[df_csv["Timestamp"] != ts]
              df_csv.to_csv(FILENAME, index=False)

            st.cache_data.clear()
            st.success("Deleted entry!")
            st.rerun()
