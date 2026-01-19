import asyncio
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError
import time
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("last_run.log", mode='w'),
        logging.StreamHandler()
    ]
)

def main():
    TRAIN_NO = "12627"  # Example Train Number
    JOURNEY_DATE = "2025-12-15" # Example Date (YYYY-MM-DD) - Adjust as needed for valid dates
    
    # Extract day for UI selection
    journey_day = str(int(JOURNEY_DATE.split("-")[2])) # e.g., "15" from "2025-12-15"
    
    # Note: JOURNEY_DATE needs to be a valid running date for the train. 
    # The script attempts to select this date.

    with sync_playwright() as p:
        logging.info("Launching browser...")
        browser = p.chromium.launch(headless=False) # Headless=False for debugging/visuals
        context = browser.new_context()
        page = context.new_page()

        try:
            logging.info("Navigating to IRCTC Online Charts...")
            page.goto("https://www.irctc.co.in/online-charts/", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000) # Extra wait for dynamic elements

            # --- Phase 1: Fetch Dynamic Schedule ---
            logging.info(f"Inputting Train Number: {TRAIN_NO}")
            
            # Robust Strategy: Click the label to focus the input, then type.
            try:
                page.locator("label").filter(has_text="Train Name/Number").first.click()
            except Exception as e:
                logging.warning(f"Label click failed: {e}. Trying generic input click.")
                page.locator("input[aria-autocomplete='list']").first.click()
            
            page.wait_for_timeout(500)
            
            # Type the train number
            page.keyboard.type(TRAIN_NO, delay=100)
            page.wait_for_timeout(2000) # Wait for dropdown options
            
            # Select the first option (The train itself)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            
            logging.info("Train selected. Waiting for Boarding Station to load...")
            page.wait_for_timeout(3000) # Increased wait
            
            # --- Select Boarding Station ---
            logging.info("Selecting Boarding Station (First Option)...")
            try:
                page.locator("label").filter(has_text="Boarding Station").first.click()
            except:
                page.locator("input[aria-autocomplete='list']").nth(1).click()
                
            page.wait_for_timeout(1000)
            page.keyboard.press("Space")
            page.wait_for_timeout(1000)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            
            logging.info("Boarding Station selected.")
            page.wait_for_timeout(1000) # Wait after selection
            
            # --- Get Distances ---
            logging.info("Fetching Schedule...")
            # The Schedule button appears after train selection
            # It might take a while or might not appear if data is cached/different.
            # We'll try to find it, but if it fails, we shouldn't crash the whole script if we can proceed.
            # However, we need station map for distance calc.
            
            station_map = {}
            try:
                schedule_btn = page.locator("button:has-text('Schedule')").first
                if schedule_btn.is_visible(timeout=5000):
                    schedule_btn.click()
                    
                    # Wait for modal/table
                    page.wait_for_selector("table", state="visible", timeout=10000)
                    
                    logging.info("Scraping Station Distances...")
                    rows = page.locator("table tr").all()
                    
                    for row in rows[1:]: # Skip header row
                        cells = row.locator("td").all()
                        if len(cells) >= 4: # Station No, Code, Name, Distance
                            try:
                                name_text = cells[2].inner_text().strip() # 3rd col is name
                                dist_text = cells[3].inner_text().strip() # 4th col is distance
                                dist_val = int(''.join(filter(str.isdigit, dist_text)))
                                station_map[name_text] = dist_val
                            except Exception as e:
                                logging.warning(f"Error parsing row: {e}")
                                continue

                    logging.info(f"Loaded {len(station_map)} stations.")
                    
                    # Close modal
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                else:
                    logging.warning("Schedule button not visible. Skipping distance calculation.")
            except Exception as e:
                 logging.warning(f"Error fetching schedule: {e}. Proceeding without distance data.")

            # --- Phase 2: Access Charts ---
            logging.info("Selecting Date...")
            
            # Strategy 1: UI Interaction
            try:
                # Click the input to open calendar
                date_input = page.locator("input.jss466").first
                if not date_input.is_visible():
                     date_input = page.locator("input[placeholder*='Date']").first
                
                date_input.click()
                page.wait_for_timeout(1000) # Wait for animation
                
                # Try to find the day
                # Common MUI selectors: button with text "15", or div/span with text "15" inside a button
                day_locator = page.locator("button").filter(has_text=journey_day).first
                if day_locator.is_visible():
                    day_locator.click()
                    logging.info(f"Clicked day '{journey_day}' via button.")
                else:
                    # Try generic text click if button not found
                    page.locator(f"text='{journey_day}'").last.click()
                    logging.info(f"Clicked day '{journey_day}' via text.")
                    
            except Exception as e:
                logging.warning(f"UI Date selection failed: {e}. Trying JS fallback.")
            
            page.wait_for_timeout(500)
            
            # Strategy 2: Verify and Force if needed
            # Check if value is correct (simple check)
            current_val = date_input.input_value()
            if journey_day not in current_val:
                logging.info("Date not updated via UI. Forcing via JS...")
                try:
                    # Remove readonly attribute
                    page.evaluate("document.querySelector('input.jss466').removeAttribute('readonly')")
                    page.wait_for_timeout(200)
                    date_input.fill(JOURNEY_DATE)
                    page.keyboard.press("Enter")
                    logging.info("Forced date via JS fill.")
                except Exception as e2:
                    logging.error(f"JS Force failed: {e2}")

            logging.info("Submitting...")
            # Force click to bypass any potential overlays
            get_chart_btn = page.locator("button:has-text('Get Train Chart')")
            get_chart_btn.click(force=True)
            
            # Wait for charts page
            # The URL might be .../vacant-berth or .../traincomposition
            page.wait_for_url(lambda url: "vacant-berth" in url or "traincomposition" in url, timeout=45000) 
            
            # --- Phase 3: Find the Vacancy ---
            logging.info("Scanning for Vacancies...")
            
            # Hardcoded fallback station map for 12627 (Karnataka Express)
            # Distances are approximate km from SBC
            fallback_station_map = {
                "SBC": 0, "BNC": 4, "BNCE": 7, "KJM": 14, "YNK": 18, 
                "DBU": 45, "GBD": 65, "HUP": 106, "PKD": 154, "SSPN": 174,
                "DMM": 186, "ATP": 219, "GY": 276, "GTL": 287, "AD": 342,
                "RC": 409, "YG": 478, "WADI": 516, "KLBG": 553, "SUR": 666,
                "KWV": 779, "DD": 853, "ANG": 937, "BAP": 1004, "KPG": 1049,
                "MMR": 1091, "JL": 1251, "BSL": 1275, "BAU": 1344, "KNW": 1399,
                "ET": 1582, "BPL": 1674, "BINA": 1812, "VGLJ": 1965, "GWL": 2062,
                "AGC": 2180, "MTJ": 2234, "NZM": 2368, "NDLS": 2375
            }
            
            if not station_map:
                logging.info("Using fallback station map for distance calculations.")
                station_map = fallback_station_map

            # Wait for page to settle
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as e:
                logging.warning(f"Wait for load state failed: {e}")
            
            # Inspect all buttons to find coaches
            logging.info("Inspecting all buttons to find coaches...")
            all_buttons = page.locator("button").all()
            coach_buttons = []
            
            for i, btn in enumerate(all_buttons):
                try:
                    txt = btn.inner_text()
                    if len(txt) < 5 and any(c.isdigit() for c in txt):
                        coach_buttons.append(btn)
                except Exception as e:
                    logging.warning(f"Error filtering button: {e}")
                    continue
            
            logging.info(f"Found {len(coach_buttons)} coach buttons.")
            
            all_vacancies = []
            
            
            for btn in coach_buttons:
                coach_name = btn.inner_text()
                logging.info(f"Checking Coach {coach_name}...")
                
                try:
                    # Intercept the API call
                    with page.expect_response(lambda response: "coachComposition" in response.url and response.status == 200, timeout=10000) as response_info:
                        btn.click()
                    
                    response = response_info.value
                    data = response.json()
                    
                    # Parse vacancies from JSON
                    if "bdd" in data:
                        for seat in data["bdd"]:
                            berth_no = seat.get("berthNo")
                            berth_code = seat.get("berthCode")
                            bsd = seat.get("bsd", [])
                            
                            current_vacancy = None
                            
                            for segment in bsd:
                                is_occupied = segment.get("occupancy", True)
                                from_stn = segment.get("from")
                                to_stn = segment.get("to")
                                
                                if not is_occupied:
                                    # Found a vacant segment
                                    if current_vacancy and current_vacancy["To"] == from_stn:
                                        # Extend current vacancy
                                        current_vacancy["To"] = to_stn
                                    else:
                                        # Start new vacancy
                                        if current_vacancy:
                                            all_vacancies.append(current_vacancy)
                                        
                                        current_vacancy = {
                                            "Coach": coach_name,
                                            "Berth": berth_no,
                                            "Type": berth_code,
                                            "From": from_stn,
                                            "To": to_stn,
                                            "Distance": 0
                                        }
                                else:
                                    # Segment is occupied, close current vacancy if any
                                    if current_vacancy:
                                        all_vacancies.append(current_vacancy)
                                        current_vacancy = None
                            
                            # Append the last vacancy if exists
                            if current_vacancy:
                                all_vacancies.append(current_vacancy)
                    
                    page.wait_for_timeout(500) # Rate limiting
                    
                except Exception as e:
                    logging.warning(f"Could not fetch/parse data for {coach_name}: {e}")
                    continue

            # Calculate distances for all found vacancies
            for vac in all_vacancies:
                if vac["From"] in station_map and vac["To"] in station_map:
                    vac["Distance"] = abs(station_map[vac["To"]] - station_map[vac["From"]])
            
            # Sort vacancies by distance (descending)
            all_vacancies.sort(key=lambda x: x["Distance"], reverse=True)

            # --- Output ---
            print("\n" + "="*30)
            print(f"Scanning Train: {TRAIN_NO}")
            print(f"Coaches Scanned: {len(coach_buttons)}")
            print(f"Total Vacancies Found: {len(all_vacancies)}")
            
            if all_vacancies:
                print("\nTop 5 Longest Vacant Segments:")
                for i, vac in enumerate(all_vacancies[:5]):
                    print(f"{i+1}. Coach {vac['Coach']}, Berth {vac['Berth']} ({vac['Type']})")
                    print(f"   {vac['From']} -> {vac['To']} ({vac['Distance']} km)")
            else:
                print("No vacancies found.")
            print("="*30 + "\n")

        except Exception as e:
            logging.error(f"An error occurred: {e}", exc_info=True)
            page.screenshot(path="error_screenshot.png")
            logging.info("Screenshot saved as error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
