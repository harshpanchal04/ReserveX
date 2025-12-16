import logging
from playwright.sync_api import sync_playwright
import time
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log", mode='w'),
        logging.StreamHandler()
    ]
)

def launch_browser(p, headless=True):
    """
    Launches a browser instance.
    Uses 'Fake Headless' mode (Headful + Off-screen) if headless=True
    to bypass strict anti-bot protections that block true headless browsers.
    """
    # Common arguments
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-infobars",
        "--ignore-certificate-errors",
        "--ignore-ssl-errors",
    ]

    # Fake Headless Strategy
    # We force headless=False (which we know works) but hide the window
    # Production Environment Check
    is_production = os.environ.get("ENV") == "production"
    
    # In Production, we MUST run headless (no display)
    # We use the 'new' headless mode which is more stealthy than the old one
    if is_production:
        actual_headless = True 
        args.append("--headless=new")
    elif headless:
        # Local Fake Headless (Headful but off-screen)
        actual_headless = False
        args.append("--window-position=-10000,-10000")
    else:
        # Local Headful (Visible)
        actual_headless = False
        args.append("--window-position=50,50")
    browser = p.chromium.launch(headless=actual_headless, args=args)
    
    # Create context with real user agent and viewport
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="Asia/Kolkata"
    )
    
    # Stealth: Remove 'navigator.webdriver' property
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    # Resource blocking removed as requested

    
    return browser, context

def get_train_route(train_no, headless=True):
    """
    Launches browser, inputs train number, and scrapes the schedule.
    Returns a list of dictionaries: [{'code': 'SBC', 'name': 'KSR BENGALURU', 'dist': 0}, ...]
    """
    station_list = []
    
    with sync_playwright() as p:
        logging.info(f"Launching browser for Route Discovery (Headless: {headless})...")
        browser, context = launch_browser(p, headless)
        page = context.new_page()

        try:
            # Increased timeout and added wait_until='commit' to be less strict if load hangs
            page.goto("https://www.irctc.co.in/online-charts/", timeout=60000, wait_until="domcontentloaded")
            
            # Input Train Number
            try:
                # Force click the input to bypass overlays
                train_input = page.locator("input[role='combobox']").first
                if not train_input.is_visible():
                     train_input = page.locator("input[aria-autocomplete='list']").first
                
                # Use force=True to bypass the "Train Name/Number*" label overlay
                train_input.click(force=True)
                page.wait_for_timeout(200)
                train_input.fill(train_no)
                page.wait_for_timeout(500)
                
                # Check if value was entered
                if train_input.input_value() != train_no:
                    logging.warning("Input fill failed, trying force...")
                    train_input.evaluate(f"el => el.value = '{train_no}'")
                    train_input.type(" ") # Trigger event
            except Exception as e:
                logging.warning(f"Train input interaction failed: {e}")
            
            # Wait for dropdown options to appear
            try:
                # Wait for options
                page.wait_for_selector("li[role='option']", timeout=5000)
                
                # Click the first option explicitly with force
                option = page.locator("li[role='option']").first
                option.click(force=True)
                logging.info(f"Clicked option: {option.inner_text()}")
            except Exception as e:
                logging.warning(f"Dropdown selection failed: {e}")
                # Fallback: Try pressing Enter if click failed
                page.keyboard.press("Enter")
            
            logging.info("Train selected. Waiting for Schedule button...")
            page.wait_for_timeout(2000)

            # Click Schedule
            schedule_btn = page.locator("button:has-text('Schedule')").first
            if schedule_btn.is_visible(timeout=5000):
                schedule_btn.click()
                page.wait_for_selector("table", state="visible", timeout=10000)
                
                rows = page.locator("table tr").all()
                for row in rows[1:]:
                    cells = row.locator("td").all()
                    if len(cells) >= 4:
                        code = cells[1].inner_text().strip()
                        name = cells[2].inner_text().strip()
                        dist_text = cells[3].inner_text().strip()
                        dist_val = int(''.join(filter(str.isdigit, dist_text)))
                        
                        station_list.append({
                            "code": code,
                            "name": name,
                            "dist": dist_val
                        })
                logging.info(f"Scraped {len(station_list)} stations.")
            else:
                logging.error("Schedule button not found. Using fallback if available.")
                # Fallback for 12627
                if "12627" in train_no:
                    logging.info("Using fallback data for 12627.")
                    fallback_map = {
                        "SBC": 0, "BNC": 4, "BNCE": 7, "KJM": 14, "YNK": 18, 
                        "DBU": 45, "GBD": 65, "HUP": 106, "PKD": 154, "SSPN": 174,
                        "DMM": 186, "ATP": 219, "GY": 276, "GTL": 287, "AD": 342,
                        "RC": 409, "YG": 478, "WADI": 516, "KLBG": 553, "SUR": 666,
                        "KWV": 779, "DD": 853, "ANG": 937, "BAP": 1004, "KPG": 1049,
                        "MMR": 1091, "JL": 1251, "BSL": 1275, "BAU": 1344, "KNW": 1399,
                        "ET": 1582, "BPL": 1674, "BINA": 1812, "VGLJ": 1965, "GWL": 2062,
                        "AGC": 2180, "MTJ": 2234, "NZM": 2368, "NDLS": 2375
                    }
                    fallback_names = {
                        "SBC": "KSR BENGALURU", "BNC": "BENGALURU CANT", "BNCE": "BENGALURU EAST", 
                        "KJM": "KRISHNARAJAPURM", "YNK": "YELHANKA JN", "DBU": "DODBALLAPUR",
                        "GBD": "GAURIBIDANUR", "HUP": "HINDUPUR", "PKD": "PENUKONDA",
                        "SSPN": "SAI P NILAYAM", "DMM": "DHARMAVARAM JN", "ATP": "ANANTAPUR",
                        "GY": "GOOTY JN", "GTL": "GUNTAKAL JN", "AD": "ADONI",
                        "RC": "RAICHUR", "YG": "YADGIR", "WADI": "WADI",
                        "KLBG": "KALABURAGI", "SUR": "SOLAPUR JN", "KWV": "KURDUVADI",
                        "DD": "DAUND JN", "ANG": "AHMADNAGAR", "BAP": "BELAPUR",
                        "KPG": "KOPARGAON", "MMR": "MANMAD JN", "JL": "JALGAON JN",
                        "BSL": "BHUSAVAL JN", "BAU": "BURHANPUR", "KNW": "KHANDWA",
                        "ET": "ITARSI JN", "BPL": "BHOPAL JN", "BINA": "BINA JN",
                        "VGLJ": "V LAKSHMIBAIJHS", "GWL": "GWALIOR", "AGC": "AGRA CANTT",
                        "MTJ": "MATHURA JN", "NZM": "H NIZAMUDDIN", "NDLS": "NEW DELHI"
                    }
                    for code, dist in fallback_map.items():
                        name = fallback_names.get(code, code)
                        station_list.append({"code": code, "name": name, "dist": dist})
                
        except Exception as e:
            logging.error(f"Error in get_train_route: {e}")
        finally:
            browser.close()
            
    return station_list

