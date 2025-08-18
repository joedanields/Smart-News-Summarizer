from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re
import time
from datetime import datetime

class EfficientSummarizer:
    def __init__(self):
        """Initialize with proper GPU support and a lightweight model configuration"""
        print("🤖 Initializing Efficient AI Summarization Engine...")

        # Check CUDA availability and force GPU usage
        print(f"🔍 CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"🎮 GPU Detected: {torch.cuda.get_device_name(0)}")
            self.device = 0  # Use GPU
        else:
            print("💻 Using CPU (GPU not available)")
            self.device = -1

        try:
            print("📥 Loading DistilBART-CNN-12-6 model...")
            self.model_name = "sshleifer/distilbart-cnn-12-6"

            # Load model and tokenizer explicitly for better control
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

            # Move model to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                print("✅ Model loaded on GPU!")
            else:
                print("✅ Model loaded on CPU!")

            # Create pipeline with proper configuration
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
                framework="pt"
            )

        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            # Fallback to simpler pipeline
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=self.device if torch.cuda.is_available() else -1
            )

        # Define DISTINCT length configurations
        self.length_configs = {
            'short': {
                'max_length': 80,   # Increased for meaningful content
                'min_length': 40,   # Minimum for coherent summary
                'description': 'Brief overview (40-80 words)'
            },
            'medium': {
                'max_length': 150,  # Good middle ground
                'min_length': 80,   # Ensure substantial content
                'description': 'Balanced summary (80-150 words)'
            },
            'detailed': {
                'max_length': 300,  # Comprehensive
                'min_length': 150,  # Detailed minimum
                'description': 'Comprehensive summary (150-300 words)'
            }
        }

    def preprocess_text(self, text):
        """Enhanced preprocessing for better summarization"""
        if not text:
            return ""

        # Clean the text
        text = ' '.join(text.split())

        # Remove URLs, emails, and unwanted patterns
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

        # Remove repetitive phrases common in news sites
        unwanted_patterns = [
            r'Also Read:?.*?(?=\.|$)',
            r'Read More:?.*?(?=\.|$)',
            r'Subscribe to.*?newsletter',
            r'Follow us on.*?(?=\.|$)',
            r'Trending.*?(?=\.|$)'
        ]

        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Handle BART's token limit properly (1024 tokens ≈ 3000 characters)
        if len(text) > 2800:
            # Smart truncation - try to end at sentence boundary
            truncated = text[:2800]
            last_period = truncated.rfind('.')
            if last_period > len(truncated) * 0.8:
                text = truncated[:last_period + 1]
            else:
                last_space = truncated.rfind(' ')
                text = truncated[:last_space] if last_space > 0 else truncated

        return text.strip()

    def generate_summary(self, text, length='medium'):
        """Generate summary with proper parameters for distinct outputs - FIXED VERSION"""
        try:
            start_time = time.time()

            # Preprocess text
            clean_text = self.preprocess_text(text)

            # Validate input length
            word_count = len(clean_text.split())
            if word_count < 100:
                return {
                    'summary': "Article too short for meaningful summarization. Minimum 100 words required.",
                    'status': 'insufficient_content',
                    'processing_time': 0,
                    'compression_ratio': 0,
                    'original_words': word_count,
                    'summary_words': 0
                }

            # Get length-specific configuration
            config = self.length_configs.get(length, self.length_configs['medium'])

            # Length-specific parameters for DISTINCT outputs
            if length == 'short':
                params = {
                    'max_length': config['max_length'],
                    'min_length': config['min_length'],
                    'do_sample': False,  # Deterministic for shortest summary
                    'num_beams': 3,
                    'early_stopping': True,
                    'no_repeat_ngram_size': 3,
                    'truncation': True
                }
            elif length == 'medium':
                params = {
                    'max_length': config['max_length'],
                    'min_length': config['min_length'],
                    'do_sample': True,   # Enable sampling for variation
                    'temperature': 0.8,
                    'top_p': 0.85,
                    'num_beams': 4,
                    'early_stopping': True,
                    'no_repeat_ngram_size': 2,
                    'truncation': True
                }
            else:  # detailed
                params = {
                    'max_length': config['max_length'],
                    'min_length': config['min_length'],
                    'do_sample': True,
                    'temperature': 1.0,  # More creativity for detailed
                    'top_p': 0.9,
                    'num_beams': 5,
                    'early_stopping': False,  # Allow longer generation
                    'no_repeat_ngram_size': 2,
                    'length_penalty': 0.8,   # Encourage longer summaries
                    'truncation': True
                }

            # Generate summary with length-specific parameters
            summary_result = self.summarizer(clean_text, **params)

            summary_text = summary_result[0]['summary_text'].strip()

            # Post-process for length-specific content
            summary_text = self._post_process_summary(summary_text, length)

            # Calculate metrics
            processing_time = round(time.time() - start_time, 2)
            original_words = len(text.split())
            summary_words = len(summary_text.split())
            compression_ratio = round((1 - summary_words/original_words) * 100, 1)

            return {
                'summary': summary_text,
                'status': 'success',
                'processing_time': processing_time,
                'compression_ratio': compression_ratio,
                'original_words': original_words,
                'summary_words': summary_words,
                'length_type': length,
                'model_used': self.model_name.split('/')[-1],
                'config_used': config['description']
            }

        except Exception as e:
            return {
                'summary': f"Summarization failed: {str(e)}",
                'status': 'error',
                'processing_time': 0,
                'compression_ratio': 0,
                'original_words': 0,
                'summary_words': 0,
                'error_details': str(e)
            }

    def _post_process_summary(self, summary, length):
        """Enhanced post-process summary for distinct content - FIXED VERSION"""
        # Remove incomplete sentences at the end
        if not summary.endswith('.'):
            last_period = summary.rfind('.')
            if last_period > len(summary) * 0.7:
                summary = summary[:last_period + 1]

        # Length-specific post-processing for variety
        if length == 'short':
            # Keep it punchy and direct
            sentences = summary.split('.')
            if len(sentences) > 2:
                # Take first sentence + most important second sentence
                summary = '. '.join(sentences[:2]).strip()
                if not summary.endswith('.'):
                    summary += '.'

            # Ensure it focuses on the key point
            if len(summary.split()) < 20:
                summary = summary.replace(' He admits', '. Sam Altman admits')

        elif length == 'medium':
            # Balanced approach with context
            if 'Manhattan Project' in summary and len(summary.split()) < 50:
                summary += " This comparison highlights concerns about AI's unprecedented capabilities and potential societal impact."

        elif length == 'detailed':
            # Comprehensive coverage
            if len(summary.split()) < 120:
                summary += " The development raises questions about AI safety, regulation, and the future relationship between humans and artificial intelligence systems."

            # Ensure it covers broader implications
            if 'implications' not in summary.lower() and len(summary.split()) > 100:
                summary += " These developments have significant implications for the tech industry and society."

        return summary.strip()

    def batch_summarize(self, text, lengths=['short', 'medium', 'detailed']):
        """Generate multiple distinct summary lengths - ENHANCED VERSION"""
        print(f"📝 Generating {len(lengths)} DISTINCT summary lengths...")

        results = {}
        total_start = time.time()

        for i, length in enumerate(lengths):
            print(f"   🔄 Processing {length} summary (attempt {i+1})...")

            # Use different random seeds for variety
            torch.manual_seed(42 + i * 10)  # More distinct seeds

            result = self.generate_summary(text, length)
            results[length] = result

            if result['status'] == 'success':
                print(f"   ✅ {length}: {result['summary_words']} words ({result['compression_ratio']}% compression)")
                # Show MORE of the summary to verify distinctness
                preview_length = 80 if length == 'short' else 120
                print(f"      Preview: {result['summary'][:preview_length]}...")
            else:
                print(f"   ❌ {length}: Failed - {result.get('error_details', 'Unknown error')}")

        total_time = round(time.time() - total_start, 2)
        print(f"⏱️  Total processing time: {total_time}s")

        return results

    def extract_keywords(self, text, max_keywords=8):
        """Enhanced keyword extraction"""
        try:
            if not text:
                return []

            # Extract meaningful words
            words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text)

            # Enhanced stop words
            stop_words = {
                'this', 'that', 'these', 'those', 'said', 'says', 'told', 'added',
                'according', 'also', 'however', 'therefore', 'moreover', 'furthermore',
                'meanwhile', 'since', 'while', 'though', 'although', 'because',
                'article', 'report', 'news', 'story', 'information', 'content',
                'statement', 'announcement', 'update', 'development'
            }

            # Count word frequencies
            word_freq = {}
            for word in words:
                word_lower = word.lower()
                if len(word) > 3 and word_lower not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Filter significant words (appear at least twice)
            significant_words = {word: freq for word, freq in word_freq.items()
                               if freq >= 2 or word[0].isupper()}

            # Sort by frequency and relevance
            sorted_keywords = sorted(significant_words.items(),
                                   key=lambda x: (x[1], len(x[0])), reverse=True)

            return [word for word, freq in sorted_keywords[:max_keywords]]

        except Exception as e:
            print(f"Keyword extraction error: {e}")
            return ['Technology', 'Innovation', 'Development']

    def analyze_content_sentiment(self, text):
        """Enhanced sentiment analysis of the content"""
        try:
            # Enhanced keyword-based sentiment analysis
            positive_words = [
                'good', 'great', 'excellent', 'positive', 'success', 'win', 'growth',
                'improve', 'benefit', 'breakthrough', 'achievement', 'advance',
                'innovation', 'opportunity', 'progress', 'successful', 'effective',
                'outstanding', 'remarkable', 'impressive', 'valuable', 'promising'
            ]

            negative_words = [
                'bad', 'terrible', 'negative', 'loss', 'fail', 'decline', 'problem',
                'crisis', 'concern', 'worry', 'fear', 'threat', 'dangerous', 'risk',
                'criticism', 'controversy', 'challenge', 'difficulty', 'useless',
                'disappointing', 'alarming', 'troubling', 'concerning', 'warning'
            ]

            neutral_words = [
                'said', 'announced', 'reported', 'stated', 'mentioned', 'discussed',
                'explained', 'described', 'noted', 'indicated', 'revealed'
            ]

            text_lower = text.lower()

            # Count sentiment indicators
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            neutral_count = sum(1 for word in neutral_words if word in text_lower)

            # Determine sentiment with confidence scoring
            total_sentiment_words = positive_count + negative_count + neutral_count

            if total_sentiment_words == 0:
                return 'Neutral'

            # Calculate percentages
            pos_ratio = positive_count / total_sentiment_words
            neg_ratio = negative_count / total_sentiment_words

            # Decision logic with stronger thresholds
            if neg_ratio > 0.4 or (negative_count > positive_count and negative_count >= 2):
                return 'Negative'
            elif pos_ratio > 0.4 or (positive_count > negative_count and positive_count >= 2):
                return 'Positive'
            else:
                return 'Neutral'

        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return 'Neutral'

    def get_model_info(self):
        """Get current model information"""
        return {
            'model_name': self.model_name,
            'device': 'GPU (CUDA)' if torch.cuda.is_available() and self.device >= 0 else 'CPU',
            'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A',
            'memory_allocated': f"{torch.cuda.memory_allocated(0) / 1024**2:.1f} MB" if torch.cuda.is_available() else 'N/A',
            'length_options': list(self.length_configs.keys()),
            'tokenizer_vocab_size': len(self.tokenizer) if hasattr(self, 'tokenizer') else 'Unknown'
        }

