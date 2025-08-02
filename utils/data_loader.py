import boto3
import pandas as pd
import streamlit as st
from io import StringIO
import os

class DataLoader:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    @st.cache_data
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
    
    @st.cache_data
    def load_price_data(_self) -> pd.DataFrame:
        """Load price data from S3 with caching"""
        try:
            objects = _self.s3_client.list_objects_v2(
                Bucket=_self.bucket_name,
                Prefix="raw-data/price_data_"
            )
            
            if not objects.get('Contents'):
                return pd.DataFrame()
            
            all_price_data = []
            for obj in objects['Contents']:
                response = _self.s3_client.get_object(
                    Bucket=_self.bucket_name,
                    Key=obj['Key']
                )
                csv_content = response['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(csv_content))
                all_price_data.append(df)
            
            if all_price_data:
                combined_df = pd.concat(all_price_data, ignore_index=True)
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                return combined_df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error loading price data: {e}")
            return pd.DataFrame()