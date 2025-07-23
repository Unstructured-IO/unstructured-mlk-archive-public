import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from urllib.parse import urljoin, urlparse
import os

def scrape_mlk_records():
    """
    Scrape all MLK assassination records from the National Archives website
    """
    base_url = "https://www.archives.gov"
    url = "https://www.archives.gov/research/mlk"
    
    print("Fetching MLK records page...")
    
    # Set up session with headers to mimic a browser
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the table containing the records
        # The table should have headers "Record Number" and "NARA Release Date"
        table = None
        tables = soup.find_all('table')
        
        for t in tables:
            headers = t.find_all('th')
            if len(headers) >= 2:
                header_text = [th.get_text().strip() for th in headers]
                if 'Record Number' in header_text and 'NARA Release Date' in header_text:
                    table = t
                    break
        
        if not table:
            print("Could not find the records table. Looking for alternative structure...")
            # Try to find any table with PDF links
            for t in tables:
                links = t.find_all('a', href=True)
                pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
                if len(pdf_links) > 10:  # If we find a table with many PDF links
                    table = t
                    print(f"Found table with {len(pdf_links)} PDF links")
                    break
        
        if not table:
            print("No suitable table found. Searching entire page for PDF links...")
            # Fallback: search entire page for PDF links
            all_links = soup.find_all('a', href=True)
            pdf_links = []
            for link in all_links:
                href = link['href']
                if '.pdf' in href.lower() or '.mp3' in href.lower():
                    full_url = urljoin(base_url, href)
                    filename = link.get_text().strip() or os.path.basename(urlparse(href).path)
                    pdf_links.append({
                        'filename': filename,
                        'url': full_url,
                        'release_date': 'Unknown'
                    })
            
            if pdf_links:
                print(f"Found {len(pdf_links)} document links on the page")
                return pdf_links
            else:
                print("No document links found on the page")
                return []
        
        # Extract data from the table
        records = []
        rows = table.find_all('tr')
        
        print(f"Found table with {len(rows)} rows")
        
        # Skip header row
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # First cell should contain the record link
                first_cell = cells[0]
                link = first_cell.find('a', href=True)
                
                if link:
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    filename = link.get_text().strip()
                    
                    # Second cell should contain the release date
                    release_date = cells[1].get_text().strip() if len(cells) > 1 else 'Unknown'
                    
                    records.append({
                        'filename': filename,
                        'url': full_url,
                        'release_date': release_date
                    })
        
        print(f"Successfully extracted {len(records)} records")
        return records
        
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return []

def save_records(records, format='csv'):
    """
    Save the records to a file
    """
    if not records:
        print("No records to save")
        return
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    if format == 'csv':
        filename = f"mlk_records_{timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'url', 'release_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"Records saved to {filename}")
    
    elif format == 'json':
        filename = f"mlk_records_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(records, jsonfile, indent=2, ensure_ascii=False)
        print(f"Records saved to {filename}")
    
    # Also save just the URLs for easy downloading
    urls_filename = f"mlk_urls_{timestamp}.txt"
    with open(urls_filename, 'w', encoding='utf-8') as urlfile:
        for record in records:
            urlfile.write(record['url'] + '\n')
    print(f"URLs saved to {urls_filename}")

def main():
    print("Starting MLK records scraper...")
    print("This will extract all document links from the National Archives MLK page")
    
    records = scrape_mlk_records()
    
    if records:
        print(f"\nFound {len(records)} records")
        print("\nFirst 5 records:")
        for i, record in enumerate(records[:5]):
            print(f"{i+1}. {record['filename']} - {record['release_date']}")
            print(f"   URL: {record['url']}")
        
        if len(records) > 5:
            print(f"... and {len(records) - 5} more records")
        
        # Save in both formats
        save_records(records, 'csv')
        save_records(records, 'json')
        
        print(f"\nSummary:")
        print(f"- Total records found: {len(records)}")
        print(f"- Files saved: CSV, JSON, and TXT (URLs only)")
        print(f"- Ready for S3 upload using the URLs file")
        
    else:
        print("No records found. Please check the website structure or network connection.")

if __name__ == "__main__":
    main()
