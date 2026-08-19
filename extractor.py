from email.mime import image
import json
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
    # print(f"article----------------------------------------------{article}")
    if article:
        name = article.find("h1", class_="doctor-card__name")
        speciality = article.find("div", class_="doctor-card__speciality")
        education = article.find("p", class_="doctor-card__education")
        experience = article.find("p", class_="doctor-card__experience")
        img = article.find("img", class_="doctor-card__photo")
        address = article.find("p", class_="address-card__location")
        map_link = article.find("a", class_="address-card__map-link")
        bio = article.find("div", class_="bio-section__text")
        footer = article.find("div", class_="bottom-ctas")
        phone_number = footer.find("a", href=lambda x: x and "tel:" in x) if footer else None


        # print(f"name----------------------------------------------{name.get_text(strip=True) if name else 'N/A'},")
        # print(f"speciality----------------------------------------------{speciality.get_text(strip=True) if speciality else 'N/A'}")
        # print(f"education----------------------------------------------{education.get_text(strip=True) if education else 'N/A'}")
        # print(f"experience----------------------------------------------{experience.get_text(strip=True) if experience else 'N/A'}")
        # print(f"img----------------------------------------------{img.get('src') if img else 'N/A'}")
        # print(f"address----------------------------------------------{address.get_text(strip=True) if address else 'N/A'}")
        # print(f"map_link----------------------------------------------{map_link.get('href') if map_link else 'N/A'}")
        # print(f"bio----------------------------------------------{bio.get_text(strip=True) if bio else 'N/A'}")
        # print(f"phone_number----------------------------------------------{phone_number.get('href').replace('tel:', '') if phone_number else 'N/A'}")


        scrap_data = {
            "name": name.get_text(strip=True) if name else 'N/A',
            "speciality": speciality.get_text(strip=True) if speciality else 'N/A',
            "education": education.get_text(strip=True) if education else 'N/A',
            "experience": experience.get_text(strip=True) if experience else 'N/A',
            "img": img.get('src') if img else 'N/A',
            "address": address.get_text(strip=True) if address else 'N/A',
            "map_link": map_link.get('href') if map_link else 'N/A',
            "bio": bio.get_text(strip=True) if bio else 'N/A',
            "phone_number": phone_number.get('href').replace('tel:', '') if phone_number else 'N/A'
        }


        json_data = json.dumps(
                scrap_data,
                ensure_ascii=False,
                indent=4
            )

        print(json_data)

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
