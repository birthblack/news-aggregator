import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

# --------------------- Configuration ---------------------
CONFIG = {
    'feeds': [
        'https://www.lemonde.fr/rss/une.xml',
        'https://www.theguardian.com/world/rss',
        'https://rss.dw.com/rdf/rss-en-world',
    ],
    'site_title': 'Daily Global News',
    'site_description': 'Top headlines from around the world in one place.',
    'output_dir': 'public',
    'max_articles': 80,
    'default_image': 'https://via.placeholder.com/600x400?text=No+Image',
    'cache_dir': 'cache'
}

# --------------------- Utility Functions ---------------------
def extract_image_from_content(url, content):
    try:
        soup = BeautifulSoup(content, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            img_url = img['src']
            if not img_url.startswith('http'):
                parsed = urlparse(url)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
            return img_url
    except Exception as e:
        print(f"Error extracting image from {url}: {e}")
    return None

def fetch_article_content(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('.', '_')
    filename = os.path.basename(parsed_url.path)
    if not filename or '.' not in filename:
        filename = str(abs(hash(url)))
    cache_file = os.path.join(CONFIG['cache_dir'], f"{domain}_{filename}.html")

    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        article_text = ''
        for tag in soup.find_all(['p', 'h2', 'h3']):
            article_text += f"<{tag.name}>{tag.get_text()}</{tag.name}>\n"

        os.makedirs(CONFIG['cache_dir'], exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(article_text)

        return article_text
    except Exception as e:
        print(f"Failed to fetch article: {url}", e)
        return None

def parse_rss_feed(feed_url):
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        channel = root.find('channel')
        items = channel.findall('item') if channel is not None else []
        entries = []

        for item in items:
            image_url = None
            media_content = item.find('.//media:content', namespaces={'media': 'http://search.yahoo.com/mrss/'})
            if media_content is not None and 'url' in media_content.attrib:
                image_url = media_content.attrib['url']
            else:
                enclosure = item.find('enclosure')
                if enclosure is not None and enclosure.attrib.get('type', '').startswith('image/'):
                    image_url = enclosure.attrib['url']

            entry = {
                'title': item.findtext('title', default='').strip(),
                'link': item.findtext('link', default='').strip(),
                'summary': BeautifulSoup(item.findtext('description', default=''), 'html.parser').get_text().strip(),
                'published': item.findtext('pubDate', default='').strip(),
                'image': image_url
            }
            entries.append(entry)
        return entries
    except Exception as e:
        print(f"Failed to parse RSS feed: {feed_url}", e)
        return []

def fetch_articles():
    articles = []
    for feed_url in CONFIG['feeds']:
        entries = parse_rss_feed(feed_url)
        for entry in entries:
            content = fetch_article_content(entry['link'])
            image_url = entry.get('image')
            if not image_url and content:
                image_url = extract_image_from_content(entry['link'], content)

            article = {
                'title': entry['title'],
                'link': entry['link'],
                'summary': entry.get('summary', ''),
                'published': entry.get('published', ''),
                'image': image_url or CONFIG['default_image'],
                'content': content
            }
            articles.append(article)
            if len(articles) >= CONFIG['max_articles']:
                break
        if len(articles) >= CONFIG['max_articles']:
            break
    return articles

# --------------------- HTML Generation ---------------------
def generate_html(articles):
    if not articles:
        print("No articles to display.")
        return

    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    hero_article = articles[0]
    hero_excerpt = BeautifulSoup(hero_article['content'] or '', 'html.parser').get_text()[:200] + '...'

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2588961592847679"
     crossorigin="anonymous"></script>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <meta name=\"description\" content=\"{CONFIG['site_description']}\">
    <title>{CONFIG['site_title']}</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body>
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-dark\">
        <div class=\"container-fluid\">
            <a class=\"navbar-brand\" href=\"#\">{CONFIG['site_title']}</a>
        </div>
    </nav>

    <div class=\"container mt-4\">
        <div class=\"alert alert-danger text-center\" role=\"alert\">
            <strong>BREAKING:</strong> {hero_article['title']}
        </div>

        <div class=\"row mb-4\">
            <div class=\"col-md-6\">
                <img src=\"{hero_article['image']}\" class=\"img-fluid rounded\" alt=\"{hero_article['title']}\">
            </div>
            <div class=\"col-md-6\">
                <h2><a href=\"article_0.html\">{hero_article['title']}</a></h2>
                <p>{hero_excerpt}</p>
            </div>
        </div>

        <div class=\"row\">
"""

    for i, article in enumerate(articles[1:], start=1):
        html += f"""
            <div class=\"col-md-4 mb-4\">
                <div class=\"card h-100\">
                    <img src=\"{article['image']}\" class=\"card-img-top\" alt=\"{article['title']}\">
                    <div class=\"card-body\">
                        <h5 class=\"card-title\"><a href=\"article_{i}.html\">{article['title']}</a></h5>
                        <p class=\"card-text\">{article['summary'][:120]}...</p>
                    </div>
                </div>
            </div>
        """

    html += f"""
        </div>

        <footer class=\"text-center mt-5 mb-3\">
            <p class=\"text-muted\">Last updated: {now}</p>
            <p class=\"text-muted\">Aggregated from multiple news sources</p>
        </footer>
    </div>

    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js\"></script>
</body>
</html>
"""

    with open(os.path.join(CONFIG['output_dir'], 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    # Generate individual article pages
    for i, article in enumerate(articles):
        article_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <!-- Global AdSense Script (REQUIRED) -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2588961592847679"
     crossorigin="anonymous"></script>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{article['title']} | {CONFIG['site_title']}</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body>
    <div class=\"container mt-4\">
        <a href=\"index.html\" class=\"btn btn-secondary mb-3\">&larr; Back to Home</a>
        <h1>{article['title']}</h1>
        <img src=\"{article['image']}\" class=\"img-fluid rounded mb-4\" alt=\"{article['title']}\">
        <div>{article['content']}</div>
    </div>
</body>
</html>
"""
        with open(os.path.join(CONFIG['output_dir'], f"article_{i}.html"), 'w', encoding='utf-8') as f:
            f.write(article_html)

# --------------------- Main Execution ---------------------
if __name__ == '__main__':
    os.makedirs(CONFIG['cache_dir'], exist_ok=True)
    articles = fetch_articles()
    generate_html(articles)
    print(f"✅ Site generated successfully in {CONFIG['output_dir']}/ folder.")
