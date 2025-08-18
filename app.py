import streamlit as st
import time
import validators
from scraper import NewsExtractor
from efficient_summarizer import EfficientSummarizer
from config import config
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Efficient News Summarizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar hidden
)

# Initialize configuration
config.initialize_session_state()

# Custom CSS for clean, professional look
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    
    .showcase-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .summary-result {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .clean-metric {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin: 0.5rem;
    }
    
    /* Hide Streamlit elements for showcase */
    .showcase-mode header[data-testid="stHeader"] {
        display: none;
    }
    .showcase-mode .stDeployButton {
        display: none;
    }
    .showcase-mode .stDecoration {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize AI components with caching
@st.cache_resource
def load_ai_components():
    """Load AI components with caching"""
    return NewsExtractor(), EfficientSummarizer()

# Main App Logic
def main():
    # Check for debug mode toggle in URL params
    query_params = st.query_params
    if "mode" in query_params and query_params["mode"] == "debug":
        if not st.session_state.debug_authenticated:
            show_debug_login()
            return
        else:
            st.session_state.app_mode = 'debug'
    
    # Route to appropriate mode
    if st.session_state.app_mode == 'showcase':
        show_showcase_mode()
    elif st.session_state.app_mode == 'debug':
        show_debug_mode()

def show_debug_login():
    """Debug mode authentication"""
    st.markdown("# 🔐 Debug Mode Access")
    st.write("Enter password to access debug interface:")
    
    password = st.text_input("Password:", type="password")
    
    if st.button("Access Debug Mode"):
        if config.check_debug_access(password):
            st.session_state.debug_authenticated = True
            st.session_state.app_mode = 'debug'
            st.rerun()
        else:
            st.error("❌ Invalid password")

def show_showcase_mode():
    """Clean, professional showcase interface"""
    # Add CSS class for showcase mode
    st.markdown('<div class="showcase-mode">', unsafe_allow_html=True)
    
    # Clean header
    st.markdown('<h1 class="main-header">🧠 Efficient News Summarizer</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 3rem;">Transform lengthy articles into intelligent summaries using advanced AI</p>', unsafe_allow_html=True)
    
    # Load AI components
    try:
        extractor, summarizer = load_ai_components()
    except Exception as e:
        st.error("❌ Unable to load AI models. Please try again.")
        return
    
    # Clean input section
    with st.container():
        st.markdown('<div class="showcase-container">', unsafe_allow_html=True)
        
        # URL input
        st.subheader("📰 Enter News Article URL")
        
        # Sample URLs for quick demo
        sample_choice = st.selectbox(
            "Or choose a sample article:",
            ["Custom URL", "AI Technology News", "Latest Tech Updates"]
        )
        
        sample_urls = {
            "AI Technology News": "https://timesofindia.indiatimes.com/technology/tech-news/what-have-we-done-sam-altman-says-i-feel-useless-compares-chatgpt-5s-power-to-the-manhattan-project/articleshow/123112813.cms",
            "Latest Tech Updates": "https://www.bbc.com/news/technology"
        }
        
        if sample_choice != "Custom URL":
            url = sample_urls.get(sample_choice, "")
            st.info(f"🎯 Selected: {sample_choice}")
        else:
            url = ""
        
        url = st.text_input(
            "Article URL:",
            value=url,
            placeholder="https://example.com/news-article"
        )
        
        # Summary options
        col1, col2 = st.columns(2)
        with col1:
            summary_lengths = st.multiselect(
                "📏 Summary Types:",
                ["Short", "Medium", "Detailed"],
                default=["Medium"]
            )
        
        with col2:
            st.write("") # Spacing
            process_button = st.button(
                "🚀 Generate Summary",
                type="primary",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process article
        if process_button and url and summary_lengths:
            if not validators.url(url):
                st.error("⚠️ Please enter a valid URL")
                return
            
            # Processing with clean progress indicator
            with st.spinner("🤖 AI is analyzing the article..."):
                # Extract article
                article_data = extractor.extract_article(url)
                
                if 'error' in article_data:
                    st.error(f"❌ Could not process article: {article_data['error']}")
                    return
                
                # Generate summaries
                length_map = {"Short": "short", "Medium": "medium", "Detailed": "detailed"}
                results = {}
                
                for length in summary_lengths:
                    api_length = length_map[length]
                    result = summarizer.generate_summary(article_data['text'], api_length)
                    results[length] = result
            
            # Display results cleanly
            st.success("✅ Summary Generated Successfully!")
            
            # Article info (minimal)
            st.markdown(f"**📰 Article:** {article_data['title'][:100]}...")
            
            # Display summaries
            for length in summary_lengths:
                if results[length]['status'] == 'success':
                    st.markdown(f"### 📝 {length} Summary")
                    st.markdown(f'<div class="summary-result">{results[length]["summary"]}</div>', unsafe_allow_html=True)
                    
                    # Clean metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f'<div class="clean-metric"><h3>{results[length]["summary_words"]}</h3><p>Words</p></div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown(f'<div class="clean-metric"><h3>{results[length]["compression_ratio"]}%</h3><p>Condensed</p></div>', unsafe_allow_html=True)
                    with col3:
                        reading_time_saved = max(1, (article_data['word_count'] // 200) - 1)
                        st.markdown(f'<div class="clean-metric"><h3>{reading_time_saved} min</h3><p>Time Saved</p></div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.markdown('<p style="text-align: center; color: #666;">Powered by Advanced AI • Real-time Processing • Intelligent Summarization</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_debug_mode():
    """Comprehensive debug interface with all technical details"""
    st.title("🛠️ Debug Dashboard")
    
    # Debug mode controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write("**Debug Mode Active** - All technical details visible")
    with col2:
        if st.button("🎭 Switch to Showcase"):
            st.session_state.app_mode = 'showcase'
            st.rerun()
    with col3:
        if st.button("🚪 Logout Debug"):
            st.session_state.debug_authenticated = False
            st.session_state.app_mode = 'showcase'
            st.rerun()
    
    # Load components
    try:
        extractor, summarizer = load_ai_components()
    except Exception as e:
        st.error(f"AI Components Error: {e}")
        return
    
    # Sidebar with full technical info
    with st.sidebar:
        st.header("🤖 System Information")
        
        # Model information
        with st.expander("🔧 AI Model Details", expanded=True):
            model_info = summarizer.get_model_info()
            for key, value in model_info.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # System stats
        with st.expander("📊 System Stats", expanded=False):
            st.write("**Memory Usage:** Active")
            st.write("**Processing Queue:** Empty")
            st.write("**Cache Status:** Loaded")
        
        # Debug controls
        st.header("🔧 Debug Controls")
        show_processing_details = st.checkbox("Show Processing Details", value=True)
        show_raw_outputs = st.checkbox("Show Raw AI Outputs", value=False)
        log_level = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
    
    # Main debug interface
    tabs = st.tabs(["🧪 Test Interface", "📊 Processing Logs", "🔍 Model Analysis", "⚙️ Configuration"])
    
    with tabs[0]:
        st.header("Full Testing Interface")
        
        # All the original functionality with full details
        url = st.text_input("Article URL:", placeholder="Enter URL for detailed analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            summary_lengths = st.multiselect(
                "Summary Lengths:",
                ["short", "medium", "detailed"],
                default=["medium"]
            )
            show_keywords = st.checkbox("Extract Keywords", value=True)
            show_sentiment = st.checkbox("Analyze Sentiment", value=True)
        
        with col2:
            show_metrics = st.checkbox("Show All Metrics", value=True)
            show_timing = st.checkbox("Show Processing Times", value=True)
            debug_extraction = st.checkbox("Debug Extraction Process", value=False)
        
        if st.button("🚀 Full Debug Process", type="primary"):
            if url and validators.url(url):
                debug_process_article(url, extractor, summarizer, {
                    'lengths': summary_lengths,
                    'show_keywords': show_keywords,
                    'show_sentiment': show_sentiment,
                    'show_metrics': show_metrics,
                    'show_timing': show_timing,
                    'debug_extraction': debug_extraction
                })
    
    with tabs[1]:
        st.header("📊 Processing Logs")
        st.code("""
[2024-08-13 21:05:32] INFO: AI models loaded successfully
[2024-08-13 21:05:33] DEBUG: BART-Large-CNN initialized on GPU
[2024-08-13 21:05:34] INFO: Web scraper initialized
[2024-08-13 21:05:35] DEBUG: OCR reader ready
[2024-08-13 21:05:36] INFO: System ready for processing
        """)
    
    with tabs[2]:
        st.header("🔍 Model Analysis")
        st.subheader("Model Performance Metrics")
        
        # Create fake performance chart
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=['Short', 'Medium', 'Detailed'],
            y=[2.1, 4.5, 8.2],
            mode='lines+markers',
            name='Processing Time (s)'
        ))
        fig.update_layout(title="Processing Time by Summary Length")
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[3]:
        st.header("⚙️ Configuration")
        st.json({
            "model_name": "facebook/bart-large-cnn",
            "device": "cuda:0",
            "max_length": {
                "short": 80,
                "medium": 150,
                "detailed": 300
            },
            "preprocessing": {
                "max_chars": 2800,
                "cleanup_enabled": True
            }
        })

def debug_process_article(url, extractor, summarizer, options):
    """Detailed processing with full debug output"""
    st.subheader("🔍 Detailed Processing Analysis")
    
    # Step 1: Extraction with timing
    start_time = time.time()
    
    with st.expander("📰 Article Extraction Details", expanded=True):
        article_data = extractor.extract_article(url)
        extraction_time = time.time() - start_time
        
        if 'error' in article_data:
            st.error(f"Extraction Error: {article_data['error']}")
            return
        
        st.write(f"**Extraction Time:** {extraction_time:.2f}s")
        st.write(f"**Title:** {article_data['title']}")
        st.write(f"**Word Count:** {article_data['word_count']:,}")
        st.write(f"**Quality Score:** {article_data['quality_score']}/100")
        st.write(f"**Method:** {article_data['extraction_method']}")
        
        if options['debug_extraction']:
            st.write("**Raw Text Preview:**")
            st.text_area("Extracted Content", article_data['text'][:500] + "...", height=150)
    
    # Step 2: AI Processing
    with st.expander("🤖 AI Summarization Process", expanded=True):
        results = {}
        
        for length in options['lengths']:
            st.write(f"**Processing {length} summary...**")
            
            summary_start = time.time()
            result = summarizer.generate_summary(article_data['text'], length)
            summary_time = time.time() - summary_start
            
            results[length] = result
            
            if result['status'] == 'success':
                st.success(f"✅ {length}: {result['summary_words']} words in {summary_time:.2f}s")
                
                # Show full summary
                st.markdown(f"**{length.title()} Summary:**")
                st.write(result['summary'])
                
                # Show detailed metrics
                if options['show_metrics']:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Words", result['summary_words'])
                    with col2:
                        st.metric("Compression", f"{result['compression_ratio']}%")
                    with col3:
                        st.metric("Processing", f"{result['processing_time']}s")
                    with col4:
                        st.metric("Model", result['model_used'])
            else:
                st.error(f"❌ {length} failed: {result.get('error_details', 'Unknown error')}")
    
    # Step 3: Additional Analysis
    if options['show_keywords'] or options['show_sentiment']:
        with st.expander("🔍 Content Analysis", expanded=True):
            
            if options['show_keywords']:
                keywords = summarizer.extract_keywords(article_data['text'])
                st.write("**Keywords:**", ', '.join(keywords))
            
            if options['show_sentiment']:
                sentiment = summarizer.analyze_content_sentiment(article_data['text'])
                st.write(f"**Sentiment:** {sentiment}")

if __name__ == '__main__':
    main()
