import asyncio
from bs4 import BeautifulSoup
# from charset_normalizer import detect
from langdetect import detect
# from langdetect import LangDetectException
from langdetect.lang_detect_exception import LangDetectException
from fastapi import FastAPI, BackgroundTasks, Depends
import requests
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
from crawler import fetch_and_parse_sitemap, get_sitemap_from_robots, store_urls_in_db
from database import ContentLanguage, Language, SessionLocal, Domain, ScrapedURL, Content, Media
from parser import get_extractor_for_url
# from rephraser import rephrase_markdown
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from downloader import download_media_to_server


app = FastAPI()
# Initialize the scheduler
scheduler = AsyncIOScheduler()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def scrape_with_selenium(url: str, device: str = "mobile") -> str:
    """Scrape a JS-rendered webpage using Selenium."""

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
    except Exception:
        print("Selenium is not installed or available.")
        return None

    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if device == "mobile":
        options.add_experimental_option(
            "mobileEmulation",
            {
                "deviceName": "iPhone 14 Pro"
            }
        )
    else:
        options.add_argument("--window-size=1843,1342")
    options.add_argument(
    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
    )

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        print(f"Opening URL: {url}")
        driver.get(url)

        print(f"Waiting for page to load: {url}")

        # Wait until browser finishes loading
        WebDriverWait(driver, 2000000).until(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

        # Give React/Next.js time to hydrate/render
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return document.body.innerText.length > 100"
            )
        )
        import time
        time.sleep(10)

        driver.find_element(By.ID, "username").send_keys("9889076306")
        driver.find_element(By.ID, "password").send_keys("12345qwertyuiop@#$")
        driver.find_element(By.XPATH,"//button[@type='submit']").click()

        print("login successful!")

        # #Find and click the button
        # button = WebDriverWait(driver, 20).until(
        #     EC.element_to_be_clickable(
        #         (By.XPATH, "//button[@data-qa-id='call_button']")
        #     )
        # )

        # print("Button found!")

        # driver.execute_script(
        # "arguments[0].scrollIntoView({block: 'center'});",
        # button
        # )

        # button.click()
        # print("Button clicked!")

        # Small additional wait for API/React rendering
        # import time
        time.sleep(30)

        html = driver.page_source
        print(f"Page loaded successfully: {url}")

        return html

    except Exception as e:
        print(f"Selenium fallback failed for {url}: {e}")
        return None

    finally:
        if driver:
            driver.quit()


def selenium_scrape_articles_task(db: Session, url: str = None):
    print(f"Starting Selenium scraping for {url}...")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        html = scrape_with_selenium(url)
        # print(f"html-------------------------------------------{html}") 


        # response = requests.get(url, headers=headers, timeout=10)
        # print(f"response.status_code--------------------{response.status_code}")
        # if response.status_code != 200:
        #     print(f"Skipping {url} - Status Code: {response.status_code}")
        #     html = scrape_with_selenium(url)
        #     if not html:
        #         print(f"Selenium failed for {url}")
        # else:
        #     html = response.content 

        # if not html:
        #     print(f"Selenium scraping failed for {url}.")
        #     return

        # soup = BeautifulSoup(html, "html.parser")

        # print(f"SOUP-------------------------------------------{soup}")
        # extractor_func = get_extractor_for_url(url)
        # scraped_data = extractor_func(soup)
        # print(f"scraped_data-------------------------------------------{scraped_data}")

        # if not scraped_data:
        #     print(f"No data extracted from {url}")
        #     return

        # # print(f"SCRAPED DATA-------------------------------------------{scraped_data}")

        # title = scraped_data.get("title")
        # image = scraped_data.get("image")
        # content = scraped_data.get("content")

        # print(f"title--------------------{title}")
        # print(f"content------------------{content}")
        # print(f"image---------------------{image}")

        # if not title:
        #     print("WARNING: Title is empty")
        # if not content:
        #     print("WARNING: Content is empty")
        # if not image:
        #     print("WARNING: Image is empty")

        # Save to database here
        # existing_content = db.query(Content).filter(Content.url_id == url).first()

        # if existing_content: 
        #     print(f"Content already exists for url_id={url}. Updating...") 
        #     existing_content.title = title[:500] 
        #     existing_content.body_description = content[:300] 
        #     existing_content.body_text = content 
        # else: 
        #     print(f"Creating new Content for url_id={url}.") 
        #     new_content = Content( 
        #         url_id=url, 
        #         title=title[:500], 
        #         body_description=content[:300], 
        #         body_text=content 
        #     ) 
        #     db.add(new_content) 
        #     db.commit() 
        #     print(f"Successfully saved content for {url}.")

    except Exception as e:
        db.rollback()
        print(
            f"Failed to scrape {url} with Selenium: {e}"
        )
    


