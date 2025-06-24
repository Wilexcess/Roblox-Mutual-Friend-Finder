# Roblox Mutuals Finder
# A simple script to find mutual friends between 2 or more Roblox users.
# By: Wilexcess

import time
import os
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import webdriver_manager and services
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

COOKIE_FILE = "cookie.txt"

# --- Browser Detection Functions (Windows-focused) ---

def is_edge_installed():
    """Checks for Microsoft Edge in common installation directories."""
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    return any(os.path.exists(path) for path in possible_paths)

def is_chrome_installed():
    """Checks for Google Chrome in common installation directories."""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    return any(os.path.exists(path) for path in possible_paths)

def is_firefox_installed():
    """Checks for Mozilla Firefox in common installation directories."""
    possible_paths = [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ]
    return any(os.path.exists(path) for path in possible_paths)

def initialize_driver():
    """Initializes a webdriver by detecting installed browsers and managing drivers."""
    print("Detecting installed browsers...")

    if is_edge_installed():
        print("Microsoft Edge detected. Setting up webdriver...")
        from selenium.webdriver.edge.options import Options as EdgeOptions
        options = EdgeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=options)

    elif is_chrome_installed():
        print("Google Chrome detected. Setting up webdriver...")
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    elif is_firefox_installed():
        print("Mozilla Firefox detected. Setting up webdriver...")
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        options = FirefoxOptions()
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)
    
    # No supported browser found.
    return None

# --- Core Script Functions ---

def get_id_from_url(url):
    try:
        return url.split('/users/')[1].split('/')[0]
    except IndexError:
        return "Unknown_ID"

def login_with_cookie(driver):
    print("Found cookie.txt, trying to log in...")
    with open(COOKIE_FILE, "r") as f:
        cookie_value = f.read().strip()
    
    driver.get("https://www.roblox.com/home")
    time.sleep(1)

    driver.add_cookie({
        'name': '.ROBLOSECURITY',
        'value': cookie_value,
        'domain': '.roblox.com'
    })
    
    driver.refresh()
    print("Cookie loaded, refreshing to log in.")
    time.sleep(3)

def handle_manual_login(driver):
    driver.get("https://www.roblox.com/login")
    input("--> Please log in to Roblox in the browser, then press Enter here to continue...")
    
    roblo_cookie = driver.get_cookie(".ROBLOSECURITY")
    
    if roblo_cookie:
        print("Login cookie found! Saving to cookie.txt for next time.")
        with open(COOKIE_FILE, "w") as f:
            f.write(roblo_cookie['value'])
        return True
    else:
        print("Login cookie not found. Make sure you logged in correctly.")
        return False

def get_user_friends(url, driver):
    user_id = get_id_from_url(url)
    print(f"\n[+] Scraping friends for User: {user_id}")
    
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.avatar-cards")))
        print("   Friend list container loaded.")
    except TimeoutException:
        print(f"Error: Page for user {user_id} timed out or no friends were loaded.")
        if "Log In" in driver.page_source:
             print("   (Login likely failed. Try deleting cookie.txt and restarting.)")
        else:
             print("   (Profile might be private, have no friends, or the URL is wrong.)")
        return None

    friends = set()
    page = 1
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.select('li.list-item.avatar-card')
        
        if not cards and page == 1:
            print(f"   No friend cards found on page for user {user_id}.")
            break

        new_friends_on_page = 0
        for card in cards:
            username_tag = card.find('div', class_='avatar-card-label', string=lambda t: t and t.strip().startswith('@'))
            if username_tag:
                username = username_tag.get_text(strip=True)[1:]
                if username not in {"AccountDeleted"} | friends:
                    friends.add(username)
                    new_friends_on_page += 1
        
        print(f"   Page {page}: Added {new_friends_on_page} friends. (Total: {len(friends)})")

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.btn-generic-right-sm:not([disabled])")
            driver.execute_script("arguments[0].click();", next_button)
            page += 1
        except NoSuchElementException:
            break
            
    print(f"   Finished with User {user_id}. Found {len(friends)} total friends.")
    return friends

def get_user_count():
    while True:
        try:
            num = int(input("\nHow many users to compare? (2+): "))
            if num >= 2: return num
            else: print("   Please enter at least 2.")
        except ValueError:
            print("   That's not a valid number.")

def main():
    print("--- Roblox Mutual Friend Finder ---")

    driver = initialize_driver()
    if not driver:
        print("\nERROR: No supported browser found (Edge, Chrome, or Firefox). Please install one to continue.")
        return

    try:
        driver.set_window_size(1200, 800)
        
        if os.path.exists(COOKIE_FILE):
            login_with_cookie(driver)
        else:
            if not handle_manual_login(driver):
                return
        
        num_users = get_user_count()
        urls = [input(f"URL for user #{i + 1}: ").strip() for i in range(num_users)]
        
        user_ids_str = " ".join([f"({get_id_from_url(url)})" for url in urls])

        friend_lists = []
        for url in urls:
            scraped_friends = get_user_friends(url, driver)
            if scraped_friends is None:
                print("\nAborting due to a scraping error.")
                return
            friend_lists.append(scraped_friends)
        
        print("\nCalculating mutuals...")
        mutuals = friend_lists[0].intersection(*friend_lists[1:])
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"mutuals_{timestamp}.txt"

        print("\n--- RESULTS ---")
        if mutuals:
            sorted_mutuals = sorted(list(mutuals))
            print(f"Found {len(sorted_mutuals)} mutuals among all {num_users} users.")
            
            with open(output_filename, "w") as f:
                f.write(f"Mutuals among {num_users} users {user_ids_str} on {timestamp}:\n")
                f.write("=" * 50 + "\n")
                for friend in sorted_mutuals:
                    print(f"- @{friend}")
                    f.write(f"@{friend}\n")
            print(f"\n[+] Results saved to: {output_filename}")
        else:
            print(f"No mutual friends found among all {num_users} users.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if driver:
            driver.quit()
        print("\nScript finished.")

if __name__ == "__main__":
    main()