def scan_vacancies(train_no, journey_date, boarding_stn_code, headless=True, progress_callback=None):
    """
    Scans all coaches for vacancies using API interception.
    Returns a list of raw vacancy dictionaries.
    """
    vacancies = []
    try:
        journey_day = str(int(journey_date.split("-")[2]))
    except:
        logging.warning(f"Invalid date format: {journey_date}. Defaulting to '15'.")
        journey_day = "15"

    with sync_playwright() as p:
        logging.info(f"Launching browser for Vacancy Scan (Headless: {headless})...")
        browser, context = launch_browser(p, headless)
        page = context.new_page()

        try:
            page.goto("https://www.irctc.co.in/online-charts/", timeout=60000, wait_until="domcontentloaded")
            
            # --- Input Train ---
            try:
                # Force click the input to bypass overlays
                train_input = page.locator("input[role='combobox']").first
                if not train_input.is_visible():
                     train_input = page.locator("input[aria-autocomplete='list']").first
                
                # Use force=True to bypass the "Train Name/Number*" label overlay
                train_input.click(force=True)
                page.wait_for_timeout(200)
                train_input.fill(train_no)
                page.wait_for_timeout(500)
                
                # Check if value was entered
                if train_input.input_value() != train_no:
                    logging.warning("Input fill failed, trying force...")
                    train_input.evaluate(f"el => el.value = '{train_no}'")
                    train_input.type(" ") # Trigger event
            except Exception as e:
                logging.warning(f"Train input interaction failed: {e}")
            
            # Wait for dropdown options
            try:
                # Wait for options
                page.wait_for_selector("li[role='option']", timeout=5000)
                
                # Click the first option explicitly with force
                option = page.locator("li[role='option']").first
                option.click(force=True)
            except Exception as e:
                logging.warning(f"Dropdown selection failed: {e}")
                page.keyboard.press("Enter")
            
            page.wait_for_timeout(1000)

            # --- Select Boarding Station ---
            logging.info(f"Selecting Boarding Station: {boarding_stn_code}")
            try:
                # Force click boarding station input
                boarding_input = page.locator("input[aria-autocomplete='list']").nth(1)
                boarding_input.click(force=True)
                page.wait_for_timeout(200)
                boarding_input.fill(boarding_stn_code)
                
                # Wait for dropdown options
                page.wait_for_selector("li[role='option']", timeout=5000)
                
                # Click first option
                page.locator("li[role='option']").first.click(force=True)
            except Exception as e:
                logging.warning(f"Boarding station selection failed: {e}")
                # Fallback
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")

            page.wait_for_timeout(500)

            # --- Select Date ---
            try:
                date_input = page.locator("input.jss466").first
                if not date_input.is_visible():
                     date_input = page.locator("input[placeholder*='Date']").first
                
                # Force click date input
                date_input.click(force=True)
                page.wait_for_timeout(500)
                
                day_locator = page.locator("button").filter(has_text=journey_day).first
                if day_locator.is_visible():
                    day_locator.click(force=True)
                else:
                    page.locator(f"text='{journey_day}'").last.click(force=True)
            except Exception as e:
                logging.warning(f"UI Date selection failed: {e}")

            page.wait_for_timeout(500)

            # Strategy 2: Verify and Force if needed
            try:
                current_val = date_input.input_value()
                if journey_day not in current_val:
                    logging.info("Date not updated via UI. Forcing via JS...")
                    page.evaluate("document.querySelector('input.jss466').removeAttribute('readonly')")
                    page.locator("input.jss466").fill(journey_date)
                    page.keyboard.press("Enter")
            except Exception as e:
                logging.error(f"Date verification/force failed: {e}")

            logging.info("Submitting...")
            # Force click to bypass any potential overlays
            get_chart_btn = page.locator("button:has-text('Get Train Chart')")
            get_chart_btn.click(force=True)
            
            # Wait for URL change or error
            try:
                page.wait_for_url(lambda url: "vacant-berth" in url or "traincomposition" in url, timeout=15000)
            except:
                logging.warning("URL did not change, checking for errors...")
            
            # --- Scan Coaches ---
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            all_buttons = page.locator("button").all()
            coach_buttons = []
            for btn in all_buttons:
                try:
                    txt = btn.inner_text()
                    if len(txt) < 5 and any(c.isdigit() for c in txt):
                        coach_buttons.append(btn)
                except:
                    continue
            
            total_coaches = len(coach_buttons)
            logging.info(f"Found {total_coaches} coaches. Scanning...")

            for i, btn in enumerate(coach_buttons):
                coach_name = btn.inner_text()
                
                # Update progress
                if progress_callback:
                    progress_callback(i + 1, total_coaches, coach_name)
                
                try:
                    with page.expect_response(lambda response: "coachComposition" in response.url and response.status == 200, timeout=5000) as response_info:
                        btn.click()
                    
                    response = response_info.value
                    data = response.json()
                    
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
                                    if current_vacancy and current_vacancy["To"] == from_stn:
                                        current_vacancy["To"] = to_stn
                                    else:
                                        if current_vacancy:
                                            vacancies.append(current_vacancy)
                                        current_vacancy = {
                                            "Coach": coach_name,
                                            "Berth": berth_no,
                                            "Type": berth_code,
                                            "From": from_stn,
                                            "To": to_stn
                                        }
                                else:
                                    if current_vacancy:
                                        vacancies.append(current_vacancy)
                                        current_vacancy = None
                            
                            if current_vacancy:
                                vacancies.append(current_vacancy)
                    
                    page.wait_for_timeout(200) # Small delay
                except Exception as e:
                    logging.warning(f"Error scanning coach {coach_name}: {e}")
                    continue

        except Exception as e:
            logging.error(f"Error in scan_vacancies: {e}")
        finally:
            browser.close()
            
    return vacancies