#-------------------------------------------------------------------------------
#                      LANGUAGE DETECTION
#-------------------------------------------------------------------------------
def detect_article_language(text: str) -> str:
    """Safely detects language code (e.g., 'en', 'hi'). Returns 'unknown' if it fails."""
    try:
        # Langdetect needs a minimum amount of text to be accurate
        if not text or len(text.strip()) < 10:
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"      


#-------------------------------------------------------------------------------
#                      APSCHEDULER SCRAP CONTENT
#-------------------------------------------------------------------------------

def scheduled_scrape_job():
    """Wrapper to handle the DB session for scheduled scraping."""
    print("Executing scheduled scrape job...")
    db = SessionLocal()
    try:
        # Run your existing synchronous scraping function
        # scrape_articles_task(db, batch_size=1)
        return
    except Exception as e:
        print(f"Scheduled scrape failed: {e}")
    finally:
        db.close()

#-------------------------------------------------------------------------------
#                      APSCHEDULER SCRAP REPHRASE CONTENT
#-------------------------------------------------------------------------------

# async def scheduled_rephrase_job():
#     """Wrapper to handle the DB session for scheduled async rephrasing."""
#     print("Executing scheduled rephrase job...")
#     db = SessionLocal()
#     try:
#         # Run your existing async rephrasing function
#         await rephrase_articles_task(db, batch_size=1)
#     except Exception as e:
#         print(f"Scheduled rephrase failed: {e}")
#     finally:
#         db.close()


#-------------------------------------------------------------------------------
#                      SCRAP REPHRASE CONTENT
#-------------------------------------------------------------------------------

# async def rephrase_articles_task(db: Session, batch_size: int, target_content_id: int = None):
#     print(f"Starting rephrasing for articles...")
    
#     # Fetch content that has NOT been rephrased yet
#     if target_content_id:
#         print(f"Starting rephrasing for specific Content ID: {target_content_id}...")
#         pending_content = (
#             db.query(Content)
#             .filter(Content.id == target_content_id)
#             .all()
#         )
#     elif batch_size is not None:
#         print(f"Fetching a batch of up to {batch_size} articles for rephrasing...")
#         pending_content = (
#             db.query(Content)
#             .filter(Content.is_rephrased == False)
#             .filter(Content.body_text != "")
#             .order_by(Content.id.desc())
#             .limit(batch_size)
#             .all()
#         )
#     else:
#         print("No batch size or target content ID provided. Exiting rephrasing task.")
#         return
            
#     if not pending_content:
#         print("No articles pending rephrasing.")
#         return

#     print("Sending articles to Ollama concurrently...")
#     tasks = [
#         rephrase_markdown(article.body_text) 
#         for article in pending_content
#     ]

#     results = await asyncio.gather(*tasks)

#     for article, new_markdown in zip(pending_content, results):
#         if new_markdown:
#             article.rephrased_text = new_markdown
#             article.is_rephrased = True
#             print(f"Successfully rephrased article ID: {article.id}")
#         else:
#             print(f"Failed to rephrase article ID: {article.id}")
            
#     # 5. Commit all changes to the database at once
#     db.commit()
#     print("Concurrent batch processing complete!")

   
    # new_markdown = rephrase_markdown(text)
    # print(new_markdown)
        
#-------------------------------------------------------------------------------
#                      WEBSITE DOMAIN EXTRACT SITE-MAPS URL
#-------------------------------------------------------------------------------
        
