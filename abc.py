# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# import time

# def scrape_with_selenium(url: str) -> str:
#     """Spins up a headless browser as a fallback to extract raw HTML."""
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

#     driver = webdriver.Chrome(options=options)

#     try:
#         driver.get(url)
#         time.sleep(4) 
        
#         return driver.page_source
#     except Exception as e:
#         print(f"Selenium fallback failed for {url}: {e}")
#         return ""
#     finally:
#         driver.quit()