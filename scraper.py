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
        "--disable-dev-shm-usage", # Stability for Docker
        "--disable-http2",         # Fix for net::ERR_HTTP2_PROTOCOL_ERROR
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
        timezone_id="Asia/Kolkata",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }
    )
    
    # Stealth: Remove 'navigator.webdriver' property
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context

def interact_with_dropdown(page, input_locator, text, label="Dropdown", related_label_text=None):
    """
    Robustly interacts with an autocomplete dropdown.
    1. Clicks related label (if provided) to focus.
    2. Focuses and types character by character (human-like).
    3. Waits for options and clicks the first one.
    """
    logging.info(f"Interacting with {label}: {text}")
    try:
        # Strategy 1: Click Label first
        if related_label_text:
            try:
                logging.info(f"Clicking label: {related_label_text}")
                # Special case for Train Name/Number which has no text in DOM
                if "Train" in related_label_text:
                    page.locator("label").first.click(force=True)
                else:
                    page.get_by_text(related_label_text, exact=False).first.click(force=True)
                page.wait_for_timeout(200)
                
                # Type into the focused element
                page.keyboard.type(text, delay=200)
                page.wait_for_timeout(500)
                
                # Jiggle to wake up React
                page.keyboard.press("Space")
                page.keyboard.press("Backspace")
                page.wait_for_timeout(500)
                
                # Force dropdown to open
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(500)
            except Exception as e:
                logging.warning(f"Label strategy failed for '{related_label_text}': {e}")
                # Fallback to direct input interaction
                input_locator.click(force=True)
                input_locator.press_sequentially(text, delay=100)
        else:
             # No label, use direct input interaction
             input_locator.click(force=True)
             input_locator.press_sequentially(text, delay=100)

        # Verify if text was entered (using the locator we have)
        if input_locator.input_value() != text:
             logging.warning(f"{label} typing failed, forcing value...")
             input_locator.evaluate(f"el => el.value = '{text}'")
             input_locator.evaluate("el => el.dispatchEvent(new Event('input', {bubbles: true}))")
             input_locator.type(" ") # Trigger key events
            
        # Wait for options
        try:
            # Wait longer for network/rendering
            page.wait_for_selector("[role='option']", state="visible", timeout=10000)
            
            # Click the first option explicitly with force
            option = page.locator("[role='option']").first
            option.click(force=True)
            logging.info(f"Selected option for {label}")
            return True
        except Exception as e:
            logging.warning(f"Dropdown options for {label} did not appear: {e}")
            # Last ditch effort: ArrowDown + Enter
            input_locator.press("ArrowDown")
            page.wait_for_timeout(200)
            page.keyboard.press("Enter")
            return False
            
    except Exception as e:
        logging.warning(f"Failed to interact with {label}: {e}")
        return False