def crawl_website_task(domain: str, db: Session):
    print(f"Starting crawl for {domain}...")
    
    sitemaps = get_sitemap_from_robots(domain)
    
    for sitemap_url in sitemaps:
        print(f"Parsing sitemap: {sitemap_url}")
        extracted_urls = fetch_and_parse_sitemap(sitemap_url)
        if extracted_urls:
            store_urls_in_db(db, domain, extracted_urls)
            print(f"Stored {len(extracted_urls)} URLs from {sitemap_url}")

    # Manually added sitemaps
    # sitemap_url_manually = [
    #     "https://www.aajtak.in/rssfeeds/news-sitemap.xml",
       # "https://www.news18.com/commonfeeds/v1/eng/sitemap/google-news.xml",
        #"https://www.news18.com/commonfeeds/v1/eng/sitemap/google-news/today.xml",
       # "https://www.news18.com/commonfeeds/v1/eng/sitemap/google-news/yesterday.xml",
      #  "https://hindi.news18.com/allstory-sitemap-data.xml",
      #  "https://hindi.news18.com/commonfeeds/v1/hin/sitemap/google-news/yesterday.xml",
       # "https://hindi.news18.com/commonfeeds/v1/hin/sitemap/google-news/today.xml"
    # ]
    
    # for site_map_man in sitemap_url_manually:
    #     print(f"Parsing manually added sitemap: {site_map_man}")
    #     extracted_urls = fetch_and_parse_sitemap(site_map_man)
    #     if extracted_urls:
    #         store_urls_in_db(db, domain, extracted_urls)
    #         print(f"Stored {len(extracted_urls)} URLs from {site_map_man}")


#-------------------------------------------------------------------------------
#                         SCRAP CONTENT
#-------------------------------------------------------------------------------

