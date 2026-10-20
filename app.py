from datetime import datetime, timedelta
import os
import pandas as pd
from PIL import Image
import streamlit as st

FILENAME = "tapat_parking_logs.csv"
IMAGE_DIR = "uploaded_photos"
HEADER_BANNER_PATH = "tapat_banner.png"

# Ensure directories exist
if not os.path.exists(IMAGE_DIR):
  os.makedirs(IMAGE_DIR)

# Define Church Locations with their own specific Parking Areas AND Services
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
        "areas": [
            "Open Parking",
        ],
        "services": [
            "1st Service",
            "2nd Service",
            "3rd Service",
            "4th Service",
            "5th Service",
        ],
    },
    "COG Trece": {
        "areas": [
            "Main Parking",
            "BIR",
        ],
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
        "areas": [
            "Main Parking",
        ],
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
        "areas": [
            "Main Parking",
        ],
        "services": [
            "Whole Day",
        ],
    },
}


@st.cache_data
def load_data():
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


st.set_page_config(
    page_title="TAPAT Parking Tracker", page_icon="🚗", layout="centered"
)

# --- LEADERSHIP VIEW URL DETECTION ---
# Checks if URL contains '?view=leadership' or '?view=summary'
query_params = st.query_params
is_leadership_view = query_params.get("view") in ["leadership", "summary"]

if is_leadership_view:
  # Hide sidebar entirely for leadership
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
  # Normal Navigation setup
  ADMIN_PASSWORD = "tapat_admin_2026"

  if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

  st.sidebar.title("Navigation & Settings")

  nav_options = [
      "Log Parking Counts",
      "View Weekly Report",
      "Summary Dashboard",
  ]
  if st.session_state.is_admin:
    nav_options.append("Data Verification")

  menu = st.sidebar.radio("Go to", nav_options)

  with st.sidebar.expander("⚙️ App Customization"):
    custom_banner = st.file_uploader(
        "Upload Header Banner Image", type=["png", "jpg", "jpeg"]
    )
    if custom_banner is not None:
      banner_img = Image.open(custom_banner)
      banner_img.save(HEADER_BANNER_PATH)
      st.success("Header banner updated! Refresh the page to see it.")

    st.markdown("---")
    if st.button("🗑️ Clear All Logged Data"):
      if os.path.exists(FILENAME):
        os.remove(FILENAME)
        st.cache_data.clear()
        st.success("All logs cleared successfully!")
        st.rerun()

    st.markdown("---")
    if not st.session_state.is_admin:
      entered_pass = st.text_input("Admin Unlock", type="password")
      if st.button("Unlock Verification Tab"):
        if entered_pass == ADMIN_PASSWORD:
          st.session_state.is_admin = True
          st.success("Unlocked!")
          st.rerun()
        else:
          st.error("Incorrect password.")
    else:
      if st.button("Lock Admin Access"):
        st.session_state.is_admin = False
        st.rerun()

# --- HEADER IMAGE SECTION ---
if os.path.exists(HEADER_BANNER_PATH):
  st.image(HEADER_BANNER_PATH, use_container_width=True)
else:
  st.title("🚗 TAPAT PARKING MANAGEMENT SYSTEM 🚗")


# --- TAB 1: LOG PARKING COUNTS ---
if menu == "Log Parking Counts":
  st.header("Church of God Dasmarinas Parking Tracker")

  selected_location = st.selectbox(
      "Select Church Location:", list(LOCATION_CONFIG.keys())
  )

  active_services = LOCATION_CONFIG[selected_location]["services"]
  active_parking_areas = LOCATION_CONFIG[selected_location]["areas"]

  selected_service = st.selectbox("Select Worship Service:", active_services)
  log_date = st.date_input("Date", datetime.now())

  st.markdown("---")
  st.subheader(f"Input Counts for: {selected_location}")
  st.caption(
      "Enter the number of Cars and Motorcycles for each area during this"
      " service."
  )

  with st.form("table_entry_form"):
    counts_data = {}

    for area in active_parking_areas:
      st.markdown(f"**📍 {area}**")
      col1, col2 = st.columns(2)
      with col1:
        cars = st.number_input(
            f"Cars ({area})", min_value=0, step=1, value=0, key=f"car_{area}"
        )
      with col2:
        motors = st.number_input(
            f"Motorcycles ({area})",
            min_value=0,
            step=1,
            value=0,
            key=f"motor_{area}",
        )
      counts_data[area] = {"cars": cars, "motors": motors}
      st.markdown("")

    st.markdown("---")
    st.subheader("📷 Incident Photograph (Optional)")
    uploaded_file = st.file_uploader(
        "Choose an image file or take a photo", type=["png", "jpg", "jpeg"]
    )

    submit_button = st.form_submit_button(
        label="💾 Save Counts & Upload Photo", use_container_width=True
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
            "Week_Number": week_num,
            "Location": selected_location,
            "Service": selected_service,
            "Parking_Area": area,
            "Car_Count": int(vals["cars"]),
            "Motorcycle_Count": int(vals["motors"]),
            "Photo_Path": saved_image_path,
        })

      new_df = pd.DataFrame(new_entries)

      try:
        df = load_data()
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(FILENAME, index=False)
        st.cache_data.clear()
        st.success(
            f"Successfully saved counts for {selected_location} -"
            f" {selected_service} (Assigned to Week {week_num})!"
        )
      except Exception as e:
        st.error(f"Error saving data: {e}")

# --- TAB 2: VIEW WEEKLY REPORT ---
elif menu == "View Weekly Report":
  st.header("📊 Weekly Summary Report")
