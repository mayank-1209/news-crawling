import requests
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import gzip

from database import Domain, ScrapedURL

def get_sitemap_from_robots(domain: str) -> list[str]:
    """Finds sitemap URLs from the robots.txt of a given domain."""
    robots_url = f"{domain}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    
    try:
        rp.read()
        sitemaps = rp.site_maps() 
        print(f"sitemaps: {sitemaps}")
        
        if sitemaps:
            filtered_sitemaps = [
                url for url in sitemaps
                if "video" not in url.lower() and "visualstories" not in url.lower() and "webstories" not in url.lower()
            ]
            if filtered_sitemaps:
                return filtered_sitemaps
    except Exception as e:
        print(f"Error reading robots.txt for {domain}: {e}")
        return [f"{domain}/sitemap.xml"]


def fetch_and_parse_sitemap(sitemap_url: str) -> list[str]:
    """Fetches a sitemap XML and extracts all <loc> URLs using BeautifulSoup."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    print(f"sitemapssssssssssssssssssss:----------------------------------{sitemap_url}")
    try:

        response = requests.get( sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()
        if sitemap_url.lower().endswith(".gz"):
            content = gzip.decompress(response.content)
        else:
            content = response.content
        soup = BeautifulSoup(content, "xml")
        urls = []

        sitemap_tags = soup.find_all("sitemap")
        if sitemap_tags:

            print(f"Sitemap index found: "f"{len(sitemap_tags)} child sitemaps")
            for sitemap in sitemap_tags:
                loc = sitemap.find("loc")
                if not loc:
                    continue
                child_sitemap_url = loc.get_text(strip=True)
                print(f"Child sitemap found: "f"{child_sitemap_url}")

                # Download child sitemap
                child_response = requests.get(child_sitemap_url,headers=headers,timeout=2)
                child_response.raise_for_status()

                # Decompress child .gz
                if child_sitemap_url.lower().endswith(".gz"):
                    child_content = gzip.decompress(child_response.content)
                    print(f"child_content========================: {child_content}")
                else:
                    child_content = child_response.content

                # Parse child sitemap
                child_soup = BeautifulSoup(child_content,"xml")

                # Extract actual URLs
                for url_tag in child_soup.find_all("url"):
                    loc = url_tag.find("loc")
                    if loc:
                        url = loc.get_text(strip=True)
                        if url:
                            print(f"url------------------------------{url}")
                            urls.append(url)

        # -----------------------------------------
        # 5. Normal sitemap containing <url>
        # -----------------------------------------
        else:
            for url_tag in soup.find_all("url"):
                loc = url_tag.find("loc")
                if loc:
                    url = loc.get_text(strip=True)
                    if url:
                        urls.append(url)

        print(
            f"Found {len(urls)} actual URLs " f"from {sitemap_url}")
        print(f"urls----------------------------------------------{urls}")
        # return urls
    except Exception as e:
        print(f"Error fetching sitemap {sitemap_url}: {e}")
        return []


def store_urls_in_db(db: Session, domain_url: str, urls: list[str]):
    """Stores the extracted URLs into the ScrapedURL table linked to a Domain."""
    
    # 1. Ensure the Domain exists
    parsed_uri = urlparse(domain_url)
    domain_name = parsed_uri.netloc or domain_url
    
    domain_record = db.query(Domain).filter(Domain.base_url == domain_url).first()
    
    if not domain_record:
        domain_record = Domain(name=domain_name, base_url=domain_url)
        db.add(domain_record)
        db.commit()
        db.refresh(domain_record)
        print(f"Created new domain record: {domain_record.name}")

    # 2. Insert unique URLs
    unique_urls = set(url.strip() for url in urls)
    for url in unique_urls:
        existing = db.query(ScrapedURL).filter(ScrapedURL.url == url).first()
        if existing:
            continue
            
    #     new_url = ScrapedURL(domain_id=domain_record.id, url=url)
    #     db.add(new_url)
    
    # db.commit()