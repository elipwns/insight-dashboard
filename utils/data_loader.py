import boto3
import pandas as pd
import streamlit as st
from io import StringIO
import os

class DataLoader:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    @st.cache_data(ttl=1800)  # 30 minutes TTL
    def load_processed_data(_self, filename: str = None) -> pd.DataFrame:
        """Load processed data from S3 with caching"""
        try:
            if filename:
                key = f"processed-data/{filename}"
            else:
                # Get the most recent processed file
                objects = _self.s3_client.list_objects_v2(
                    Bucket=_self.bucket_name,
                    Prefix="processed-data/"
                )
                if not objects.get('Contents'):
                    return pd.DataFrame()
                
                # Sort by last modified and get most recent
                latest = sorted(objects['Contents'], 
                              key=lambda x: x['LastModified'], 
                              reverse=True)[0]
                key = latest['Key']
            
            response = _self.s3_client.get_object(
                Bucket=_self.bucket_name,
                Key=key
            )
            
            csv_content = response['Body'].read().decode('utf-8')
            df = pd.read_csv(StringIO(csv_content))
            return df
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)  # 1 hour TTL
    def load_historical_data(_self) -> pd.DataFrame:
        """Load historical data from S3 with caching"""
        try:
            objects = _self.s3_client.list_objects_v2(
                Bucket=_self.bucket_name,
                Prefix="raw-data/historical_data_"
            )
            
            if not objects.get('Contents'):
                return pd.DataFrame()
            
            # Get most recent historical file
            latest = sorted(objects['Contents'], 
                          key=lambda x: x['LastModified'], 
                          reverse=True)[0]
            
            response = _self.s3_client.get_object(
                Bucket=_self.bucket_name,
                Key=latest['Key']
            )
            
            csv_content = response['Body'].read().decode('utf-8')
            df = pd.read_csv(StringIO(csv_content))
            return df
            
        except Exception as e:
            st.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)  # 5 minutes TTL for faster price updates
    def load_price_data(_self) -> pd.DataFrame:
        """Load price data from S3 with caching (includes quick updates)"""
        try:
            all_price_data = []
            
            # Load regular price data
            objects = _self.s3_client.list_objects_v2(
                Bucket=_self.bucket_name,
                Prefix="raw-data/price_data_"
            )
            
            for obj in objects.get('Contents', []):
                response = _self.s3_client.get_object(
                    Bucket=_self.bucket_name,
                    Key=obj['Key']
                )
                csv_content = response['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(csv_content))
                all_price_data.append(df)
            
            # Load quick price updates
            quick_objects = _self.s3_client.list_objects_v2(
                Bucket=_self.bucket_name,
                Prefix="raw-data/quick_prices_"
            )
            
            for obj in quick_objects.get('Contents', []):
                response = _self.s3_client.get_object(
                    Bucket=_self.bucket_name,
                    Key=obj['Key']
                )
                csv_content = response['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(csv_content))
                # Add missing columns for compatibility
                if 'category' not in df.columns:
                    df['category'] = 'CRYPTO'
                if 'volume_24h' not in df.columns:
                    df['volume_24h'] = 0
                if 'volatility' not in df.columns:
                    df['volatility'] = abs(df.get('change_24h', 0))
                if 'volume_price_ratio' not in df.columns:
                    df['volume_price_ratio'] = 0
                if 'market_cap' not in df.columns:
                    df['market_cap'] = 0
                all_price_data.append(df)
            
            if all_price_data:
                combined_df = pd.concat(all_price_data, ignore_index=True, sort=False)
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                # Keep all historical data, don't remove duplicates by symbol
                return combined_df.sort_values('timestamp')
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error loading price data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=1800)  # 30 minutes TTL
    def load_fear_greed_data(_self) -> pd.DataFrame:
        """Load Fear & Greed Index data from S3 with caching"""
        try:
            objects = _self.s3_client.list_objects_v2(
                Bucket=_self.bucket_name,
                Prefix="raw-data/fear_greed_index_"
            )
            
            if not objects.get('Contents'):
                return pd.DataFrame()
            
            all_fg_data = []
            for obj in objects['Contents']:
                response = _self.s3_client.get_object(
                    Bucket=_self.bucket_name,
                    Key=obj['Key']
                )
                csv_content = response['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(csv_content))
                all_fg_data.append(df)
            
            if all_fg_data:
                combined_df = pd.concat(all_fg_data, ignore_index=True)
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                return combined_df.sort_values('timestamp')
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error loading Fear & Greed data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=1800)  # 30 minutes TTL
    def load_trending_data(_self) -> pd.DataFrame:
        """Load trending opportunities data from S3 with caching"""
        try:
            objects = _self.s3_client.list_objects_v2(
                Bucket=_self.bucket_name,
                Prefix="raw-data/trending_opportunities_"
            )
            
            if not objects.get('Contents'):
                return pd.DataFrame()
            
            all_trending_data = []
            for obj in objects['Contents']:
                response = _self.s3_client.get_object(
                    Bucket=_self.bucket_name,
                    Key=obj['Key']
                )
                csv_content = response['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(csv_content))
                all_trending_data.append(df)
            
            if all_trending_data:
                combined_df = pd.concat(all_trending_data, ignore_index=True)
                combined_df['detected_at'] = pd.to_datetime(combined_df['detected_at'])
                return combined_df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error loading trending data: {e}")
            return pd.DataFrame()