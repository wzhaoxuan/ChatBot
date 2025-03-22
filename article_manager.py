import requests
from bs4 import BeautifulSoup
import csv
import os
from typing import Dict, List, Union
from datetime import datetime

class ArticleManager:
    def __init__(self):
        self.articles = []

    def scrape_webpage(self, url: str) -> Dict[str, str]:
        """
        Scrapes content from a webpage and returns it in a structured format
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic article info
            article = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': '',
                'date_scraped': datetime.now().isoformat(),
            }
            
            # Extract main content - this is a simple implementation
            # You may need to adjust selectors based on specific website structure
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            if main_content:
                # Remove script and style elements
                for element in main_content(['script', 'style']):
                    element.decompose()
                article['content'] = main_content.get_text(separator=' ').strip()
            
            self.articles.append(article)
            return article
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def save_to_html(self, filename: str):
        """
        Saves articles to an HTML file
        """
        html_content = """
        <html>
        <head><title>Scraped Articles</title></head>
        <body>
        """
        
        for article in self.articles:
            html_content += f"""
            <article>
                <h2>{article['title']}</h2>
                <p><small>Scraped from: <a href="{article['url']}">{article['url']}</a></small></p>
                <p><small>Date scraped: {article['date_scraped']}</small></p>
                <div class="content">{article['content']}</div>
            </article>
            <hr>
            """
            
        html_content += "</body></html>"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def save_to_csv(self, filename: str):
        """
        Saves articles to a CSV file
        """
        if not self.articles:
            return
            
        fieldnames = self.articles[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.articles)

    def load_from_csv(self, filename: str):
        """
        Loads articles from a CSV file
        """
        if not os.path.exists(filename):
            return
            
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.articles.extend(list(reader))

    def clear_articles(self):
        """
        Clears the current articles list
        """
        self.articles = []

    def get_articles(self) -> List[Dict[str, str]]:
        """
        Returns the list of articles
        """
        return self.articles
