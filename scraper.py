import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure output paths
OUTPUT_FOLDER = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "suta_scraper_output")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure HTTP session with retries
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=100)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def fetch_products():
    """Fetch all products with pagination and connection reuse"""
    base_url = "https://suta.in/collections/gift-box/products.json"
    all_products = []
    page = 1
    session = create_session()

    while True:
        url = f"{base_url}?limit=250&page={page}"
        logger.info(f"Fetching page {page}")
        
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Error fetching page {page}: {str(e)}")
            break

        products = data.get("products", [])
        if not products:
            break

        for p in products:
            image_url = p["images"][0]["src"] if p["images"] else None
            all_products.append({
                "title": p["title"],
                "price": p["variants"][0]["price"],
                "image_url": image_url,
                "url": f"https://suta.in/products/{p['handle']}"
            })

        logger.info(f"✅ Page {page}: {len(products)} products")
        page += 1

    return all_products

def save_products(products):
    """Save product data with image URLs instead of downloading images"""
    output_file = os.path.join(OUTPUT_FOLDER, "suta_products.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for product in products:
            f.write(f"Name: {product['title']}\n")
            f.write(f"Price: ₹{product['price']}\n")
            f.write(f"URL: {product['url']}\n")
            
            if product["image_url"]:
                f.write(f"Image URL: {product['image_url']}\n")
            else:
                f.write("No image available\n")
            
            f.write("-" * 40 + "\n")
    
    logger.info(f"Saved details to {output_file}")

if __name__ == "__main__":
    logger.info("📦 Starting product scrape...")
    products = fetch_products()
    logger.info(f"🔍 Total products found: {len(products)}")
    save_products(products)
    logger.info("✅ Done! Check the output folder on your Desktop.")