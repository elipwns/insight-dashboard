import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import DataLoader
from utils.voting_system import VotingSystem
from dotenv import load_dotenv
from datetime import datetime, timedelta
from monthly_predictions_page import monthly_predictions_page

load_dotenv()

def create_sentiment_gauge(value, title, size='large', show_delta=False, delta_ref=None, is_fear_greed=False, is_community_sentiment=False):
    """Standardized sentiment gauge with dynamic zone highlighting"""
    import plotly.graph_objects as go
    
    # Create progressive filling based on value
    dim_color = "#2A2A2A"  # Dark gray for unfilled zones
    steps = []
    zones = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    zone_colors = ["#DC143C", "#FF6347", "#FFD700", "#32CD32", "#228B22"]
    
    for i, (start, end) in enumerate(zones):
        if value > end:
            # Zone completely filled
            steps.append({'range': [start, end], 'color': zone_colors[i]})
        elif value > start:
            # Zone partially filled - split into filled and unfilled parts
            steps.append({'range': [start, value], 'color': zone_colors[i]})
            steps.append({'range': [value, end], 'color': dim_color})
        else:
            # Zone not filled at all
            steps.append({'range': [start, end], 'color': dim_color})
    
    # Size configurations
    if size == 'large':
        height = 400
        title_size = 24
        number_size = 40
        bar_thickness = 0.3
    else:  # mini
        height = 200
        title_size = 14
        number_size = 20
        bar_thickness = 0.2
    
    # Build gauge
    mode = "gauge+number"
    if show_delta and delta_ref is not None:
        mode += "+delta"
    
    # Configure number display based on gauge type
    if is_fear_greed:
        # Fear & Greed text labels
        if value <= 25:
            text_label = "Extreme Fear"
        elif value <= 45:
            text_label = "Fear"
        elif value <= 55:
            text_label = "Neutral"
        elif value <= 75:
            text_label = "Greed"
        else:
            text_label = "Extreme Greed"
        
        number_config = {'font': {'size': number_size, 'color': 'white'}, 'valueformat': 'none'}
        mode = "gauge"
    elif is_community_sentiment:
        # Community sentiment text labels
        if value <= 25:
            text_label = "Very Bearish"
        elif value <= 45:
            text_label = "Bearish"
        elif value <= 55:
            text_label = "Neutral"
        elif value <= 75:
            text_label = "Bullish"
        else:
            text_label = "Very Bullish"
        
        number_config = {'font': {'size': number_size, 'color': 'white'}, 'valueformat': 'none'}
        mode = "gauge"
    else:
        # Regular percentage display
        number_config = {'valueformat': '.0f', 'suffix': '%', 'font': {'size': number_size, 'color': 'white'}}
    
    indicator = go.Indicator(
        mode=mode,
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': f"<b style='color:white'>{title}</b>",
            'font': {'size': title_size, 'color': 'white'}
        },
        number=number_config,
        gauge={
            'axis': {
                'range': [None, 100],
                'tickwidth': 2,
                'tickcolor': "white",
                'tickfont': {'color': 'white'},
                'tickmode': 'array',
                'tickvals': [0, 20, 40, 60, 80, 100],
                'ticktext': ['0', '20', '40', '60', '80', '100']
            },
            'bar': {'color': 'rgba(0,0,0,0)'},  # Hide bar completely
            'bgcolor': "rgba(0,0,0,0.1)",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': steps
        }
    )
    
    if show_delta and delta_ref is not None:
        indicator.delta = {'reference': delta_ref, 'valueformat': '.0f', 'suffix': ' vs last week', 'font': {'color': 'white'}}
    
    fig = go.Figure(indicator)
    
    # Add custom text for special gauge types
    if is_fear_greed or is_community_sentiment:
        fig.add_annotation(
            x=0.5, y=0.3,
            text=f"<b style='font-size:{number_size}px; color:white'>{text_label}</b>",
            showarrow=False,
            xref="paper", yref="paper"
        )
    
    fig.update_layout(
        height=height,
        font={'color': "white", 'family': "Arial"},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=10) if size == 'mini' else dict(l=20, r=20, t=40, b=20),
        xaxis=dict(scaleanchor="y", scaleratio=1)  # Force 1:1 aspect ratio for circular shapes
    )
    
    return fig

st.set_page_config(
    page_title="Trading Insights",
    page_icon="📊",
    layout="wide"
)

# Auto-refresh configuration
AUTO_REFRESH_INTERVAL = 3600  # 1 hour

