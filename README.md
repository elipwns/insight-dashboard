# Insight Dashboard

Interactive Streamlit dashboard for visualizing financial sentiment analysis and price correlations.

## 🎯 Purpose

Provides real-time market sentiment insights and historical trend analysis through intuitive visualizations.

## 📊 Dashboard Features

### 📊 Insights Page (Main View)
- **Current Market Sentiment**: Real-time pulse from last 3 days
- **Market Category Breakdown**: CRYPTO, US_STOCKS, ECONOMICS sentiment
- **Price vs Sentiment Trends**: Historical correlation analysis
- **Dual-Axis Charts**: Price lines with stacked sentiment bars

### 🔧 Debug Page (Technical View)
- **System Status**: Data validation and health checks
- **Raw Data Tables**: Inspect sentiment and price data
- **Category Distribution**: Detailed breakdown by source
- **Time Range Validation**: Ensure data freshness

## 🚀 Usage

### Local Development
```bash
streamlit run app/main.py
```

### Deployed Version
- **Target URL**: trading.elikloft.com (pending domain fix)
- **Alternative**: elikloft.com/trading (path-based routing)
- **Current Status**: Deployed but domain configuration issues

## 📈 Visualization Types

### Current Sentiment (Top Chart)
- **Time Range**: Last 3 days only
- **Purpose**: At-a-glance current market pulse
- **Format**: Stacked bars (Bullish/Neutral/Bearish)
- **Categories**: Ordered as CRYPTO, ECONOMICS, US_STOCKS, OTHER

### Historical Trends (Bottom Chart)
- **Time Range**: All available data
- **Purpose**: Long-term correlation analysis
- **Format**: Dual-axis with price line + sentiment bars
- **Aggregation**: Daily averages for trend clarity

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# AWS (required)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

# S3 (required)
S3_BUCKET_NAME=automated-trading-data-bucket
```

### Dependencies
```bash
pip install -r requirements.txt
```

Key packages:
- `streamlit` - Web dashboard framework
- `plotly` - Interactive charts
- `pandas` - Data manipulation
- `boto3` - AWS S3 integration

## 🎨 Design Choices

### Color Scheme
- **Bullish**: Green (#00CC44)
- **Neutral**: Gray (#888888)  
- **Bearish**: Red (#FF4444)
- **Price Line**: Black with white outline for visibility

### Chart Types
- **Stacked Bars**: Show full sentiment distribution
- **Line Charts**: Price trends over time
- **Dual-Axis**: Compare different scales (price vs percentage)

### User Experience
- **Page Navigation**: Clean sidebar with Insights/Debug pages
- **Expandable Sections**: Category definitions on demand
- **Responsive Design**: Works on desktop and mobile
- **Loading States**: Clear feedback when data is unavailable

## 📊 Current Data Display

### Metrics (Top Row)
- **Market Sentiment**: Overall bullish percentage
- **Community Posts**: Total analyzed posts
- **Market Categories**: Number of active categories

### Category Definitions
- **CRYPTO**: Digital assets and blockchain discussions
- **ECONOMICS**: Macro trends and long-term wealth strategies  
- **US_STOCKS**: Traditional equity markets and value investing
- **OTHER**: Miscellaneous financial discussions

## 🔧 Technical Implementation

### Data Loading
- **Real-time**: Loads fresh data from S3 on each page refresh
- **Caching**: Streamlit built-in caching for performance
- **Error Handling**: Graceful fallbacks when data unavailable

### Chart Rendering
- **Plotly Integration**: Interactive charts with zoom/pan
- **Responsive**: Auto-sizing based on container width
- **Performance**: Optimized for daily aggregated data

### Page Structure
```python
# Multi-page app with sidebar navigation
def presentation_page():  # Main insights view
def debug_page():        # Technical details
def main():             # Navigation logic
```

## 🌐 Deployment Status

### Current Deployment
- **Platform**: Cloud hosting (Streamlit Cloud)
- **Status**: ✅ Application deployed successfully
- **Domain**: ✅ https://trading.elikloft.com working

## 🎯 Future Enhancements

### High Priority
- **Auto-Refresh**: Real-time data updates without manual refresh
- **Mobile Optimization**: Improve responsive design
- **Data Pipeline**: Automated processing after collection

### Medium Priority
- **Export Features**: Download charts as images/PDFs
- **Time Range Filters**: Custom date range selection
- **Alert System**: Notifications for extreme sentiment shifts

### Low Priority
- **Themes**: Dark/light mode toggle
- **Customization**: User-configurable chart types
- **API Integration**: Direct data feeds without S3 dependency

## 📊 Data Insights Displayed

### Current Status (Example)
- **Market Sentiment**: 65% Bullish
- **Community Posts**: 1,314 analyzed
- **Market Categories**: 3 active
- **Data Points**: 1 price + 1 sentiment per day

### Trend Analysis
- **Daily Aggregation**: Smooths noise while preserving trends
- **Correlation Tracking**: Visual relationship between sentiment and price
- **Category Comparison**: Different market segments side-by-side

## 🐛 Known Issues

### Dashboard
- **Data Refresh**: Manual refresh required for new data
- **Mobile**: Some charts may be cramped on small screens
- **Loading**: No progress indicators for slow S3 loads

## 📁 File Structure

```
insight-dashboard/
├── app/
│   └── main.py                 # Main dashboard application
├── utils/
│   └── data_loader.py         # S3 data loading utilities
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── requirements.txt           # Python dependencies
└── runtime.txt               # Python version for deployment
```

---

*Part of the automated-trading pipeline*
*Previous: ai-workbench processes sentiment data*
*Data Source: Reads from S3 processed-data/*