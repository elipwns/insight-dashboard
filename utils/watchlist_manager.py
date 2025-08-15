#!/usr/bin/env python3
"""
Simple Watchlist Manager
Allows users to add/remove stocks from tracking
"""

import boto3
import json
import streamlit as st
import os

class WatchlistManager:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.watchlist_key = "user_data/watchlists.json"
    
    def load_watchlists(self):
        """Load all user watchlists"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.watchlist_key
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except:
            return {"users": {}}
    
    def save_watchlists(self, data):
        """Save watchlists to S3"""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.watchlist_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
    
    def add_stock(self, user_name, symbol):
        """Add stock to user's watchlist (max 20 stocks per user)"""
        data = self.load_watchlists()
        if user_name not in data["users"]:
            data["users"][user_name] = {"stocks": []}
        
        # Limit to 20 stocks per user
        if len(data["users"][user_name]["stocks"]) >= 20:
            return False
        
        symbol = symbol.upper().strip()
        if symbol not in data["users"][user_name]["stocks"]:
            data["users"][user_name]["stocks"].append(symbol)
            self.save_watchlists(data)
            return True
        return False
    
    def remove_stock(self, user_name, symbol):
        """Remove stock from user's watchlist"""
        data = self.load_watchlists()
        if user_name in data["users"]:
            symbol = symbol.upper().strip()
            if symbol in data["users"][user_name]["stocks"]:
                data["users"][user_name]["stocks"].remove(symbol)
                self.save_watchlists(data)
                return True
        return False
    
    def get_user_stocks(self, user_name):
        """Get user's watchlist"""
        data = self.load_watchlists()
        return data["users"].get(user_name, {}).get("stocks", [])
    
    def get_all_tracked_stocks(self):
        """Get all stocks being tracked by any user"""
        data = self.load_watchlists()
        all_stocks = set()
        for user_data in data["users"].values():
            all_stocks.update(user_data.get("stocks", []))
        return list(all_stocks)
    
    def render_watchlist_widget(self, user_name="default"):
        """Render watchlist management widget"""
        st.subheader(f"📋 {user_name.title()}'s Watchlist")
        
        # Current watchlist
        stocks = self.get_user_stocks(user_name)
        if stocks:
            cols = st.columns(min(len(stocks), 4))
            for i, stock in enumerate(stocks):
                with cols[i % 4]:
                    if st.button(f"❌ {stock}", key=f"remove_{stock}_{user_name}"):
                        if self.remove_stock(user_name, stock):
                            st.success(f"Removed {stock}")
                            st.rerun()
        else:
            st.info("No stocks in watchlist yet")
        
        # Add new stock
        col1, col2 = st.columns([3, 1])
        with col1:
            new_stock = st.text_input("Add stock symbol:", placeholder="AAPL", key=f"add_stock_{user_name}")
        with col2:
            if st.button("Add", key=f"add_btn_{user_name}"):
                if new_stock:
                    result = self.add_stock(user_name, new_stock)
                    if result:
                        st.success(f"Added {new_stock.upper()}")
                        st.rerun()
                    else:
                        stocks = self.get_user_stocks(user_name)
                        if len(stocks) >= 20:
                            st.error("Watchlist full (20 stock limit)")
                        else:
                            st.warning(f"{new_stock.upper()} already in watchlist")
        
        return stocks