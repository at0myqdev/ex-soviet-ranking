import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Ex-Soviet Football Ranking",
    page_icon="⚽",
    layout="wide"
)

# Title
st.title("⚽ Ex-Soviet Republics Football Ranking System")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    # Read the Excel file
    df = pd.read_excel('Ex Soviet Ranking - finished 24 25.xlsx', sheet_name=0)
    
    # Extract nation rankings (rows 3-17, based on the structure)
    nations_df = df.iloc[2:17].copy()
    
    # Set proper column names
    nations_df.columns = df.iloc[1]
    
    # Clean up the dataframe
    nations_df = nations_df[['Country', '2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25', 'Total', 'Total2', 'Total3', 'Total4']].copy()
    
    # Convert numeric columns
    numeric_cols = ['2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25', 'Total', 'Total2', 'Total3', 'Total4']
    for col in numeric_cols:
        nations_df[col] = pd.to_numeric(nations_df[col], errors='coerce')
    
    # Sort by Total4 (final score)
    nations_df = nations_df.sort_values('Total4', ascending=False).reset_index(drop=True)
    nations_df.index = nations_df.index + 1  # Start ranking from 1
    
    return nations_df

# Load the data
try:
    df = load_data()
    
    # Main ranking table
    st.header("🏆 Current Nation Rankings (2024/25)")
    
    # Display metrics for top 3
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🥇 1st Place", df.iloc[0]['Country'], f"{df.iloc[0]['Total4']:.2f} pts")
    with col2:
        st.metric("🥈 2nd Place", df.iloc[1]['Country'], f"{df.iloc[1]['Total4']:.2f} pts")
    with col3:
        st.metric("🥉 3rd Place", df.iloc[2]['Country'], f"{df.iloc[2]['Total4']:.2f} pts")
    
    st.markdown("---")
    
    # Full ranking table
    st.subheader("📊 Complete Rankings")
    
    # Create display dataframe
    display_df = df[['Country', 'Total', 'Total2', 'Total3', 'Total4']].copy()
    display_df.columns = ['Country', 'UEFA Coefficient', 'AFC Coefficient', 'FIFA Ranking', 'Final Score']
    
    # Format numbers
    display_df['UEFA Coefficient'] = display_df['UEFA Coefficient'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    display_df['AFC Coefficient'] = display_df['AFC Coefficient'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    display_df['FIFA Ranking'] = display_df['FIFA Ranking'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    display_df['Final Score'] = display_df['Final Score'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    
    st.dataframe(display_df, use_container_width=True, hide_index=False)
    
    st.markdown("---")
    
    # Visualizations
    st.header("📈 Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Final Scores", "Coefficient Breakdown", "Historical UEFA"])
    
    with tab1:
        # Bar chart of final scores
        fig = px.bar(
            df, 
            x='Country', 
            y='Total4',
            title='Final Scores by Country',
            labels={'Total4': 'Final Score', 'Country': 'Country'},
            color='Total4',
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Stacked bar chart showing breakdown
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='UEFA Coefficient',
            x=df['Country'],
            y=df['Total'],
            marker_color='#1f77b4'
        ))
        
        fig.add_trace(go.Bar(
            name='AFC Coefficient',
            x=df['Country'],
            y=df['Total2'],
            marker_color='#ff7f0e'
        ))
        
        fig.add_trace(go.Bar(
            name='FIFA Ranking',
            x=df['Country'],
            y=df['Total3'],
            marker_color='#2ca02c'
        ))
        
        fig.update_layout(
            title='Coefficient Breakdown by Country',
            barmode='group',
            height=500,
            xaxis_title='Country',
            yaxis_title='Points'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Line chart for UEFA coefficients over time
        uefa_cols = ['2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25']
        
        fig = go.Figure()
        
        for idx, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=uefa_cols,
                y=[row[col] for col in uefa_cols],
                mode='lines+markers',
                name=row['Country']
            ))
        
        fig.update_layout(
            title='UEFA Coefficients Over Time',
            xaxis_title='Season',
            yaxis_title='UEFA Coefficient',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Info section
    st.markdown("---")
    st.header("ℹ️ About the Ranking System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Calculation Method:**
        - **UEFA Coefficient**: Weighted average of last 5 years
        - **AFC Coefficient**: Weighted average for Asian leagues
        - **FIFA Ranking**: Average of historical FIFA rankings
        - **Final Score (Total4)**: Combined score from all three components
        """)
    
    with col2:
        st.markdown("""
        **Countries Included:**
        - 15 Ex-Soviet Republics
        - Ukraine, Russia, Azerbaijan, Uzbekistan, Armenia
        - Moldova, Latvia, Kazakhstan, Georgia, Kyrgyzstan
        - Estonia, Lithuania, Belarus, Turkmenistan, Tajikistan
        """)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please make sure the Excel file is in the same directory as this script.")
