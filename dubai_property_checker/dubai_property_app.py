# dubai_property_app.py - Dubai Property OUVC Web Dashboard

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os
from typing import Dict, Optional, List
import json
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')  # Assuming dubai_property_ouvc.py is in 'core' subfolder
sys.path.insert(0, core_dir)
sys.path.insert(0, current_dir)


# Import the main valuation module
from dubai_property_ouvc import (
    analyze_dubai_property,
    Property,
    PropertyType,
    Area,
    AREA_YIELDS,
    DubaiPropertyValuator,
    BayutClient
)

# Page configuration
st.set_page_config(
    page_title="Dubai Property OUVC",
    page_icon="🏢",
    layout="wide"
)

# Custom CSS for Dubai-themed styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .verdict-box {
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
    }
    .buy-verdict { background: #4CAF50; color: white; }
    .hold-verdict { background: #FFC107; color: white; }
    .avoid-verdict { background: #f44336; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

if 'api_keys_set' not in st.session_state:
    st.session_state.api_keys_set = False

# Header
st.title("🏢 Dubai Property OUVC")
st.caption("Objective Undervalued Checker for UAE Real Estate")

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Keys section
    with st.expander("API Keys Setup", expanded=not st.session_state.api_keys_set):
        bayut_key = st.text_input(
            "Bayut API Key (RapidAPI)",
            type="password",
            help="Get from RapidAPI Bayut endpoint"
        )
        dld_key = st.text_input(
            "DLD API Key (Optional)",
            type="password",
            help="Dubai Land Department API"
        )
        
        if st.button("Save API Keys"):
            if bayut_key:
                os.environ["BAYUT_API_KEY"] = bayut_key
                if dld_key:
                    os.environ["DLD_API_KEY"] = dld_key
                st.session_state.api_keys_set = True
                st.success("✅ API Keys saved!")
                st.rerun()
            else:
                st.error("Bayut API Key is required!")
    
    # Market Insights
    st.header("📊 Market Insights")
    
    # Display area yields
    selected_area_sidebar = st.selectbox(
        "Select Area for Yields",
        options=[area.value for area in Area],
        format_func=lambda x: x.replace('-', ' ').title()
    )
    
    if selected_area_sidebar:
        area_enum = Area(selected_area_sidebar)
        if area_enum in AREA_YIELDS:
            yields = AREA_YIELDS[area_enum]
            col1, col2, col3 = st.columns(3)
            col1.metric("Min", f"{yields['min']}%")
            col2.metric("Avg", f"{yields['avg']}%")
            col3.metric("Max", f"{yields['max']}%")
    
    # Quick Stats
    st.header("📈 Today's Stats")
    st.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    if st.session_state.analysis_history:
        st.metric("Properties Analyzed", len(st.session_state.analysis_history))

# Main content area
if not st.session_state.api_keys_set:
    st.warning("⚠️ Please configure API keys in the sidebar to continue")
    st.stop()

# Property Input Form
st.header("🔍 Property Analysis")

# Create tabs for different input methods
tab1, tab2, tab3 = st.tabs(["Quick Analysis", "Detailed Analysis", "Batch Analysis"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        area = st.selectbox(
            "Area",
            options=[area.value for area in Area],
            format_func=lambda x: x.replace('-', ' ').title()
        )
        
        property_type = st.selectbox(
            "Property Type",
            options=[pt.value for pt in PropertyType],
            format_func=lambda x: x.title()
        )
        
        bedrooms = st.number_input(
            "Bedrooms",
            min_value=0,
            max_value=10,
            value=2
        )
    
    with col2:
        size_sqft = st.number_input(
            "Size (sqft)",
            min_value=100,
            max_value=20000,
            value=1200,
            step=50
        )
        
        asking_price = st.number_input(
            "Asking Price (AED)",
            min_value=100000,
            max_value=50000000,
            value=1800000,
            step=50000,
            format="%d"
        )
        
        # Quick calculate button
        analyze_quick = st.button("🚀 Analyze Property", type="primary", use_container_width=True)

with tab2:
    st.subheader("Additional Details")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        bathrooms = st.number_input(
            "Bathrooms",
            min_value=1,
            max_value=10,
            value=2
        )
        
        furnished = st.selectbox(
            "Furnished",
            options=[None, True, False],
            format_func=lambda x: "Not Specified" if x is None else ("Yes" if x else "No")
        )
    
    with col4:
        service_charge = st.number_input(
            "Service Charge (AED/sqft/year)",
            min_value=0.0,
            max_value=50.0,
            value=15.0,
            step=0.5
        )
        
        parking_spaces = st.number_input(
            "Parking Spaces",
            min_value=0,
            max_value=5,
            value=1
        )
    
    with col5:
        view_type = st.selectbox(
            "View Type",
            options=[None, "sea view", "burj khalifa", "marina view", 
                    "golf course", "city view", "garden view"],
            format_func=lambda x: "Not Specified" if x is None else x.title()
        )
        
        floor_number = st.number_input(
            "Floor Number",
            min_value=0,
            max_value=100,
            value=10
        )
    
    analyze_detailed = st.button("🔬 Detailed Analysis", type="primary", use_container_width=True)

with tab3:
    st.subheader("Upload Multiple Properties")
    
    uploaded_file = st.file_uploader(
        "Upload CSV with properties",
        type=['csv'],
        help="CSV should have columns: area, property_type, bedrooms, size_sqft, asking_price_aed"
    )
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        
        if st.button("📊 Analyze Batch", type="primary"):
            results = []
            progress_bar = st.progress(0)
            
            for idx, row in df.iterrows():
                try:
                    result = analyze_dubai_property(
                        area=row['area'],
                        property_type=row['property_type'],
                        bedrooms=row['bedrooms'],
                        size_sqft=row['size_sqft'],
                        asking_price_aed=row['asking_price_aed']
                    )
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})
                
                progress_bar.progress((idx + 1) / len(df))
            
            # Show batch results
            st.success(f"Analyzed {len(results)} properties!")
            
            # Create summary DataFrame
            summary_data = []
            for i, r in enumerate(results):
                if "error" not in r:
                    summary_data.append({
                        "Property": f"#{i+1}",
                        "Asking Price": df.iloc[i]['asking_price_aed'],
                        "Est. Value": r['estimated_value'],
                        "Ratio": r['price_to_estimate_ratio'],
                        "Yield": r['estimated_rental_yield'],
                        "Verdict": r['valuation_signals']['overall_verdict']
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Download button for results
                csv = summary_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results",
                    data=csv,
                    file_name=f"dubai_property_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

# Analysis Results Section
if analyze_quick or analyze_detailed:
    with st.spinner("🔄 Analyzing property..."):
        try:
            # Prepare parameters
            params = {
                "area": area,
                "property_type": property_type,
                "bedrooms": bedrooms,
                "size_sqft": size_sqft,
                "asking_price_aed": asking_price
            }
            
            # Add detailed parameters if available
            if analyze_detailed:
                params.update({
                    "bathrooms": bathrooms,
                    "furnished": furnished,
                    "service_charge_sqft": service_charge if service_charge > 0 else None,
                    "view_type": view_type
                })
            
            # Run analysis
            result = analyze_dubai_property(**params)
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                if "suggestion" in result:
                    st.info(f"💡 {result['suggestion']}")
            else:
                # Store in history
                st.session_state.analysis_history.append({
                    "timestamp": datetime.now(),
                    "params": params,
                    "result": result
                })
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                # Verdict Box
                verdict = result['valuation_signals']['overall_verdict']
                verdict_class = "buy-verdict" if "BUY" in verdict else "hold-verdict" if "HOLD" in verdict else "avoid-verdict"
                
                st.markdown(f"""
                <div class="verdict-box {verdict_class}">
                    {verdict}
                </div>
                """, unsafe_allow_html=True)
                
                # Key Metrics
                st.subheader("📊 Key Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Estimated Value",
                        f"AED {result['estimated_value']:,.0f}",
                        f"{(result['estimated_value'] - asking_price):+,.0f}"
                    )
                
                with col2:
                    ratio = result['price_to_estimate_ratio']
                    st.metric(
                        "Price Ratio",
                        f"{ratio:.2f}x",
                        "Undervalued" if ratio < 0.95 else "Fair" if ratio < 1.05 else "Overvalued"
                    )
                
                with col3:
                    st.metric(
                        "Rental Yield",
                        f"{result['estimated_rental_yield']:.1f}%",
                        "Good" if result['estimated_rental_yield'] > 6 else "Average"
                    )
                
                with col4:
                    st.metric(
                        "Confidence",
                        result['valuation_signals']['confidence'].upper(),
                        f"{result['comparable_properties']} comps"
                    )
                
                # Confidence Interval Chart
                st.subheader("💰 Valuation Range")
                
                fig = go.Figure()
                
                # Add confidence interval
                fig.add_trace(go.Scatter(
                    x=["Low", "Estimated", "High"],
                    y=[
                        result['confidence_interval']['low'],
                        result['estimated_value'],
                        result['confidence_interval']['high']
                    ],
                    mode='lines+markers',
                    name='Valuation Range',
                    line=dict(color='blue', width=2),
                    marker=dict(size=10)
                ))
                
                # Add asking price line
                fig.add_hline(
                    y=asking_price,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Asking: AED {asking_price:,.0f}"
                )
                
                fig.update_layout(
                    title="Property Valuation Analysis",
                    xaxis_title="Estimate Type",
                    yaxis_title="Value (AED)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Model Performance
                with st.expander("🤖 Model Details"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Model Predictions")
                        model_df = pd.DataFrame({
                            "Model": result['model_predictions'].keys(),
                            "Prediction (AED)": result['model_predictions'].values(),
                            "Accuracy": result['model_accuracy'].values()
                        })
                        st.dataframe(model_df, use_container_width=True)
                    
                    with col2:
                        st.subheader("Data Sources")
                        source_df = pd.DataFrame(
                            list(result['data_sources'].items()),
                            columns=["Source", "Count"]
                        )
                        
                        fig = px.pie(
                            source_df,
                            values='Count',
                            names='Source',
                            title="Comparable Properties by Source"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Key Factors
                st.subheader("🎯 Key Valuation Factors")
                for factor in result['valuation_signals']['key_factors']:
                    st.info(f"• {factor}")
                
                # Market Insights
                with st.expander("📈 Market Insights"):
                    insights = result['market_insights']
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Days on Market", insights.get('avg_days_on_market', 'N/A'))
                    with col2:
                        trend = insights.get('price_trend_3m', 0)
                        st.metric("3M Price Trend", f"{trend*100:+.1f}%")
                    with col3:
                        st.metric("Buyer Demand", insights.get('buyer_demand', 'N/A').upper())
                
                # Rental Analysis
                with st.expander("🏠 Rental Analysis"):
                    rental = result['rental_data']
                    
                    # Create rental range chart
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=["Minimum", "Average", "Maximum"],
                        y=[
                            rental['min_annual_rent'],
                            rental['avg_annual_rent'],
                            rental['max_annual_rent']
                        ],
                        text=[
                            f"AED {rental['min_annual_rent']:,.0f}",
                            f"AED {rental['avg_annual_rent']:,.0f}",
                            f"AED {rental['max_annual_rent']:,.0f}"
                        ],
                        textposition='outside'
                    ))
                    
                    fig.update_layout(
                        title="Expected Annual Rental Income",
                        yaxis_title="Annual Rent (AED)",
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calculate ROI
                    years_to_recover = asking_price / rental['avg_annual_rent']
                    st.metric("Years to Recover Investment", f"{years_to_recover:.1f}")
                
                # Export Report
                st.subheader("📄 Export Report")
                
                report_data = {
                    "analysis_date": datetime.now().isoformat(),
                    "property": params,
                    "results": result
                }
                
                col1, col2 = st.columns(2)
                with col1:
                    # JSON export
                    json_str = json.dumps(report_data, indent=2, default=str)
                    st.download_button(
                        label="📥 Download JSON Report",
                        data=json_str,
                        file_name=f"property_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                with col2:
                    # Create PDF-ready summary
                    summary = f"""
DUBAI PROPERTY VALUATION REPORT
================================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

PROPERTY DETAILS
----------------
Location: {area.replace('-', ' ').title()}
Type: {property_type.title()}
Bedrooms: {bedrooms}
Size: {size_sqft:,} sqft
Asking Price: AED {asking_price:,.0f}

VALUATION RESULTS
-----------------
Estimated Value: AED {result['estimated_value']:,.0f}
Confidence Range: AED {result['confidence_interval']['low']:,.0f} - {result['confidence_interval']['high']:,.0f}
Price Ratio: {result['price_to_estimate_ratio']:.2f}x
Rental Yield: {result['estimated_rental_yield']:.1f}%

VERDICT: {result['valuation_signals']['overall_verdict']}
Confidence Level: {result['valuation_signals']['confidence'].upper()}

KEY FACTORS:
{chr(10).join('- ' + f for f in result['valuation_signals']['key_factors'])}
                    """
                    
                    st.download_button(
                        label="📥 Download Text Report",
                        data=summary,
                        file_name=f"property_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
        
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("Please check your inputs and API keys")

# History Section
if st.session_state.analysis_history:
    st.header("📜 Analysis History")
    
    # Convert history to DataFrame
    history_data = []
    for item in st.session_state.analysis_history[-10:]:  # Last 10 analyses
        params = item['params']
        result = item['result']
        history_data.append({
            "Time": item['timestamp'].strftime('%H:%M:%S'),
            "Area": params['area'].replace('-', ' ').title(),
            "Type": params['property_type'],
            "Beds": params['bedrooms'],
            "Size": f"{params['size_sqft']:,}",
            "Asking": f"AED {params['asking_price_aed']:,.0f}",
            "Est. Value": f"AED {result['estimated_value']:,.0f}",
            "Verdict": result['valuation_signals']['overall_verdict']
        })
    
    history_df = pd.DataFrame(history_data)
    st.dataframe(history_df, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Dubai Property OUVC v1.0 | Made with ❤️ for smart property investors")
st.caption("Data sources: Bayut API, Dubai Land Department, RERA Rental Index")