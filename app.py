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

# Configuration mapping locations, areas, and services
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

# Header Banner
if os.path.exists(HEADER_BANNER_PATH):
  st.image(HEADER_BANNER_PATH, use_container_width=True)
else:
  st.title("🚗 TAPAT Parking Management System")

# Navigation Menu
st.sidebar.title("Navigation & Settings")
menu = st.sidebar.radio(
    "Go to",
    ["Log Parking Counts", "View Weekly Report", "Summary Dashboard"],
)

df = load_data()

# App Customization
with st.sidebar.expander("⚙️ App Customization"):
  custom_banner = st.file_uploader(
      "Upload Header Banner Image", type=["png", "jpg", "jpeg"]
  )
  if custom_banner is not None:
    banner_img = Image.open(custom_banner)
    banner_img.save(HEADER_BANNER_PATH)
    st.success("Header banner updated! Refresh page.")

# --- TAB 1: LOG PARKING COUNTS ---
if menu == "Log Parking Counts":
  st.header("Church of God Dasmarinas")

  selected_location = st.selectbox(
      "Select Church Location:", list(LOCATION_CONFIG.keys())
  )
  active_services = LOCATION_CONFIG[selected_location]["services"]
  active_parking_areas = LOCATION_CONFIG[selected_location]["areas"]

  selected_service = st.selectbox("Select Worship Service:", active_services)
  log_date = st.date_input("Date", datetime.now())

  st.markdown("---")
  st.subheader(f"Input Counts for: {selected_location}")

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

    st.markdown("---")
    uploaded_file = st.file_uploader(
        "📷 Attach Verification Photo (Optional)", type=["png", "jpg", "jpeg"]
    )
    submit_button = st.form_submit_button(
        label="💾 Save Counts", use_container_width=True
    )

    if submit_button:
      now = datetime.now()
      week_num = log_date.isocalendar()[1]
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
        st.success("Successfully saved counts!")
      except Exception as e:
        st.error(f"Error saving data: {e}")

# --- TAB 2: VIEW WEEKLY REPORT ---
elif menu == "View Weekly Report":
  st.header("📊 Weekly Summary Report")
  if df.empty:
    st.info("No parking logs found yet.")
  else:
    current_week = datetime.now().isocalendar()[1]
    selected_week = st.number_input(
        "Select Week Number:",
        min_value=1,
        max_value=53,
        value=int(current_week),
    )
    filtered_df = df[df["Week_Number"] == selected_week]

    if filtered_df.empty:
      st.warning(f"No records found for Week {selected_week}.")
    else:
      report_location = st.selectbox(
          "Filter Report by Location:",
          ["All Locations"] + list(LOCATION_CONFIG.keys()),
      )
      if report_location != "All Locations":
        filtered_df = filtered_df[filtered_df["Location"] == report_location]

      if not filtered_df.empty:
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
              summary_table["Parking_Area"],
              categories=custom_order,
              ordered=True,
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

# --- TAB 3: EXECUTIVE DASHBOARD ---
elif menu == "Dashboard (Tab 3)":
  st.header("📈 TAPAT Executive Parking Dashboard")
  st.caption(
      "Comprehensive weekly traffic metrics and location breakdowns for"
      " leadership."
  )

  if df.empty:
    st.info("No parking logs found yet.")
  else:
    col_week, col_loc = st.columns(2)
    current_week = datetime.now().isocalendar()[1]

    with col_week:
      selected_week = st.number_input(
          "Select Dashboard Week:",
          min_value=1,
          max_value=53,
          value=int(current_week),
          key="dash_week",
      )

    with col_loc:
      selected_dash_loc = st.selectbox(
          "Filter Dashboard Location:",
          ["All Locations"] + list(LOCATION_CONFIG.keys()),
          key="dash_loc_filter",
      )

    week_df = df[df["Week_Number"] == selected_week]

    if week_df.empty:
      st.warning(f"No parking data recorded for Week {selected_week}.")
    else:
      if selected_dash_loc != "All Locations":
        filtered_dash_df = week_df[week_df["Location"] == selected_dash_loc]
      else:
        filtered_dash_df = week_df

      if filtered_dash_df.empty:
        st.warning(
            f"No records logged for {selected_dash_loc} in Week {selected_week}."
        )
      else:
        # Top Metrics
        total_cars_all = filtered_dash_df["Car_Count"].sum()
        total_motors_all = filtered_dash_df["Motorcycle_Count"].sum()
        grand_total_vehicles = total_cars_all + total_motors_all

        st.markdown("---")
        st.subheader("🌐 Overall Ministry Grand Totals")

        col1, col2, col3 = st.columns(3)
        col1.metric("🚘 Grand Total Cars", f"{total_cars_all:,}")
        col2.metric("🛵 Grand Total Motorcycles", f"{total_motors_all:,}")
        col3.metric("🚘+🛵 Overall Vehicles Total", f"{grand_total_vehicles:,}")

        st.markdown("---")

        # Location Breakdowns
        if selected_dash_loc == "All Locations":
          target_locations = list(LOCATION_CONFIG.keys())
        else:
          target_locations = [selected_dash_loc]

        for loc in target_locations:
          loc_df = week_df[week_df["Location"] == loc]
          if not loc_df.empty:
            st.markdown(f"### 📍 {loc}")
            service_grouped = (
                loc_df.groupby("Service")[["Car_Count", "Motorcycle_Count"]]
                .sum()
                .reset_index()
            )

            loc_cars = 0
            loc_motors = 0
            for _, row in service_grouped.iterrows():
              svc = row["Service"]
              c = int(row["Car_Count"])
              m = int(row["Motorcycle_Count"])
              loc_cars += c
              loc_motors += m
              st.write(f"• **{svc}:** {c:,} Cars | {m:,} Motorcycles")

            loc_combined = loc_cars + loc_motors
            st.info(
                f"**{loc} Subtotal:** {loc_cars:,} Cars + {loc_motors:,}"
                f" Motorcycles = **{loc_combined:,} Total Vehicles**"
            )
            st.markdown("")
