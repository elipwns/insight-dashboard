import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import DataLoader
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Trading Insights",
    page_icon="📊",
    layout="wide"
)

def presentation_page():
    st.title("📊 Trading Insights")
    st.markdown("*Market sentiment analysis from financial communities*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    
    if df.empty:
        st.warning("No data available. Please run the data collection pipeline.")
        return
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'sentiment_label' in df.columns:
            bullish_pct = (df['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
            st.metric("Market Sentiment", f"{bullish_pct:.0f}% Bullish")
    
    with col2:
        total_posts = len(df)
        st.metric("Community Posts", f"{total_posts:,}")
    
    with col3:
        categories = df['category'].nunique() if 'category' in df.columns else 0
        st.metric("Market Categories", categories)
    
    # Market Overview - Recent Sentiment (Last 3 Days)
    if 'sentiment_label' in df.columns and 'category' in df.columns:
        # Filter to recent data only
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=3)
        recent_df = df[df['timestamp'] >= recent_cutoff].copy()
        
        if recent_df.empty:
            st.warning("No recent data (last 3 days) available for current sentiment analysis.")
            recent_df = df  # Fall back to all data if no recent data
        
        # Create bullish/bearish categories
        recent_df['sentiment_category'] = recent_df['sentiment_label'].map({
            '1 star': 'Bearish', '2 stars': 'Bearish', '3 stars': 'Neutral',
            '4 stars': 'Bullish', '5 stars': 'Bullish'
        })
        
        # Market category analysis with custom ordering (recent data only)
        category_sentiment = recent_df.groupby(['category', 'sentiment_category']).size().unstack(fill_value=0)
        category_sentiment_pct = category_sentiment.div(category_sentiment.sum(axis=1), axis=0) * 100
        
        # Custom category order: alphabetical except OTHER at end
        category_order = ['CRYPTO', 'ECONOMICS', 'US_STOCKS']
        if 'OTHER' in category_sentiment_pct.index:
            category_order.append('OTHER')
        
        # Reorder the dataframe
        category_sentiment_pct = category_sentiment_pct.reindex([cat for cat in category_order if cat in category_sentiment_pct.index])
        
        st.subheader("Current Market Sentiment (Last 3 Days)")
        
        # Category descriptions
        with st.expander("📋 Category Definitions"):
            st.markdown("""
            - **CRYPTO**: Digital assets and blockchain (Bitcoin, Ethereum, general crypto)
            - **ECONOMICS**: Macro trends and long-term wealth (economic policy, FIRE movement)
            - **US_STOCKS**: Traditional equity markets (WSB, r/investing, r/stocks, value investing)
            - **OTHER**: Miscellaneous financial discussions not categorized above
            """)
        
        import plotly.graph_objects as go
        
        fig_category = go.Figure()
        
        categories = category_sentiment_pct.index
        
        # Add each sentiment as a separate trace for stacking
        if 'Bullish' in category_sentiment_pct.columns:
            fig_category.add_trace(go.Bar(
                name='Bullish',
                x=categories,
                y=category_sentiment_pct['Bullish'],
                marker_color='#00CC44'
            ))
        
        if 'Neutral' in category_sentiment_pct.columns:
            fig_category.add_trace(go.Bar(
                name='Neutral',
                x=categories,
                y=category_sentiment_pct['Neutral'],
                marker_color='#888888'
            ))
        
        if 'Bearish' in category_sentiment_pct.columns:
            fig_category.add_trace(go.Bar(
                name='Bearish',
                x=categories,
                y=category_sentiment_pct['Bearish'],
                marker_color='#FF4444'
            ))
        
        fig_category.update_layout(
            barmode='stack',
            title="Market Sentiment Overview",
            xaxis_title="Market Category",
            yaxis_title="Percentage",
            showlegend=True
        )
        st.plotly_chart(fig_category, use_container_width=True)
        
        # Price vs Sentiment Analysis (Historical Trends)
        price_df = loader.load_price_data()
        if not price_df.empty:
            st.subheader("Price vs Sentiment Trends Over Time")
            
            available_assets = price_df['symbol'].unique()
            selected_asset = st.selectbox("Asset:", available_assets, index=0 if len(available_assets) > 0 else None, key="asset_selector")
            
            if selected_asset:
                asset_prices = price_df[price_df['symbol'] == selected_asset].copy().sort_values('timestamp')
                sentiment_data = df[df['category'] == 'CRYPTO'].copy() if 'category' in df.columns else df.copy()  # Use all historical data for trends
                
                if not sentiment_data.empty:
                    sentiment_data['timestamp'] = pd.to_datetime(sentiment_data['timestamp'])
                    sentiment_data['date'] = sentiment_data['timestamp'].dt.date
                    asset_prices['date'] = asset_prices['timestamp'].dt.date
                    
                    # Calculate all sentiment categories
                    sentiment_data['sentiment_category'] = sentiment_data['sentiment_label'].map({
                        '1 star': 'Bearish', '2 stars': 'Bearish', '3 stars': 'Neutral',
                        '4 stars': 'Bullish', '5 stars': 'Bullish'
                    })
                    
                    # Group by date and sentiment category
                    daily_sentiment = sentiment_data.groupby(['date', 'sentiment_category']).size().unstack(fill_value=0)
                    daily_sentiment_pct = daily_sentiment.div(daily_sentiment.sum(axis=1), axis=0) * 100
                    daily_sentiment_pct = daily_sentiment_pct.reset_index()
                    
                    daily_prices = asset_prices.groupby('date')['price'].mean().reset_index()
                    
                    try:
                        from plotly.subplots import make_subplots
                        import plotly.graph_objects as go
                        
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # Add sentiment bars (stacked)
                        if not daily_sentiment_pct.empty and len(daily_sentiment_pct) > 0:
                            if 'Bullish' in daily_sentiment_pct.columns:
                                fig.add_trace(go.Bar(
                                    x=daily_sentiment_pct['date'], 
                                    y=daily_sentiment_pct['Bullish'],
                                    name="Bullish %", 
                                    marker_color='rgba(0, 204, 68, 0.6)'
                                ), secondary_y=True)
                            if 'Neutral' in daily_sentiment_pct.columns:
                                fig.add_trace(go.Bar(
                                    x=daily_sentiment_pct['date'], 
                                    y=daily_sentiment_pct['Neutral'],
                                    name="Neutral %", 
                                    marker_color='rgba(136, 136, 136, 0.6)'
                                ), secondary_y=True)
                            if 'Bearish' in daily_sentiment_pct.columns:
                                fig.add_trace(go.Bar(
                                    x=daily_sentiment_pct['date'], 
                                    y=daily_sentiment_pct['Bearish'],
                                    name="Bearish %", 
                                    marker_color='rgba(255, 68, 68, 0.6)'
                                ), secondary_y=True)
                        
                        if not daily_prices.empty and len(daily_prices) > 0:
                            fig.add_trace(go.Scatter(
                                x=daily_prices['date'], 
                                y=daily_prices['price'],
                                mode='lines+markers', 
                                name=f"{selected_asset} Price",
                                line=dict(color='black', width=4),
                                marker=dict(color='black', size=10, line=dict(color='white', width=2))
                            ), secondary_y=False)
                        
                        fig.update_layout(
                            title=f"{selected_asset} Price vs Sentiment", 
                            xaxis_title="Date", 
                            barmode='stack'
                        )
                        fig.update_yaxes(title_text=f"{selected_asset} Price ($)", secondary_y=False)
                        fig.update_yaxes(title_text="Sentiment Distribution (%)", secondary_y=True, range=[0, 100])
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating chart: {e}")
                        st.write("Debug info:")
                        st.write(f"Daily sentiment shape: {daily_sentiment_pct.shape if not daily_sentiment_pct.empty else 'Empty'}")
                        st.write(f"Daily prices shape: {daily_prices.shape if not daily_prices.empty else 'Empty'}")
        else:
            st.info("💡 Price data not available. Run the price collector to enable correlation analysis.")

def debug_page():
    st.title("🔧 Debug & System Status")
    st.markdown("*Detailed system information and data validation*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    price_df = loader.load_price_data()
    
    # System Status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        if 'sentiment_score' in df.columns:
            avg_confidence = df['sentiment_score'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    with col3:
        unique_sources = df['url'].nunique() if 'url' in df.columns else 0
        st.metric("Unique Sources", unique_sources)
    with col4:
        st.metric("Price Data Points", len(price_df))
    
    # Data Validation
    st.subheader("Data Validation")
    
    if not df.empty:
        st.write(f"**Sentiment Data:** {len(df)} records")
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            st.write(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        if 'category' in df.columns:
            category_dist = df['category'].value_counts()
            st.write("**Category Distribution:**")
            category_order = ['CRYPTO', 'ECONOMICS', 'US_STOCKS']
            if 'OTHER' in category_dist.index:
                category_order.append('OTHER')
            ordered_dist = category_dist.reindex([cat for cat in category_order if cat in category_dist.index])
            st.write(ordered_dist)
        
        if 'sentiment_label' in df.columns:
            sentiment_dist = df['sentiment_label'].value_counts()
            st.write("**Sentiment Distribution:**")
            st.write(sentiment_dist)
    
    if not price_df.empty:
        st.write(f"**Price Data:** {len(price_df)} records")
        if 'timestamp' in price_df.columns:
            price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
            st.write(f"Time range: {price_df['timestamp'].min()} to {price_df['timestamp'].max()}")
        
        st.write("**Available Assets:**", list(price_df['symbol'].unique()))
    
    # Raw Data Tables
    st.subheader("Raw Data Sample")
    
    tab1, tab2 = st.tabs(["Sentiment Data", "Price Data"])
    
    with tab1:
        if not df.empty:
            st.dataframe(df.head(50), use_container_width=True)
        else:
            st.warning("No sentiment data available")
    
    with tab2:
        if not price_df.empty:
            st.dataframe(price_df.head(50), use_container_width=True)
        else:
            st.warning("No price data available")

def main():
    # Page navigation
    page = st.sidebar.selectbox("Navigate", ["📊 Insights", "🔧 Debug"], key="page_nav")
    
    if page == "📊 Insights":
        presentation_page()
    else:
        debug_page()

if __name__ == "__main__":
    main()