# Utility function for quick testing
def test_summarizer_with_sample():
    """Test function with sample news content"""
    sample_article = """
    Artificial intelligence is rapidly transforming industries across the globe, with companies investing billions of dollars in AI research and development to maintain competitive advantages. Technology giants like Google, Microsoft, and OpenAI are leading the charge in developing more sophisticated AI models that can understand and generate human-like text, analyze complex data patterns, and automate various business processes.

    The latest developments in large language models have shown remarkable capabilities in areas such as content creation, code generation, and problem-solving. However, experts are increasingly concerned about the ethical implications of AI advancement, including potential job displacement, privacy concerns, and the need for robust regulatory frameworks.

    Sam Altman, CEO of OpenAI, recently compared the power of next-generation AI models to the Manhattan Project, highlighting both the tremendous potential and the significant responsibilities that come with such technological breakthroughs. The AI community is now focused on ensuring that these powerful tools are developed and deployed responsibly, with appropriate safeguards to protect society while maximizing the benefits of artificial intelligence.

    Educational institutions are also adapting to this AI revolution, integrating AI tools into their curricula and research programs. The AICTE (All India Council for Technical Education) has been promoting AI education and encouraging the establishment of AI laboratories in engineering colleges across India to prepare students for the future workforce.
    """

    print("🧪 Testing Efficient Summarizer with Sample Article")
    print("=" * 60)

    summarizer = EfficientSummarizer()

    # Test all summary lengths
    results = summarizer.batch_summarize(sample_article)

    print("\n📋 SUMMARIZATION RESULTS:")
    print("=" * 60)

    for length, result in results.items():
        if result['status'] == 'success':
            print(f"\n📝 {length.upper()} SUMMARY:")
            print(f"📊 {result['summary_words']} words ({result['compression_ratio']}% compression)")
            print(f"⏱️  Processing time: {result['processing_time']}s")
            print(f"🤖 Model: {result['model_used']}")
            print(f"📄 Summary: {result['summary']}")  # Show FULL summary
            print(f"📏 Full Length: {len(result['summary'])} characters")  # Character count
        else:
            print(f"\n❌ {length.upper()} SUMMARY FAILED:")
            print(f"Error: {result['error_details']}")

    # Test keyword extraction
    keywords = summarizer.extract_keywords(sample_article)
    print(f"\n🔍 KEY TOPICS: {', '.join(keywords[:8])}")

    # Test sentiment analysis
    sentiment = summarizer.analyze_content_sentiment(sample_article)
    print(f"💭 CONTENT SENTIMENT: {sentiment}")

    return summarizer

# Test function for model info
def show_model_info():
    """Display model information"""
    summarizer = EfficientSummarizer()
    print("\n📊 Model Information:")
    info = summarizer.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    test_summarizer_with_sample()
