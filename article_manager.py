import requests
from bs4 import BeautifulSoup
import csv
import os
from typing import Dict, List, Union, Optional, Any
from datetime import datetime
import pandas as pd
import logging
from pathlib import Path
from embed_manager import EmbedManager
from pinecone_manager import PineconeManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArticleManager:
    def __init__(self, embed_manager: EmbedManager, pinecone_manager: PineconeManager):
        """
        Initialize the ArticleManager with required dependencies.
        
        Args:
            embed_manager: Instance of EmbedManager for generating embeddings
            pinecone_manager: Instance of PineconeManager for storing embeddings
        """
        self.embed_manager = embed_manager
        self.pinecone_manager = pinecone_manager
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

    def process_csv_file(self, file_path: str) -> None:
        """
        Process a CSV file, generate embeddings for all text content, and store them in Pinecone.
        
        Args:
            file_path: Path to the CSV file
        """
        try:
            # Read CSV file
            logger.info(f"Reading CSV file: {file_path}")
            df = pd.read_csv(file_path)
            
            if df.empty:
                logger.warning(f"CSV file is empty: {file_path}")
                return
                
            # Get all columns
            columns = df.columns.tolist()
            logger.info(f"Found {len(columns)} columns: {', '.join(columns)}")
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Combine all text content from all columns
                    text_content = " ".join(str(row[col]) for col in columns if pd.notna(row[col]))
                    
                    if not text_content.strip():
                        logger.warning(f"Row {index} contains no text content")
                        continue
                    
                    # Generate embedding
                    embedding = self.embed_manager.generate_embedding(text_content)
                    
                    # Store in Pinecone
                    self.pinecone_manager.upsert_embedding(
                        vector=embedding,
                        metadata={
                            "text": text_content,
                            "source_file": Path(file_path).name,
                            "row_index": index,
                            **{col: str(row[col]) for col in columns if pd.notna(row[col])}
                        }
                    )
                    
                    logger.info(f"Successfully processed row {index} from {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {str(e)}")
                    continue
                    
        except pd.errors.EmptyDataError:
            logger.error(f"CSV file is empty: {file_path}")
        except pd.errors.ParserError as e:
            logger.error(f"Error parsing CSV file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise

    def process_csv_files(self, data_dir: str = "data") -> None:
        """
        Process all CSV files in the specified directory.
        
        Args:
            data_dir: Path to the directory containing CSV files
        """
        try:
            directory = Path(data_dir)
            
            if not directory.exists():
                logger.error(f"Directory not found: {data_dir}")
                return
                
            csv_files = list(directory.glob("*.csv"))
            
            if not csv_files:
                logger.warning(f"No CSV files found in directory: {data_dir}")
                return
                
            logger.info(f"Found {len(csv_files)} CSV files to process")
            
            for csv_file in csv_files:
                logger.info(f"Processing file: {csv_file}")
                self.process_csv_file(str(csv_file))
                
        except Exception as e:
            logger.error(f"Error processing directory {data_dir}: {str(e)}")
            raise

    def get_article_count(self) -> int:
        """
        Get the total number of articles stored in Pinecone.
        
        Returns:
            int: Number of articles
        """
        return self.pinecone_manager.get_vector_count()

    def search_articles(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for articles using a text query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing search results
        """
        query_embedding = self.embed_manager.generate_embedding(query)
        results = self.pinecone_manager.query_vectors(query_embedding, top_k)
        return results

if __name__ == "__main__":
    # Initialize managers
    embed_manager = EmbedManager()
    pinecone_manager = PineconeManager()
    article_manager = ArticleManager(embed_manager, pinecone_manager)
    
    # Process all CSV files in the data directory
    article_manager.process_csv_files()
