from email.mime import image

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from downloader import download_media_to_server

def extract_hindi_news18(soup: BeautifulSoup) -> dict:
    """Extraction rules specifically for hindi.news18.com"""
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
        
    # Content
    article = soup.find("article") 
    content = ""
    if article:
        content = "\n\n".join(
        md(str(tag), heading_style="ATX").strip()    
        # tag.get_text(" ", strip=True)
        for tag in article.find_all(["h2", "div"])
        if tag.get_text(strip=True)
    )
    # print(content)
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

        # article = soup.find("div", class_="container story-container")
        # if article:
        #     texts = []
        #     for tag in article.find_all(["h2", "p"]):
        #         texts.append(tag.get_text(strip=True))
        #         content = "\n\n".join(texts)
        #         # print(content)
        # return {"title": title, "image": image, "content": content}

    article = soup.find("div", class_="container story-container")
    content =""
    
    if article:
        content = "\n\n".join(
        md(str(tag), heading_style="ATX").strip()    
        # tag.get_text(" ", strip=True)
        for tag in article.find_all(["h2", "p"])
        if tag.get_text(strip=True)
    )
    return {"title": title, "image": image, "content": content}    
    
    # if article:
    #     content = md(str(article), heading_style="ATX", strip=['script', 'style'])        
    #     content = "\n".join([line for line in content.splitlines() if line.strip()])
    # return {"title": title, "image": image, "content": content}      

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
        md(str(tag), heading_style="ATX").strip()    
        # tag.get_text(" ", strip=True)
        for tag in article.find_all(["h2", "p"])
        if tag.get_text(strip=True)
    )

    # print(content)
    return {"title": title, "image": image, "content": content}


def extract_indiloves(soup: BeautifulSoup) -> dict:
    """Extraction rules specifically for infiloves"""
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
        md(str(tag), heading_style="ATX").strip()    
        # tag.get_text(" ", strip=True)
        for tag in article.find_all(["h1","h2", "p"])
        if tag.get_text(strip=True)
    )

    # print(f"content----------------------------------------------{content}")
    return {"title": title, "image": image, "content": content}


def extract_practo(soup: BeautifulSoup) -> dict:
    """Extraction rules specifically for Practo"""
    # image = ""
    # og_image = soup.find("meta", property="og:image")
    # if og_image:
    #     image = og_image.get("content", "")
    # else:
    #     first_img = soup.find("img")
    #     if first_img:
    #         image = first_img.get("src", "")
            
    # article = soup.find("article", class_="doctor-card")
    # print(f"article----------------------------------------------{article}")


    article = soup.find("div", class_="doctor-profile")
    # content = ""
    print(f"article----------------------------------------------{article}")
    if article:
        phone_element = article.find(attrs={"data-qa-id": "phone_number"})

        if phone_element:
            phone_number = phone_element.get_text(strip=True)
            print("Phone number:", phone_number)
    # print(f"content----------------------------------------------{content}")
    # return {"image": image, "content": content}

def extract_default(soup: BeautifulSoup) -> dict:
    """Fallback rules if we don't have a specific scraper for the domain"""
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
        md(str(tag), heading_style="ATX").strip()    
        # tag.get_text(" ", strip=True)
        for tag in article.find_all(["h2", "div"])
        if tag.get_text(strip=True)
    )
    # print(content)
    return {"title": title, "image": image, "content": content}
