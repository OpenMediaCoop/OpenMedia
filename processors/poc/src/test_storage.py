import asyncio
from datetime import datetime
from storage import PgVectorStorage
from models import NewsInput, ScrapingMetadataInput
import sys

async def test_storage():
    # Initialize storage
    storage = PgVectorStorage()
    
    # Try to connect with retries
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            await storage.connect()
            print("Successfully connected to database!")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to connect to database after {max_retries} attempts")
                print(f"Error: {str(e)}")
                sys.exit(1)
            print(f"Connection failed, retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

    try:
        # Create sample news data
        news_input = NewsInput(
            title="Test News Article",
            content="This is a test article content for testing the storage implementation.",
            summary="Test summary",
            embedding=[0.1] * 1536,  # Sample embedding vector
            summary_embedding=[0.2] * 1536,  # Sample summary embedding vector
            topic_classification={"category": "test", "subcategory": "storage"},
            writing_analysis={"readability": 0.8, "complexity": 0.3},
            published_at=datetime.now(),
            author_id=1,
            facts={"key_fact": "This is a test"},
            entities={"person": ["John Doe"]},
            keywords=["test", "storage", "implementation"],
            ambiguity_score=0.1,
            context_score=0.9,
            relevance_score=0.8
        )

        # Insert news and get the ID
        news_id = await storage.insert_news(news_input)
        print(f"Inserted news with ID: {news_id}")

        # Create sample scraping metadata
        meta_input = ScrapingMetadataInput(
            news_id=news_id,
            source="test_source",
            url="https://example.com/test-article",
            original_published_at=datetime.now(),
            http_status=200,
            headers={"content-type": "text/html"},
            raw_html="<html><body>Test HTML content</body></html>"
        )

        # Insert scraping metadata
        await storage.insert_scraping_metadata(meta_input)
        print("Inserted scraping metadata")
        print("Test completed successfully!")

    except Exception as e:
        print(f"Error during test: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_storage()) 