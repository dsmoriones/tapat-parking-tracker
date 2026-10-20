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

# --- MODERN UI STYLING & CSS INJECTION (FIXED FOR DARK MODE) ---
st.markdown(
    """
    <style>
        /* Theme-aware metric card styling */
        [data-testid="stMetric"] {
            background-color: var(--background-secondary-color, #f8f9fa);
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color, #e9ecef);
        }
        
        /* Ensure metric text remains readable */
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: var(--text-color, #1e293b) !important;
        }

        /* Style headers */
        h1, h2, h3 {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Custom containers */
        div[data-testid="stVerticalBlock"] > div[style*="border"] {
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- LEADERSHIP VIEW URL DETECTION ---
query_params = st.query_params
is_leadership_view = query_params.get("view") in ["leadership", "summary"]

if is_leadership_view:
  # Hide sidebar entirely for leadership link view
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
  # --- ADMIN AUTHENTICATION FOR SECRET TAB ---
  ADMIN_PASSWORD = "tapat_admin_2026"

  if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

  # Sidebar navigation & settings
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

  df = load_data()

  if df.empty:
    st.info("No parking logs found yet.")
  else:
    today = datetime.now()
    if today.weekday() == 6:
      curr_calc_date = today - timedelta(days=1)
    else:
      curr_calc_date = today

    current_week = curr_calc_date.isocalendar()[1]

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

      if filtered_df.empty:
        st.warning(
            f"No records found for {report_location} in Week {selected_week}."
        )
      else:
        filtered_df["Total_Vehicles"] = (
            filtered_df["Car_Count"] + filtered_df["Motorcycle_Count"]
        )

        st.subheader(f"Summary Breakdown for Week {selected_week}")

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

        total_cars = filtered_df["Car_Count"].sum()
        total_motors = filtered_df["Motorcycle_Count"].sum()
        grand_total = filtered_df["Total_Vehicles"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cars", total_cars)
        col2.metric("Total Motorcycles", total_motors)
        col3.metric("Combined Grand Total", grand_total)

        csv_data = summary_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Weekly Report (CSV)",
            data=csv_data,
            file_name=(
                f"tapat_weekly_report_week_{selected_week}_{report_location.replace(' ', '_')}.csv"
            ),
            mime="text/csv",
        )

        photos = filtered_df[
            filtered_df["Photo_Path"].notna() & (filtered_df["Photo_Path"] != "")
        ]["Photo_Path"].unique()

        if len(photos) > 0:
          st.markdown("---")
          st.subheader("🖼️ Attached Verification Photos")
          cols = st.columns(min(len(photos), 3))
          for idx, photo_path in enumerate(photos):
            if os.path.exists(photo_path):
              with cols[idx % 3]:
                st.image(
                    photo_path,
                    caption=os.path.basename(photo_path),
                    use_container_width=True,
                )

# --- TAB 3: SUMMARY DASHBOARD ---
elif menu == "Summary Dashboard":
  st.header("📈 Weekly Parking Leadership Dashboard")
  st.caption(
      "Executive overview of service-by-service vehicle counts and location"
      " subtotals."
  )

  # Share link helper box for Marshals (hidden when viewed via leadership link)
  if not is_leadership_view:
    with st.expander("🔗 Share Leadership Link"):
      st.info(
          "Send this direct link to church leadership so they can view only the"
          " clean summary dashboard:"
      )
      st.code(
          "https://tapat-parking-tracker.streamlit.app/?view=leadership",
          language="text",
      )

  df = load_data()

  if df.empty:
    st.info("No parking logs recorded yet.")
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
          "Filter by Church Location:",
          ["All Locations"] + list(LOCATION_CONFIG.keys()),
          key="dash_loc_filter",
      )

    week_df = df[df["Week_Number"] == selected_week]

    if week_df.empty:
      st.warning(f"No records found for Week {selected_week}.")
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
        total_cars_all = filtered_dash_df["Car_Count"].sum()
        total_motors_all = filtered_dash_df["Motorcycle_Count"].sum()
        grand_total_vehicles = total_cars_all + total_motors_all

        st.markdown("---")
        st.subheader("🌐 Ministry Overall Summary")

        # Visually appealing card metrics
        c1, c2, c3 = st.columns(3)
        with c1:
          st.metric("🚘 Total Cars", f"{total_cars_all:,}")
        with c2:
          st.metric("🛵 Total Motorcycles", f"{total_motors_all:,}")
        with c3:
          st.metric("📊 Grand Total Vehicles", f"{grand_total_vehicles:,}")

        st.markdown("---")

        if selected_dash_loc == "All Locations":
          target_locations = list(LOCATION_CONFIG.keys())
        else:
          target_locations = [selected_dash_loc]

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
  st.caption(
      "Clean single-line entries showing timestamps, locations, and total"
      " vehicle counts."
  )

  df_verify = load_data()

  if df_verify.empty:
    st.info("No parking log entries found.")
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

      col_text, col_btn = st.columns([5, 1])

      with col_text:
        st.markdown(
            f"🕒 **`{ts}`** | 📍 **{loc}** ({svc}) — Date: `{dt}` | 🚘"
            f" `{cars}` Cars | 🛵 `{motors}` Motors | **Total: {tot}**"
        )

      with col_btn:
        if st.button("🗑️ Delete", key=f"del_submission_{idx}"):
          df_verify = df_verify[df_verify["Timestamp"] != ts].reset_index(
              drop=True
          )
          df_verify.to_csv(FILENAME, index=False)
          st.cache_data.clear()
          st.success("Deleted submission entry!")
          st.rerun()

      st.markdown("---")
