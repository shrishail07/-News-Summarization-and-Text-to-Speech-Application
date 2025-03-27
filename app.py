import streamlit as st
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from collections import defaultdict
from gtts import gTTS
import base64

# Configure page
st.set_page_config(page_title="Company Sentiment Analyzer", page_icon="📈")

# Topic keywords
TOPIC_KEYWORDS = {
    "Electric Vehicles": ["ev", "electric vehicle", "battery", "charging"],
    "Stock Market": ["stock", "share", "investment", "market cap"],
    "Innovation": ["innovation", "breakthrough", "new tech", "invention"],
    "Regulations": ["regulation", "law", "legal", "compliance"],
    "Autonomous Vehicles": ["self-driving", "autonomous", "fsd", "autopilot"]
}

def fetch_news(company, max_articles=5):
    """Fetch news articles from Google News RSS"""
    url = f'https://news.google.com/rss/search?q={company}&hl=en-US&gl=US&ceid=US:en'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Explicitly specify XML parser
        soup = BeautifulSoup(response.content, 'lxml-xml')  # Changed from 'xml' to 'lxml-xml'
        items = soup.find_all('item')[:max_articles]
        
        return [{
            "title": item.title.text if item.title else "No title",
            "link": item.link.text if item.link else "#",
            "summary": item.description.text if item.description else "No summary available",
            "source": item.source.text if item.source else "Unknown"
        } for item in items]
    
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

def analyze_sentiment(text):
    """Classify sentiment as Positive, Negative, or Neutral"""
    try:
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.1:
            return "Positive"
        elif polarity < -0.1:
            return "Negative"
        return "Neutral"
    except:
        return "Neutral"

def extract_topics(text):
    """Simple keyword-based topic extraction"""
    if not text:
        return ["General"]
    
    text_lower = text.lower()
    topics = []
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    return topics if topics else ["General"]

def generate_report(company):
    """Generate the complete analysis report"""
    articles = fetch_news(company)
    if not articles:
        return None
    
    sentiment_counts = defaultdict(int)
    processed_articles = []
    
    for article in articles:
        sentiment = analyze_sentiment(article["title"])
        sentiment_counts[sentiment] += 1
        
        processed_articles.append({
            "Title": article["title"],
            "Summary": article["summary"],
            "Sentiment": sentiment,
            "Topics": extract_topics(f"{article['title']} {article['summary']}")
        })
    
    total = sum(sentiment_counts.values())
    
    report = {
        "Company": company,
        "Articles": processed_articles,
        "Comparative Sentiment Score": {
            "Sentiment Distribution": dict(sentiment_counts),
            "Positive Ratio": f"{sentiment_counts['Positive']/total:.1%}" if total else "0%"
        }
    }
    
    return report

def generate_hindi_summary(report):
    """Create a Hindi summary text from the report"""
    if not report:
        return "कोई रिपोर्ट उपलब्ध नहीं है"
    
    company = report["Company"]
    positive = report["Comparative Sentiment Score"]["Sentiment Distribution"].get("Positive", 0)
    negative = report["Comparative Sentiment Score"]["Sentiment Distribution"].get("Negative", 0)
    neutral = report["Comparative Sentiment Score"]["Sentiment Distribution"].get("Neutral", 0)
    
    summary = f"""
    {company} के लिए समाचार विश्लेषण:
    कुल लेख: {positive + negative + neutral}
    सकारात्मक: {positive}
    नकारात्मक: {negative}
    तटस्थ: {neutral}
    
    प्रमुख समाचार:
    """
    
    for i, article in enumerate(report["Articles"][:3], 1):
        sentiment_map = {
            "Positive": "सकारात्मक",
            "Negative": "नकारात्मक",
            "Neutral": "तटस्थ"
        }
        summary += f"""
        {i}. {article['Title']}
        भावना: {sentiment_map.get(article['Sentiment'], article['Sentiment'])}
        """
    
    return summary

# Streamlit UI
st.title("📰 Company News Sentiment Analyzer")
st.write("Analyze news sentiment for any public company")

company = st.text_input("Enter company name (e.g., Tesla, Apple):", "Tesla")

if st.button("Analyze"):
    with st.spinner("Fetching and analyzing news..."):
        report = generate_report(company)
        
        if report:
            st.success("Analysis complete!")
            
            # Show summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Positive", report["Comparative Sentiment Score"]["Sentiment Distribution"].get("Positive", 0))
            col2.metric("Negative", report["Comparative Sentiment Score"]["Sentiment Distribution"].get("Negative", 0))
            col3.metric("Neutral", report["Comparative Sentiment Score"]["Sentiment Distribution"].get("Neutral", 0))
            
            # Show articles
            st.subheader("Top News Articles")
            for article in report["Articles"]:
                with st.expander(f"{article['Title']} ({article['Sentiment']})"):
                    st.write(article["Summary"])
                    st.write(f"Topics: {', '.join(article['Topics'])}")
            
            # Hindi audio section
            st.subheader("Hindi Audio Summary")
            hindi_summary = generate_hindi_summary(report)
            st.text(hindi_summary)
            
            # Generate audio
            tts = gTTS(text=hindi_summary, lang='hi')
            tts.save("hindi_summary.mp3")
            
            # Play audio in app
            audio_file = open("hindi_summary.mp3", "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
            
            # Download button
            st.download_button(
                label="Download Hindi Summary (MP3)",
                data=audio_bytes,
                file_name=f"{company}_hindi_summary.mp3",
                mime="audio/mp3"
            )
        else:
            st.error(f"Could not fetch news for {company}. Please try another company.") 