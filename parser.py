from urllib.parse import urlparse

from extractor import extract_aajtak, extract_default, extract_hindi_news18, extract_indiloves, extract_new18


# def extract_default(url: str):
#     """Default extractor used when no site-specific parser is available."""
#     raise ValueError(f"No extractor available for URL: {url}")

# Map domain strings to their specific functions
EXTRACTOR_MAP = {
    "www.news18.com": extract_new18,
    "www.hindi.news18.com": extract_hindi_news18,
    "www.aajtak.in": extract_aajtak,
    "indiloves.in": extract_indiloves,
}

def get_extractor_for_url(url: str):
    """Parses the URL and returns the correct extraction function."""
    domain = urlparse(url).netloc

    print(f"domain          {domain}")
    
    # Check if the domain is in our map; if not, return the default extractor
    return EXTRACTOR_MAP.get(domain, extract_default)