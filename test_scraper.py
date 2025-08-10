from scraper import NewsExtractor
import time

def test_enhanced_scraper():
    extractor = NewsExtractor()
    
    # Test URLs with actual articles (you'll need to update these with current articles)
    test_urls = [
        "https://www.bbc.com/news/articles/cy98vyg91evo",
        "https://timesofindia.indiatimes.com/technology/tech-news/ripple-to-pay-125-million-fine-as-us-dismisses-one-of-the-biggest-cryptocurrency-lawsuits/articleshow/123200422.cms",
        "https://timesofindia.indiatimes.com/technology/tech-news/what-have-we-done-sam-altman-says-i-feel-useless-compares-chatgpt-5s-power-to-the-manhattan-project/articleshow/123112813.cms"
    ]
    
    print("Testing Enhanced News Scraper")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nTest {i}: {url}")
        print("-" * 50)
        
        # Extract article
        result = extractor.extract_article(url)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            continue
        
        # Display results
        print(f"Success!")
        print(f"Title: {result['title'][:60]}...")
        print(f"Word Count: {result['word_count']:,}")
        print(f"Quality Score: {result['quality_score']}/100")
        print(f"Method: {result['extraction_method']}")
        
        if result.get('authors'):
            print(f"Authors: {', '.join(result['authors'][:2])}")
        
        if result.get('publish_date'):
            print(f"Published: {result['publish_date']}")
        
        # Get detailed stats
        stats = extractor.get_article_stats(result)
        print(f"Reading Time: {stats['estimated_reading_time']} minutes")
        print(f"Sentences: {stats['sentence_count']}")
        
        # Show first 150 characters of content
        if result['text']:
            preview = result['text'][:150].strip()
            print(f"Preview: {preview}...")
        
        print(f"Extraction completed at: {result['extracted_at'].strftime('%H:%M:%S')}")
        
        # Be respectful to servers
        time.sleep(2)

if __name__ == "__main__":
    test_enhanced_scraper()
