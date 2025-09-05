import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.data_loader import DataLoader
from datetime import datetime, timedelta

def monthly_predictions_page():
    st.title("📅 Monthly Predictions")
    st.markdown("*AI-powered monthly price forecasts with performance tracking*")
    st.markdown("---")
    
    # Load predictions data
    loader = DataLoader()
    
    # Show data freshness
    df = loader.load_processed_data()
    loader.show_data_freshness(df)
    
    try:
        # Try to load predictions from S3
        response = loader.s3_client.get_object(
            Bucket=loader.bucket_name,
            Key="predictions/monthly_predictions.json"
        )
        predictions_data = json.loads(response['Body'].read().decode('utf-8'))
    except:
        st.warning("No monthly predictions found. Generate new predictions below.")
        st.info("💡 **How it works**: Generate predictions for next month → Track real prices → Evaluate performance at month end")
        predictions_data = {"predictions": [], "performance": []}
    
    # Current month predictions
    current_month = datetime.now().strftime('%Y-%m')
    next_month = (datetime.now().replace(day=1) + timedelta(days=32)).strftime('%Y-%m')
    
    # Show prediction status
    st.info(f"📅 **Current Month**: {current_month} | **Predicting For**: {next_month}")
    
    # Get predictions for next month (should be only one per symbol)
    current_predictions = [p for p in predictions_data.get('predictions', []) if p.get('target_month') == next_month]
    
    # Show if there are predictions for other months
    if not current_predictions:
        all_predictions = predictions_data.get('predictions', [])
        if all_predictions:
            other_months = set(p['target_month'] for p in all_predictions)
            st.info(f"📋 **Existing predictions for**: {', '.join(sorted(other_months))}")
    
    if current_predictions:
        st.subheader(f"🎯 Active Predictions for {next_month}")
        st.markdown("*These predictions will be evaluated at the end of the month using historical price data*")
        
        # Get current price data
        price_df = loader.load_price_data()
        
        # Sort by symbol for consistent display
        current_predictions.sort(key=lambda x: x['symbol'])
        
        # Show prediction summary
        if len(current_predictions) == 1:
            pred = current_predictions[0]
            confidence_pct = pred['confidence_band'] * 100
            confidence_level = "🟢 High" if confidence_pct < 7 else "🟡 Medium" if confidence_pct < 10 else "🔴 Low"
            st.success(f"🎯 **Active Prediction**: {pred['symbol']} - {confidence_level} confidence (±{confidence_pct:.1f}%)")
        elif len(current_predictions) > 1:
            st.info(f"📊 **{len(current_predictions)} Active Predictions** - Tracking multiple symbols")
        
        # Clear prediction display
        for pred in current_predictions:
            symbol = pred['symbol']
            starting_price = pred['current_price']
            predicted_price = pred['predicted_price']
            change_pct = pred['prediction_change_pct']
            
            # Get actual current price
            current_price = "N/A"
            if not price_df.empty:
                symbol_prices = price_df[price_df['symbol'] == symbol]
                if not symbol_prices.empty:
                    latest_price = symbol_prices.iloc[-1]['price']
                    current_price = f"${latest_price:.0f}"
            
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 2])
                
                with col1:
                    prediction_date = datetime.fromisoformat(pred['prediction_date']).strftime('%Y-%m-%d %H:%M UTC')
                    st.metric(f"{symbol} Starting", f"${starting_price:.0f}")
                    st.caption(f"Price on {prediction_date}")
                
                with col2:
                    upper_band = pred['upper_band']
                    lower_band = pred['lower_band']
                    st.metric(f"{symbol} Target", f"${predicted_price:.0f}", f"{change_pct:+.1f}%")
                    st.caption(f"Range: ${lower_band:.0f} to ${upper_band:.0f}")
                
                with col3:
                    confidence_pct = pred['confidence_band'] * 100
                    confidence_level = "🟢 High" if confidence_pct < 7 else "🟡 Medium" if confidence_pct < 10 else "🔴 Low"
                    st.metric("AI Confidence", f"{confidence_level}")
                    st.caption(f"±{confidence_pct:.1f}% band | Current: {current_price}")
                
                st.markdown("---")
        
        # Load real price data for tracking
        price_df = loader.load_price_data()
        
        if not price_df.empty:
            st.subheader("📈 Prediction vs Reality Tracking")
            st.markdown("*Real price data tracking against predictions*")
            
            fig = go.Figure()
            
            for pred in current_predictions:
                symbol = pred['symbol']
                prediction_date = datetime.fromisoformat(pred['prediction_date']).date()
                target_date = datetime.strptime(pred['target_month'], '%Y-%m').date().replace(day=28)
                
                # Get real price data for this symbol
                symbol_prices = price_df[price_df['symbol'] == symbol].copy()
                if not symbol_prices.empty:
                    symbol_prices['timestamp'] = pd.to_datetime(symbol_prices['timestamp'])
                    symbol_prices['date'] = symbol_prices['timestamp'].dt.date
                    
                    prediction_datetime = pd.to_datetime(pred['prediction_date'])
                    
                    # Historical prices (before/at prediction date) + extend to prediction point
                    hist_prices = symbol_prices[symbol_prices['timestamp'] <= prediction_datetime]
                    if not hist_prices.empty:
                        # Add prediction point to historical line to eliminate gap
                        hist_x = list(hist_prices['timestamp']) + [prediction_datetime]
                        hist_y = list(hist_prices['price']) + [pred['current_price']]
                        
                        fig.add_trace(go.Scatter(
                            x=hist_x,
                            y=hist_y,
                            mode='lines',
                            name=f'{symbol} Historical',
                            line=dict(color='white', width=3)
                        ))
                    
                    # Current/tracking prices (only data collected AFTER prediction was made)
                    prediction_datetime = pd.to_datetime(pred['prediction_date'])
                    current_prices = symbol_prices[symbol_prices['timestamp'] > prediction_datetime]
                    if not current_prices.empty:
                        fig.add_trace(go.Scatter(
                            x=current_prices['timestamp'],
                            y=current_prices['price'],
                            mode='lines+markers',
                            name=f'{symbol} Actual',
                            line=dict(color='lime', width=4),
                            marker=dict(size=6, color='lime')
                        ))
                
                # Prediction starting point (use prediction's stored price)
                fig.add_trace(go.Scatter(
                    x=[prediction_datetime],
                    y=[pred['current_price']],
                    mode='markers',
                    name=f'{symbol} Prediction Start',
                    marker=dict(size=15, color='yellow', symbol='star')
                ))
                
                # Prediction line to target (from prediction start point)
                fig.add_trace(go.Scatter(
                    x=[prediction_datetime, target_date],
                    y=[pred['current_price'], pred['predicted_price']],
                    mode='lines+markers',
                    name=f'{symbol} AI Prediction',
                    line=dict(color='orange', width=4, dash='dash'),
                    marker=dict(size=10, color='orange')
                ))
                

                

            
            fig.update_layout(
                title="Prediction vs Reality Tracking (Real Data)",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("""
            **Chart Legend:**
            - **White line**: Historical prices (real data)
            - **Yellow star**: Prediction starting point
            - **Orange dashed line**: AI prediction path
            - **Lime line**: Actual price movement (real data)
            """)
        else:
            st.info("💡 Price data not available for tracking. Run the price collector to enable real-time tracking.")
    
    # Performance tracking
    performance_data = predictions_data.get('performance', [])
    
    if performance_data:
        st.subheader("🎯 Prediction Performance History")
        st.markdown("*Performance is evaluated using actual historical prices from the target month*")
        
        # Performance metrics
        recent_performance = performance_data[-5:]  # Last 5 evaluations
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if recent_performance:
                avg_error = sum(p['error_pct'] for p in recent_performance) / len(recent_performance)
                st.metric("Avg Error", f"{avg_error:.1f}%")
        
        with col2:
            if recent_performance:
                good_ratings = sum(1 for p in recent_performance if p['rating'] in ['Excellent', 'Good'])
                accuracy = (good_ratings / len(recent_performance)) * 100
                st.metric("Accuracy", f"{accuracy:.0f}%")
        
        with col3:
            if recent_performance:
                ratings = [p['rating'] for p in recent_performance]
                good_ratings = sum(1 for r in ratings if r in ['Excellent', 'Good'])
                success_rate = (good_ratings / len(ratings)) * 100
                st.metric("Success Rate", f"{success_rate:.0f}%")
        
        # Performance table
        st.subheader("📊 Detailed Performance")
        
        perf_df = pd.DataFrame(performance_data)
        if not perf_df.empty:
            # Format for display
            display_df = perf_df[['target_month', 'symbol', 'predicted_price', 'actual_price', 'error_pct', 'rating']].copy()
            display_df['predicted_price'] = display_df['predicted_price'].apply(lambda x: f"${x:.0f}")
            display_df['actual_price'] = display_df['actual_price'].apply(lambda x: f"${x:.0f}")
            display_df['error_pct'] = display_df['error_pct'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True)
        
        # Performance chart
        if len(performance_data) > 1:
            st.subheader("📈 Error Trend")
            
            perf_df['evaluation_date'] = pd.to_datetime(perf_df['evaluation_date'])
            
            fig_perf = go.Figure()
            
            for symbol in perf_df['symbol'].unique():
                symbol_data = perf_df[perf_df['symbol'] == symbol]
                fig_perf.add_trace(go.Scatter(
                    x=symbol_data['evaluation_date'],
                    y=symbol_data['error_pct'],
                    mode='lines+markers',
                    name=f'{symbol} Error %',
                    line=dict(width=3)
                ))
            
            fig_perf.update_layout(
                title="Prediction Error Over Time",
                xaxis_title="Date",
                yaxis_title="Error (%)",
                height=300
            )
            
            st.plotly_chart(fig_perf, use_container_width=True)
    
    # Model information
    st.subheader("🤖 Model Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Current Model:**
        - Type: Sentiment-based predictor with feedback
        - Features: Sentiment trend, price momentum, community votes
        - Learning: Adjusts based on past performance
        - Evaluation: Historical price comparison
        """)
    
    with col2:
        st.markdown("""
        **Performance Ratings:**
        - **Excellent**: <3% error
        - **Good**: <6% error  
        - **Fair**: <8% error
        - **Poor**: <10% error
        - **Failed**: >10% error
        """)
    
    # Run prediction button
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Generate New Monthly Predictions"):
            with st.spinner("Generating predictions..."):
                try:
                    # Import and run the monthly predictor
                    ai_workbench_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ai-workbench')
                    sys.path.insert(0, ai_workbench_path)
                    from monthly_predictor import MonthlyPredictor
                    
                    predictor = MonthlyPredictor()
                    results = predictor.run_monthly_prediction_cycle()
                    
                    st.success("✅ Monthly predictions generated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error generating predictions: {e}")
    
    with col2:
        if st.button("📊 Evaluate Past Performance"):
            with st.spinner("Evaluating past predictions..."):
                try:
                    ai_workbench_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ai-workbench')
                    sys.path.insert(0, ai_workbench_path)
                    from monthly_predictor import MonthlyPredictor
                    
                    predictor = MonthlyPredictor()
                    # Just run evaluation, no new predictions
                    history = predictor.load_predictions_history()
                    
                    # Evaluate August predictions if they exist
                    performance = predictor.evaluate_last_month_prediction('BTC')
                    if performance:
                        history['performance'].append(performance)
                        predictor.save_predictions_history(history)
                        st.success(f"✅ Evaluated August prediction: {performance['rating']} ({performance['error_pct']:.1f}% error)")
                    else:
                        st.info("No predictions to evaluate or already evaluated")
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error evaluating performance: {e}")
    
    # Disclaimers
    st.markdown("---")
    st.error("⚠️ **PREDICTION DISCLAIMERS**")
    st.markdown("""
    - These are experimental AI predictions, not financial advice
    - Models are in early development with limited historical validation
    - Cryptocurrency and stock markets are highly unpredictable
    - Past performance does not guarantee future results
    - Only invest what you can afford to lose completely
    - Always do your own research before making investment decisions
    """)