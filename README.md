# Longest Vacant Seat Finder

A Python tool to find the longest vacant seat segment on Indian Railways trains using Playwright and Pandas.

## Prerequisites

1.  **Python 3.7+** installed.
2.  **Chrome/Chromium** browser installed.

## Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Install Playwright browsers:
    ```bash
    playwright install
    ```

## Usage

1.  Open `vacancy_finder.py` and update the `TRAIN_NO` and `JOURNEY_DATE` variables at the top of the `main()` function.
2.  Run the script:
    ```bash
    python vacancy_finder.py
    ```

## Notes

-   **Robustness**: The script now uses API interception to fetch accurate vacancy data directly from the server, making it much more reliable than DOM scraping.
-   **Date Selection**: Includes a robust multi-strategy date picker that handles read-only inputs and dynamic calendars.
-   **Debugging**: Detailed logs are saved to `last_run.log`, and error screenshots are captured as `error_screenshot.png`.
