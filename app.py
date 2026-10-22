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
TURSO_DB_URL = "https://tapat-parking-db-dsmoriones.aws-eu-west-1.turso.io"
TURSO_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3OTI2NzkwNTAsImlkIjoiMDFhMTYzZGEtMWQwMS03NjFjLTkxNGEtZmNhZjMxM2ZlMjdjIiwia2lkIjoiWk00cjVhRGMxMFYxY2Z4amJGa2YtRjZHR2VmeW9ybEt5eHVJMEpXS0tYdyIsInJpZCI6ImEwZWYxNGIwLWU0MDUtNGE1MS1iNWUxLTRjYTQ1YmZhMjI2NSJ9.zNV0rP2eHB8WdIMSuIhAHA4BWICwGmb2PU8HDH3dhdhW96DJRA7vyWqA1153216q3eRHXB3e0zjaeuHRomKoAQ"

FILENAME = "tapat_parking_logs.csv"
IMAGE_DIR = "uploaded_photos"
HEADER_BANNER_PATH = "tapat_banner.png"

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


st.set_page_config(
    page_title="TAPAT Parking Tracker", page_icon="🚗", layout="centered"
)

# --- MODERN ENHANCED UI STYLING & POLISHED CARDS ---
st.markdown(
    """
    <style>
        /* Card & Metric Container Customization */
        [data-testid="stMetric"] {
            background-color: var(--background-secondary-color, #1e293b);
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color, #334155);
        }
        /* Primary Submit Buttons */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
        }
        /* Input Form Card Separation */
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
        img_filename =