def scrape_articles_task(db: Session,  batch_size: int, url=None):
    import random

    if batch_size:
        print(f"Starting content extraction for " f"{batch_size} articles...")

        pending_count = (
            db.query(ScrapedURL)
            .filter(
                ScrapedURL.is_scraped == False
            )
            .count()
        )

        if pending_count == 0:
            print("No pending URLs available.")
            return

        if pending_count > batch_size:
            random_offset = random.randint(
                0,
                pending_count - batch_size
            )
        else:
            random_offset = 0

        print(f"Pending URLs: {pending_count}")
        print(f"Random offset: {random_offset}")

        pending_urls = (
            db.query(ScrapedURL)
            .filter(
                ScrapedURL.is_scraped == False
            )
            .order_by(
                ScrapedURL.id.desc()
            )
            .offset(random_offset)
            .limit(batch_size)
            .all()
        )

    elif url:

        print(f"Starting content extraction for {url} ...")

        pending_urls = (
            db.query(ScrapedURL)
            .filter(
                ScrapedURL.url == url
            )
            .all()
        )

        # ---------------------------------------------
        # URL not found -> fallback to random URL
        # ---------------------------------------------

        if not pending_urls:

            print(f"URL not found: {url}")
            print("Picking a random pending URL instead...")

            pending_count = (
                db.query(ScrapedURL)
                .filter(
                    ScrapedURL.is_scraped == False
                )
                .count()
            )

            if pending_count == 0:
                print("No pending URLs available.")
                return

            random_offset = random.randint(
                0,
                pending_count - 1
            )

            pending_urls = (
                db.query(ScrapedURL)
                .filter(
                    ScrapedURL.is_scraped == False
                )
                .order_by(
                    ScrapedURL.id.desc()
                )
                .offset(random_offset)
                .limit(1)
                .all()
            )

    else:

        # ---------------------------------------------
        # No batch_size AND no URL
        # -> Pick one random pending URL
        # ---------------------------------------------

        print("Neither url nor batch_size provided.")
        print("Picking a random pending URL...")

        pending_count = (
            db.query(ScrapedURL)
            .filter(
                ScrapedURL.is_scraped == False
            )
            .count()
        )

        if pending_count == 0:
            print("No pending URLs available.")
            return

        random_offset = random.randint(
            0,
            pending_count - 1
        )

        print(f"Random offset: {random_offset}")

        pending_urls = (
            db.query(ScrapedURL)
            .filter(
                ScrapedURL.is_scraped == False
            )
            .order_by(
                ScrapedURL.id.desc()
            )
            .offset(random_offset)
            .limit(1)
            .all()
        )   

    if not pending_urls:
        print("No pending URLs found in the database.")
        return

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
 
    for item in pending_urls:
        try:
            response = requests.get(item.url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Skipping {item.url} - Status Code: {response.status_code}")
                html = scrape_with_selenium(item.url)
                if not html:
                    print(f"Selenium failed for {item.url}")
                    continue
            else:
                html = response.content 

            soup = BeautifulSoup(html, 'html.parser')

            extractor_func = get_extractor_for_url(item.url)
            scraped_data = extractor_func(soup)

            title = scraped_data["title"]
            image = scraped_data["image"]
            content = scraped_data["content"] 

#-------------------------------------------------------------------------------
#          use MySQL UPSERT---- duplicate → update
#-------------------------------------------------------------------------------            

            # stmt = insert(Content).values(
            # url_id=item.id,
            # title=title[:500],
            # body_description=content[:600],
            # body_text=content,
            # rephrased_text=None,
            # is_rephrased=False,
            # )

            # stmt = stmt.on_duplicate_key_update(
            # title=stmt.inserted.title,
            # body_description=stmt.inserted.body_description,
            # body_text=stmt.inserted.body_text,
            # )

            # db.execute(stmt)
            # db.flush()
#-------------------------------------------------------------------------------
#          application-level safeguard.---- duplicate → update
#-------------------------------------------------------------------------------
            
            
            existing_content = (
                db.query(Content) .filter(Content.url_id == item.id).first())

            if existing_content:
                print(f"Content already exists for url_id={item.id}")

                new_content = existing_content

                # Update existing content
                new_content.title = title[:500]
                new_content.body_description = content[:300]
                new_content.body_text = content

            else:

                print(f"Creating new Content for url_id={item.id}")

                new_content = Content(
                    url_id=item.id,
                    title=title[:500],
                    body_description=content[:300],
                    body_text=content
                )

                db.add(new_content)

            # Get content.id without committing
            db.flush()

            print(f"content id: {new_content.id}")
            print("-------------------------------------------")

            # --- 2. Save Media ---

            # --- NEW: Download the image to your server ---
            local_image_path = ""
            if image:
                print(f"Downloading image: {image}")
                local_image_path = download_media_to_server(image)
                print(f"local_image_path-------------------{local_image_path}")

            print(f"image---------------- {image}")
            if local_image_path:
                new_media = Media(
                    content_id=new_content.id,
                    media_url=local_image_path, # e.g., "static/media/123-uuid.jpg"
                    base_url=image,  
                )
                
            print(f"new-media --------------{ new_media}")    
            db.add(new_media)
            db.commit()
            db.refresh(new_media) 
            
            # --- 3. Detect & Save Language ---
            # Fall back to title if the body content is missing
            text_to_analyze = content if content else title

            # print(f"text_to_analyze------------------------{text_to_analyze}")
            lang_code = detect_article_language(text_to_analyze)

            print(f"lang_code------------------{lang_code}")

            if lang_code != 'unknown':
                language_record = db.query(Language).filter(Language.code == lang_code).first()
                
            if not language_record:
                language_record = Language(
                    code=lang_code, 
                    name=lang_code.upper() 
                )

            print(f"language_record---------------------------{language_record}")    
            db.add(language_record)
            db.commit()
            db.refresh(language_record)
                
                # Link the Content to the Language
            content_lang = ContentLanguage(
                content_id=new_content.id,
                language_id=language_record.id
            )
            print(f"content_lang-------------------------{content_lang}")
            db.add(content_lang)

            # --- 4. Mark URL as scraped ---
            item.is_scraped = True
            db.commit()
            
            print(f"Successfully saved: {title[:50]}... [Language: {lang_code}]")
            
        except Exception as e:
            db.rollback()
            item.is_scraped = True
            print(f"Failed to scrape {item.url}: {e}")
            


#-------------------------------------------------------------------------------
#                               APSCHEDULER 
#-------------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("Starting up APScheduler...")
    
    # Schedule the scraper to run every 15 minutes
    # scheduler.add_job(
    #     scheduled_scrape_job, 
    #     'interval', 
    #     seconds=5, 
    #     id="scrape_job", 
    #     replace_existing=True,
    #     max_instances=1,
    #     coalesce=True,
    # )
    
    # Schedule the AI rephraser to run every 30 minutes
    # scheduler.add_job(
    #     scheduled_rephrase_job, 
    #     'interval', 
    #     minutes=30, 
    #     id="rephrase_job", 
    #     replace_existing=True
    # )
    
    # scheduler.start()
    
    # Yield control back to FastAPI so it can accept API requests
    yield
    
    # --- SHUTDOWN LOGIC ---
    print("Shutting down APScheduler...")
    scheduler.shutdown()

# Apply the lifespan to your FastAPI app instance
app = FastAPI(lifespan=lifespan)



#-------------------------------------------------------------------------------
#                               FASTAPI ENDPOINTS
#-------------------------------------------------------------------------------

@app.post("/crawl/")
async def start_crawl(domain: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    domain = domain.rstrip('/')
    background_tasks.add_task(crawl_website_task, domain, db)
    return {
        "message": f"Crawling started in the background for {domain}",
        "status": "Accepted"
    }


@app.get("/urls/")
def get_crawled_urls(domain: str = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(ScrapedURL)
    
    if domain:
        query = query.join(Domain).filter(Domain.base_url == domain.rstrip('/'))
    
    results = query.limit(limit).all()
    return {"count": len(results), "urls": [r.url for r in results]}


@app.post("/scrape-content/")
async def trigger_content_scraping(
    background_tasks: BackgroundTasks,
    batch_size: int = None, 
    url: str = None, 
    db: Session = Depends(get_db)
):
    background_tasks.add_task(scrape_articles_task, db, batch_size, url)
    return {
        "message": f"Started background task to scrape up to {url} articles.",
        "status": "Accepted"
    }

@app.post("/selenium-scrape-content/")
async def selenium_trigger_content_scraping(
    background_tasks: BackgroundTasks,
    # batch_size: int = None, 
    url: str = None, 
    db: Session = Depends(get_db)
):
    background_tasks.add_task(selenium_scrape_articles_task, db, url)
    return {
        "message": f"Started background task to scrape up to {url} articles.",
        "status": "Accepted"
    }


# @app.post("/scrape-content/batch/")
# async def trigger_content_scraping(
#     background_tasks: BackgroundTasks, 
#     batch_size: int = None, 
#     db: Session = Depends(get_db)
# ):
#     background_tasks.add_task(scrape_articles_task, db, batch_size)
#     return {
#         "message": f"Started background task to scrape up to {batch_size} articles.",
#         "status": "Accepted"
#     }


# @app.post("/rephrase-content/url/")
# async def trigger_url_rephrasing(
#     background_tasks: BackgroundTasks, 
#     text: str, 
#     db: Session = Depends(get_db)
# ):
#     """Triggers the AI to rewrite scraped articles."""
#     background_tasks.add_task(rephrase_articles_task, db, text)
    
#     return {
#         "message": f"Started background task to rephrase up to articles.",
#         "status": "Accepted"
#     }    


# @app.post("/rephrase-content/")
# async def trigger_batch_rephrasing(
#     background_tasks: BackgroundTasks, 
#     content_id: int = None,
#     batch_size: int = 5, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Rephrases a batch of un-rephrased articles.
#     Example: POST /rephrase-content/batch/?batch_size=10
#     """
#     background_tasks.add_task(rephrase_articles_task, db, batch_size, content_id)
    
#     return {
#         "message": f"Started background task to rephrase up to {batch_size} articles.",
#         "status": "Accepted"
#     }


# @app.post("/rephrase-content/single/")
# async def trigger_single_rephrasing(
#     content_id: int, 
#     background_tasks: BackgroundTasks, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Rephrases one specific article by its Content ID.
#     Example: POST /rephrase-content/single/?content_id=12
#     """
#     background_tasks.add_task(rephrase_articles_task, db, batch_size=None, target_content_id=content_id)
    
#     return {
#         "message": f"Started background task to rephrase Content ID: {content_id}.",
#         "status": "Accepted"
#     }