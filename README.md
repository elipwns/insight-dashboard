# Insight Dashboard

Streamlit dashboard for visualizing financial sentiment analysis and trading insights.

## Part of 3-Repo System

- **[Data Harvester](https://github.com/elipwns/data-harvester)** - Web scraping pipeline
- **[AI Workbench](https://github.com/elipwns/ai-workbench)** - Financial sentiment analysis
- **[Insight Dashboard](https://github.com/elipwns/insight-dashboard)** ← You are here

## Current Status

✅ **Working Components:**
- Real-time financial sentiment visualization
- S3 data integration with auto-refresh
- Interactive charts and metrics
- Star rating sentiment display (1-5 stars)

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS settings
   ```

3. **Run dashboard:**
   ```bash
   streamlit run app/main.py
   ```

4. **View at:** http://localhost:8501

## Features

- **Metrics Dashboard**: Total records, positive sentiment %, confidence scores
- **Sentiment Distribution**: Pie chart of 1-5 star ratings
- **Data Table**: Recent processed data with sentiment scores
- **Auto-refresh**: Updates when new data is processed

## Architecture

- **`app/main.py`** - Main Streamlit application
- **`utils/data_loader.py`** - S3 data loading with caching

## Data Flow

1. Processed data from AI Workbench → S3 `processed-data/`
2. Dashboard loads latest data automatically
3. Real-time visualization updates

## Requirements

- Python 3.10+
- AWS credentials configured
- S3 bucket: `automated-trading-data-bucket`
- Processed data from AI Workbench
