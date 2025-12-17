import streamlit as st
import pandas as pd
import asyncio
import sys
from scraper import get_train_route, scan_vacancies
from solver import process_vacancies, find_all_seat_chains

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
from utils import generate_ticket_pdf, render_visual_timeline, render_route_map

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
    st.header("🛏️ Comfort Filters")
    st.caption("Only find seats that match:")
    filter_lb = st.checkbox("Lower Berth (LB)", value=True)
    filter_sl = st.checkbox("Side Lower (SL)", value=True)
    filter_ac = st.checkbox("AC Coaches (1A/2A/3A)", value=True)
    filter_other = st.checkbox("Others (UB/MB/SU)", value=True)
    
    # Build preference list
    berth_prefs = []
    if filter_lb: berth_prefs.extend(["LB", "L"])
    if filter_sl: berth_prefs.extend(["SL", "SU", "R", "P"]) 
    if filter_other: berth_prefs.extend(["UB", "U", "MB", "M", "SM"])
    
    st.markdown("---")
    st.header("🔃 Sort Results")
    sort_option = st.selectbox(
        "Sort By:",
        ["Distance (High to Low)", "Distance (Low to High)"],
        index=0
    )



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
    
    # Show Route Map Context
    with st.expander("📍 Route Context: Full Station List", expanded=False):
        st.markdown(render_route_map(st.session_state.station_list, start_code, end_code), unsafe_allow_html=True)
    
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
            
            # Dump to JSON for debugging
            import json
            with open("vacancies_debug.json", "w") as f:
                json.dump(raw_data, f, indent=4)
            st.toast("Debug logs saved to vacancies_debug.json")
            
            status_text.text("Scanning Complete!")
            progress_bar.progress(100)
            
            if not raw_data:
                st.warning("No vacancies found on this train.")
            else:
                st.success(f"Scan Complete! Found {len(raw_data)} vacant segments.")
        except Exception as e:
            st.error(f"Scanning failed: {e}")

    # --- Phase 4: Results (Dynamic) ---
    # This runs on every rerun, so filters apply immediately
    if st.session_state.raw_vacancies:
        st.divider()
        st.header("3. Optimization Results")
        
        # Process data with Filters
        processed_data = process_vacancies(
            st.session_state.raw_vacancies, 
            st.session_state.station_map, 
            start_code, 
            end_code,
            berth_preferences=berth_prefs,
            ac_only=filter_ac
        )
        
        if not processed_data:
            st.warning("No vacancies found matching your Comfort Filters.")
        else:
            # Apply Sorting (Controlled by Sidebar)
            if sort_option == "Distance (High to Low)":
                processed_data.sort(key=lambda x: x['Coverage_Km'], reverse=True)
            elif sort_option == "Distance (Low to High)":
                processed_data.sort(key=lambda x: x['Coverage_Km'], reverse=False)
            
            # Initialize Selection State
            if 'selected_seat_idx' not in st.session_state:
                st.session_state.selected_seat_idx = 0
            
            # Ensure index is valid (if filters changed and list shrank)
            if st.session_state.selected_seat_idx >= len(processed_data):
                st.session_state.selected_seat_idx = 0
                
            best_seat = processed_data[st.session_state.selected_seat_idx]
            
            # --- Layout: Two Columns for Details ---
            col_res1, col_res2 = st.columns(2)
            
            # --- Left: Single Seat Selection ---
            with col_res1:
                st.subheader("🏆 Best Single Seat")
                
                # Display Selected Seat
                st.info(f"**Selected:** {best_seat['Coach']} - {best_seat['Berth']} ({best_seat['Type']})")
                st.metric(
                    label="Coverage", 
                    value=f"{best_seat['Coverage_Pct']}%",
                    delta=f"{best_seat['Coverage_Km']} km"
                )
                st.write(f"**From:** {best_seat['From']} ➡️ **To:** {best_seat['To']}")
                
                # "X More Options" List
                remaining_count = len(processed_data)
                with st.expander(f"See {remaining_count} more options"):
                    st.caption("Select a seat to view details:")
                    # Scrollable Container
                    with st.container(height=200):
                        for i, seat in enumerate(processed_data):
                            # Highlight selected
                            btn_type = "primary" if i == st.session_state.selected_seat_idx else "secondary"
                            label = f"{seat['Coach']}-{seat['Berth']} ({seat['Coverage_Km']} km)"
                            if st.button(label, key=f"seat_btn_{i}", type=btn_type, use_container_width=True):
                                st.session_state.selected_seat_idx = i
                                st.rerun()

            # --- Right: Hacker Chain ---
            with col_res2:
                st.subheader("🔗 Hacker Chain")
                
                # Find ALL valid chains
                all_chains = find_all_seat_chains(processed_data, st.session_state.station_map, start_code, end_code)
                
                if all_chains:
                    # Initialize Chain Selection State
                    if 'selected_chain_idx' not in st.session_state:
                        st.session_state.selected_chain_idx = 0
                    
                    if st.session_state.selected_chain_idx >= len(all_chains):
                        st.session_state.selected_chain_idx = 0
                        
                    selected_chain = all_chains[st.session_state.selected_chain_idx]
                    
                    st.success(f"Journey Possible with {len(selected_chain)-1} Swaps!")
                    
                    # Visual Timeline (Now with Intermediates)
                    st.markdown(
                        render_visual_timeline(selected_chain, st.session_state.station_list), 
                        unsafe_allow_html=True
                    )
                    
                    with st.expander("View Chain Details"):
                        for idx, leg in enumerate(selected_chain):
                            st.write(f"**Leg {idx+1}:** {leg['From']} ➡️ {leg['To']} | **{leg['Coach']} - {leg['Berth']}**")
                    
                    # "See More" for Hacker Chains
                    if len(all_chains) > 1:
                        remaining_chains = len(all_chains) - 1
                        with st.expander(f"See {remaining_chains} Other Options"):
                            st.caption("Select an alternative seat combination:")
                            with st.container(height=200):
                                for i, chain in enumerate(all_chains):
                                    # Skip the currently selected one? No, show all for easy switching, but highlight selected.
                                    
                                    # Create a label summarizing the chain: "S1-45 -> B1-20 (1 Swap)"
                                    summary = " ➝ ".join([f"{leg['Coach']}-{leg['Berth']}" for leg in chain])
                                    swaps = len(chain) - 1
                                    label = f"{summary} ({swaps} Swaps)"
                                    
                                    btn_type = "primary" if i == st.session_state.selected_chain_idx else "secondary"
                                    if st.button(label, key=f"chain_btn_{i}", type=btn_type, use_container_width=True):
                                        st.session_state.selected_chain_idx = i
                                        st.rerun()
                    else:
                        st.caption("ℹ️ Only 1 optimal chain found for this route.")
                else:
                    st.error("Cannot cover the full journey even with seat hopping.")
                    selected_chain = [] # Empty chain

            # --- Central Download Section ---
            st.divider()
            st.subheader("🎟️ Download Ticket")
            
            # Toggle for Ticket Type
            ticket_type = st.radio(
                "Select Ticket Type:",
                ["🏆 Single Seat Ticket", "🔗 Hacker Chain Ticket"],
                horizontal=True
            )
            
            # Prepare Data for Download
            download_chain = []
            file_name = ""
            
            if ticket_type == "🏆 Single Seat Ticket":
                # Create a single-leg chain for the selected seat
                download_chain = [best_seat]
                file_name = f"train_surfer_{train_no}_single.pdf"
                st.caption(f"Downloading ticket for: **{best_seat['Coach']} - {best_seat['Berth']}**")
                
            else: # Hacker Chain
                if all_chains:
                    download_chain = selected_chain
                    file_name = f"train_surfer_{train_no}_hacker.pdf"
                    st.caption(f"Downloading ticket for **{len(selected_chain)} segments**.")
                else:
                    st.warning("No Hacker Chain available to download.")
            
            # Download Button
            if download_chain:
                ticket_pdf = generate_ticket_pdf(download_chain, train_no, journey_date, start_code, end_code)
                st.download_button(
                    label="⬇️ Download PDF Ticket",
                    data=ticket_pdf,
                    file_name=file_name,
                    mime="application/pdf",
                    use_container_width=True
                )

            # --- Data Table ---
            st.subheader("📊 All Options")
            df = pd.DataFrame(processed_data)
            display_cols = ["Coach", "Berth", "Type", "From", "To", "Distance", "Coverage_Pct"]
            st.dataframe(
                df[display_cols].style.background_gradient(subset=['Coverage_Pct'], cmap="Greens"),
                use_container_width=True
            )

else:
    st.info("👈 Please fetch the train route from the sidebar to begin.")
