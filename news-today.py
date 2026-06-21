import os
import re
import feedparser
import requests
import urllib3
import calendar
from datetime import datetime, timedelta, timezone

# Suppress the "InsecureRequestWarning" alerts
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FEEDS = {
    "Next_Platform": "https://www.nextplatform.com/feed/",
    "Data_Center_Dynamics": "https://www.datacenterdynamics.com/en/rss.xml",
    "Semiconductor_Engineering": "https://semiengineering.com/feed/",
    "Epoch_AI": "https://epochai.substack.com/feed",
    "SemiAnalysis": "https://www.semianalysis.com/feed",
    "Fabricated_Knowledge": "https://www.fabricatedknowledge.com/feed"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text)[:50].strip()

def clean_html(raw_html):
    clean_re = re.compile('<.*?>')
    return re.sub(clean_re, '', raw_html)

def fetch_daily_ai_news():
    today_str = datetime.today().strftime('%Y-%m-%d')
    output_dir = os.path.join(os.getcwd(), today_str)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created daily directory: {output_dir}\n")
    else:
        print(f"Directory {output_dir} already exists.\n")

    # --- THE FIX: Define our 24-hour cutoff window in UTC ---
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"Filtering out articles published before: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

    for source_name, url in FEEDS.items():
        print(f"Fetching from {source_name}...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15, verify=False)
            
            if response.status_code != 200:
                print(f"  [Error] Blocked! HTTP Status {response.status_code}.")
                continue
                
            feed = feedparser.parse(response.text)
            
            if not feed.entries:
                print("  [Warning] Connection succeeded, but no articles were found in the feed.")
                continue
                
            saved_count = 0
            skipped_count = 0
            
            for entry in feed.entries:
                # --- Date Filtering Logic ---
                # feedparser normalizes dates into a 9-tuple (time.struct_time) in UTC
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    # Convert the 9-tuple UTC time to a timezone-aware datetime object
                    timestamp = calendar.timegm(entry.published_parsed)
                    article_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    
                    # If it's older than 24 hours, skip it completely
                    if article_date < cutoff_time:
                        skipped_count += 1
                        continue 
                else:
                    # If a feed item lacks a timestamp, we skip it to prevent junk data
                    skipped_count += 1
                    continue
                # -----------------------------

                title = getattr(entry, 'title', 'No Title')
                link = getattr(entry, 'link', 'No Link')
                published = getattr(entry, 'published', 'Unknown Date')
                
                if 'content' in entry:
                    raw_content = entry.content[0].value
                else:
                    raw_content = getattr(entry, 'summary', 'No summary available.')
                    
                clean_content = clean_html(raw_content)

                safe_title = clean_filename(title)
                filename = f"{source_name}_{safe_title}.txt"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"SOURCE: {source_name}\n")
                    f.write(f"TITLE: {title}\n")
                    f.write(f"DATE: {published}\n")
                    f.write(f"URL: {link}\n")
                    f.write("-" * 40 + "\n\n")
                    f.write(f"CONTENT:\n{clean_content}\n")
                
                saved_count += 1
                
            print(f"  [Success] Saved {saved_count} new articles (Skipped {skipped_count} old ones).")
            
        except requests.exceptions.RequestException as e:
            print(f"  [Network Error] Failed to connect: {e}")
        except Exception as e:
            print(f"  [Error] Something went wrong parsing the data: {e}")

    print(f"\nAll done! Check your folder here: {output_dir}")

if __name__ == "__main__":
    fetch_daily_ai_news()
