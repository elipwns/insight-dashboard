import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import DataLoader
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

st.set_page_config(
    page_title="Trading Insights",
    page_icon="📊",
    layout="wide"
)

# Auto-refresh configuration
AUTO_REFRESH_INTERVAL = 21600  # 6 hours in seconds (4x daily checks)

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
        refresh_time = datetime.now().strftime('%H:%M:%S')
        next_refresh = (datetime.now() + timedelta(seconds=AUTO_REFRESH_INTERVAL)).strftime('%H:%M')
        st.sidebar.markdown(f"⏰ **Last updated**: {refresh_time}")
        st.sidebar.markdown(f"⏱️ **Next refresh**: {next_refresh} (6h)")
        
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
    
    # Manual refresh button (always available)
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()

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
        
        # Calculate last week sentiment for comparison
        week_ago_cutoff = pd.Timestamp.now() - pd.Timedelta(days=10)
        last_week_cutoff = pd.Timestamp.now() - pd.Timedelta(days=3)
        last_week_df = df[(df['timestamp'] >= week_ago_cutoff) & (df['timestamp'] < last_week_cutoff)].copy()
        
        if not last_week_df.empty:
            last_week_bullish = (last_week_df['sentiment_label'].isin(['4 stars', '5 stars'])).mean() * 100
            last_week_neutral = (last_week_df['sentiment_label'] == '3 stars').mean() * 100
            last_week_needle = last_week_bullish + (last_week_neutral * 0.5)
        else:
            last_week_needle = 50  # Default to neutral if no data
        
        st.subheader("🌡️ Market Sentiment Gauge")
        
        import plotly.graph_objects as go
        
        # Create enhanced gauge with fire danger styling
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = needle_value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {
                'text': "<b>Market Sentiment</b><br><span style='font-size:0.8em;color:gray'>Community Pulse</span>",
                'font': {'size': 24}
            },
            delta = {'reference': last_week_needle, 'valueformat': '.0f', 'suffix': ' vs last week'},
            number = {'valueformat': '.0f', 'suffix': '%', 'font': {'size': 40}},
            gauge = {
                'axis': {
                    'range': [None, 100],
                    'tickwidth': 1,
                    'tickcolor': "darkblue",
                    'tickmode': 'array',
                    'tickvals': [0, 20, 40, 60, 80, 100],
                    'ticktext': ['0', '20', '40', '60', '80', '100']
                },
                'bar': {'color': "darkblue", 'thickness': 0.2},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 20], 'color': "#DC143C"},    # Extreme Bearish (Dark Red)
                    {'range': [20, 40], 'color': "#FF6347"},   # Bearish (Tomato)
                    {'range': [40, 60], 'color': "#FFD700"},   # Neutral (Gold)
                    {'range': [60, 80], 'color': "#32CD32"},   # Bullish (Lime Green)
                    {'range': [80, 100], 'color': "#228B22"}   # Extreme Bullish (Forest Green)
                ]
            }
        ))
        
        fig.update_layout(
            height=400,
            font={'color': "black", 'family': "Arial"},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
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
                
                # Market category analysis with custom ordering (recent data only)
                category_sentiment = recent_df.groupby(['category', 'sentiment_category']).size().unstack(fill_value=0)
                category_sentiment_pct = category_sentiment.div(category_sentiment.sum(axis=1), axis=0) * 100
                
                # Custom category order: alphabetical except OTHER at end
                category_order = ['CRYPTO', 'ECONOMICS', 'US_STOCKS']
                if 'OTHER' in category_sentiment_pct.index:
                    category_order.append('OTHER')
                
                # Reorder the dataframe
                category_sentiment_pct = category_sentiment_pct.reindex([cat for cat in category_order if cat in category_sentiment_pct.index])
                
                # Category descriptions
                st.markdown("""
                **Category Definitions:**
                - **CRYPTO**: Digital assets and blockchain (Bitcoin, Ethereum, general crypto)
                - **ECONOMICS**: Macro trends and long-term wealth (economic policy, FIRE movement)
                - **US_STOCKS**: Traditional equity markets (WSB, r/investing, r/stocks, value investing)
                - **OTHER**: Miscellaneous financial discussions not categorized above
                """)
                
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                # Create individual gauges for each category
                categories = category_sentiment_pct.index
                num_categories = len(categories)
                
                if num_categories > 0:
                    cols = st.columns(num_categories)
                    
                    for i, category in enumerate(categories):
                        with cols[i]:
                            # Calculate category sentiment
                            cat_bullish = category_sentiment_pct.loc[category, 'Bullish'] if 'Bullish' in category_sentiment_pct.columns else 0
                            cat_neutral = category_sentiment_pct.loc[category, 'Neutral'] if 'Neutral' in category_sentiment_pct.columns else 0
                            cat_needle = cat_bullish + (cat_neutral * 0.5)
                            
                            # Create mini gauge for category
                            fig_cat = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = cat_needle,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': f"<b>{category}</b>", 'font': {'size': 16}},
                                number = {'valueformat': '.0f', 'suffix': '%', 'font': {'size': 24}},
                                gauge = {
                                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                                    'bar': {'color': "darkblue", 'thickness': 0.15},
                                    'bgcolor': "white",
                                    'borderwidth': 1,
                                    'bordercolor': "gray",
                                    'steps': [
                                        {'range': [0, 20], 'color': "#DC143C"},
                                        {'range': [20, 40], 'color': "#FF6347"},
                                        {'range': [40, 60], 'color': "#FFD700"},
                                        {'range': [60, 80], 'color': "#32CD32"},
                                        {'range': [80, 100], 'color': "#228B22"}
                                    ]
                                }
                            ))
                            
                            fig_cat.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig_cat, use_container_width=True)
                            
                            # Show breakdown percentages
                            st.caption(f"🟢 {cat_bullish:.0f}% • ⚪ {cat_neutral:.0f}% • 🔴 {category_sentiment_pct.loc[category, 'Bearish'] if 'Bearish' in category_sentiment_pct.columns else 0:.0f}%")
    
    st.markdown("---")
    
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

