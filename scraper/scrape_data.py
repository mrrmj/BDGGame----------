from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime
import os
import csv

def rgba_to_color_name(rgba):
    """Convert RGBA to standardized color names with validation"""
    if not rgba or not isinstance(rgba, str):
        return "Unknown"
    
    rgba = rgba.lower().replace(" ", "")
    
    # Modern color mapping (update these with actual site values)
    color_map = {
        "rgba(255,0,0,": "Red",
        "rgba(0,128,0,": "Green",
        "rgba(148,0,211,": "Violet",
        "rgba(0,0,255,": "Blue",
        "rgba(255,255,0,": "Yellow"
    }
    
    for pattern, color in color_map.items():
        if rgba.startswith(pattern):
            return color
    return "Unknown"

def scrape_game_history(driver):
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.record")))

        data = []
        rows = driver.find_elements(By.CSS_SELECTOR, "div.van-row")
        print(f"🎯 Found {len(rows)} records")

        for row in rows:
            try:
                period = row.find_element(By.CSS_SELECTOR, "div.van-col.van-col--10").text.strip()

                # ✅ Fallback logic for number
                number = None
                try:
                    number = row.find_element(By.CSS_SELECTOR, "div.van-col.van-col--5.numcenter").text.strip()
                except:
                    five_cols = row.find_elements(By.CSS_SELECTOR, "div.van-col.van-col--5")
                    if five_cols:
                        number = five_cols[0].text.strip()
                if number is None:
                    raise ValueError("Number not found in row")

                # Size detection
                cols = row.find_elements(By.CSS_SELECTOR, "div.van-col.van-col--5")
                size = None
                for col in cols:
                    text = col.text.strip()
                    if "Big" in text:
                        size = "Big"
                        break
                    elif "Small" in text:
                        size = "Small"
                        break
                if size is None:
                    raise ValueError("Size not found in row")

                # Color detection with improved handling
                color_element = row.find_element(By.CSS_SELECTOR, "div.van-col.van-col--4")
                color_style = color_element.value_of_css_property("background-color")

                # Skip ONLY if completely transparent AND no color-indicating text
                if color_style.strip().lower() == "rgba(0, 0, 0, 0)":
                    try:
                        # Fallback to text color if background is transparent
                        color_text = color_element.text.strip()
                        if color_text in ["Red", "Green", "Violet", "Blue", "Yellow"]:
                            color = color_text
                        else:
                            raise ValueError("Transparent with no color text")
                    except:
                        raise ValueError("Skipping row with transparent color")
                else:
                    color = rgba_to_color_name(color_style)

                data.append([period, number, size, color])

            except Exception as e:
                print(f"⚠️ Skipping malformed row: {e}")
                continue

        return pd.DataFrame(data, columns=["Period", "Number", "Size", "Color"])

    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        driver.save_screenshot("scrape_error.png")
        return None

def monitor_results(driver, interval=60, max_retries=3):
    known_periods = set()
    retry_count = 0

    if os.path.exists("data/known_periods.txt"):
        with open("data/known_periods.txt", "r") as f:
            known_periods = set(f.read().splitlines())

    try:
        print(f"\n🔍 Starting monitoring (checking every {interval}s)...")
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if retry_count % 5 == 0:
                driver.refresh()
                time.sleep(3)

            df = scrape_game_history(driver)

            if df is None or df.empty:
                retry_count += 1
                if retry_count >= max_retries:
                    print("❌ Max retries reached, refreshing...")
                    driver.refresh()
                    time.sleep(5)
                    retry_count = 0
                continue

            retry_count = 0

            new_results = df[~df['Period'].isin(known_periods)]

            if not new_results.empty:
                print(f"\n🆕 New Results @ {current_time}:")
                print(new_results[["Period", "Number", "Size", "Color"]])

                save_path = "data/new_results.csv"
                header = not os.path.exists(save_path)
                new_results.to_csv(save_path, mode='a', header=header, index=False)

                known_periods.update(new_results['Period'])
                with open("data/known_periods.txt", "w") as f:
                    f.write("\n".join(known_periods))
            else:
                print(f"⏳ No new results @ {current_time}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Monitoring error: {e}")
    finally:
        with open("data/known_periods.txt", "w") as f:
            f.write("\n".join(known_periods))

def save_verification_data(prediction, actual):
    """Store prediction vs actual for analysis"""
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Write header if file doesn't exist
        file_exists = os.path.exists("data/verification.csv")
        
        with open("data/verification.csv", "a", newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Prediction", "Actual"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prediction, actual])
        print("✅ Verification data saved successfully")
    except Exception as e:
        print(f"❌ Error saving verification data: {e}")

if __name__ == "__main__":
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # uncomment to run headless
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://bdggameapps.com/")  # 🔁 Replace with actual login URL

    input("🔐 Login manually and press ENTER to start monitoring...")

    monitor_results(driver, interval=60)