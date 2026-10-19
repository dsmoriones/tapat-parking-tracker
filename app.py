from datetime import datetime
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

# --- HEADER IMAGE SECTION ---
if os.path.exists(HEADER_BANNER_PATH):
  st.image(HEADER_BANNER_PATH, use_container_width=True)
else:
  st.title("🚗 TAPAT Parking Management System")

# Sidebar navigation & settings
st.sidebar.title("Navigation & Settings")
menu = st.sidebar.radio(
    "Go to",
    ["Log Parking Counts", "View Weekly Report", "Summary Dashboard"],
)

with st.sidebar.expander("⚙️ App Customization"):
  custom_banner = st.file_uploader(
      "Upload Header Banner Image", type=["png", "jpg", "jpeg"]
  )
  if custom_banner is not None:
    banner_img = Image.open(custom_banner)
    banner_img.save(HEADER_BANNER_PATH)
    st.success("Header banner updated! Refresh the page to see it.")

  st.markdown("---")
  st.subheader("🗑️ Data Reset Options")
  if st.button(
      "Clear All Logged Data",
      type="primary",
      help="Clicking this permanently deletes all logged test entries.",
  ):
    if os.path.exists(FILENAME):
      os.remove(FILENAME)
      st.cache_data.clear()
      st.success("All parking logs cleared successfully!")
      st.rerun()
    else:
      st.info("No data log file found to reset.")

# --- TAB 1: LOG PARKING COUNTS ---
if menu == "Log Parking Counts":
  st.header("Church of God Dasmarinas Parking Tracker")

  # 1. Select Location first
  selected_location = st.selectbox(
      "Select Church Location:", list(LOCATION_CONFIG.keys())
  )

  # Fetch specific services and areas for the chosen location
  active_services = LOCATION_CONFIG[selected_location]["services"]
  active_parking_areas = LOCATION_CONFIG[selected_location]["areas"]

  # 2. Select Worship Service dynamically based on the chosen location
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

    # Create
