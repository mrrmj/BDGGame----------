from scraper.login import login_to_bdg
from scraper.scrape_data import scrape_game_history, monitor_results, save_verification_data
from model.train_model import train_model
from predict_next import get_last_prediction, verify_prediction
from utils.config import USERNAME, PASSWORD, DATA_FILE
import time
import sys
import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def ensure_directories():
    """Create required directories"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("model", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def initialize_data_collection(driver):
    """Collect initial data with improved retry logic"""
    print("\n🔍 Running initial data collection...")
    wait = WebDriverWait(driver, 30)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.van-row")))
    
    history_df = None
    attempt = 0
    max_attempts = 5
    min_records = 5  # Reduced minimum for initial testing
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\nAttempt {attempt}/{max_attempts}")
        
        try:
            temp_df = scrape_game_history(driver)
            if temp_df is not None and len(temp_df) > 0:
                if history_df is None:
                    history_df = temp_df
                else:
                    history_df = pd.concat([history_df, temp_df]).drop_duplicates()
                print(f"✓ Collected {len(temp_df)} records (Total: {len(history_df)})")
                
                if len(history_df) >= min_records:
                    break
        except Exception as e:
            print(f"⚠️ Collection error: {e}")
        
        time.sleep(5)
    
    if history_df is None or history_df.empty:
        raise Exception("Failed to collect initial data")
    
    # Save initial data
    history_df.to_csv(DATA_FILE, index=False)
    print(f"\n💾 Saved {len(history_df)} records to {DATA_FILE}")
    return history_df

def enhanced_monitoring(driver, interval=60):
    """Improved monitoring with prediction verification"""
    known_periods = set()
    if os.path.exists("data/known_periods.txt"):
        with open("data/known_periods.txt", "r") as f:
            known_periods = set(f.read().splitlines())

    try:
        print("\n👀 Starting enhanced monitoring...")
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Refresh periodically
            if len(known_periods) % 5 == 0:
                driver.refresh()
                time.sleep(3)
            
            # Scrape current results
            df = scrape_game_history(driver)
            if df is None or df.empty:
                print("⚠️ No data scraped, retrying...")
                time.sleep(interval)
                continue
            
            # Process new results
            new_results = df[~df['Period'].isin(known_periods)]
            if not new_results.empty:
                print(f"\n🆕 New Results @ {current_time}:")
                print(new_results[["Period", "Number", "Size", "Color"]])
                
                # Save new results
                save_path = "data/new_results.csv"
                header = not os.path.exists(save_path)
                new_results.to_csv(save_path, mode='a', header=header, index=False)
                
                # Verify predictions
                for _, result in new_results.iterrows():
                    last_pred = get_last_prediction()
                    actual = {
                        "Color": result["Color"],
                        "Number": result["Number"],
                        "Size": result["Size"]
                    }
                    
                    # Convert prediction to verification format
                    pred_str = f"{last_pred['color']}_{last_pred['size']}"
                    is_correct = verify_prediction(pred_str, actual)
                    
                    if is_correct:
                        print(f"✅ Prediction Verified! Period: {result['Period']}")
                    else:
                        print(f"⚠️ Prediction Failed! Period: {result['Period']}")
                    
                    # Save verification data
                    save_verification_data(last_pred, actual)
                
                # Update known periods
                known_periods.update(new_results['Period'])
                with open("data/known_periods.txt", "w") as f:
                    f.write("\n".join(known_periods))
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    finally:
        with open("data/known_periods.txt", "w") as f:
            f.write("\n".join(known_periods))

def main():
    print("🚀 Starting BDG Prediction System v2.0")
    ensure_directories()
    
    # Initialize driver
    driver = login_to_bdg(USERNAME, PASSWORD)
    if not driver:
        sys.exit(1)
    
    try:
        # Initial data collection
        history_df = initialize_data_collection(driver)
        
        # Train initial model
        print("\n🤖 Training initial model...")
        if not train_model(DATA_FILE):
            raise Exception("Initial model training failed")
        
        # Start monitoring
        input("\n🔐 Login confirmed. Press ENTER to start monitoring...")
        enhanced_monitoring(driver, interval=60)
            
    except Exception as e:
        print(f"❌ System error: {e}")
        driver.save_screenshot("logs/system_error.png")
    finally:
        driver.quit()
        print("✅ System shutdown complete")

if __name__ == "__main__":
    main()