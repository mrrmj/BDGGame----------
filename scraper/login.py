from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import time

def safe_find_click(driver, wait, by, locator, retries=3):
    for attempt in range(retries):
        try:
            element = wait.until(EC.element_to_be_clickable((by, locator)))

            # Scroll element into view to avoid overlays blocking the click
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)

            try:
                element.click()
                return True
            except ElementClickInterceptedException:
                # Try JS click if normal click is intercepted
                driver.execute_script("arguments[0].click();", element)
                return True

        except StaleElementReferenceException:
            if attempt == retries - 1:
                raise
            time.sleep(0.5)
    return False

def safe_find_send_keys(driver, wait, by, locator, keys, retries=3):
    for attempt in range(retries):
        try:
            element = wait.until(EC.presence_of_element_located((by, locator)))
            element.click()
            element.clear()
            element.send_keys(keys)
            return True
        except StaleElementReferenceException:
            if attempt == retries - 1:
                raise
            time.sleep(0.5)
    return False

def click_confirm_cookie(driver, wait):
    try:
        confirm_button = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='promptBtn']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='promptBtn']")))

        for _ in range(3):
            try:
                confirm_button.click()
                print("✅ Confirm button clicked")
                return True
            except ElementClickInterceptedException:
                print("⚠️ Click intercepted, retrying...")
                time.sleep(1)
        print("❌ Failed to click Confirm button after retries")
        return False

    except TimeoutException:
        print("ℹ️ Confirm button not found, assuming no popup")
        return False

def login_to_bdg(username, password):
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://bdggameapps.com/")

        # Step 1: Click the initial "Login" button
        safe_find_click(driver, wait, By.XPATH, "//button[text()='Login']")

        # NEW STEP: Wait for overlay (start-page) to disappear before clicking second login button
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "start-page")))

        # Step 2: Click second login button inside form
        safe_find_click(driver, wait, By.XPATH, "//button[@class='login']")

        # # Step 3: Wait for the URL to change away from bdginf.com
        # time.sleep(2)  # Optional: slight buffer
        # wait.until(lambda d: "bdginf.com/#/login" not in d.current_url)

        # # ❌ Check if still redirected to bdginf
        # if "bdginf.com/#/login" in driver.current_url:
        #     print(f"❌ Redirected to wrong URL: {driver.current_url}")
        #     driver.save_screenshot("wrong_url.png")
        #     driver.quit()
        #     return None

        # print(f"✅ On correct page: {driver.current_url}")
        # Step 3: Enter username
        safe_find_send_keys(driver, wait, By.XPATH, "//input[@name='userNumber']", username)

        # Step 4: Enter password
        safe_find_send_keys(driver, wait, By.XPATH, "(//input[@type='password'])[1]", password)

        # Step 5: Click the final login button
        safe_find_click(driver, wait, By.XPATH, "//button[@class='active']")

        # Step 6: Wait for login modal to disappear
        wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class,'login-modal')]")))

        print("✅ Login successful!")

        # Step 7: Click confirm cookie button if it appears
        click_confirm_cookie(driver, wait)

        # Step 8: Click on "Lottery"
        safe_find_click(driver, wait, By.XPATH, "//div[text()='Lottery']")
        print("✅ Clicked 'Lottery'")

        # Step 9: Scroll slightly to make next button visible
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(1)

        # Step 10: Click "Win Go 1Min"
        safe_find_click(driver, wait, By.XPATH, "//span[text()='Win Go 1Min']")
        print("✅ Clicked 'Win Go 1Min'")

        return driver

    except Exception as e:
        print(f"❌ Login failed: {e}")
        driver.save_screenshot("login_error.png")
        driver.quit()
        return None