def predictions_page():
    st.title("🔮 Price Predictions")
    st.markdown("*AI-powered price forecasting (Demo)*")
    st.markdown("---")
    
    # Demo predictions with synthetic data
    st.info("📊 **Demo Mode**: Using synthetic data for model demonstration")
    
    # Asset selector
    asset = st.selectbox("Select Asset:", ['BTC', 'ETH'], key="pred_asset")
    
    # Generate demo predictions
    import numpy as np
    np.random.seed(42)
    
    current_price = 102000 if asset == 'BTC' else 3800
    
    # Prediction timeframes with confidence
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pred_1h = current_price * (1 + np.random.normal(0.001, 0.01))
        change_1h = ((pred_1h - current_price) / current_price) * 100
        st.metric("1 Hour", f"${pred_1h:.0f}", f"{change_1h:+.2f}%")
        st.caption("Confidence: 65%")
    
    with col2:
        pred_1d = current_price * (1 + np.random.normal(0.02, 0.03))
        change_1d = ((pred_1d - current_price) / current_price) * 100
        st.metric("1 Day", f"${pred_1d:.0f}", f"{change_1d:+.2f}%")
        st.caption("Confidence: 58%")
    
    with col3:
        pred_3d = current_price * (1 + np.random.normal(0.05, 0.05))
        change_3d = ((pred_3d - current_price) / current_price) * 100
        st.metric("3 Days", f"${pred_3d:.0f}", f"{change_3d:+.2f}%")
        st.caption("Confidence: 52%")
    
    with col4:
        pred_7d = current_price * (1 + np.random.normal(0.08, 0.08))
        change_7d = ((pred_7d - current_price) / current_price) * 100
        st.metric("7 Days", f"${pred_7d:.0f}", f"{change_7d:+.2f}%")
        st.caption("Confidence: 48%")
    
    st.markdown("---")
    
    # Model Performance Section
    st.subheader("🎯 Model Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Direction Accuracy (Last 30 Days)**")
        st.metric("Correct Predictions", "17/30", "57%")
        st.progress(0.57)
        
        st.markdown("**Feature Importance**")
        features_df = pd.DataFrame({
            'Feature': ['Sentiment Mean', 'RSI', 'Volume Ratio', 'SMA 7'],
            'Importance': [0.28, 0.25, 0.24, 0.23]
        })
        
        import plotly.express as px
        fig = px.bar(features_df, x='Importance', y='Feature', orientation='h')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Return Prediction Error**")
        st.metric("Mean Absolute Error", "4.2%", "-0.8%")
        st.progress(0.75)  # Lower error = better (inverted)
        
        st.markdown("**Model Status**")
        st.success("✅ Models trained and active")
        st.info("📊 Training data: 99 samples")
        st.warning("⚠️ Demo mode - not for trading")
    
    st.markdown("---")
    
    # Prediction Chart
    st.subheader("📈 Prediction Visualization")
    
    # Generate sample historical + prediction data ending today
    from datetime import datetime, timedelta
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=39)
    dates = pd.date_range(start=start_date, end=end_date + timedelta(days=10), freq='D')
    historical_prices = []
    price = current_price * 0.92
    
    for i in range(30):  # 30 days historical
        price *= (1 + np.random.normal(0.01, 0.02))
        historical_prices.append(price)
    
    # Future predictions
    future_prices = []
    for i in range(10):  # 10 days future
        price *= (1 + np.random.normal(0.015, 0.025))
        future_prices.append(price)
    
    # Create chart
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Historical prices
    fig.add_trace(go.Scatter(
        x=dates[:30],
        y=historical_prices,
        mode='lines',
        name='Historical Price',
        line=dict(color='white', width=3)
    ))
    
    # Predicted prices
    fig.add_trace(go.Scatter(
        x=dates[29:],  # Overlap last historical point
        y=[historical_prices[-1]] + future_prices,
        mode='lines',
        name='Predicted Price',
        line=dict(color='orange', width=3, dash='dash')
    ))
    
    # Confidence bands - fan out from current price like a triangle
    current_price_point = historical_prices[-1]
    future_dates = dates[29:]
    
    # Create expanding confidence bands that start narrow and widen over time
    upper_band = []
    lower_band = []
    
    for i, (date, price) in enumerate(zip(future_dates, [current_price_point] + future_prices)):
        # Expand uncertainty linearly with time (starts at 1% and grows to 15%)
        uncertainty = 0.01 + (i * 0.014)  # 1% to 15% over 10 days
        upper_band.append(price * (1 + uncertainty))
        lower_band.append(price * (1 - uncertainty))
    
    fig.add_trace(go.Scatter(
        x=dates[29:],
        y=upper_band,
        fill=None,
        mode='lines',
        line_color='rgba(0,0,0,0)',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=dates[29:],
        y=lower_band,
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,0,0,0)',
        name='Confidence Band',
        fillcolor='rgba(255,165,0,0.2)'
    ))
    
    fig.update_layout(
        title=f"{asset} Price Prediction",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Disclaimers
    st.markdown("---")
    st.error("⚠️ **IMPORTANT DISCLAIMERS**")
    st.markdown("""
    - This is NOT financial advice
    - Demo mode with synthetic data
    - Models are experimental and unvalidated
    - Do not use for actual trading decisions
    - Past performance does not predict future results
    """)

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
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = needle_value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "<b>Tesla Community Sentiment</b>", 'font': {'size': 20}},
            number = {'valueformat': '.0f', 'suffix': '%', 'font': {'size': 32}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "red", 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 20], 'color': "#8B0000"},    # Dark Red
                    {'range': [20, 40], 'color': "#DC143C"},   # Crimson
                    {'range': [40, 60], 'color': "#FFD700"},   # Gold
                    {'range': [60, 80], 'color': "#32CD32"},   # Lime Green
                    {'range': [80, 100], 'color': "#228B22"}   # Forest Green
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=350, font={'color': "black"})
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
        subreddit = str(post.get('subreddit', 'unknown'))
        with st.expander(f"r/{subreddit} - {post.get('sentiment_label', 'N/A')}"):
            title = str(post.get('title', 'No title'))
            title = title[:100] + "..." if len(title) > 100 else title
            st.write(f"**{title}**")
            if pd.notna(post.get('content')) and len(str(post.get('content'))) > 0:
                content = str(post.get('content'))[:300] + "..." if len(str(post.get('content'))) > 300 else str(post.get('content'))
                st.write(content)
            st.caption(f"Sentiment: {post.get('sentiment_label', 'N/A')} | Score: {post.get('score', 'N/A')} | Comments: {post.get('num_comments', 'N/A')}")
    
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
    auto_refresh_enabled = st.sidebar.checkbox("🔄 Auto-refresh (6 hours)", value=True)
    if not auto_refresh_enabled:
        # Override the global setting
        global AUTO_REFRESH_INTERVAL
        AUTO_REFRESH_INTERVAL = 0
    
    # Page navigation
    page = st.sidebar.selectbox("Navigate", ["📊 Insights", "🔮 Predictions", "🔥 Trending", "📈 Indicators", "🌍 Macro Analysis", "🧠 AI Insights", "⚡ Tesla Watch", "🔧 Debug"], key="page_nav")
    
    if page == "📊 Insights":
        presentation_page()
    elif page == "🔮 Predictions":
        predictions_page()
    elif page == "🔥 Trending":
        trending_opportunities_page()
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