def get_train_route(train_no, headless=True):
    """
    Launches browser, inputs train number and date, and scrapes the Boarding Station dropdown.
    Returns a list of dictionaries: [{'code': 'SBC', 'name': 'KSR BENGALURU', 'dist': 0}, ...]
    """
    station_list = []
    
    with sync_playwright() as p:
        logging.info(f"Launching browser for Route Discovery (Headless: {headless})...")
        browser, context = launch_browser(p, headless)
        page = context.new_page()

        try:
            # Relaxed wait condition to 'commit' to bypass WAF tarpitting
            page.goto("https://www.irctc.co.in/online-charts/", timeout=60000, wait_until="commit")
            
            try:
                page.wait_for_load_state("domcontentloaded", timeout=10000)
            except:
                pass
            
            # 1. Input Train Number
            try:
                train_input = page.locator("input[role='combobox']").first
                if not train_input.is_visible():
                     train_input = page.locator("input[aria-autocomplete='list']").first
                
                # Use helper with label click strategy
                if not interact_with_dropdown(page, train_input, train_no, "Train Number", related_label_text="Train Name/Number"):
                    logging.error("Failed to select train.")
                    return []
                
            except Exception as e:
                logging.warning(f"Train input interaction failed: {e}")
                return []
            
            page.wait_for_timeout(1000)

            # 2. Select Date (Required to populate Boarding Stations)
            try:
                logging.info("Selecting Date...")
                date_input = page.locator("input.jss466").first
                if not date_input.is_visible():
                     date_input = page.locator("input[placeholder*='Date']").first
                
                # Click to open calendar
                date_input.click(force=True)
                page.wait_for_timeout(500)
                
                # Just click the "Today" or first available day
                day_button = page.locator("button.MuiPickersDay-day").first
                if day_button.is_visible():
                    day_button.click(force=True)
                else:
                    page.keyboard.press("Enter")
                
                page.wait_for_timeout(500)
            except Exception as e:
                logging.warning(f"Date selection failed: {e}")

            page.wait_for_timeout(1000)

            # 3. Scrape Boarding Station Dropdown
            logging.info("Scraping Boarding Station dropdown...")
            try:
                # Find boarding input
                boarding_input = page.locator("input[aria-autocomplete='list']").nth(1)
                
                # Click to open dropdown
                try:
                    page.get_by_text("Boarding Station", exact=False).first.click(force=True)
                except:
                    boarding_input.click(force=True)
                
                page.wait_for_timeout(500)
                boarding_input.press("ArrowDown")
                
                # Wait for options
                page.wait_for_selector("[role='option']", state="visible", timeout=10000)
                
                # Get all options
                options = page.locator("[role='option']").all()
                logging.info(f"Found {len(options)} boarding stations.")
                
                for i, opt in enumerate(options):
                    text = opt.inner_text().strip()
                    # Format 1: "CODE - NAME"
                    if " - " in text:
                        parts = text.split(" - ", 1)
                        code = parts[0].strip()
                        name = parts[1].strip()
                    # Format 2: "NAME (CODE)" e.g. "HOWRAH JN (HWH)"
                    elif "(" in text and text.endswith(")"):
                        parts = text.split("(")
                        name = parts[0].strip()
                        code = parts[-1].replace(")", "").strip()
                    else:
                        code = text
                        name = text
                    
                    station_list.append({
                        "code": code,
                        "name": name,
                        "dist": i * 10 # Dummy distance
                    })
                    
            except Exception as e:
                logging.warning(f"Failed to scrape boarding stations: {e}")
                
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
            # Relaxed wait condition
            page.goto("https://www.irctc.co.in/online-charts/", timeout=60000, wait_until="commit")
            try:
                page.wait_for_load_state("domcontentloaded", timeout=10000)
            except:
                pass
            
            # --- Input Train ---
            try:
                train_input = page.locator("input[role='combobox']").first
                if not train_input.is_visible():
                     train_input = page.locator("input[aria-autocomplete='list']").first
                
                if not interact_with_dropdown(page, train_input, train_no, "Train Number", related_label_text="Train Name/Number"):
                    logging.error("Failed to select train.")
                    return []
            except Exception as e:
                logging.warning(f"Train input interaction failed: {e}")
                return []
            
            page.wait_for_timeout(1000)

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

            page.wait_for_timeout(1000)

            # --- Select Boarding Station ---
            logging.info(f"Selecting Boarding Station: {boarding_stn_code}")
            try:
                # Find boarding input (usually the second autocomplete input)
                boarding_input = page.locator("input[aria-autocomplete='list']").nth(1)
                
                if not interact_with_dropdown(page, boarding_input, boarding_stn_code, "Boarding Station", related_label_text="Boarding Station"):
                     logging.error(f"Failed to select boarding station {boarding_stn_code}")
                     return []
            except Exception as e:
                logging.warning(f"Boarding station selection failed: {e}")
                return []

            logging.info("Submitting...")
            try:
                # Force click to bypass any potential overlays
                get_chart_btn = page.locator("button:has-text('Get Train Chart')").first
                get_chart_btn.click(force=True)
                
                # Wait for URL change or error
                try:
                    page.wait_for_url(lambda url: "vacant-berth" in url or "traincomposition" in url, timeout=15000)
                except:
                    logging.warning("URL did not change, checking for errors...")
                    
                # Check for "No Charts Found" or similar errors
                if page.locator("text=Chart not prepared").is_visible():
                    logging.warning("Chart not prepared for this train/date.")
                    return []
            except Exception as e:
                logging.error(f"Failed to click Get Train Chart: {e}")
                return []
            
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
