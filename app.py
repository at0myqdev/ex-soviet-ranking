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

# Country code to full name mapping
COUNTRY_NAMES = {
    'UKR': 'Ukraine',
    'RUS': 'Russia',
    'AZE': 'Azerbaijan',
    'UZB': 'Uzbekistan',
    'ARM': 'Armenia',
    'MDA': 'Moldova',
    'LVA': 'Latvia',
    'KAZ': 'Kazakhstan',
    'GEO': 'Georgia',
    'KGZ': 'Kyrgyzstan',
    'EST': 'Estonia',
    'LTU': 'Lithuania',
    'BLR': 'Belarus',
    'TKM': 'Turkmenistan',
    'TJK': 'Tajikistan'
}

# Load data
@st.cache_data
def load_data():
    # Read the Excel file
    df = pd.read_excel('Ex Soviet Ranking - finished 24 25.xlsx', sheet_name=0, header=None)
    
    # Extract nation rankings (rows 3-17, index 2-16)
    nations_df = df.iloc[2:17].copy()
    
    # Reset index
    nations_df = nations_df.reset_index(drop=True)
    
    # Assign column names based on the actual structure
    nations_df.columns = [
        'Rank', 'League', 'Country', 'CCode',
        'UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25',
        'Total_UEFA', 'AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25',
        'Total_AFC', 'FIFA_20_09_2018', 'FIFA_19_09_2019', 'FIFA_17_09_2020', 'FIFA_16_09_2021',
        'FIFA_25_08_2022', 'FIFA_21_09_2023', 'FIFA_19_09_2024', 'FIFA_18_09_2025',
        'Total_FIFA', 'Total4'
    ]
    
    # Get country names from codes
    nations_df['Country_Name'] = nations_df['CCode'].map(COUNTRY_NAMES)
    
    # Convert numeric columns
    numeric_cols = ['Rank', 'UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25',
                    'Total_UEFA', 'AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25',
                    'Total_AFC', 'FIFA_20_09_2018', 'FIFA_19_09_2019', 'FIFA_17_09_2020', 'FIFA_16_09_2021',
                    'FIFA_25_08_2022', 'FIFA_21_09_2023', 'FIFA_19_09_2024', 'FIFA_18_09_2025',
                    'Total_FIFA', 'Total4']
    
    for col in numeric_cols:
        nations_df[col] = pd.to_numeric(nations_df[col], errors='coerce')
    
    return nations_df

# Load the data
try:
    df = load_data()
    
    # Main ranking table
    st.header("🏆 Current Nation Rankings (2024/25)")
    
    # Display metrics for top 3
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🥇 1st Place", df.iloc[0]['Country_Name'], f"{df.iloc[0]['Total4']:.2f} pts")
    with col2:
        st.metric("🥈 2nd Place", df.iloc[1]['Country_Name'], f"{df.iloc[1]['Total4']:.2f} pts")
    with col3:
        st.metric("🥉 3rd Place", df.iloc[2]['Country_Name'], f"{df.iloc[2]['Total4']:.2f} pts")
    
    st.markdown("---")
    
    # Full ranking table - exactly as in Excel
    st.subheader("📊 Complete Rankings Table")
    
    # Create display dataframe with all columns from Excel
    display_df = df[[
        'Rank', 'CCode', 
        'UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25', 'Total_UEFA',
        'AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25', 'Total_AFC',
        'FIFA_20_09_2018', 'FIFA_19_09_2019', 'FIFA_17_09_2020', 'FIFA_16_09_2021',
        'FIFA_25_08_2022', 'FIFA_21_09_2023', 'FIFA_19_09_2024', 'FIFA_18_09_2025', 'Total_FIFA',
        'Total4'
    ]].copy()
    
    # Rename columns to match Excel headers
    display_df.columns = [
        'Rank', 'Country',
        '2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25', 'Total',
        '2018', '2019', '2021', '2022', '2023/24', '2024/25', 'Total.1',
        '20.09.2018', '19.09.2019', '17.09.2020', '16.09.2021',
        '25.08.2022', '21.09.2023', '19.09.2024', '18.09.2025', 'Total.2',
        'Total.3'
    ]
    
    # Format numbers to match Excel (2 decimal places where applicable) - ROBUST VERSION
    def format_value(x):
        # Handle Series or array-like objects
        if isinstance(x, pd.Series):
            return x.iloc[0] if len(x) > 0 else ""

        # Check for NaN/None
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""

        # Try to convert to float and format
        try:
            val = float(x)
            return f"{val:.2f}"
        except (ValueError, TypeError):
            return ""

    for col in display_df.columns:
        if col not in ['Rank', 'Country']:
            display_df[col] = display_df[col].map(format_value)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Visualizations
    st.header("📈 Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Final Scores", "Coefficient Breakdown", "Historical UEFA"])
    
    with tab1:
        # Bar chart of final scores
        fig = px.bar(
            df, 
            x='Country_Name', 
            y='Total4',
            title='Final Scores by Country',
            labels={'Total4': 'Final Score', 'Country_Name': 'Country'},
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
            x=df['Country_Name'],
            y=df['Total_UEFA'],
            marker_color='#1f77b4'
        ))
        
        fig.add_trace(go.Bar(
            name='AFC Coefficient',
            x=df['Country_Name'],
            y=df['Total_AFC'],
            marker_color='#ff7f0e'
        ))
        
        fig.add_trace(go.Bar(
            name='FIFA Ranking',
            x=df['Country_Name'],
            y=df['Total_FIFA'],
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
        uefa_cols = ['UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25']
        uefa_labels = ['2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25']
        
        fig = go.Figure()
        
        for idx, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=uefa_labels,
                y=[row[col] for col in uefa_cols],
                mode='lines+markers',
                name=row['Country_Name']
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
        - **UEFA Coefficient**: Sum of coefficients from 2018/19 to 2024/25
        - **AFC Coefficient**: Sum of coefficients from 2018 to 2024/25
        - **FIFA Ranking**: Average of FIFA rankings from 2018 to 2025
        - **Final Score (Total4)**: Combined weighted score from all three components
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
    import traceback
    st.code(traceback.format_exc())
