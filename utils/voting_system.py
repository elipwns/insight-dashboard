#!/usr/bin/env python3
"""
Simple voting system for sentiment gauges
Stores votes in S3 as JSON files
"""

import boto3
import json
import streamlit as st
from datetime import datetime
import os

class VotingSystem:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    def load_votes(self, category, symbol=None):
        """Load existing votes for a category/symbol"""
        key = f"votes/{category}_{symbol}.json" if symbol else f"votes/{category}.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except:
            return {"bullish": 0, "bearish": 0, "votes": []}
    
    def save_vote(self, category, sentiment, symbol=None):
        """Save a new vote"""
        votes_data = self.load_votes(category, symbol)
        
        # Add vote
        if sentiment == "bullish":
            votes_data["bullish"] += 1
        else:
            votes_data["bearish"] += 1
        
        # Store vote details
        votes_data["votes"].append({
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": st.session_state.get("session_id", "anonymous")
        })
        
        # Save to S3
        key = f"votes/{category}_{symbol}.json" if symbol else f"votes/{category}.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(votes_data, indent=2),
            ContentType='application/json'
        )
        
        return votes_data
    
    def render_voting_widget(self, category, symbol=None, label="Community Sentiment"):
        """Render voting buttons and results"""
        votes_data = self.load_votes(category, symbol)
        
        total_votes = votes_data["bullish"] + votes_data["bearish"]
        bullish_pct = (votes_data["bullish"] / total_votes * 100) if total_votes > 0 else 50
        
        st.markdown(f"**{label} - Community Vote**")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🟢 Bullish", key=f"bull_{category}_{symbol}"):
                self.save_vote(category, "bullish", symbol)
                st.rerun()
        
        with col2:
            if st.button("🔴 Bearish", key=f"bear_{category}_{symbol}"):
                self.save_vote(category, "bearish", symbol)
                st.rerun()
        
        with col3:
            if total_votes > 0:
                st.metric("Community", f"{bullish_pct:.0f}% bullish", f"{total_votes} votes")
            else:
                st.metric("Community", "No votes yet", "Be the first!")
        
        return votes_data