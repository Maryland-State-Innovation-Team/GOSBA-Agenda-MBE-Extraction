import os
import re
import glob
import time
import webbrowser
from bs4 import BeautifulSoup
from datetime import datetime

PDF_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'pdf_cache'))
DOWNLOADS_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')


def get_most_recent_file(directory):
    files = glob.glob(os.path.join(directory, '*'))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def download_agendas_from_html_input(year=None):
    if year is not None:
        url = f'https://bpw.maryland.gov/Pages/meetingDocuments_year.aspx?year={year}'
        print(f"Opening {url} in your browser. Please copy the page source and paste it below.")
        webbrowser.open(url, new=0, autoraise=True)
    print("Paste the HTML source below. End input with a line containing only 'END':")
    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)
    html = '\n'.join(lines)
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        text = a.get_text(strip=True)
        if not text.lower().endswith('agenda'):
            continue
        td = a.find_previous('td', class_='ms-gb')
        if not td:
            continue
        date_str = td.get_text(strip=True)
        try:
            date = datetime.strptime(date_str, '%B %d, %Y')
        except ValueError:
            try:
                date = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                continue
        filename = f"{date.strftime('%Y-%m-%d')}-agenda.pdf"
        filepath = os.path.join(PDF_CACHE_DIR, filename)
        if os.path.exists(filepath):
            continue
        href = a.get('href')
        if not href:
            continue
        if not href.startswith('http'):
            href = 'https://bpw.maryland.gov' + href
        print(f"Opening {href} in browser. Please download and save as PDF.")
        webbrowser.open(href, new=0, autoraise=True)
        input("Press Enter after the PDF has finished downloading...")
        most_recent = get_most_recent_file(DOWNLOADS_DIR)
        if not most_recent or not most_recent.lower().endswith('.pdf'):
            print("No PDF found in Downloads. Skipping.")
            continue
        dest = filepath
        print(f"Moving {most_recent} to {dest}")
        try:
            os.rename(most_recent, dest)
        except Exception as e:
            print(f"Failed to move file: {e}")
