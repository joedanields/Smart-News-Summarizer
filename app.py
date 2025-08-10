import streamlit as st
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import validators
from scraper import NewsExtractor
from summarizer import SmartSummarizer

# Page configuration for professional look
st.set_page_config(
    page_title="Smart News Summarizer - AICTE Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .summary-box {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .demo-info {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components with caching for performance
@st.cache_resource
def load_ai_components():
    """Load AI components with caching for better performance"""
    with st.spinner("🤖 Loading AI models... (This may take a moment on first run)"):
        extractor = NewsExtractor()
        summarizer = SmartSummarizer()
    return extractor, summarizer

# Load components
try:
    extractor, summarizer = load_ai_components()
    st.success("✅ AI models loaded successfully!")
except Exception as e:
    st.error(f"❌ Error loading AI models: {e}")
    st.stop()

# Main header
st.markdown('<h1 class="main-header">🧠 Smart News Summarizer</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered News Article Summarization | AICTE Lab Innovation</p>', unsafe_allow_html=True)

# Sidebar for navigation and info
with st.sidebar:
    st.header("🎯 Demo Controls")
    
    # Model information
    with st.expander("🤖 AI Model Info", expanded=False):
        model_info = summarizer.get_model_info()
        for key, value in model_info.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    # Demo mode selector
    demo_mode = st.selectbox(
        "📺 Presentation Mode:",
        ["Interactive Demo", "Quick Test", "Batch Processing"]
    )
    
    # Sample URLs for quick testing
    st.subheader("🚀 Quick Demo URLs")
    sample_urls = {
        "AI/Technology": "https://timesofindia.indiatimes.com/technology/tech-news/what-have-we-done-sam-altman-says-i-feel-useless-compares-chatgpt-5s-power-to-the-manhattan-project/articleshow/123112813.cms",
        "BBC Tech News": "https://www.bbc.com/news/technology",
        "Science News": "https://www.theguardian.com/science",
    }
    
    selected_sample = st.selectbox("Select sample article:", ["Custom URL"] + list(sample_urls.keys()))
    
    if st.button("🎬 Start AICTE Demo Sequence", type="primary", use_container_width=True):
        st.session_state['demo_sequence'] = True

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📰 Article Input")
    
    # URL input
    if selected_sample != "Custom URL":
        default_url = sample_urls[selected_sample]
        st.info(f"🎯 Demo Mode: Using {selected_sample} article")
    else:
        default_url = ""
    
    url = st.text_input(
        "Enter News Article URL:",
        value=default_url,
        placeholder="https://example.com/news-article",
        help="Paste any news article URL from major news sites"
    )
    
    # Summary options
    col_opts1, col_opts2 = st.columns(2)
    
    with col_opts1:
        summary_lengths = st.multiselect(
            "📏 Summary Lengths:",
            ["short", "medium", "detailed"],
            default=["medium"],
            help="Select multiple lengths for comparison"
        )
    
    with col_opts2:
        show_metrics = st.checkbox("📊 Show detailed metrics", value=True)
        show_keywords = st.checkbox("🔍 Extract keywords", value=True)

with col2:
    st.header("⚡ Processing Controls")
    
    # Main processing button
    process_button = st.button(
        "🚀 Summarize Article",
        type="primary",
        use_container_width=True,
        disabled=not url or not summary_lengths
    )
    
    if url and not validators.url(url):
        st.warning("⚠️ Please enter a valid URL")
    
    # Demo information
    st.markdown("""
    <div class="demo-info">
        <h4>🎯 AICTE Lab Demo Features</h4>
        <ul>
            <li>Real-time AI processing</li>
            <li>Multiple summary lengths</li>
            <li>Compression analytics</li>
            <li>Keyword extraction</li>
            <li>Performance metrics</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Processing logic
if process_button and url and summary_lengths:
    # Validate URL
    if not validators.url(url):
        st.error("❌ Invalid URL format")
    else:
        # Create processing container
        processing_container = st.container()
        
        with processing_container:
            st.header("🔄 Processing Pipeline")
            
            # Step 1: Article Extraction
            with st.spinner("📰 Extracting article content..."):
                progress_bar = st.progress(0)
                progress_bar.progress(25, text="Connecting to news source...")
                
                start_time = time.time()
                article_data = extractor.extract_article(url)
                
                if 'error' in article_data:
                    st.error(f"❌ Extraction failed: {article_data['error']}")
                    st.stop()
                
                progress_bar.progress(50, text="Article extracted successfully!")
            
            # Article Information Display
            st.success("✅ Article extracted successfully!")
            
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.metric(
                    label="📝 Word Count",
                    value=f"{article_data['word_count']:,}",
                    help="Original article length"
                )
            
            with col_info2:
                st.metric(
                    label="🎯 Quality Score",
                    value=f"{article_data['quality_score']}/100",
                    help="Content quality assessment"
                )
            
            with col_info3:
                reading_time = max(1, article_data['word_count'] // 200)
                st.metric(
                    label="⏰ Reading Time",
                    value=f"{reading_time} min",
                    help="Estimated reading time"
                )
            
            # Article details in expandable section
            with st.expander("📄 Article Details", expanded=False):
                st.write(f"**Title:** {article_data['title']}")
                st.write(f"**Source:** {url}")
                if article_data.get('authors'):
                    st.write(f"**Authors:** {', '.join(article_data['authors'])}")
                if article_data.get('publish_date'):
                    st.write(f"**Published:** {article_data['publish_date']}")
                st.write(f"**Extraction Method:** {article_data['extraction_method']}")
                st.write(f"**Extracted At:** {article_data['extracted_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Step 2: AI Summarization
            st.header("🤖 AI Summarization")
            
            with st.spinner("🧠 Generating AI summaries..."):
                progress_bar.progress(75, text="AI models processing content...")
                
                # Generate summaries
                summary_results = summarizer.batch_summarize(article_data['text'], summary_lengths)
                
                progress_bar.progress(100, text="Processing complete!")
            
            total_processing_time = round(time.time() - start_time, 2)
            
            # Results Display
            st.header("📋 Summarization Results")
            
            # Create tabs for different summary lengths
            if len(summary_lengths) > 1:
                tabs = st.tabs([f"📝 {length.title()}" for length in summary_lengths])
                
                for i, length in enumerate(summary_lengths):
                    with tabs[i]:
                        result = summary_results.get(length, {})
                        
                        if result.get('status') == 'success':
                            # Summary display
                            st.markdown(f"""
                            <div class="summary-box">
                                <h4>{length.title()} Summary ({result['summary_words']} words)</h4>
                                <p style="font-size: 1.1rem; line-height: 1.6;">{result['summary']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Metrics for this summary
                            if show_metrics:
                                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                                
                                with col_m1:
                                    st.metric("📊 Words", result['summary_words'])
                                
                                with col_m2:
                                    st.metric("🗜️ Compression", f"{result['compression_ratio']}%")
                                
                                with col_m3:
                                    st.metric("⏱️ Processing", f"{result['processing_time']}s")
                                
                                with col_m4:
                                    time_saved = max(0, reading_time - 1)
                                    st.metric("⚡ Time Saved", f"{time_saved} min")
                        else:
                            st.error(f"❌ {length} summary failed: {result.get('error_details', 'Unknown error')}")
            
            else:
                # Single summary display
                length = summary_lengths[0]
                result = summary_results.get(length, {})
                
                if result.get('status') == 'success':
                    st.markdown(f"""
                    <div class="summary-box">
                        <h3>{length.title()} Summary</h3>
                        <p style="font-size: 1.2rem; line-height: 1.6;">{result['summary']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Single summary metrics
                    if show_metrics:
                        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
                        
                        with col_s1:
                            st.metric("📊 Original Words", f"{article_data['word_count']:,}")
                        
                        with col_s2:
                            st.metric("📝 Summary Words", result['summary_words'])
                        
                        with col_s3:
                            st.metric("🗜️ Compression", f"{result['compression_ratio']}%")
                        
                        with col_s4:
                            st.metric("⏱️ Processing Time", f"{result['processing_time']}s")
                        
                        with col_s5:
                            time_saved = max(0, reading_time - 1)
                            st.metric("⚡ Time Saved", f"{time_saved} min")
            
            # Additional insights
            if show_keywords or show_metrics:
                st.header("📊 Content Analysis")
                
                col_analysis1, col_analysis2 = st.columns(2)
                
                with col_analysis1:
                    if show_keywords:
                        keywords = summarizer.extract_keywords(article_data['text'])
                        st.subheader("🔍 Key Topics")
                        
                        # Display keywords as tags
                        keyword_html = " ".join([f'<span style="background-color: #e1f5fe; padding: 0.3rem 0.6rem; margin: 0.2rem; border-radius: 15px; display: inline-block; font-size: 0.9rem;">{keyword}</span>' for keyword in keywords[:8]])
                        st.markdown(keyword_html, unsafe_allow_html=True)
                
                with col_analysis2:
                    sentiment = summarizer.analyze_content_sentiment(article_data['text'])
                    st.subheader("💭 Content Sentiment")
                    
                    sentiment_color = {"Positive": "green", "Negative": "red", "Neutral": "gray"}[sentiment]
                    st.markdown(f'<p style="font-size: 1.5rem; color: {sentiment_color}; font-weight: bold;">🔮 {sentiment}</p>', unsafe_allow_html=True)
            
            # Performance summary
            st.header("🎯 Processing Summary")
            
            col_perf1, col_perf2, col_perf3 = st.columns(3)
            
            with col_perf1:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>⚡ Total Processing</h4>
                    <h2>{total_processing_time}s</h2>
                    <p>Lightning fast AI processing</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_perf2:
                avg_compression = sum(r.get('compression_ratio', 0) for r in summary_results.values()) / len(summary_results)
                st.markdown(f"""
                <div class="metric-container">
                    <h4>🗜️ Average Compression</h4>
                    <h2>{avg_compression:.1f}%</h2>
                    <p>Content efficiently condensed</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_perf3:
                st.markdown(f"""
                <div class="metric-container">
                    <h4>📚 Information Efficiency</h4>
                    <h2>{reading_time}→1 min</h2>
                    <p>Reading time optimized</p>
                </div>
                """, unsafe_allow_html=True)

# Footer with AICTE branding
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <h3>🎓 AICTE Lab Innovation Project</h3>
    <p><strong>Smart News Summarizer</strong> - Demonstrating AI capabilities in Natural Language Processing</p>
    <p>Developed for AICTE Lab Inauguration | Powered by BART-Large-CNN & Advanced Web Scraping</p>
    <p style="font-size: 0.9rem;">Features: Real-time Processing • Multi-length Summaries • Quality Analytics • Performance Metrics</p>
</div>
""", unsafe_allow_html=True)