# Add auto-refresh functionality
def add_auto_refresh():
    """Add auto-refresh to the dashboard"""
    # Only add auto-refresh script if enabled
    if AUTO_REFRESH_INTERVAL > 0:
        st.markdown(
            f"""
            <script>
            // Show refresh indicator before reload
            setTimeout(function(){{
                document.body.style.opacity = '0.7';
                var refreshDiv = document.createElement('div');
                refreshDiv.innerHTML = '🔄 Refreshing data...';
                refreshDiv.style.position = 'fixed';
                refreshDiv.style.top = '50%';
                refreshDiv.style.left = '50%';
                refreshDiv.style.transform = 'translate(-50%, -50%)';
                refreshDiv.style.background = 'rgba(0,0,0,0.8)';
                refreshDiv.style.color = 'white';
                refreshDiv.style.padding = '20px';
                refreshDiv.style.borderRadius = '10px';
                refreshDiv.style.zIndex = '9999';
                document.body.appendChild(refreshDiv);
                
                setTimeout(function(){{
                    window.location.reload();
                }}, 2000);
            }}, {AUTO_REFRESH_INTERVAL * 1000 - 2000});
            </script>
            """,
            unsafe_allow_html=True
        )
    
    # Only show refresh info and add script if auto-refresh is enabled
    if AUTO_REFRESH_INTERVAL > 0:
        refresh_time = datetime.now().strftime('%H:%M:%S UTC')
        st.sidebar.markdown(f"⏰ **Last updated**: {refresh_time}")
        st.sidebar.markdown(f"🔄 **Auto-refresh**: Every hour")
        
        # Add a small progress bar for refresh countdown
        progress_placeholder = st.sidebar.empty()
        st.sidebar.markdown(
            """
            <style>
            .refresh-countdown {
                font-size: 12px;
                color: #666;
                text-align: center;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown("⏸️ **Auto-refresh**: Disabled")
    


def presentation_page():
    add_auto_refresh()  # Enable auto-refresh for this page
    
    st.title("📊 Trading Insights")
    st.markdown("*Market sentiment analysis from financial communities*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    
    # Data freshness indicator
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        latest_data_time = df['timestamp'].max()
        # Convert to UTC for consistent comparison
        if latest_data_time.tz is None:
            # Assume UTC if no timezone info
            latest_data_time = latest_data_time.tz_localize('UTC')
        now_utc = pd.Timestamp.now(tz='UTC')
        hours_old = (now_utc - latest_data_time).total_seconds() / 3600
        
        if hours_old < 6:
            freshness_color = "green"
            freshness_icon = "🟢"
        elif hours_old < 24:
            freshness_color = "orange" 
            freshness_icon = "🟡"
        else:
            freshness_color = "red"
            freshness_icon = "🔴"
        
        st.sidebar.markdown(f"{freshness_icon} **Data age**: {hours_old:.1f}h old")
    else:
        st.sidebar.markdown("⚪ **Data**: No data available")
    
    if df.empty:
        st.warning("No data available. Please run the data collection pipeline.")
        return
    
    # Sentiment Gauge
    if 'sentiment_label' in df.columns:
        # Calculate current sentiment percentages (last 3 days)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=3)
        recent_df = df[df['timestamp'] >= recent_cutoff].copy()
        
        if recent_df.empty:
            recent_df = df  # Fallback to all data
        
        bullish_pct = (recent_df['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
        neutral_pct = (recent_df['sentiment_label'] == '3 stars').mean() * 100
        bearish_pct = (recent_df['sentiment_label'].isin(['1 star', '2 stars'])).mean() * 100
        needle_value = bullish_pct + (neutral_pct * 0.5)
        
        # Calculate last week sentiment for comparison (only if we have enough data)
        week_ago_cutoff = pd.Timestamp.now() - pd.Timedelta(days=10)
        last_week_cutoff = pd.Timestamp.now() - pd.Timedelta(days=3)
        last_week_df = df[(df['timestamp'] >= week_ago_cutoff) & (df['timestamp'] < last_week_cutoff)].copy()
        
        show_delta = False
        last_week_needle = None
        
        if not last_week_df.empty and len(last_week_df) >= 10:  # Need at least 10 data points
            last_week_bullish = (last_week_df['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
            last_week_neutral = (last_week_df['sentiment_label'] == '3 stars').mean() * 100
            last_week_needle = last_week_bullish + (last_week_neutral * 0.5)
            show_delta = True
        
        st.subheader("🌡️ Market Sentiment Gauge")
        
        import plotly.graph_objects as go
        
        # Use standardized gauge
        fig = create_sentiment_gauge(
            value=needle_value,
            title="Market Sentiment<br><span style='font-size:0.8em;color:lightgray'>Community Pulse</span>",
            size='large',
            show_delta=show_delta,
            delta_ref=last_week_needle,
            is_community_sentiment=True
        )
        
        # Create two-column layout for gauges
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig, use_container_width=True)
            
            # Add explanation below the gauge
            st.caption("🗣️ **Community discussions**: Reddit posts, Bluesky sentiment, social trends")
        
        with col2:
            # Load Fear & Greed data for comparison
            fear_greed_df = loader.load_fear_greed_data()
            
            if not fear_greed_df.empty:
                latest_fg = fear_greed_df.iloc[-1]
                fg_value = latest_fg['fear_greed_value']
                fg_classification = latest_fg['fear_greed_classification']
                
                # Official Fear & Greed gauge
                fig_fg = create_sentiment_gauge(
                    value=fg_value,
                    title="Official Crypto<br><a href='https://alternative.me/crypto/fear-and-greed-index/' target='_blank' style='color:lightblue'>Fear & Greed Index</a>",
                    size='large',
                    is_fear_greed=True
                )
                st.plotly_chart(fig_fg, use_container_width=True)
                
                # Add explanation below the gauge
                st.caption("📊 **Market-wide indicators**: Price momentum, volatility, volume, surveys")
            else:
                st.info("💡 Fear & Greed Index data not available. Run the fear_greed_collector to enable comparison.")
        
        # Interpretation text with contrarian signals
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if needle_value >= 80:
                st.success("🚀 **EXTREME BULLISH** - Market euphoria detected")
                st.caption("⚠️ Contrarian signal: Potential selling opportunity")
            elif needle_value >= 60:
                st.success("📈 **BULLISH** - Positive sentiment dominates")
            elif needle_value >= 40:
                st.info("⚖️ **NEUTRAL** - Mixed market sentiment")
            elif needle_value >= 20:
                st.warning("📉 **BEARISH** - Negative sentiment prevails")
            else:
                st.error("🔥 **EXTREME BEARISH** - Market fear/panic")
                st.caption("💡 Contrarian signal: Potential buying opportunity")
            
            # Show comparison if F&G data available
            if not fear_greed_df.empty:
                difference = needle_value - fg_value
                if abs(difference) < 10:
                    st.info(f"📊 **Aligned**: Community sentiment ({needle_value:.0f}%) closely matches official F&G ({fg_value}%)")
                elif difference > 10:
                    st.success(f"📈 **Divergence**: Community more bullish (+{difference:.0f}%) than market indicators")
                    st.caption("💡 *Retail optimism vs market caution - potential rally fuel*")
                else:
                    st.warning(f"📉 **Divergence**: Community more bearish ({abs(difference):.0f}%) than market indicators")
                    st.caption("⚠️ *Retail pessimism vs market greed - potential distribution phase*")
        
        # Small metrics below gauge
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Bullish", f"{bullish_pct:.0f}%")
        with col2:
            st.metric("Neutral", f"{neutral_pct:.0f}%")
        with col3:
            st.metric("Bearish", f"{bearish_pct:.0f}%")
        with col4:
            if 'platform' in recent_df.columns:
                bluesky_count = len(recent_df[recent_df['platform'] == 'bluesky'])
                reddit_count = len(recent_df[recent_df['platform'].isna() | (recent_df['platform'] != 'bluesky')])
                st.metric("Data Sources", f"R:{reddit_count} B:{bluesky_count}")
            else:
                latest_data = recent_df['timestamp'].max().strftime('%Y-%m-%d') if 'timestamp' in recent_df.columns else 'N/A'
                st.metric("Latest Data", latest_data)
        
        # Add gauge explanation
        with st.expander("📖 Understanding the Gauges"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **🗣️ Community Sentiment**
                - **Source**: Reddit & Bluesky discussions
                - **Measures**: Retail investor mood
                - **Best for**: Early sentiment shifts
                - **Contrarian signal**: Extreme readings often mark reversals
                """)
            with col2:
                st.markdown("""
                **📊 Official Fear & Greed**
                - **Source**: [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/)
                - **Measures**: Market-wide indicators
                - **Includes**: Price momentum, volatility, volume
                - **Best for**: Current market state validation
                """)
            
            st.info("""
            **💡 Divergence Signals:**
            - **Community Bearish + Market Greedy** = Potential top/distribution
            - **Community Bullish + Market Fearful** = Potential bottom/accumulation
            - **Both Aligned** = Trend confirmation
            """)
        

    
        # Platform comparison (expandable)
        with st.expander("🔄 Platform Comparison (Reddit vs Bluesky)"):
            if 'platform' in recent_df.columns:
                # Create sentiment_category column for platform comparison
                recent_df['sentiment_category'] = recent_df['sentiment_label'].map({
                    '1 star': 'Bearish', '2 stars': 'Bearish', '3 stars': 'Neutral',
                    '4 stars': 'Bullish', '5 stars': 'Bullish'
                })
                
                # Debug info
                st.write(f"**Debug**: Total recent posts: {len(recent_df)}")
                platform_counts = recent_df['platform'].value_counts(dropna=False)
                st.write(f"**Platform breakdown**: {dict(platform_counts)}")
                
                # Separate Reddit and Bluesky data
                reddit_data = recent_df[recent_df['platform'].isna() | (recent_df['platform'] != 'bluesky')]
                bluesky_data = recent_df[recent_df['platform'] == 'bluesky']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🟠 Reddit")
                    if not reddit_data.empty:
                        reddit_sentiment = reddit_data['sentiment_category'].value_counts(normalize=True) * 100
                        st.write(f"🟢 Bullish: {reddit_sentiment.get('Bullish', 0):.0f}%")
                        st.write(f"⚪ Neutral: {reddit_sentiment.get('Neutral', 0):.0f}%")
                        st.write(f"🔴 Bearish: {reddit_sentiment.get('Bearish', 0):.0f}%")
                        st.caption(f"{len(reddit_data)} posts analyzed")
                    else:
                        st.info("No Reddit data")
                
                with col2:
                    st.subheader("🦋 Bluesky")
                    if not bluesky_data.empty:
                        bluesky_sentiment = bluesky_data['sentiment_category'].value_counts(normalize=True) * 100
                        st.write(f"🟢 Bullish: {bluesky_sentiment.get('Bullish', 0):.0f}%")
                        st.write(f"⚪ Neutral: {bluesky_sentiment.get('Neutral', 0):.0f}%")
                        st.write(f"🔴 Bearish: {bluesky_sentiment.get('Bearish', 0):.0f}%")
                        st.caption(f"{len(bluesky_data)} posts analyzed")
                    else:
                        st.info("No Bluesky data in recent timeframe")
            else:
                st.info("Platform data not available")
        
        # Category breakdown (expandable)
        with st.expander("📊 Detailed Category Breakdown (Last 3 Days)"):
            if 'category' in df.columns:
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
                
                # Extract crypto-specific sentiment by detecting coin mentions
                def get_crypto_breakdown(df):
                    import re
                    crypto_data = {'BTC': [], 'ETH': [], 'XMR': [], 'LTC': [], 'OTHER_CRYPTO': []}
                    
                    for _, row in df[df['category'] == 'CRYPTO'].iterrows():
                        text = f"{row.get('title', '')} {row.get('content', '')} {row.get('subreddit', '')}".lower()
                        
                        # Check for specific coin mentions
                        if any(term in text for term in ['bitcoin', 'btc', 'r/bitcoin', 'r/btc', 'bitcoinmarkets']):
                            crypto_data['BTC'].append(row)
                        elif any(term in text for term in ['ethereum', 'eth', 'r/ethereum', 'r/ethtrader', 'r/ethfinance']):
                            crypto_data['ETH'].append(row)
                        elif any(term in text for term in ['monero', 'xmr', 'r/monero', 'r/xmrtrader']):
                            crypto_data['XMR'].append(row)
                        elif any(term in text for term in ['litecoin', 'ltc', 'r/litecoin', 'r/litecoinmarkets']):
                            crypto_data['LTC'].append(row)
                        else:
                            crypto_data['OTHER_CRYPTO'].append(row)
                    
                    return crypto_data
                
                crypto_breakdown = get_crypto_breakdown(recent_df)
                
                # Calculate sentiment for each crypto
                crypto_sentiments = {}
                for crypto, posts in crypto_breakdown.items():
                    if posts:
                        crypto_df = pd.DataFrame(posts)
                        crypto_df['sentiment_category'] = crypto_df['sentiment_label'].map({
                            '1 star': 'Bearish', '2 stars': 'Bearish', '3 stars': 'Neutral',
                            '4 stars': 'Bullish', '5 stars': 'Bullish'
                        })
                        sentiment_counts = crypto_df['sentiment_category'].value_counts(normalize=True) * 100
                        bullish = sentiment_counts.get('Bullish', 0)
                        neutral = sentiment_counts.get('Neutral', 0)
                        bearish = sentiment_counts.get('Bearish', 0)
                        crypto_sentiments[crypto] = {
                            'bullish': bullish, 'neutral': neutral, 'bearish': bearish,
                            'needle': bullish + (neutral * 0.5), 'count': len(posts)
                        }
                
                # Non-crypto categories
                non_crypto_df = recent_df[recent_df['category'] != 'CRYPTO']
                category_sentiment = non_crypto_df.groupby(['category', 'sentiment_category']).size().unstack(fill_value=0)
                category_sentiment_pct = category_sentiment.div(category_sentiment.sum(axis=1), axis=0) * 100
                
                # Category descriptions
                st.markdown("""
                **Category Definitions:**
                - **BTC/ETH/XMR/LTC**: Specific cryptocurrency sentiment
                - **OTHER_CRYPTO**: General crypto discussions
                - **ECONOMICS**: Macro trends and long-term wealth
                - **US_STOCKS**: Traditional equity markets
                """)
                
                import plotly.graph_objects as go
                
                # Display crypto breakdown first
                if crypto_sentiments:
                    st.markdown("**🪙 Cryptocurrency Breakdown**")
                    crypto_cols = st.columns(len([k for k, v in crypto_sentiments.items() if v['count'] > 0]))
                    col_idx = 0
                    
                    for crypto, sentiment in crypto_sentiments.items():
                        if sentiment['count'] > 0:
                            with crypto_cols[col_idx]:
                                fig_crypto = create_sentiment_gauge(
                                    value=sentiment['needle'],
                                    title=crypto,
                                    size='mini'
                                )
                                st.plotly_chart(fig_crypto, use_container_width=True)
                                st.caption(f"🟢 {sentiment['bullish']:.0f}% • ⚪ {sentiment['neutral']:.0f}% • 🔴 {sentiment['bearish']:.0f}%")
                                st.caption(f"{sentiment['count']} posts")
                            col_idx += 1
                
                # Display other categories
                if not category_sentiment_pct.empty:
                    st.markdown("**📊 Other Categories**")
                    other_cols = st.columns(len(category_sentiment_pct.index))
                    
                    for i, category in enumerate(category_sentiment_pct.index):
                        with other_cols[i]:
                            cat_bullish = category_sentiment_pct.loc[category, 'Bullish'] if 'Bullish' in category_sentiment_pct.columns else 0
                            cat_neutral = category_sentiment_pct.loc[category, 'Neutral'] if 'Neutral' in category_sentiment_pct.columns else 0
                            cat_needle = cat_bullish + (cat_neutral * 0.5)
                            
                            fig_cat = create_sentiment_gauge(
                                value=cat_needle,
                                title=category,
                                size='mini'
                            )
                            st.plotly_chart(fig_cat, use_container_width=True)
                            st.caption(f"🟢 {cat_bullish:.0f}% • ⚪ {cat_neutral:.0f}% • 🔴 {category_sentiment_pct.loc[category, 'Bearish'] if 'Bearish' in category_sentiment_pct.columns else 0:.0f}%")
    
    st.markdown("---")
    
    # Trending Tickers Section
    st.subheader("🔥 Trending Tickers")
    
    # Extract ticker mentions from recent data
    if not recent_df.empty:
        import re
        
        def extract_tickers(text):
            if not isinstance(text, str):
                return []
            # Look for $TICKER or standalone TICKER patterns
            patterns = [r'\$([A-Z]{2,5})\b', r'\b([A-Z]{2,5})\b']
            tickers = []
            for pattern in patterns:
                matches = re.findall(pattern, text.upper())
                tickers.extend(matches)
            # Filter common words and focus on likely tickers
            valid_tickers = ['GME', 'AMC', 'TSLA', 'AAPL', 'NVDA', 'MSFT', 'BTC', 'ETH', 'DOGE', 'SHIB', 'SPY', 'QQQ']
            return [t for t in tickers if t in valid_tickers]
        
        # Count ticker mentions
        ticker_mentions = {}
        for _, row in recent_df.iterrows():
            text = f"{row.get('title', '')} {row.get('content', '')}"
            tickers = extract_tickers(text)
            for ticker in tickers:
                ticker_mentions[ticker] = ticker_mentions.get(ticker, 0) + 1
        
        if ticker_mentions:
            # Sort by mentions and show top 6
            top_tickers = sorted(ticker_mentions.items(), key=lambda x: x[1], reverse=True)[:6]
            
            cols = st.columns(3)
            for i, (ticker, mentions) in enumerate(top_tickers):
                with cols[i % 3]:
                    # Calculate sentiment for this ticker
                    ticker_posts = []
                    for _, row in recent_df.iterrows():
                        text = f"{row.get('title', '')} {row.get('content', '')}"
                        if ticker in extract_tickers(text):
                            ticker_posts.append(row)
                    
                    if ticker_posts:
                        ticker_df = pd.DataFrame(ticker_posts)
                        bullish_pct = (ticker_df['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
                        
                        # Color based on sentiment
                        if bullish_pct >= 60:
                            sentiment_color = "🟢"
                        elif bullish_pct >= 40:
                            sentiment_color = "🟡"
                        else:
                            sentiment_color = "🔴"
                        
                        st.metric(
                            f"{sentiment_color} ${ticker}",
                            f"{mentions} mentions",
                            f"{bullish_pct:.0f}% bullish"
                        )
        else:
            st.info("No trending tickers detected in recent discussions")
    else:
        st.info("No recent data available for ticker analysis")
    
    st.markdown("---")
    
    # Monthly Prediction Performance (only show if real data exists)
    try:
        response = loader.s3_client.get_object(
            Bucket=loader.bucket_name,
            Key="predictions/monthly_predictions.json"
        )
        predictions_data = json.loads(response['Body'].read().decode('utf-8'))
        performance_data = predictions_data.get('performance', [])
        
        if performance_data:
            st.subheader("🎯 Monthly Prediction Performance")
            
            # Get last 3 performances for rolling display
            recent_performance = performance_data[-3:]
            
            cols = st.columns(len(recent_performance))
            for i, perf in enumerate(recent_performance):
                with cols[i]:
                    rating = perf['rating']
                    symbol = perf['symbol']
                    error = perf['error_pct']
                    month = perf['target_month']
                    
                    if rating == 'Excellent':
                        st.success(f"🎉 **{rating}** 🎉")
                    elif rating == 'Good':
                        st.success(f"✅ **{rating}**")
                    elif rating == 'Fair':
                        st.info(f"⚖️ **{rating}**")
                    elif rating == 'Poor':
                        st.warning(f"⚠️ **{rating}**")
                    else:  # Failed
                        st.error(f"❌ **{rating}**")
                    
                    st.caption(f"{symbol} {month}")
                    st.caption(f"{error:.1f}% error")
            
            # Overall stats
            if len(performance_data) >= 3:
                excellent_count = sum(1 for p in performance_data if p['rating'] == 'Excellent')
                good_count = sum(1 for p in performance_data if p['rating'] == 'Good')
                success_rate = ((excellent_count + good_count) / len(performance_data)) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🏆 Excellent", excellent_count)
                with col2:
                    st.metric("✅ Good", good_count)
                with col3:
                    st.metric("Success Rate", f"{success_rate:.0f}%")
            
            st.markdown("---")
    except:
        pass  # No predictions data available
    
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
                                line=dict(color='white', width=6),
                                marker=dict(color='white', size=12, line=dict(color='black', width=3)),
                                opacity=1.0
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
    
    # Sample posts from both platforms
    with st.expander("📝 Sample Posts by Platform"):
        if 'platform' in recent_df.columns:
            # Separate data again for sample posts
            reddit_posts = recent_df[recent_df['platform'].isna() | (recent_df['platform'] != 'bluesky')]
            bluesky_posts = recent_df[recent_df['platform'] == 'bluesky']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🟠 Reddit Posts")
                if not reddit_posts.empty:
                    for i, row in reddit_posts.head(3).iterrows():
                        content = str(row.get('content', ''))[:100]
                        sentiment = row.get('sentiment_label', 'N/A')
                        subreddit = row.get('subreddit', 'N/A')
                        if pd.isna(subreddit) or str(subreddit).lower() == 'nan':
                            subreddit = 'unknown'
                        st.write(f"**r/{subreddit}** | {sentiment}")
                        st.caption(f"{content}...")
                        st.write("---")
                else:
                    st.info("No Reddit posts in recent data")
            
            with col2:
                st.subheader("🦋 Bluesky Posts")
                if not bluesky_posts.empty:
                    for i, row in bluesky_posts.head(3).iterrows():
                        content = str(row.get('content', ''))[:100]
                        sentiment = row.get('sentiment_label', 'N/A')
                        author = row.get('author_handle', 'N/A')
                        if pd.isna(author) or str(author).lower() == 'nan':
                            author = 'unknown'
                        st.write(f"**@{author}** | {sentiment}")
                        st.caption(f"{content}...")
                        st.write("---")
                else:
                    st.info("No Bluesky posts in recent data")
        else:
            st.info("Platform data not available")

def macro_analysis_page():
    st.title("🌍 Macro Analysis")
    st.markdown("*Bitcoin fundamentals and macro-economic context*")
    st.markdown("---")
    
    loader = DataLoader()
    historical_df = loader.load_historical_data()
    
    if historical_df.empty:
        st.warning("No historical data available. Run the historical backfill script.")
        return
    
    # Bitcoin Supply Scarcity Chart
    btc_supply_data = historical_df[historical_df['metric'] == 'total-bitcoins'].copy()
    if not btc_supply_data.empty:
        btc_supply_data['date'] = pd.to_datetime(btc_supply_data['date'])
        btc_supply_data = btc_supply_data.sort_values('date')
        
        # Calculate supply percentage
        btc_supply_data['supply_percentage'] = (btc_supply_data['value'] / 21_000_000) * 100
        
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        st.subheader("🪙 Bitcoin Supply Scarcity (2009-Present)")
        
        fig_supply = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Supply progression line
        fig_supply.add_trace(go.Scatter(
            x=btc_supply_data['date'],
            y=btc_supply_data['value'],
            mode='lines',
            name='BTC Supply',
            line=dict(color='#FF9500', width=3)
        ), secondary_y=False)
        
        # Supply percentage line
        fig_supply.add_trace(go.Scatter(
            x=btc_supply_data['date'],
            y=btc_supply_data['supply_percentage'],
            mode='lines',
            name='% of Max Supply',
            line=dict(color='white', width=2, dash='dash')
        ), secondary_y=True)
        
        # Add halving events (vertical lines)
        past_halvings = ['2012-11-28', '2016-07-09', '2020-05-11', '2024-04-20']
        future_halvings = ['2028-04-20']  # Estimated next halving (~4 years after 2024)
        
        # Past halvings (solid red lines)
        for i, halving_date in enumerate(past_halvings):
            fig_supply.add_shape(
                type="line",
                x0=halving_date, x1=halving_date,
                y0=0, y1=1,
                yref="paper",
                line=dict(color="red", width=2, dash="dot"),
                opacity=0.7
            )
            fig_supply.add_annotation(
                x=halving_date,
                y=1.02,
                yref="paper",
                text=f"Halving {i+1}",
                showarrow=False,
                font=dict(color="red", size=10)
            )
        
        # Future halvings (dashed orange lines)
        for i, halving_date in enumerate(future_halvings):
            fig_supply.add_shape(
                type="line",
                x0=halving_date, x1=halving_date,
                y0=0, y1=1,
                yref="paper",
                line=dict(color="orange", width=2, dash="dash"),
                opacity=0.5
            )
            fig_supply.add_annotation(
                x=halving_date,
                y=1.02,
                yref="paper",
                text=f"Halving {len(past_halvings)+i+1} (Est.)",
                showarrow=False,
                font=dict(color="orange", size=10)
            )
        
        fig_supply.update_layout(title="Bitcoin Supply Scarcity (2009-Present)")
        fig_supply.update_yaxes(title_text="BTC Supply (Millions)", secondary_y=False)
        fig_supply.update_yaxes(title_text="% of Max Supply", secondary_y=True)
        
        st.plotly_chart(fig_supply, use_container_width=True)
        
        # Current supply metrics
        latest_supply = btc_supply_data.iloc[-1]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Supply", f"{latest_supply['value']:,.0f} BTC")
        with col2:
            st.metric("% Mined", f"{latest_supply['supply_percentage']:.1f}%")
        with col3:
            remaining = 21_000_000 - latest_supply['value']
            st.metric("Remaining", f"{remaining:,.0f} BTC")
    
    # Bitcoin Market Cap vs M2 Money Supply
    m2_data = historical_df[historical_df['metric'] == 'M2SL'].copy()
    btc_market_cap_data = historical_df[historical_df['metric'] == 'market-cap'].copy()
    
    if not m2_data.empty and not btc_market_cap_data.empty:
        st.subheader("💰 Bitcoin Market Cap vs USD M2 Money Supply")
        
        # Prepare data
        m2_data['date'] = pd.to_datetime(m2_data['date'])
        m2_data = m2_data.sort_values('date')
        btc_market_cap_data['date'] = pd.to_datetime(btc_market_cap_data['date'])
        btc_market_cap_data = btc_market_cap_data.sort_values('date')
        
        # Convert M2 from billions to trillions for better scale
        m2_data['m2_trillions'] = m2_data['value'] / 1000
        # Convert BTC market cap from USD to trillions
        btc_market_cap_data['btc_cap_trillions'] = btc_market_cap_data['value'] / 1_000_000_000_000
        
        fig_ratio = make_subplots(specs=[[{"secondary_y": True}]])
        
        # M2 Money Supply (left axis)
        fig_ratio.add_trace(go.Scatter(
            x=m2_data['date'],
            y=m2_data['m2_trillions'],
            mode='lines',
            name='USD M2 Supply',
            line=dict(color='#FF6B6B', width=4)
        ), secondary_y=False)
        
        # Bitcoin Market Cap (right axis)
        fig_ratio.add_trace(go.Scatter(
            x=btc_market_cap_data['date'],
            y=btc_market_cap_data['btc_cap_trillions'],
            mode='lines',
            name='Bitcoin Market Cap',
            line=dict(color='#FF9500', width=4)
        ), secondary_y=True)
        
        fig_ratio.update_layout(title="Bitcoin Market Cap vs USD M2 Money Supply")
        fig_ratio.update_yaxes(title_text="USD M2 Supply (Trillions $)", secondary_y=False)
        fig_ratio.update_yaxes(title_text="Bitcoin Market Cap (Trillions $)", secondary_y=True)
        
        st.plotly_chart(fig_ratio, use_container_width=True)
        
        # Calculate ratio metrics
        if not m2_data.empty and not btc_market_cap_data.empty:
            latest_m2 = m2_data.iloc[-1]
            latest_btc_cap = btc_market_cap_data.iloc[-1]
            btc_to_m2_ratio = (latest_btc_cap['value'] / (latest_m2['value'] * 1_000_000_000)) * 100  # Convert M2 to actual USD
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("M2 Money Supply", f"${latest_m2['m2_trillions']:.1f}T")
            with col2:
                st.metric("Bitcoin Market Cap", f"${latest_btc_cap['btc_cap_trillions']:.2f}T")
            with col3:
                st.metric("BTC/M2 Ratio", f"{btc_to_m2_ratio:.2f}%")
                st.caption("Bitcoin as % of USD money supply")
    
    # USD Money Supply vs Bitcoin Supply (Original Chart)
    m1_data = historical_df[historical_df['metric'] == 'M1SL'].copy()
    
    if not m1_data.empty or not m2_data.empty:
        st.subheader("💵 USD Money Supply vs Bitcoin (Fixed Supply Contrast)")
        
        fig_usd = make_subplots(specs=[[{"secondary_y": True}]])
        
        # M2 Money Supply (left axis)
        if not m2_data.empty:
            fig_usd.add_trace(go.Scatter(
                x=m2_data['date'],
                y=m2_data['value'],
                mode='lines',
                name='USD M2 Supply (Billions)',
                line=dict(color='#FF6B6B', width=4)
            ), secondary_y=False)
        
        # Bitcoin supply (right axis)
        if not btc_supply_data.empty:
            fig_usd.add_trace(go.Scatter(
                x=btc_supply_data['date'],
                y=btc_supply_data['value'],
                mode='lines',
                name='Bitcoin Supply (Millions)',
                line=dict(color='#FF9500', width=4)
            ), secondary_y=True)
        
        fig_usd.update_layout(title="USD Money Printing vs Bitcoin Fixed Supply")
        fig_usd.update_yaxes(title_text="USD M2 Supply (Billions $)", secondary_y=False)
        fig_usd.update_yaxes(title_text="Bitcoin Supply (Millions BTC)", secondary_y=True)
        
        st.plotly_chart(fig_usd, use_container_width=True)
        
        # Money supply metrics
        if not m2_data.empty:
            latest_m2 = m2_data.iloc[-1]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("M2 Money Supply", f"${latest_m2['value']:,.0f}B")
            with col2:
                if len(m2_data) > 12:
                    year_ago = m2_data.iloc[-12]['value']
                    growth_rate = ((latest_m2['value'] - year_ago) / year_ago) * 100
                    st.metric("USD M2 Growth", f"{growth_rate:.1f}%")
            with col3:
                if not btc_supply_data.empty:
                    btc_latest = btc_supply_data.iloc[-1]['value']
                    st.metric("BTC Supply", f"{btc_latest:,.0f}")
    
    # Bitcoin Network Health Chart
    hash_rate_data = historical_df[historical_df['metric'] == 'hash-rate'].copy()
    difficulty_data = historical_df[historical_df['metric'] == 'difficulty'].copy()
    
    if not hash_rate_data.empty or not difficulty_data.empty:
        st.subheader("🔒 Bitcoin Network Health (Security & Difficulty)")
        
        fig_network = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Hash Rate (network security)
        if not hash_rate_data.empty:
            hash_rate_data['date'] = pd.to_datetime(hash_rate_data['date'])
            hash_rate_data = hash_rate_data.sort_values('date')
            # Convert to EH/s (blockchain.info returns TH/s, so divide by 1M to get EH/s)
            hash_rate_data['hash_rate_eh'] = hash_rate_data['value'] / 1_000_000
            
            fig_network.add_trace(go.Scatter(
                x=hash_rate_data['date'],
                y=hash_rate_data['hash_rate_eh'],
                mode='lines',
                name='Hash Rate (EH/s)',
                line=dict(color='#00CC44', width=3)
            ), secondary_y=False)
        
        # Mining Difficulty
        if not difficulty_data.empty:
            difficulty_data['date'] = pd.to_datetime(difficulty_data['date'])
            difficulty_data = difficulty_data.sort_values('date')
            # Convert to trillions for readability
            difficulty_data['difficulty_t'] = difficulty_data['value'] / 1_000_000_000_000
            
            fig_network.add_trace(go.Scatter(
                x=difficulty_data['date'],
                y=difficulty_data['difficulty_t'],
                mode='lines',
                name='Mining Difficulty (T)',
                line=dict(color='#FF6B6B', width=3)
            ), secondary_y=True)
        
        # Add halving events (vertical lines)
        past_halvings = ['2012-11-28', '2016-07-09', '2020-05-11', '2024-04-20']
        future_halvings = ['2028-04-20']
        
        # Past halvings (solid red lines)
        for i, halving_date in enumerate(past_halvings):
            fig_network.add_shape(
                type="line",
                x0=halving_date, x1=halving_date,
                y0=0, y1=1,
                yref="paper",
                line=dict(color="red", width=2, dash="dot"),
                opacity=0.7
            )
            fig_network.add_annotation(
                x=halving_date,
                y=1.02,
                yref="paper",
                text=f"Halving {i+1}",
                showarrow=False,
                font=dict(color="red", size=10)
            )
        
        # Future halvings (dashed orange lines)
        for i, halving_date in enumerate(future_halvings):
            fig_network.add_shape(
                type="line",
                x0=halving_date, x1=halving_date,
                y0=0, y1=1,
                yref="paper",
                line=dict(color="orange", width=2, dash="dash"),
                opacity=0.5
            )
            fig_network.add_annotation(
                x=halving_date,
                y=1.02,
                yref="paper",
                text=f"Halving {len(past_halvings)+i+1} (Est.)",
                showarrow=False,
                font=dict(color="orange", size=10)
            )
        
        fig_network.update_layout(title="Bitcoin Network Security Growth (2009-Present)")
        fig_network.update_yaxes(title_text="Hash Rate (Exahashes/sec)", secondary_y=False)
        fig_network.update_yaxes(title_text="Mining Difficulty (Trillions)", secondary_y=True)
        
        st.plotly_chart(fig_network, use_container_width=True)
        
        # Network health metrics
        col1, col2, col3 = st.columns(3)
        if not hash_rate_data.empty:
            latest_hash = hash_rate_data.iloc[-1]
            with col1:
                st.metric("Current Hash Rate", f"{latest_hash['hash_rate_eh']:.0f} EH/s")
        
        if not difficulty_data.empty:
            latest_diff = difficulty_data.iloc[-1]
            with col2:
                st.metric("Mining Difficulty", f"{latest_diff['difficulty_t']:.1f}T")
        
        with col3:
            st.metric("Network Security", "Exponential Growth")

def indicators_page():
    st.title("📈 Technical Indicators")
    st.markdown("*Technical analysis and feature engineering for ML models*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    price_df = loader.load_price_data()
    
    if price_df.empty:
        st.warning("No price data available. Run the price collector to enable technical indicators.")
        return
    
    # Asset selection
    available_assets = price_df['symbol'].unique()
    selected_asset = st.selectbox("Select Asset:", available_assets, index=0 if len(available_assets) > 0 else None)
    
    if selected_asset:
        # Get price data for selected asset
        asset_prices = price_df[price_df['symbol'] == selected_asset].copy().sort_values('timestamp')
        asset_prices['timestamp'] = pd.to_datetime(asset_prices['timestamp'])
        asset_prices = asset_prices.set_index('timestamp')
        
        # Calculate technical indicators
        def calculate_sma(prices, window):
            return prices.rolling(window=window).mean()
        
        def calculate_ema(prices, window):
            return prices.ewm(span=window).mean()
        
        def calculate_rsi(prices, window=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        def calculate_bollinger_bands(prices, window=20, num_std=2):
            sma = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()
            upper = sma + (std * num_std)
            lower = sma - (std * num_std)
            return upper, sma, lower
        
        # Check if we have enough data
        if len(asset_prices) < 21:
            st.warning(f"Need at least 21 data points for indicators. Currently have {len(asset_prices)} points.")
            return
        
        # Calculate indicators with error handling
        asset_prices['SMA_7'] = calculate_sma(asset_prices['price'], 7)
        asset_prices['SMA_21'] = calculate_sma(asset_prices['price'], 21)
        asset_prices['EMA_12'] = calculate_ema(asset_prices['price'], 12)
        asset_prices['EMA_26'] = calculate_ema(asset_prices['price'], 26)
        asset_prices['RSI'] = calculate_rsi(asset_prices['price'])
        asset_prices['BB_Upper'], asset_prices['BB_Middle'], asset_prices['BB_Lower'] = calculate_bollinger_bands(asset_prices['price'])
        
        # MACD
        asset_prices['MACD'] = asset_prices['EMA_12'] - asset_prices['EMA_26']
        asset_prices['MACD_Signal'] = calculate_ema(asset_prices['MACD'], 9)
        asset_prices['MACD_Histogram'] = asset_prices['MACD'] - asset_prices['MACD_Signal']
        
        # Drop NaN values for visualization
        asset_prices_clean = asset_prices.dropna()
        
        # Sentiment momentum (if sentiment data available)
        if not df.empty and 'sentiment_label' in df.columns:
            # Calculate daily sentiment
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            # Create sentiment categories
            df['sentiment_category'] = df['sentiment_label'].map({
                '1 star': 'Bearish', '2 stars': 'Bearish', '3 stars': 'Neutral',
                '4 stars': 'Bullish', '5 stars': 'Bullish'
            })
            
            # Daily sentiment aggregation
            daily_sentiment = df.groupby(['date', 'sentiment_category']).size().unstack(fill_value=0)
            daily_sentiment_pct = daily_sentiment.div(daily_sentiment.sum(axis=1), axis=0) * 100
            
            if 'Bullish' in daily_sentiment_pct.columns:
                daily_sentiment_pct['sentiment_score'] = daily_sentiment_pct['Bullish'] - daily_sentiment_pct.get('Bearish', 0)
                daily_sentiment_pct['sentiment_momentum_3d'] = daily_sentiment_pct['sentiment_score'].rolling(3).mean()
                daily_sentiment_pct['sentiment_momentum_7d'] = daily_sentiment_pct['sentiment_score'].rolling(7).mean()
        
        # Price & Moving Averages Chart
        st.subheader(f"{selected_asset} Price & Moving Averages")
        
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        fig_price = go.Figure()
        
        # Price line
        fig_price.add_trace(go.Scatter(
            x=asset_prices_clean.index,
            y=asset_prices_clean['price'],
            mode='lines',
            name='Price',
            line=dict(color='white', width=3)
        ))
        
        # Moving averages (only show where data exists)
        if 'SMA_7' in asset_prices_clean.columns and not asset_prices_clean['SMA_7'].isna().all():
            fig_price.add_trace(go.Scatter(
                x=asset_prices_clean.index,
                y=asset_prices_clean['SMA_7'],
                mode='lines',
                name='SMA 7',
                line=dict(color='#00CC44', width=2)
            ))
        
        if 'SMA_21' in asset_prices_clean.columns and not asset_prices_clean['SMA_21'].isna().all():
            fig_price.add_trace(go.Scatter(
                x=asset_prices_clean.index,
                y=asset_prices_clean['SMA_21'],
                mode='lines',
                name='SMA 21',
                line=dict(color='#FF6B6B', width=2)
            ))
        
        fig_price.update_layout(title=f"{selected_asset} Price with Moving Averages")
        st.plotly_chart(fig_price, use_container_width=True)
        
        # RSI Chart
        st.subheader("RSI (Relative Strength Index)")
        
        fig_rsi = go.Figure()
        
        if 'RSI' in asset_prices_clean.columns and not asset_prices_clean['RSI'].isna().all():
            fig_rsi.add_trace(go.Scatter(
                x=asset_prices_clean.index,
                y=asset_prices_clean['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#FF9500', width=2)
            ))
        
        # RSI levels
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
        fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="Neutral (50)")
        
        fig_rsi.update_layout(title="RSI Indicator", yaxis_title="RSI", yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # MACD Chart
        st.subheader("MACD (Moving Average Convergence Divergence)")
        
        fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                                subplot_titles=["MACD Line & Signal", "MACD Histogram"])
        
        # MACD line and signal
        if 'MACD' in asset_prices_clean.columns and not asset_prices_clean['MACD'].isna().all():
            fig_macd.add_trace(go.Scatter(
                x=asset_prices_clean.index,
                y=asset_prices_clean['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='#00CC44', width=2)
            ), row=1, col=1)
        
        if 'MACD_Signal' in asset_prices_clean.columns and not asset_prices_clean['MACD_Signal'].isna().all():
            fig_macd.add_trace(go.Scatter(
                x=asset_prices_clean.index,
                y=asset_prices_clean['MACD_Signal'],
                mode='lines',
                name='Signal',
                line=dict(color='#FF6B6B', width=2)
            ), row=1, col=1)
        
        # MACD histogram
        if 'MACD_Histogram' in asset_prices_clean.columns and not asset_prices_clean['MACD_Histogram'].isna().all():
            colors = ['green' if x >= 0 else 'red' for x in asset_prices_clean['MACD_Histogram']]
            fig_macd.add_trace(go.Bar(
                x=asset_prices_clean.index,
                y=asset_prices_clean['MACD_Histogram'],
                name='Histogram',
                marker_color=colors
            ), row=2, col=1)
        
        fig_macd.update_layout(title="MACD Indicator")
        st.plotly_chart(fig_macd, use_container_width=True)
        
        # Current indicator values
        st.subheader("Current Indicator Values")
        
        if not asset_prices_clean.empty:
            latest = asset_prices_clean.iloc[-1]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if pd.notna(latest['RSI']):
                    st.metric("RSI", f"{latest['RSI']:.1f}")
                    if latest['RSI'] > 70:
                        st.caption("🔴 Overbought")
                    elif latest['RSI'] < 30:
                        st.caption("🟢 Oversold")
                    else:
                        st.caption("⚪ Neutral")
                else:
                    st.metric("RSI", "N/A")
                    st.caption("Insufficient data")
            
            with col2:
                if pd.notna(latest['MACD']) and pd.notna(latest['MACD_Signal']):
                    macd_signal = "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
                    st.metric("MACD Signal", macd_signal)
                    st.caption(f"MACD: {latest['MACD']:.2f}")
                else:
                    st.metric("MACD Signal", "N/A")
                    st.caption("Insufficient data")
            
            with col3:
                if pd.notna(latest['SMA_21']):
                    sma_trend = "Bullish" if latest['price'] > latest['SMA_21'] else "Bearish"
                    st.metric("SMA Trend", sma_trend)
                    st.caption(f"Price vs SMA21: {((latest['price'] / latest['SMA_21']) - 1) * 100:.1f}%")
                else:
                    st.metric("SMA Trend", "N/A")
                    st.caption("Insufficient data")
            
            with col4:
                if pd.notna(latest['BB_Upper']) and pd.notna(latest['BB_Lower']):
                    bb_position = (latest['price'] - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower'])
                    st.metric("BB Position", f"{bb_position:.2f}")
                    if bb_position > 0.8:
                        st.caption("🔴 Near Upper Band")
                    elif bb_position < 0.2:
                        st.caption("🟢 Near Lower Band")
                    else:
                        st.caption("⚪ Middle Range")
                else:
                    st.metric("BB Position", "N/A")
                    st.caption("Insufficient data")
        
        # Feature Engineering Summary
        st.subheader("ML Features Summary")
        st.markdown("*These indicators will be used as features for price prediction models*")
        
        # Create feature summary with error handling
        if not asset_prices_clean.empty:
            latest = asset_prices_clean.iloc[-1]
            features_df = pd.DataFrame({
                'Feature': ['RSI', 'MACD', 'SMA_7', 'SMA_21', 'Price_Change_1d', 'Price_Change_7d'],
                'Current_Value': [
                    f"{latest['RSI']:.1f}" if pd.notna(latest['RSI']) else 'N/A',
                    f"{latest['MACD']:.2f}" if pd.notna(latest['MACD']) else 'N/A',
                    f"{latest['SMA_7']:.2f}" if pd.notna(latest['SMA_7']) else 'N/A',
                    f"{latest['SMA_21']:.2f}" if pd.notna(latest['SMA_21']) else 'N/A',
                    f"{((latest['price'] / asset_prices_clean['price'].iloc[-2]) - 1) * 100:.1f}%" if len(asset_prices_clean) > 1 else 'N/A',
                    f"{((latest['price'] / asset_prices_clean['price'].iloc[-8]) - 1) * 100:.1f}%" if len(asset_prices_clean) > 7 else 'N/A'
                ],
                'Description': [
                    'Momentum oscillator (0-100)',
                    'Trend following indicator',
                    '7-day simple moving average',
                    '21-day simple moving average',
                    '1-day price change %',
                    '7-day price change %'
                ]
            })
        else:
            features_df = pd.DataFrame({'Feature': ['No data'], 'Current_Value': ['N/A'], 'Description': ['Insufficient price data']})
        
        st.dataframe(features_df, use_container_width=True)



def debug_page():
    st.title("🔧 Debug & System Status")
    st.markdown("*Detailed system information and data validation*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    price_df = loader.load_price_data()
    
    # System Status
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        total_posts = len(df)
        st.metric("Community Posts", f"{total_posts:,}")
    with col3:
        categories = df['category'].nunique() if 'category' in df.columns else 0
        st.metric("Market Categories", categories)
    with col4:
        if 'sentiment_score' in df.columns:
            avg_confidence = df['sentiment_score'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    with col5:
        unique_sources = df['url'].nunique() if 'url' in df.columns else 0
        st.metric("Unique Sources", unique_sources)
    with col6:
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

def trending_opportunities_page():
    add_auto_refresh()  # Enable auto-refresh for trending page
    
    st.title("🔥 Trending Opportunities")
    st.markdown("*Multi-signal detection of emerging investment opportunities*")
    st.markdown("---")
    
    # Risk disclaimer
    st.error("""
    🚨 **EXTREME RISK WARNING**
    
    - This is NOT financial advice
    - Most trending opportunities FAIL (90%+ loss rate)
    - Only invest what you can afford to lose completely
    - Many "opportunities" are pump-and-dump schemes
    - Do your own research before making any decisions
    """)
    
    loader = DataLoader()
    trending_df = loader.load_trending_data()
    
    # Trending data freshness
    if not trending_df.empty and 'detected_at' in trending_df.columns:
        latest_detection = pd.to_datetime(trending_df['detected_at']).max()
        hours_old = (pd.Timestamp.now() - latest_detection).total_seconds() / 3600
        
        if hours_old < 2:
            st.sidebar.markdown(f"🟢 **Trending data**: {hours_old:.1f}h old")
        elif hours_old < 12:
            st.sidebar.markdown(f"🟡 **Trending data**: {hours_old:.1f}h old")
        else:
            st.sidebar.markdown(f"🔴 **Trending data**: {hours_old:.1f}h old")
    
    if trending_df.empty:
        st.warning("No trending opportunities detected. Run the trending detector to find emerging plays.")
        st.info("💡 The system analyzes Reddit mention spikes, volume anomalies, and sentiment shifts to identify potential opportunities before they become mainstream.")
        return
    
    # Filter to recent opportunities (last 24 hours)
    trending_df['detected_at'] = pd.to_datetime(trending_df['detected_at'])
    recent_cutoff = pd.Timestamp.now() - pd.Timedelta(hours=24)
    recent_trending = trending_df[trending_df['detected_at'] >= recent_cutoff].copy()
    
    if recent_trending.empty:
        st.info("No trending opportunities detected in the last 24 hours.")
        st.write("**Historical Opportunities (Last 7 Days):**")
        recent_trending = trending_df.head(10)  # Show last 10 if no recent ones
    
    # Sort by composite score
    recent_trending = recent_trending.sort_values('composite_score', ascending=False)
    
    st.subheader(f"🔥 Top Trending Opportunities ({len(recent_trending)} detected)")
    
    # Display trending opportunities
    for idx, opp in recent_trending.head(10).iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{opp['symbol']}**")
                st.caption(opp['reason'])
            
            with col2:
                st.metric("Score", f"{opp['composite_score']:.2f}")
            
            with col3:
                st.metric("Mentions", f"{opp['recent_mentions']}↑")
            
            with col4:
                alert_colors = {
                    'EXTREME': '🔴',
                    'HIGH': '🟠', 
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                st.write(f"{alert_colors.get(opp['alert_level'], '⚪')} {opp['alert_level']}")
            
            # Risk warning
            if opp['alert_level'] in ['EXTREME', 'HIGH']:
                st.caption(opp['risk_warning'])
            
            st.markdown("---")
    
    # Signal breakdown chart
    if not recent_trending.empty:
        st.subheader("📊 Signal Breakdown (Top 5 Opportunities)")
        
        top_5 = recent_trending.head(5)
        
        # Extract individual scores (assuming they're stored as strings, need to parse)
        signal_data = []
        for idx, opp in top_5.iterrows():
            # Parse individual scores if they exist
            try:
                scores = eval(opp.get('individual_scores', '{}')) if isinstance(opp.get('individual_scores'), str) else opp.get('individual_scores', {})
                signal_data.append({
                    'Symbol': opp['symbol'],
                    'Reddit': scores.get('reddit', 0),
                    'Volume': scores.get('volume', 0),
                    'Price': scores.get('price', 0),
                    'Sentiment': scores.get('sentiment', 0)
                })
            except:
                # Fallback if parsing fails
                signal_data.append({
                    'Symbol': opp['symbol'],
                    'Reddit': opp['composite_score'] * 0.4,  # Approximate based on weights
                    'Volume': opp['composite_score'] * 0.3,
                    'Price': opp['composite_score'] * 0.2,
                    'Sentiment': opp['composite_score'] * 0.1
                })
        
        signals_df = pd.DataFrame(signal_data)
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Add each signal as a separate trace
        fig.add_trace(go.Bar(name='Reddit Mentions', x=signals_df['Symbol'], y=signals_df['Reddit'], marker_color='#FF6B6B'))
        fig.add_trace(go.Bar(name='Volume Spike', x=signals_df['Symbol'], y=signals_df['Volume'], marker_color='#4ECDC4'))
        fig.add_trace(go.Bar(name='Price Movement', x=signals_df['Symbol'], y=signals_df['Price'], marker_color='#45B7D1'))
        fig.add_trace(go.Bar(name='Sentiment Shift', x=signals_df['Symbol'], y=signals_df['Sentiment'], marker_color='#96CEB4'))
        
        fig.update_layout(
            barmode='stack',
            title='Multi-Signal Detection Breakdown',
            xaxis_title='Symbol',
            yaxis_title='Signal Strength (0-1)',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detection methodology
    with st.expander("🔍 How Detection Works"):
        st.markdown("""
        **Multi-Signal Detection Algorithm:**
        
        1. **Reddit Mentions (40%)**: Tracks mention spikes vs 30-day baseline
        2. **Volume Spike (30%)**: Unusual trading volume detection
        3. **Price Movement (20%)**: Significant price changes
        4. **Sentiment Shift (10%)**: Bullish sentiment increases
        
        **Alert Levels:**
        - 🔴 **EXTREME** (0.8+): Market euphoria, likely pump & dump
        - 🟠 **HIGH** (0.6-0.8): High volatility, significant risk
        - 🟡 **MEDIUM** (0.4-0.6): Elevated activity, moderate risk
        - 🟢 **LOW** (0.0-0.4): Minor elevation above normal
        
        **Data Sources:**
        - Reddit: wallstreetbets, investing, cryptocurrency, etc.
        - Price/Volume: Yahoo Finance, CoinGecko APIs
        - Sentiment: FinBERT analysis of social discussions
        """)

def tesla_watch_page():
    st.title("⚡ Tesla Watch")
    st.markdown("*Dedicated Tesla sentiment and risk analysis*")
    st.markdown("---")
    
    # Tesla warning banner
    st.error("""
    🚨 **TESLA RISK ASSESSMENT: HIGH VOLATILITY**
    
    Tesla exhibits extreme price swings driven by:
    - Elon Musk's social media activity and public statements
    - EV market competition and regulatory changes
    - Autonomous driving promises vs reality
    - Valuation disconnect from traditional auto metrics
    - Retail investor sentiment and meme stock behavior
    """)
    
    loader = DataLoader()
    df = loader.load_processed_data()
    price_df = loader.load_price_data()
    
    if df.empty:
        st.warning("No data available. Run the data collection pipeline.")
        return
    
    # Filter Tesla-related posts
    tesla_keywords = ['tesla', 'tsla', 'elon', 'musk', 'cybertruck', 'model 3', 'model y', 'model s', 'autopilot', 'fsd']
    tesla_pattern = '|'.join(tesla_keywords)
    
    # Search in title and content (handle NaN values)
    tesla_posts = df[
        df['title'].astype(str).str.contains(tesla_pattern, case=False, na=False) |
        df['content'].astype(str).str.contains(tesla_pattern, case=False, na=False)
    ].copy()
    
    if tesla_posts.empty:
        st.warning("No Tesla-related posts found in recent data.")
        return
    
    # Tesla metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tesla Posts", len(tesla_posts))
    
    with col2:
        if 'sentiment_label' in tesla_posts.columns:
            bullish_pct = (tesla_posts['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
            st.metric("Bullish Sentiment", f"{bullish_pct:.0f}%")
    
    with col3:
        # Get TSLA price if available
        if not price_df.empty and 'symbol' in price_df.columns:
            tsla_price = price_df[price_df['symbol'] == 'TSLA']
            if not tsla_price.empty:
                latest_price = tsla_price['price'].iloc[-1]
                st.metric("TSLA Price", f"${latest_price:.2f}")
            else:
                st.metric("TSLA Price", "N/A")
        else:
            st.metric("TSLA Price", "N/A")
    
    with col4:
        # Community spread
        if 'subreddit' in tesla_posts.columns:
            communities = tesla_posts['subreddit'].nunique()
            st.metric("Communities", communities)
        else:
            st.metric("Communities", "N/A")
    
    # Tesla sentiment gauge
    if 'sentiment_label' in tesla_posts.columns:
        st.subheader("⚡ Tesla Sentiment Pulse")
        
        bullish_pct = (tesla_posts['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
        neutral_pct = (tesla_posts['sentiment_label'] == '3 stars').mean() * 100
        bearish_pct = (tesla_posts['sentiment_label'].isin(['1 star', '2 stars'])).mean() * 100
        needle_value = bullish_pct + (neutral_pct * 0.5)
        
        import plotly.graph_objects as go
        
        fig = create_sentiment_gauge(
            value=needle_value,
            title="Tesla Community Sentiment",
            size='large'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tesla-specific interpretation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if needle_value >= 80:
                st.error("🚨 **EXTREME EUPHORIA** - Peak hype, potential crash risk")
                st.caption("⚠️ Contrarian signal: Consider taking profits")
            elif needle_value >= 60:
                st.success("🚀 **BULLISH MOMENTUM** - Positive Tesla sentiment")
            elif needle_value >= 40:
                st.info("⚖️ **MIXED SIGNALS** - Tesla sentiment uncertain")
            elif needle_value >= 20:
                st.warning("📉 **BEARISH TREND** - Negative Tesla sentiment")
            else:
                st.error("🔥 **PANIC MODE** - Extreme fear, potential bounce")
                st.caption("💰 Contrarian signal: Possible buying opportunity")
    
    # Recent Tesla posts
    st.subheader("📝 Recent Tesla Discussions")
    
    # Sort by timestamp and show recent posts
    if 'timestamp' in tesla_posts.columns:
        tesla_posts['timestamp'] = pd.to_datetime(tesla_posts['timestamp'])
        recent_tesla = tesla_posts.sort_values('timestamp', ascending=False).head(10)
    else:
        recent_tesla = tesla_posts.head(10)
    
    for idx, post in recent_tesla.iterrows():
        # Check if this is a Bluesky or Reddit post
        platform = post.get('platform', 'reddit')
        
        if platform == 'bluesky':
            author = post.get('author_handle', 'unknown')
            source_display = f"@{author}"
            # Bluesky metrics
            likes = post.get('like_count', 0)
            reposts = post.get('repost_count', 0)
            metrics = f"Likes: {likes} | Reposts: {reposts}"
        else:
            # Reddit post
            subreddit = post.get('subreddit', 'unknown')
            if pd.isna(subreddit) or str(subreddit).lower() == 'nan':
                subreddit = 'unknown'
            source_display = f"r/{subreddit}"
            # Reddit metrics
            score = post.get('score', 'N/A')
            comments = post.get('num_comments', 'N/A')
            metrics = f"Score: {score} | Comments: {comments}"
        
        with st.expander(f"{source_display} - {post.get('sentiment_label', 'N/A')}"):
            if pd.notna(post.get('content')) and len(str(post.get('content'))) > 0:
                content = str(post.get('content'))[:300] + "..." if len(str(post.get('content'))) > 300 else str(post.get('content'))
                st.write(content)
            st.caption(f"Sentiment: {post.get('sentiment_label', 'N/A')} | {metrics}")
    
    # Tesla risk factors
    st.subheader("⚠️ Tesla-Specific Risk Factors")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📈 Volatility Drivers:**
        - Elon Musk tweets and public statements
        - Quarterly delivery numbers vs expectations
        - FSD/Autopilot regulatory developments
        - Competition from traditional automakers
        - China market dynamics and regulations
        """)
    
    with col2:
        st.markdown("""
        **🚨 Warning Signs to Watch:**
        - Extreme sentiment spikes (>80% or <20%)
        - Delivery guidance cuts or misses
        - Regulatory investigations or recalls
        - Key executive departures
        - Margin compression in core business
        """)
    
    # Tesla vs market comparison
    if not price_df.empty:
        st.subheader("📉 Tesla vs Market Performance")
        
        # Get Tesla and SPY data if available
        tsla_data = price_df[price_df['symbol'] == 'TSLA'].copy()
        spy_data = price_df[price_df['symbol'] == 'SPY'].copy()
        
        if not tsla_data.empty and not spy_data.empty:
            # Simple comparison chart
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            tsla_data['timestamp'] = pd.to_datetime(tsla_data['timestamp'])
            spy_data['timestamp'] = pd.to_datetime(spy_data['timestamp'])
            
            fig.add_trace(go.Scatter(
                x=tsla_data['timestamp'],
                y=tsla_data['price'],
                mode='lines',
                name='TSLA',
                line=dict(color='red', width=3)
            ), secondary_y=False)
            
            fig.add_trace(go.Scatter(
                x=spy_data['timestamp'],
                y=spy_data['price'],
                mode='lines',
                name='SPY (S&P 500)',
                line=dict(color='blue', width=2)
            ), secondary_y=True)
            
            fig.update_layout(title="Tesla vs S&P 500 Performance")
            fig.update_yaxes(title_text="TSLA Price ($)", secondary_y=False)
            fig.update_yaxes(title_text="SPY Price ($)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tesla price data not available for comparison")
    
    # Disclaimer
    st.markdown("---")
    st.error("""
    ⚠️ **TESLA INVESTMENT DISCLAIMER**
    
    Tesla is an extremely volatile stock with unique risks:
    - High correlation with Elon Musk's public statements
    - Regulatory risks in autonomous driving
    - Intense competition in EV market
    - Valuation based on future promises, not current fundamentals
    
    This analysis is for informational purposes only and not financial advice.
    """)

def ipo_page():
    st.title("🏢 IPO Tracker")
    st.markdown("*Sentiment analysis for recent and upcoming IPOs*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    
    if df.empty:
        st.warning("No data available. Please run the data collection pipeline.")
        return
    
    # IPO symbols to track
    ipo_symbols = ['BLSH', 'RIVN', 'LCID', 'HOOD', 'COIN', 'RBLX']
    
    # Filter IPO-related posts
    ipo_keywords = ['ipo', 'bullish', 'blsh'] + [s.lower() for s in ipo_symbols]
    ipo_pattern = '|'.join(ipo_keywords)
    
    ipo_posts = df[
        df['title'].astype(str).str.contains(ipo_pattern, case=False, na=False) |
        df['content'].astype(str).str.contains(ipo_pattern, case=False, na=False)
    ].copy()
    
    # IPO Sentiment Grid (3x3)
    st.subheader("📊 IPO Sentiment Dashboard")
    
    # Track 9 IPO symbols
    ipo_symbols = ['BLSH', 'RIVN', 'LCID', 'HOOD', 'COIN', 'RBLX', 'SNOW', 'ABNB', 'UBER']
    
    import plotly.graph_objects as go
    
    # Create 3x3 grid
    for row in range(3):
        cols = st.columns(3)
        for col_idx in range(3):
            symbol_idx = row * 3 + col_idx
            if symbol_idx < len(ipo_symbols):
                symbol = ipo_symbols[symbol_idx]
                
                with cols[col_idx]:
                    # Filter posts for this symbol
                    symbol_posts = df[
                        df['title'].astype(str).str.contains(symbol.lower(), case=False, na=False) |
                        df['content'].astype(str).str.contains(symbol.lower(), case=False, na=False)
                    ].copy()
                    
                    # Check if posts have sentiment data
                    has_sentiment = not symbol_posts.empty and 'sentiment_label' in symbol_posts.columns and not symbol_posts['sentiment_label'].isna().all()
                    
                    if has_sentiment:
                        # Filter out posts with NaN sentiment
                        symbol_posts = symbol_posts[symbol_posts['sentiment_label'].notna()]
                        
                        if not symbol_posts.empty:
                            bullish_pct = (symbol_posts['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
                            neutral_pct = (symbol_posts['sentiment_label'] == '3 stars').mean() * 100
                            needle_value = bullish_pct + (neutral_pct * 0.5)
                            post_count = len(symbol_posts)
                            

                            
                            # Mini gauge with standardized function
                            fig = create_sentiment_gauge(
                                value=needle_value,
                                title=symbol,
                                size='mini'
                            )
                            fig.update_layout(height=180, margin=dict(l=5, r=5, t=35, b=5))
                            st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"{post_count} posts")
                            
                            # Add voting widget
                            voting_system = VotingSystem()
                            voting_system.render_voting_widget("ipo", symbol)
                        else:
                            # Posts found but no valid sentiment
                            st.write(f"**{symbol}**")
                            st.write("📊")
                            st.caption("No Sentiment")
                            
                            # Add voting widget
                            voting_system = VotingSystem()
                            voting_system.render_voting_widget("ipo", symbol)
                    else:
                        # No data - show placeholder
                        st.write(f"**{symbol}**")
                        st.write("📊")
                        st.caption("No Data")
                        
                        # Add voting widget
                        voting_system = VotingSystem()
                        voting_system.render_voting_widget("ipo", symbol)
        
    # Recent IPO discussions
    st.subheader("📝 Recent IPO Discussions")
    
    if not ipo_posts.empty:
        if 'timestamp' in ipo_posts.columns:
            ipo_posts['timestamp'] = pd.to_datetime(ipo_posts['timestamp'])
            recent_ipo = ipo_posts.sort_values('timestamp', ascending=False).head(5)
        else:
            recent_ipo = ipo_posts.head(5)
        
        for idx, post in recent_ipo.iterrows():
            # Check if this is a Bluesky or Reddit post
            platform = post.get('platform', 'reddit')
            
            if platform == 'bluesky':
                author = post.get('author_handle', 'unknown')
                source_display = f"@{author}"
            else:
                subreddit = post.get('subreddit', 'unknown')
                if pd.isna(subreddit) or str(subreddit).lower() == 'nan':
                    subreddit = 'unknown'
                source_display = f"r/{subreddit}"
            
            with st.expander(f"{source_display} - {post.get('sentiment_label', 'N/A')}"):
                if pd.notna(post.get('content')) and len(str(post.get('content'))) > 0:
                    content = str(post.get('content'))[:200] + "..." if len(str(post.get('content'))) > 200 else str(post.get('content'))
                    st.write(content)
                st.caption(f"Sentiment: {post.get('sentiment_label', 'N/A')} | Platform: {platform.title()}")
    else:
        st.info("No IPO-related posts found in recent data.")
        st.caption("The system will start tracking IPO sentiment as discussions emerge.")
    
    st.markdown("---")
    
    # Other IPO tracking
    st.subheader("📈 Other IPO Sentiment")
    
    if not ipo_posts.empty:
        # IPO category breakdown
        other_ipos = ipo_posts[~ipo_posts['title'].astype(str).str.contains('bullish|blsh', case=False, na=False)]
        
        if not other_ipos.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Other IPO Posts", len(other_ipos))
                if 'sentiment_label' in other_ipos.columns:
                    other_bullish = (other_ipos['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
                    st.metric("Avg Bullish %", f"{other_bullish:.0f}%")
            
            with col2:
                # Most mentioned IPO symbols
                all_text = " ".join(other_ipos['title'].astype(str) + " " + other_ipos['content'].astype(str))
                symbol_mentions = {}
                for symbol in ipo_symbols:
                    if symbol != 'BLSH':
                        count = all_text.upper().count(symbol)
                        if count > 0:
                            symbol_mentions[symbol] = count
                
                if symbol_mentions:
                    top_symbol = max(symbol_mentions, key=symbol_mentions.get)
                    st.metric("Most Mentioned", f"{top_symbol} ({symbol_mentions[top_symbol]})")
        else:
            st.info("No other IPO discussions found.")
    
    # IPO risk warning
    st.markdown("---")
    st.error("""
    ⚠️ **IPO INVESTMENT RISKS**
    
    IPOs carry significant risks:
    - Limited trading history and price discovery
    - Lock-up period expirations can cause selling pressure
    - Hype-driven pricing often leads to volatility
    - Insider selling after lock-up periods
    - Market conditions can dramatically affect performance
    
    This analysis is for informational purposes only.
    """)

def ai_insights_page():
    st.title("🧠 AI Insights")
    st.markdown("*What the AI is seeing in financial discussions*")
    st.markdown("---")
    
    loader = DataLoader()
    df = loader.load_processed_data()
    
    if df.empty:
        st.warning("No data available for AI analysis.")
        return
    
    # Word frequency analysis
    st.subheader("📝 Most Common Words")
    
    # Combine all text content
    all_text = ""
    for _, row in df.iterrows():
        title = str(row.get('title', ''))
        content = str(row.get('content', ''))
        all_text += f" {title} {content}"
    
    # Basic word processing
    import re
    words = re.findall(r'\b\w+\b', all_text.lower())
    
    # Filter out common stop words and nan values
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'nan', 'none', 'null'}
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2 and word != 'nan']
    
    # Count word frequency
    from collections import Counter
    word_counts = Counter(filtered_words)
    
    # Display top words
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 20 Words:**")
        top_words = word_counts.most_common(20)
        for word, count in top_words:
            st.write(f"{word}: {count}")
    
    with col2:
        # Top financial terms chart
        if top_words:
            import plotly.graph_objects as go
            
            # Create bar chart of top 10 words
            top_10 = top_words[:10]
            words, counts = zip(*top_10)
            
            fig = go.Figure(data=[
                go.Bar(x=list(words), y=list(counts), marker_color='#FF9500')
            ])
            fig.update_layout(
                title="Top Financial Terms",
                xaxis_title="Words",
                yaxis_title="Frequency",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No words to display")
    
    # Sentiment by category analysis
    if 'category' in df.columns and 'sentiment_label' in df.columns:
        st.subheader("📈 AI Sentiment Analysis by Category")
        
        category_sentiment = df.groupby(['category', 'sentiment_label']).size().unstack(fill_value=0)
        
        import plotly.express as px
        
        # Convert to percentage
        category_sentiment_pct = category_sentiment.div(category_sentiment.sum(axis=1), axis=0) * 100
        
        fig = px.bar(category_sentiment_pct, 
                    title="AI Sentiment Distribution by Category",
                    labels={'value': 'Percentage', 'index': 'Category'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent AI processing stats
    st.subheader("🤖 AI Processing Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Texts Analyzed", len(df))
    
    with col2:
        if 'sentiment_score' in df.columns:
            avg_confidence = df['sentiment_score'].mean()
            st.metric("Avg AI Confidence", f"{avg_confidence:.3f}")
    
    with col3:
        unique_words = len(set(filtered_words))
        st.metric("Unique Words Found", unique_words)
    
    with col4:
        if 'sentiment_label' in df.columns:
            sentiment_variety = df['sentiment_label'].nunique()
            st.metric("Sentiment Categories", sentiment_variety)

def main():
    # Back to main site link
    st.sidebar.markdown("---")
    st.sidebar.markdown("🏠 [← Back to elikloft.com](https://elikloft.com)")
    st.sidebar.markdown("---")
    
    # Connection status
    try:
        loader = DataLoader()
        # Quick connection test
        test_df = loader.load_processed_data()
        if not test_df.empty:
            st.sidebar.markdown("🟢 **Status**: Connected")
        else:
            st.sidebar.markdown("🟡 **Status**: No data")
    except:
        st.sidebar.markdown("🔴 **Status**: Connection error")
    
    st.sidebar.markdown("---")
    
    # Auto-refresh toggle
    auto_refresh_enabled = st.sidebar.checkbox("🔄 Auto-refresh (1 hour)", value=True)
    if not auto_refresh_enabled:
        # Override the global setting
        global AUTO_REFRESH_INTERVAL
        AUTO_REFRESH_INTERVAL = 0
    
    # Manual cache clear button
    if st.sidebar.button("🔄 Force Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Page navigation
    page = st.sidebar.selectbox("Navigate", ["📊 Insights", "🏢 IPOs", "📅 Monthly Predictions", "📈 Indicators", "🌍 Macro Analysis", "🧠 AI Insights", "⚡ Tesla Watch", "🔧 Debug"], key="page_nav")
    
    if page == "📊 Insights":
        presentation_page()
    elif page == "🏢 IPOs":
        ipo_page()
    elif page == "📅 Monthly Predictions":
        monthly_predictions_page()

    elif page == "📈 Indicators":
        indicators_page()
    elif page == "🌍 Macro Analysis":
        macro_analysis_page()
    elif page == "🧠 AI Insights":
        ai_insights_page()
    elif page == "⚡ Tesla Watch":
        tesla_watch_page()
    else:
        debug_page()

if __name__ == "__main__":
    main()