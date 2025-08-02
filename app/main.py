import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import DataLoader
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Data Insights Dashboard",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("📊 Data Insights Dashboard")
    st.markdown("---")
    
    # Load data
    loader = DataLoader()
    df = loader.load_processed_data()
    
    if df.empty:
        st.warning("No processed data available. Please run the AI workbench first.")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(df))
    
    with col2:
        if 'sentiment_label' in df.columns:
            positive_pct = (df['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
            st.metric("Positive Sentiment", f"{positive_pct:.1f}%")
    
    with col3:
        if 'sentiment_score' in df.columns:
            avg_confidence = df['sentiment_score'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    
    with col4:
        unique_sources = df['url'].nunique() if 'url' in df.columns else 0
        st.metric("Unique Sources", unique_sources)
    
    # Charts
    if 'sentiment_label' in df.columns:
        st.subheader("Financial Sentiment Distribution")
        fig = px.pie(df, names='sentiment_label', title="Financial Sentiment Analysis (Star Ratings)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Sentiment by subreddit - more useful than time trends
        if 'subreddit' in df.columns:
            st.subheader("Sentiment by Community")
            
            # Create bullish/bearish categories
            df['sentiment_category'] = df['sentiment_label'].map({
                '1 star': 'Bearish',
                '2 stars': 'Bearish', 
                '3 stars': 'Neutral',
                '4 stars': 'Bullish',
                '5 stars': 'Bullish'
            })
            
            # Group by subreddit and sentiment
            subreddit_sentiment = df.groupby(['subreddit', 'sentiment_category']).size().unstack(fill_value=0)
            subreddit_sentiment_pct = subreddit_sentiment.div(subreddit_sentiment.sum(axis=1), axis=0) * 100
            
            # Create stacked bar chart
            fig_subreddit = px.bar(subreddit_sentiment_pct.reset_index(), 
                                 x='subreddit', y=['Bullish', 'Neutral', 'Bearish'],
                                 title="Sentiment Distribution by Subreddit (%)",
                                 color_discrete_map={'Bullish': 'green', 'Bearish': 'red', 'Neutral': 'gray'})
            fig_subreddit.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig_subreddit, use_container_width=True)
    
    # Data table
    st.subheader("Recent Data")
    st.dataframe(df.head(100), use_container_width=True)

if __name__ == "__main__":
    main()