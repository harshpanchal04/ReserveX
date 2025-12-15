import streamlit as st
import pandas as pd
import asyncio
import sys
from scraper import get_train_route, scan_vacancies
from solver import process_vacancies, find_seat_chain

# Fix for Windows Event Loop Policy (NotImplementedError)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="Train Surfer", page_icon="🚆", layout="wide")

# --- Session State Management ---
if 'station_list' not in st.session_state:
    st.session_state.station_list = []
if 'station_map' not in st.session_state:
    st.session_state.station_map = {}
if 'raw_vacancies' not in st.session_state:
    st.session_state.raw_vacancies = []
if 'route_fetched' not in st.session_state:
    st.session_state.route_fetched = False

# --- UI Header ---
st.title("🚆 Train Surfer")
st.markdown("### Maximize Comfort. Minimize Hassle.")
st.markdown("Find the longest vacant seat segments or the optimal 'seat hopping' strategy for your journey.")

# --- Sidebar: Phase 1 (Route Discovery) ---
# --- Sidebar: Phase 1 (Route Discovery) ---
with st.sidebar:
    st.header("1. Journey Details")
    train_no = st.text_input("Train Number", value="12627")
    journey_date = st.text_input("Journey Date (YYYY-MM-DD)", value="2025-12-15")
    
    # Developer Mode Toggle
    dev_mode = st.checkbox("🛠️ Developer Mode", value=False, help="Show browser window while scanning")
    headless_mode = not dev_mode
    
    if st.button("Fetch Route"):
        with st.spinner("Fetching Train Schedule..."):
            try:
                stations = get_train_route(train_no, headless=headless_mode)
                if stations:
                    st.session_state.station_list = stations
                    st.session_state.station_map = {s['code']: s['dist'] for s in stations}
                    st.session_state.route_fetched = True
                    st.success(f"Route Loaded! {len(stations)} Stations found.")
                else:
                    st.error("Failed to fetch route. Check logs.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("### ℹ️ How it Works")
    with st.expander("See Technical Details"):
        st.markdown("""
        **1. Route Discovery:**
        - Scrapes the official schedule to map station codes to distances (km).
        
        **2. Vacancy Scanning:**
        - Uses **Playwright** to intercept internal APIs (`coachComposition`).
        - Scans every coach (S1, S2, B1...) to find partial vacancies.
        
        **3. The 'Hacker' Algorithm:**
        - **Single Seat:** Finds the longest continuous segment.
        - **Seat Hopping:** Uses a **Greedy Algorithm** to chain vacancies together, minimizing seat swaps.
        """)

# --- Main Area ---

if st.session_state.route_fetched:
    st.header("2. Select Your Segment")
    
    # Create formatted options for dropdowns: "SBC - KSR BENGALURU"
    station_options = [f"{s['code']} - {s['name']}" for s in st.session_state.station_list]
    
    col1, col2 = st.columns(2)
    with col1:
        start_option = st.selectbox("Boarding Station", station_options)
    with col2:
        end_option = st.selectbox("Destination Station", station_options, index=len(station_options)-1)
        
    start_code = start_option.split(" - ")[0]
    end_code = end_option.split(" - ")[0]
    
    if st.button("Find Seats"):
        st.markdown("### 🔍 Scanning for Vacancies...")
        
        # Progress Bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, coach_name):
            progress = int((current / total) * 100)
            progress_bar.progress(progress)
            status_text.text(f"Scanning Coach {coach_name}... ({current}/{total})")

        try:
            # Scan vacancies
            raw_data = scan_vacancies(
                train_no, 
                journey_date, 
                start_code, 
                headless=headless_mode,
                progress_callback=update_progress
            )
            st.session_state.raw_vacancies = raw_data
            
            status_text.text("Scanning Complete!")
            progress_bar.progress(100)
            
            if not raw_data:
                st.warning("No vacancies found on this train.")
            else:
                st.success(f"Scan Complete! Found {len(raw_data)} vacant segments.")
        except Exception as e:
            st.error(f"Scanning failed: {e}")

    # --- Phase 4: Results ---
    if st.session_state.raw_vacancies:
        st.divider()
        st.header("3. Optimization Results")
        
        # Process data for the specific segment
        processed_data = process_vacancies(
            st.session_state.raw_vacancies, 
            st.session_state.station_map, 
            start_code, 
            end_code
        )
        
        if not processed_data:
            st.warning("No vacancies found overlapping with your selected journey segment.")
        else:
            # --- Metric 1: Longest Single Seat ---
            # Sort by Coverage %
            processed_data.sort(key=lambda x: x['Coverage_Pct'], reverse=True)
            best_seat = processed_data[0]
            
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.subheader("🏆 Best Single Seat")
                st.metric(
                    label=f"Coach {best_seat['Coach']} - Berth {best_seat['Berth']} ({best_seat['Type']})", 
                    value=f"{best_seat['Coverage_Pct']}% Coverage",
                    delta=f"{best_seat['Coverage_Km']} km"
                )
                st.write(f"**From:** {best_seat['From']} ➡️ **To:** {best_seat['To']}")
                
            # --- Metric 2: Hacker Chain ---
            with col_res2:
                st.subheader("🔗 Hacker Chain")
                chain = find_seat_chain(processed_data, st.session_state.station_map, start_code, end_code)
                
                if chain:
                    st.success(f"Full Journey Possible with {len(chain)-1} Swaps!")
                    for idx, leg in enumerate(chain):
                        st.write(f"**Leg {idx+1}:** {leg['From']} ➡️ {leg['To']} | **{leg['Coach']} - {leg['Berth']}**")
                else:
                    st.error("Cannot cover the full journey even with seat hopping.")

            # --- Data Table ---
            st.subheader("📊 All Options")
            df = pd.DataFrame(processed_data)
            
            # Reorder columns for display
            display_cols = ["Coach", "Berth", "Type", "From", "To", "Distance", "Coverage_Pct"]
            st.dataframe(
                df[display_cols].style.background_gradient(subset=['Coverage_Pct'], cmap="Greens"),
                use_container_width=True
            )

else:
    st.info("👈 Please fetch the train route from the sidebar to begin.")
