from bs4 import BeautifulSoup

def extract_hindi_news18(soup: BeautifulSoup) -> dict:
    """Extraction rules specifically for hindi.news18.com"""
    # Title
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "No Title"
    
    # Image
    image = ""
    og_image = soup.find("meta", property="og:image")
    if og_image:
        image = og_image.get("content", "")
        
    # Content
    content = ""
    article_body = soup.find("div", class_="article-content-box") # Example class for News18
    if article_body:
        texts = [p.get_text(strip=True) for p in article_body.find_all("p")]
        content = "\n\n".join(texts)
        
    return {"title": title, "image": image, "content": content}


def extract_aajtak(soup: BeautifulSoup) -> dict:
    """Extraction rules specifically for aajtak.in"""
    title = ""
    if soup.find("meta", property="og:title"):
        title = soup.find("meta", property="og:title").get("content")
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = "No Title"

    image = ""
    og_image = soup.find("meta", property="og:image")
    if og_image:
        image = og_image.get("content", "")
    else:
        first_img = soup.find("img")
        if first_img:
            image = first_img.get("src", "")

    article = soup.find("div", class_="container story-container")
    if article:
        texts = []
        for tag in article.find_all(["h2", "p"]):
            texts.append(tag.get_text(strip=True))
            content = "\n\n".join(texts)
            # print(content)
    return {"title": title, "image": image, "content": content}

def extract_new18(soup: BeautifulSoup) -> dict:
    """Extraction rules specifically for news18.com"""
    title = ""
    if soup.find("meta", property="og:title"):
        title = soup.find("meta", property="og:title").get("content")
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = "No Title"
    
    image = ""
    og_image = soup.find("meta", property="og:image")
    if og_image:
        image = og_image.get("content", "")
    else:
        first_img = soup.find("img")
        if first_img:
            image = first_img.get("src", "")
        
    article = soup.find("article")

    content = ""

    if article:
        content = "\n\n".join(
        tag.get_text(" ", strip=True)
        for tag in article.find_all(["h2", "p"])
        if tag.get_text(strip=True)
    )

    # print(content)
    return {"title": title, "image": image, "content": content}


def extract_default(soup: BeautifulSoup) -> dict:
    """Fallback rules if we don't have a specific scraper for the domain"""
    title = soup.title.get_text(strip=True) if soup.title else "No Title"
    image = ""
    content_div = soup.find("div", class_="container story-container") # Your original default
    content = "\n\n".join([p.get_text(strip=True) for p in content_div.find_all("p")]) if content_div else ""
    
    return {"title": title, "image": image, "content": content}

