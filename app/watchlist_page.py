import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.watchlist_manager import WatchlistManager
from utils.data_loader import DataLoader

def watchlist_page():
    st.title("📋 User Watchlists")
    st.markdown("*Manage stock watchlists for enhanced tracking*")
    st.markdown("---")
    
    # Load data and show freshness
    loader = DataLoader()
    df = loader.load_processed_data()
    loader.show_data_freshness(df)
    
    watchlist_manager = WatchlistManager()
    
    # User selection
    user_name = st.selectbox("Select User:", ["jack", "eli", "guest"], index=0)
    
    # Render watchlist widget
    stocks = watchlist_manager.render_watchlist_widget(user_name)
    
    st.markdown("---")
    
    # Show all tracked stocks
    st.subheader("🎯 All Tracked Stocks")
    all_stocks = watchlist_manager.get_all_tracked_stocks()
    
    if all_stocks:
        # Display in columns
        cols = st.columns(4)
        for i, stock in enumerate(sorted(all_stocks)):
            with cols[i % 4]:
                st.code(stock)
        
        st.info(f"📊 **{len(all_stocks)} stocks** are being tracked across all users")
    else:
        st.info("No stocks in any watchlists yet")
    
    # Instructions
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        **Adding Stocks:**
        - Enter any stock symbol (e.g., AAPL, TSLA, SPY)
        - Stocks are automatically tracked in trending detection
        - All users' stocks are combined for analysis
        
        **Integration:**
        - Added stocks appear in trending tickers analysis
        - Sentiment analysis includes watchlist stocks
        - Data updates with next collection cycle
        
        **Multi-User:**
        - Each user has their own watchlist
        - All watchlists are combined for system tracking
        - Easy to manage different interests
        """)