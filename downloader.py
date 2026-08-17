import os
import requests
import uuid
from urllib.parse import urlparse

# Create a dedicated directory on your server to store the files
MEDIA_DIR = "static/media"
os.makedirs(MEDIA_DIR, exist_ok=True)

def download_media_to_server(remote_url: str) -> str:
    """
    Downloads a file from a URL, saves it to the server disk, 
    and returns the local file path.
    """
    if not remote_url:
        return ""
        
    try:
        # 1. Extract the file extension (e.g., '.jpg', '.png') from the URL
        parsed_url = urlparse(remote_url)
        ext = os.path.splitext(parsed_url.path)[1]
        if not ext:
            ext = ".jpg"  # Default fallback if URL hides the extension
            
        # 2. Generate a unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        local_path = os.path.join(MEDIA_DIR, unique_filename)

        # 3. Stream the download (crucial for large files and memory safety)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        with requests.get(remote_url, headers=headers, stream=True, timeout=15) as response:
            response.raise_for_status()
            
            # Open local file in binary write mode ('wb')
            with open(local_path, 'wb') as file:
                # Download and write the file in 8KB chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        
        # Return the local path so we can save it in the database
        return local_path
        
    except Exception as e:
        print(f"Failed to download media from {remote_url}: {e}")
        return ""