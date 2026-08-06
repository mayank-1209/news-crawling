import asyncio
from bs4 import BeautifulSoup
# from charset_normalizer import detect
from langdetect import detect
# from langdetect import LangDetectException
from langdetect.lang_detect_exception import LangDetectException
from fastapi import FastAPI, BackgroundTasks, Depends
import requests
from sqlalchemy.orm import Session

from crawler import fetch_and_parse_sitemap, get_sitemap_from_robots, store_urls_in_db
from database import ContentLanguage, Language, SessionLocal, Domain, ScrapedURL, Content, Media
from parser import get_extractor_for_url
from rephraser import rephrase_markdown

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def detect_article_language(text: str) -> str:
    """Safely detects language code (e.g., 'en', 'hi'). Returns 'unknown' if it fails."""
    try:
        # Langdetect needs a minimum amount of text to be accurate
        if not text or len(text.strip()) < 10:
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"      

async def rephrase_articles_task(db: Session, batch_size: int, target_content_id: int = None):
    print(f"Starting rephrasing for articles...")
    
    # Fetch content that has NOT been rephrased yet
    if target_content_id:
        print(f"Starting rephrasing for specific Content ID: {target_content_id}...")
        pending_content = (
            db.query(Content)
            .filter(Content.id == target_content_id)
            .all()
        )
    elif batch_size is not None:
        print(f"Fetching a batch of up to {batch_size} articles for rephrasing...")
        pending_content = (
            db.query(Content)
            .filter(Content.is_rephrased == False)
            .filter(Content.body_text != "")
            .order_by(Content.id.desc())
            .limit(batch_size)
            .all()
        )
    else:
        print("No batch size or target content ID provided. Exiting rephrasing task.")
        return
            
    if not pending_content:
        print("No articles pending rephrasing.")
        return

    print("Sending articles to Ollama concurrently...")
    tasks = [
        rephrase_markdown(article.body_text) 
        for article in pending_content
    ]

    results = await asyncio.gather(*tasks)

    for article, new_markdown in zip(pending_content, results):
        if new_markdown:
            article.rephrased_text = new_markdown
            article.is_rephrased = True
            print(f"Successfully rephrased article ID: {article.id}")
        else:
            print(f"Failed to rephrase article ID: {article.id}")
            
    # 5. Commit all changes to the database at once
    db.commit()
    print("Concurrent batch processing complete!")

   
    # new_markdown = rephrase_markdown(text)
    # print(new_markdown)
        
        
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


def scrape_articles_task(db: Session,  batch_size: int, url=None):
    if batch_size:
        print(f"Starting content extraction for {batch_size} articles...")   
        pending_urls = db.query(ScrapedURL).filter(ScrapedURL.is_scraped == False).order_by(ScrapedURL.id.desc()).limit(batch_size).all() 
    elif url:
        print(f"Starting content extraction for {url} ...")  
        pending_urls = db.query(ScrapedURL).filter(ScrapedURL.url == url).all()  
    else:
        print("Neither url nor batch_size provided")
        return    

    # print(f"path  {pending_urls} ")    

    if not pending_urls:
        print("No pending URLs found in the database.")
        return

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for item in pending_urls:
        try:
            response = requests.get(item.url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Skipping {item.url} - Status Code: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')

            extractor_func = get_extractor_for_url(item.url)
            scraped_data = extractor_func(soup)

            title = scraped_data["title"]
            image = scraped_data["image"]
            content = scraped_data["content"]

            # --- 1. Save Content ---
            new_content = Content(
                url_id=item.id, 
                title=title[:500], 
                body_description=content[:600],
                body_text=content
            )

            print(f"new-content   {new_content}")
            db.add(new_content)
            db.commit()
            db.refresh(new_content) 

            print("-------------------------------------------")

            # --- 2. Save Media ---

            print(f"image---------------- {image}")
            if image:
                new_media = Media(
                    content_id=new_content.id,
                    media_url=image,
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
            print(f"Failed to scrape {item.url}: {e}")
            db.rollback()



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
    batch_size: int = 10, 
    url: str = None, 
    db: Session = Depends(get_db)
):
    background_tasks.add_task(scrape_articles_task, db, batch_size, url)
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


@app.post("/rephrase-content/")
async def trigger_batch_rephrasing(
    background_tasks: BackgroundTasks, 
    content_id: int = None,
    batch_size: int = 5, 
    db: Session = Depends(get_db)
):
    """
    Rephrases a batch of un-rephrased articles.
    Example: POST /rephrase-content/batch/?batch_size=10
    """
    background_tasks.add_task(rephrase_articles_task, db, batch_size, content_id)
    
    return {
        "message": f"Started background task to rephrase up to {batch_size} articles.",
        "status": "Accepted"
    }


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