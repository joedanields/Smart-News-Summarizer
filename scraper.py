import newspaper
from newspaper import Article
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import validators

class NewsExtractor:
    def __init__(self):
        """Initialize the news extractor with enhanced configurations"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configure newspaper settings
        self.config = newspaper.Config()
        self.config.browser_user_agent = self.session.headers['User-Agent']
        self.config.request_timeout = 10
        self.config.number_threads = 1
        self.config.fetch_images = False
        self.config.memoize_articles = False
        self.config.follow_meta_refresh = True
    
    def validate_url(self, url):
        """Enhanced URL validation"""
        if not validators.url(url):
            return False, "Invalid URL format"
        
        try:
            response = self.session.head(url, timeout=5)
            if response.status_code == 200:
                return True, "URL is accessible"
            else:
                return False, f"HTTP {response.status_code} error"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def extract_article(self, url):
        """Enhanced extraction with better error handling and validation"""
        # Validate URL first
        is_valid, message = self.validate_url(url)
        if not is_valid:
            return {'error': f"URL validation failed: {message}"}
        
        try:
            # Add delay to avoid being blocked
            time.sleep(1)
            
            # Method 1: Using newspaper3k with enhanced configuration
            article = Article(url, config=self.config)
            
            try:
                article.download()
                article.parse()
                
                # Validate content quality
                if article.text and len(article.text.split()) > 50:
                    # Clean and validate the extracted data
                    cleaned_data = self._validate_and_clean_data({
                        'title': article.title,
                        'text': article.text,
                        'authors': article.authors,
                        'publish_date': article.publish_date,
                        'source_url': url,
                        'word_count': len(article.text.split()),
                        'extraction_method': 'newspaper3k'
                    })
                    
                    if cleaned_data['word_count'] >= 100:  # Ensure minimum content length
                        return cleaned_data
                    else:
                        print(f"Content too short ({cleaned_data['word_count']} words), trying fallback...")
                        return self._fallback_extraction(url)
                else:
                    print("Primary extraction returned insufficient content, trying fallback...")
                    return self._fallback_extraction(url)
                    
            except Exception as newspaper_error:
                print(f"Newspaper3k failed: {newspaper_error}")
                return self._fallback_extraction(url)
                
        except Exception as e:
            print(f"Primary extraction completely failed: {e}")
            return self._fallback_extraction(url)
    
    def _fallback_extraction(self, url):
        """Enhanced fallback extraction method with multiple strategies"""
        try:
            # Strategy 1: Direct requests with BeautifulSoup
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            unwanted_elements = [
                'script', 'style', 'nav', 'header', 'footer', 'aside',
                'advertisement', 'ad', 'sidebar', 'menu', 'popup'
            ]
            
            for element_type in unwanted_elements:
                for element in soup.find_all(element_type):
                    element.decompose()
            
            # Remove elements by class/id that typically contain ads or navigation
            unwanted_classes = [
                'advertisement', 'ad', 'ads', 'sidebar', 'menu', 'nav',
                'header', 'footer', 'popup', 'modal', 'cookie', 'subscribe'
            ]
            
            for class_name in unwanted_classes:
                for element in soup.find_all(class_=re.compile(class_name, re.I)):
                    element.decompose()
                for element in soup.find_all(id=re.compile(class_name, re.I)):
                    element.decompose()
            
            # Extract title with multiple fallbacks
            title = self._extract_title(soup)
            
            # Extract main content with multiple strategies
            text = self._extract_content(soup)
            
            # Extract metadata
            authors = self._extract_authors(soup)
            publish_date = self._extract_publish_date(soup)
            
            if text and len(text.split()) > 50:
                cleaned_data = self._validate_and_clean_data({
                    'title': title,
                    'text': text,
                    'authors': authors,
                    'publish_date': publish_date,
                    'source_url': url,
                    'word_count': len(text.split()),
                    'extraction_method': 'fallback_beautifulsoup'
                })
                return cleaned_data
            else:
                return {'error': f"Insufficient content extracted. Only {len(text.split()) if text else 0} words found."}
                
        except requests.exceptions.RequestException as e:
            return {'error': f"Network error during fallback extraction: {str(e)}"}
        except Exception as e:
            return {'error': f"Fallback extraction failed: {str(e)}"}
    
    def _extract_title(self, soup):
        """Extract title with multiple fallback strategies"""
        # Strategy 1: Standard title tag
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Clean up title (remove site name, etc.)
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove "| Site Name"
            title = re.sub(r'\s*-\s*.*$', '', title)   # Remove "- Site Name"
            if len(title) > 10:
                return title
        
        # Strategy 2: Meta property titles
        meta_titles = [
            soup.find('meta', property='og:title'),
            soup.find('meta', attrs={'name': 'twitter:title'}),
            soup.find('meta', attrs={'name': 'title'})
        ]
        
        for meta in meta_titles:
            if meta and meta.get('content'):
                return meta.get('content').strip()
        
        # Strategy 3: H1 tags
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Title not found"
    
    def _extract_content(self, soup):
        """Extract main content with multiple strategies"""
        # Strategy 1: Common article selectors
        content_selectors = [
            'article',
            '.article-body', '.story-body', '.post-content', '.entry-content',
            '.content', '.main-content', '.article-content', '.story-content',
            '[role="main"]', 'main', '.post-body', '.article-text'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True, separator=' ')
                if len(text.split()) > 100:  # Good content length
                    return self._clean_extracted_text(text)
        
        # Strategy 2: Paragraph-based extraction
        paragraphs = soup.find_all('p')
        if paragraphs:
            combined_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            if len(combined_text.split()) > 100:
                return self._clean_extracted_text(combined_text)
        
        # Strategy 3: Div-based extraction (last resort)
        content_divs = soup.find_all('div')
        for div in content_divs:
            text = div.get_text(strip=True)
            if len(text.split()) > 200:  # Higher threshold for div content
                return self._clean_extracted_text(text)
        
        # Strategy 4: Full body text (very last resort)
        body_text = soup.get_text(strip=True, separator=' ')
        return self._clean_extracted_text(body_text)
    
    def _extract_authors(self, soup):
        """Extract author information"""
        authors = []
        
        # Common author selectors
        author_selectors = [
            '.author', '.byline', '.writer', '.journalist',
            '[rel="author"]', '.post-author', '.article-author'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                author = element.get_text(strip=True)
                if author and len(author) < 100:  # Reasonable author name length
                    authors.append(author)
        
        # Meta tag authors
        meta_authors = [
            soup.find('meta', attrs={'name': 'author'}),
            soup.find('meta', property='article:author')
        ]
        
        for meta in meta_authors:
            if meta and meta.get('content'):
                authors.append(meta.get('content').strip())
        
        return list(set(authors))  # Remove duplicates
    
    def _extract_publish_date(self, soup):
        """Extract publish date - FIXED VERSION"""
        try:
            # Method 1: Property-based meta tags
            date_meta_property = soup.find('meta', property='article:published_time')
            if date_meta_property and date_meta_property.get('content'):
                try:
                    from dateutil import parser
                    return parser.parse(date_meta_property.get('content'))
                except:
                    pass
            
            # Method 2: Name-based meta tags
            date_meta_name = soup.find('meta', attrs={'name': 'publishdate'})
            if date_meta_name and date_meta_name.get('content'):
                try:
                    from dateutil import parser
                    return parser.parse(date_meta_name.get('content'))
                except:
                    pass
            
            # Method 3: Date meta tag
            date_meta = soup.find('meta', attrs={'name': 'date'})
            if date_meta and date_meta.get('content'):
                try:
                    from dateutil import parser
                    return parser.parse(date_meta.get('content'))
                except:
                    pass
            
            # Method 4: Time elements
            time_elements = soup.find_all('time')
            for time_elem in time_elements:
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    try:
                        from dateutil import parser
                        return parser.parse(datetime_attr)
                    except:
                        pass
            
            # Method 5: JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        date_published = data.get('datePublished')
                        if date_published:
                            from dateutil import parser
                            return parser.parse(date_published)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                date_published = item.get('datePublished')
                                if date_published:
                                    from dateutil import parser
                                    return parser.parse(date_published)
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"Date extraction error: {e}")
            return None
    
    def _clean_extracted_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common unwanted phrases
        unwanted_phrases = [
            r'subscribe to.*?newsletter',
            r'follow us on.*?social media',
            r'share this article',
            r'related articles?',
            r'advertisement',
            r'click here',
            r'read more',
            r'continue reading',
            r'also read:?',
            r'trending now',
            r'breaking news',
            r'live updates'
        ]
        
        for phrase in unwanted_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Clean up punctuation and special characters
        text = re.sub(r'[^\w\s.,!?;:()\[\]{}"\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove lines that are likely navigation or ads
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not any(word in line.lower() for word in 
                ['advertisement', 'sponsored', 'cookie', 'privacy policy', 'terms of service']):
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()
    
    def _validate_and_clean_data(self, data):
        """Validate and clean extracted data"""
        # Clean title
        if data.get('title'):
            data['title'] = data['title'][:200]  # Limit title length
            data['title'] = re.sub(r'\s+', ' ', data['title']).strip()
        
        # Clean text
        if data.get('text'):
            data['text'] = self._clean_extracted_text(data['text'])
            data['word_count'] = len(data['text'].split())
        
        # Validate authors
        if data.get('authors'):
            cleaned_authors = []
            for author in data['authors']:
                if len(author) < 100 and author.lower() not in ['admin', 'editor', 'staff']:
                    cleaned_authors.append(author)
            data['authors'] = cleaned_authors[:5]  # Max 5 authors
        
        # Add extraction timestamp
        data['extracted_at'] = datetime.now()
        
        # Add content quality score
        data['quality_score'] = self._calculate_quality_score(data)
        
        return data
    
    def _calculate_quality_score(self, data):
        """Calculate content quality score (0-100)"""
        score = 0
        
        # Word count scoring (0-40 points)
        word_count = data.get('word_count', 0)
        if word_count > 1000:
            score += 40
        elif word_count > 500:
            score += 35
        elif word_count > 300:
            score += 30
        elif word_count > 200:
            score += 25
        elif word_count > 100:
            score += 20
        else:
            score += 10
        
        # Title quality (0-20 points)
        title = data.get('title', '')
        if len(title) > 20 and 'not found' not in title.lower():
            score += 20
        elif len(title) > 10:
            score += 15
        elif len(title) > 5:
            score += 10
        
        # Author information (0-10 points)
        if data.get('authors') and len(data.get('authors', [])) > 0:
            score += 10
        
        # Date information (0-10 points)
        if data.get('publish_date'):
            score += 10
        
        # Text quality (0-20 points)
        text = data.get('text', '')
        sentences = len([s for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10])
        if sentences > 20:
            score += 20
        elif sentences > 10:
            score += 15
        elif sentences > 5:
            score += 10
        
        return min(score, 100)  # Cap at 100

    def get_article_stats(self, article_data):
        """Get comprehensive statistics about extracted article"""
        if 'error' in article_data:
            return {'error': article_data['error']}
        
        text = article_data.get('text', '')
        
        # Calculate reading time (average 200 words per minute)
        reading_time = max(1, round(len(text.split()) / 200))
        
        # Count sentences more accurately
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
        
        # Count paragraphs
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 10]
        
        stats = {
            'word_count': len(text.split()),
            'character_count': len(text),
            'sentence_count': len(sentences),
            'paragraph_count': max(1, len(paragraphs)),
            'estimated_reading_time': reading_time,
            'quality_score': article_data.get('quality_score', 0),
            'extraction_method': article_data.get('extraction_method', 'unknown'),
            'has_authors': bool(article_data.get('authors')),
            'has_date': bool(article_data.get('publish_date')),
            'title_length': len(article_data.get('title', '')),
            'extracted_at': article_data.get('extracted_at'),
            'average_sentence_length': round(len(text.split()) / max(1, len(sentences)), 1),
            'average_paragraph_length': round(len(text.split()) / max(1, len(paragraphs)), 1)
        }
        
        return stats

# Utility function for quick testing
def quick_test_url(url):
    """Quick utility function to test a single URL"""
    extractor = NewsExtractor()
    print(f"Testing: {url}")
    
    result = extractor.extract_article(url)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Success!")
    print(f"📝 Title: {result['title']}")
    print(f"📊 Words: {result['word_count']}")
    print(f"🎯 Quality: {result['quality_score']}/100")
    print(f"⚙️  Method: {result['extraction_method']}")
    
    # Show preview
    preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
    print(f"🔍 Preview: {preview}")
    
    return True

if __name__ == "__main__":
    # Quick test when run directly
    test_url = "https://timesofindia.indiatimes.com/technology/tech-news/what-have-we-done-sam-altman-says-i-feel-useless-compares-chatgpt-5s-power-to-the-manhattan-project/articleshow/123112813.cms"
    quick_test_url(test_url)
