import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math

# Page config
st.set_page_config(
    page_title="Ex-Soviet Football Ranking",
    page_icon="⚽",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        min-width: 0px !important;
    }
    /* Adjust label size for very small columns */
    .stMetric label {
        font-size: 12px !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 16px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0 0;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
    }
    h2 {
        color: #2c3e50;
    }
    /* Custom CSS for compact tables in 4-column layout */
    [data-testid="stDataFrame"] {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

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

# Country code to emoji flag mapping
FLAG_EMOJI = {
    'UKR': '🇺🇦',
    'RUS': '🇷🇺',
    'AZE': '🇦🇿',
    'UZB': '🇺🇿',
    'ARM': '🇦🇲',
    'MDA': '🇲🇩',
    'LVA': '🇱🇻',
    'KAZ': '🇰🇿',
    'GEO': '🇬🇪',
    'KGZ': '🇰🇬',
    'EST': '🇪🇪',
    'LTU': '🇱🇹',
    'BLR': '🇧🇾',
    'TKM': '🇹🇲',
    'TJK': '🇹🇯'
}

# --- HELPER FUNCTIONS ---

def get_league_tier_name(position):
    """Returns the league name based on overall position."""
    if position <= 20:
        return "🥇 Premier League"
    elif position <= 44:
        return "🥈 Championship"
    elif position <= 68:
        return "🥉 League One"
    elif position <= 92:
        return "📋 League Two"
    else:
        return "⬇️ Below League Two"

def calculate_zoom(lat_min, lat_max, lon_min, lon_max):
    """Calculates optimal zoom level for mapbox."""
    delta_lat = abs(lat_max - lat_min)
    delta_lon = abs(lon_max - lon_min)
    
    # Calibrated zoom logic
    padding_factor = 1.5 
    zoom_lon = math.log2((360 * 2.0) / (max(delta_lon, 0.01) * padding_factor))
    zoom_lat = math.log2((180 * 2.0) / (max(delta_lat, 0.01) * padding_factor))
    
    # Default to 4.0 if single point or error, max 10 to avoid too close
    zoom = min(min(zoom_lon, zoom_lat), 10)
    return max(zoom, 1.0) # Prevent negative zoom

# --- DATA LOADING ---

@st.cache_data(ttl=0)
def load_and_calculate_data():
    # Load LeagueRanking.csv
    league_df = pd.read_csv('LeagueRanking.csv', sep=',', decimal='.')
    
    # Convert numeric columns to float
    uefa_cols = ['UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25']
    afc_cols = ['AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25']
    fifa_cols = ['FIFA_2018_09_20', 'FIFA_2019_09_19', 'FIFA_2020_09_17', 'FIFA_2021_09_16', 'FIFA_2022_08_25', 'FIFA_2023_09_21', 'FIFA_2024_09_19', 'FIFA_2025_09_18']
    
    for col in uefa_cols + afc_cols + fifa_cols:
        league_df[col] = pd.to_numeric(league_df[col], errors='coerce').fillna(0)
    
    # Calculate total_uefa
    weights = [0.6, 0.7, 0.8, 0.9, 1.0]
    uefa_last_5 = uefa_cols[-5:]
    league_df['total'] = league_df.apply(lambda row: sum([row[uefa_last_5[i]] * weights[i] for i in range(len(uefa_last_5))]) / 5, axis=1)
    
    # Calculate total_afc
    afc_last_5 = afc_cols[-5:]
    league_df['total2'] = league_df.apply(lambda row: sum([row[afc_last_5[i]] * weights[i] for i in range(len(afc_last_5))]) / 5, axis=1)
    
    # Calculate total_fifa
    fifa_last_5 = fifa_cols[-5:]
    league_df['total3'] = league_df.apply(lambda row: sum([row[fifa_last_5[i]] * weights[i] for i in range(len(fifa_last_5))]) / 5, axis=1)
    
    # Calculate total4 (Nation Coefficient)
    league_df['total4'] = ((league_df['total'] * 0.3) + (league_df['total2'] * 0.1) + (league_df['total3'] * 0.6)) / 100
    
    # Add metadata
    league_df['country_name'] = league_df['country_code'].map(COUNTRY_NAMES)
    league_df['flag'] = league_df['country_code'].map(FLAG_EMOJI)
    
    # Sort
    league_df = league_df.sort_values('total4', ascending=False).reset_index(drop=True)
    
    return league_df

@st.cache_data(ttl=0)
def calculate_club_coefficients(league_df):
    # Load ClubCoef.csv
    club_df = pd.read_csv('ClubCoef.csv', sep=',', decimal='.')
    
    # Convert numeric columns
    numeric_cols = ['year', 'league_tier', 'league_games', 'league_points', 'group', 'group_games', 'group_points']
    for col in numeric_cols:
        club_df[col] = pd.to_numeric(club_df[col], errors='coerce')
    
    if 'lat' in club_df.columns: club_df['lat'] = pd.to_numeric(club_df['lat'], errors='coerce')
    if 'lon' in club_df.columns: club_df['lon'] = pd.to_numeric(club_df['lon'], errors='coerce')
    
    # Row Coefficient Calculation
    def calculate_row_coefficient(row):
        league_tier = row['league_tier']
        league_games = row['league_games']
        league_points = row['league_points']
        group = row['group']
        group_games = row['group_games']
        group_points = row['group_points']
        
        has_group = pd.notna(group) and pd.notna(group_games) and pd.notna(group_points)
        
        if not has_group:
            if league_games != 0 and league_tier != 0:
                return (league_points / league_games) * (league_tier ** -0.95)
            else:
                return 0
        else:
            if group == 1 or group == 2:
                league_part = 0
                if league_games != 0 and league_tier != 0:
                    league_part = (league_points / league_games) * (league_tier ** -0.95)
                
                group_part = 0
                if group_games != 0 and league_tier != 0:
                    multiplier = 1 if group == 1 else 0.913
                    group_part = (group_points / group_games) * (league_tier ** -0.95) * multiplier
                
                return (league_part + group_part) / 2
            else:
                return 0
    
    club_df['row_coefficient'] = club_df.apply(calculate_row_coefficient, axis=1)
    if 'team' in club_df.columns: club_df['team'] = club_df['team'].astype(str).str.strip()

    # Aggregate by Club
    club_results = []
    
    for (country_code, team_code), group in club_df.groupby(['country_code', 'team_code']):
        top_5 = group.nlargest(5, 'year')
        
        if len(top_5) > 0:
            avg_coefficient = top_5['row_coefficient'].fillna(0).mean()
            nation_coef_val = league_df[league_df['country_code'] == country_code]['total4'].values
            nation_coef = nation_coef_val[0] if len(nation_coef_val) > 0 else 0
            point_avg = avg_coefficient * nation_coef
            
            # Extract coordinates (first non-null)
            lat = group['lat'].dropna().iloc[0] if not group['lat'].dropna().empty else None
            lon = group['lon'].dropna().iloc[0] if not group['lon'].dropna().empty else None

            club_results.append({
                'country_code': country_code,
                'team': group['team'].iloc[0],
                'team_code': team_code,
                'point_avg': point_avg,
                'avg_coefficient': avg_coefficient,
                'nation_coef': nation_coef,
                'lat': lat,
                'lon': lon
            })
    
    club_results_df = pd.DataFrame(club_results)
    club_results_df = club_results_df.sort_values('point_avg', ascending=False).reset_index(drop=True)
    
    # Add overall position and League Name
    club_results_df['overall_position'] = range(1, len(club_results_df) + 1)
    club_results_df['league_tier_name'] = club_results_df['overall_position'].apply(get_league_tier_name)
    
    # Add metadata
    club_results_df['country_name'] = club_results_df['country_code'].map(COUNTRY_NAMES)
    club_results_df['flag'] = club_results_df['country_code'].map(FLAG_EMOJI)
    
    return club_results_df, club_df

def generate_flag_bar(present_country_codes):
    all_codes = sorted(list(FLAG_EMOJI.keys()))
    html = "<div style='display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px;'>"
    for code in all_codes:
        flag = FLAG_EMOJI[code]
        if code in present_country_codes:
            html += f"<span style='opacity: 1.0; font-size: 1.2rem; cursor: help;' title='{COUNTRY_NAMES[code]}'>{flag}</span>"
        else:
            html += f"<span style='opacity: 0.2; filter: grayscale(100%); font-size: 1.2rem; cursor: help;' title='Not represented: {COUNTRY_NAMES[code]}'>{flag}</span>"
    html += "</div>"
    return html

# --- MAIN APP ---

try:
    league_df = load_and_calculate_data()
    club_results_df, club_df = calculate_club_coefficients(league_df)
    
    # HEADER
    st.title("⚽ Ex-Soviet Republics Football Ranking System")
    st.markdown("*Comprehensive ranking based on UEFA, AFC coefficients and FIFA rankings*")
    st.markdown("---")
    
    # 1. NATION RANKINGS (SUMMARY)
    st.header("🏆 Current Nation Rankings (2024/25)")
    
    rankings_html = """<div style="display: flex; flex-direction: row; justify-content: space-between; overflow-x: auto; padding-bottom: 15px; gap: 10px;">"""
    for idx, row in league_df.iterrows():
        rank = idx + 1
        rank_display = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            
        rankings_html += f"""
        <div style="text-align: center; flex: 1; min-width: 60px;">
            <div style="font-weight: bold; font-size: 1rem; margin-bottom: 5px;">{rank_display}</div>
            <div style="font-size: 3rem; line-height: 1.1; margin-bottom: 5px; cursor: help;" title="{row['country_name']}">{row['flag']}</div>
            <div style="font-size: 0.85rem; color: #555; background: #f0f2f6; border-radius: 5px; padding: 2px 5px;">{row['total4']:.2f}</div>
        </div>"""
    rankings_html += "</div>"
    st.markdown(rankings_html, unsafe_allow_html=True)
    st.markdown("---")
    
    # 2. FULL NATION TABLE
    st.subheader("📊 Complete Nation Rankings")
    display_df = league_df[['flag', 'country_name', 'total', 'total2', 'total3', 'total4']].copy()
    display_df.columns = ['🏴', 'Country', 'UEFA Coefficient', 'AFC Coefficient', 'FIFA Ranking', 'Nation Coefficient']
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
    
    for col in ['UEFA Coefficient', 'AFC Coefficient', 'FIFA Ranking', 'Nation Coefficient']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "0.0000")
    
    st.dataframe(
        display_df, use_container_width=True, hide_index=True,
        height=(len(display_df) + 1) * 35 + 3,
        column_config={"Rank": st.column_config.NumberColumn("Rank", format="%d")}
    )
    st.markdown("---")
    
    # 3. TOP CLUBS
    st.header("🏅 Top Club Rankings (by ClubCoef)")
    top_clubs = club_results_df.head(20).copy()
    
    st.subheader("⭐ Top 5 Clubs")
    cols = st.columns(5)
    for idx in range(min(5, len(top_clubs))):
        with cols[idx]:
            club = top_clubs.iloc[idx]
            st.markdown(f"### {club['flag']}")
            st.markdown(f"**#{idx+1}**")
            st.markdown(f"**{club['team']}**")
            st.metric("ClubCoef", f"{club['point_avg']:.4f}")
            st.caption(club['country_name'])
    st.markdown("---")
    
    st.subheader("📋 Top 20 Clubs")
    display_clubs = top_clubs[['flag', 'team', 'country_name', 'point_avg']].copy()
    display_clubs.columns = ['🏴', 'Club', 'Country', 'ClubCoef']
    display_clubs.insert(0, 'Rank', range(1, len(display_clubs) + 1))
    display_clubs['ClubCoef'] = display_clubs['ClubCoef'].apply(lambda x: f"{x:.4f}")
    st.dataframe(display_clubs, use_container_width=True, hide_index=True)
    st.markdown("---")
    
    # 4. VISUALIZATIONS
    st.header("📈 Visualizations")
    
    # Added "Global Map" as the new first tab (or last, depending on preference. Put first for visibility).
    tabs = st.tabs([
        "🗺️ Global Map",
        "Nation Coefficients", 
        "Coefficient Breakdown", 
        "Historical UEFA", 
        "Historical AFC", 
        "Top Clubs", 
        "🏆 League System", 
        "🌍 Country Rankings"
    ])
    
    # TAB: GLOBAL MAP
    with tabs[0]:
        st.markdown("### 🗺️ Map of All Ex-Soviet Clubs")
        st.markdown("Locations of all clubs in the database.")
        
        map_all_clubs = club_results_df.dropna(subset=['lat', 'lon']).copy()
        
        if not map_all_clubs.empty:
            # Create hover text column for cleaner Mapbox display
            # Customdata: 0=Flag, 1=Country, 2=League Name, 3=Coef
            
            fig_global = px.scatter_mapbox(
                map_all_clubs,
                lat="lat", lon="lon",
                hover_name="team",
                # We use custom_data to pass the extra info to the template
                hover_data={
                    "flag": True, 
                    "country_name": True,
                    "league_tier_name": True,
                    "point_avg": True,
                    "lat": False, "lon": False
                },
                color_discrete_sequence=["#0068c9"], # Single blue color
                zoom=2.5,
                height=600
            )
            
            fig_global.update_traces(
                marker=dict(size=10, opacity=0.8),
                hovertemplate=(
                    "<b>%{hovertext}</b><br><br>"
                    "%{customdata[0]} %{customdata[1]}<br>"
                    "🏆 %{customdata[2]}<br>"
                    "Coef: %{customdata[3]:.4f}<extra></extra>"
                )
            )
            
            fig_global.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0},
                # Center roughly on the region
                mapbox=dict(center=dict(lat=50, lon=60))
            )
            
            st.plotly_chart(fig_global, use_container_width=True)
        else:
            st.warning("No coordinate data available for clubs.")

    # TAB: NATION COEFFICIENTS
    with tabs[1]:
        fig = px.bar(
            league_df, x='country_name', y='total4',
            title='Nation Coefficients by Country',
            labels={'total4': 'Nation Coefficient', 'country_name': 'Country'},
            color='total4', color_continuous_scale='Oryel', text='flag'
        )
        fig.update_traces(textposition='outside', textfont_size=20)
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB: BREAKDOWN
    with tabs[2]:
        fig = go.Figure()
        fig.add_trace(go.Bar(name='UEFA (30%)', x=league_df['country_name'], y=league_df['total'], marker_color='#1f77b4', text=league_df['flag'], textposition='outside'))
        fig.add_trace(go.Bar(name='AFC (10%)', x=league_df['country_name'], y=league_df['total2'], marker_color='#ff7f0e'))
        fig.add_trace(go.Bar(name='FIFA (60%)', x=league_df['country_name'], y=league_df['total3'], marker_color='#2ca02c'))
        fig.update_layout(title='Coefficient Breakdown', barmode='group', height=500, xaxis_title='Country', yaxis_title='Points')
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB: HISTORICAL UEFA
    with tabs[3]:
        uefa_cols = ['UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25']
        uefa_labels = ['2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25']
        fig = go.Figure()
        for idx, row in league_df.iterrows():
            fig.add_trace(go.Scatter(x=uefa_labels, y=[row[col] for col in uefa_cols], mode='lines+markers', name=f"{row['flag']} {row['country_name']}"))
        fig.update_layout(title='UEFA Coefficients Over Time', height=600, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
    # TAB: HISTORICAL AFC
    with tabs[4]:
        afc_cols = ['AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25']
        afc_labels = ['2018', '2019', '2021', '2022', '2023/24', '2024/25']
        fig = go.Figure()
        for idx, row in league_df.iterrows():
            fig.add_trace(go.Scatter(x=afc_labels, y=[row[col] for col in afc_cols], mode='lines+markers', name=f"{row['flag']} {row['country_name']}"))
        fig.update_layout(title='AFC Coefficients Over Time', height=600, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB: TOP CLUBS CHART
    with tabs[5]:
        top_15 = club_results_df.head(15).copy()
        fig = px.bar(
            top_15, x='team', y='point_avg', title='Top 15 Clubs by ClubCoef',
            labels={'point_avg': 'ClubCoef', 'team': 'Club'},
            color='point_avg', color_continuous_scale='Oryel', text='flag', hover_data=['country_name']
        )
        fig.update_traces(textposition='outside', textfont_size=18)
        fig.update_layout(showlegend=False, height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB: LEAGUE SYSTEM
    with tabs[6]:
        st.markdown("## 🏆 Theoretical Ex-Soviet League System")
        st.markdown("*English football pyramid style - 4 divisions based on club coefficients*")
        st.info("**System Overview:** The league system groups the top 92 clubs into 4 tiers.")
        
        all_clubs = club_results_df.copy()
        premier_league = all_clubs.iloc[0:20].copy()
        championship = all_clubs.iloc[20:44].copy()
        league_one = all_clubs.iloc[44:68].copy()
        league_two = all_clubs.iloc[68:92].copy()
        
        tiers_data = [
            (premier_league, "🥇 Premier League", 1),
            (championship, "🥈 Championship", 2),
            (league_one, "🥉 League One", 3),
            (league_two, "📋 League Two", 4)
        ]
        
        # 1. Tables
        table_cols = st.columns(4)
        for idx, (league_df_tier, league_name, tier) in enumerate(tiers_data):
            with table_cols[idx]:
                st.subheader(f"{league_name}")
                st.markdown(generate_flag_bar(league_df_tier['country_code'].unique()), unsafe_allow_html=True)
                st.caption(f"Avg Coef: {league_df_tier['point_avg'].mean():.2f}")
                
                display = league_df_tier[['flag', 'team', 'point_avg']].copy()
                display.columns = ['🏴', 'Club', 'Coef']
                display.insert(0, 'Pos', range(1, len(display) + 1))
                display['Coef'] = display['Coef'].apply(lambda x: f"{x:.2f}")
                
                # Status
                display['Status'] = ''
                if tier == 1:
                    if display.index[0] == 0: display.loc[0, 'Status'] = '🏆 C'
                    display.loc[display.index[-3:], 'Status'] = '🔻 R'
                else:
                    display.loc[display.index[0:2], 'Status'] = '🔼 P'
                    display.loc[display.index[2:6], 'Status'] = '🎲 PO'
                    if tier < 4: display.loc[display.index[-3:], 'Status'] = '🔻 R'
                
                st.dataframe(
                    display, use_container_width=True, hide_index=True,
                    height=(len(display) + 1) * 35 + 5,
                    column_config={"Pos": st.column_config.NumberColumn("Pos", format="%d")}
                )
    
        # 2. Maps
        map_cols = st.columns(4)
        for idx, (league_df_tier, league_name, tier) in enumerate(tiers_data):
            with map_cols[idx]:
                map_data = league_df_tier.dropna(subset=['lat', 'lon'])
                if not map_data.empty:
                    st.markdown(f"###### 📍 {league_name} Map")
                    
                    # Zoom Calc
                    lat_min, lat_max = map_data['lat'].min(), map_data['lat'].max()
                    lon_min, lon_max = map_data['lon'].min(), map_data['lon'].max()
                    center_lat, center_lon = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2
                    zoom_level = calculate_zoom(lat_min, lat_max, lon_min, lon_max)

                    # Plot
                    fig_map = px.scatter_mapbox(
                        map_data, lat="lat", lon="lon", hover_name="team",
                        hover_data={"flag": True, "point_avg": True, "league_tier_name": True, "lat": False, "lon": False},
                        height=450
                    )
                    fig_map.update_traces(
                        marker=dict(size=15, color='#0068c9', opacity=0.75),
                        hovertemplate="<b>%{hovertext}</b><br><br>%{customdata[0]}<br>🏆 %{customdata[2]}<br>Coef: %{customdata[1]:.4f}<extra></extra>"
                    )
                    fig_map.update_layout(
                        mapbox_style="open-street-map", margin={"r":5,"t":5,"l":5,"b":5},
                        mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=zoom_level)
                    )
                    st.plotly_chart(fig_map, use_container_width=True)

        # 3. Distribution Chart
        st.markdown("---")
        st.subheader("📊 Distribution of Clubs in the League System")
        clubs_per_nation = all_clubs[all_clubs['overall_position'] <= 92]['country_name'].value_counts().reset_index()
        clubs_per_nation.columns = ['country_name', 'clubs_in_system']
        if 'clubs_in_system' in league_df.columns: league_df = league_df.drop(columns=['clubs_in_system'])
        league_df = league_df.merge(clubs_per_nation, on='country_name', how='left').fillna({'clubs_in_system': 0})
        df_plot = league_df.sort_values('clubs_in_system', ascending=False)
        df_plot['x_label'] = df_plot['flag'] + " " + df_plot['country_name']
        
        fig_system = px.bar(
            df_plot, x='x_label', y='clubs_in_system', labels={'clubs_in_system': 'Number of Clubs', 'x_label': 'Country'},
            color='clubs_in_system', color_continuous_scale='Oryel', text='clubs_in_system'
        )
        fig_system.update_traces(textposition='outside')
        fig_system.update_layout(xaxis_tickangle=-45, height=600, showlegend=False, margin=dict(t=50))
        st.plotly_chart(fig_system, use_container_width=True)

    # TAB: COUNTRY RANKINGS
    with tabs[7]:
        st.markdown("## 🌍 Club Rankings by Country")
        col1, col2 = st.columns([1, 3])
        countries_with_clubs = sorted(club_results_df['country_code'].unique())
        
        with col1:
            selected_country = st.selectbox("Select Country:", countries_with_clubs, format_func=lambda x: f"{FLAG_EMOJI.get(x, '')} {COUNTRY_NAMES.get(x, x)}")
        with col2:
            st.markdown(f"# {FLAG_EMOJI.get(selected_country, '')} {COUNTRY_NAMES.get(selected_country, '')}")
        
        st.markdown("---")
        
        country_clubs = club_results_df[club_results_df['country_code'] == selected_country].copy()
        country_clubs['national_rank'] = range(1, len(country_clubs) + 1)
        
        # New Country Map Section
        st.subheader(f"🗺️ Map of Clubs in {COUNTRY_NAMES.get(selected_country)}")
        
        country_map_data = country_clubs.dropna(subset=['lat', 'lon'])
        
        if not country_map_data.empty:
            # Calc Zoom
            lat_min, lat_max = country_map_data['lat'].min(), country_map_data['lat'].max()
            lon_min, lon_max = country_map_data['lon'].min(), country_map_data['lon'].max()
            center_lat, center_lon = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2
            zoom_level = calculate_zoom(lat_min, lat_max, lon_min, lon_max)
            
            fig_country_map = px.scatter_mapbox(
                country_map_data,
                lat="lat", lon="lon",
                hover_name="team",
                hover_data={"flag": True, "league_tier_name": True, "point_avg": True, "lat": False, "lon": False},
                color_discrete_sequence=["#0068c9"],
                height=500
            )
            
            fig_country_map.update_traces(
                marker=dict(size=15, opacity=0.8),
                hovertemplate="<b>%{hovertext}</b><br><br>🏆 %{customdata[1]}<br>Coef: %{customdata[2]:.4f}<extra></extra>"
            )
            
            fig_country_map.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":0,"l":0,"b":0},
                mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=zoom_level)
            )
            st.plotly_chart(fig_country_map, use_container_width=True)
        else:
            st.info("No GPS coordinates available for clubs in this country.")

        st.markdown("---")
        
        # Metrics & Tables (Existing)
        nation_coef = league_df[league_df['country_code'] == selected_country]['total4'].values[0] if len(league_df[league_df['country_code'] == selected_country]) > 0 else 0
        clubs_in_system = len(country_clubs[country_clubs['overall_position'] <= 92])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Nation Rank", f"#{league_df[league_df['country_code'] == selected_country].index[0] + 1}")
        m2.metric("Nation Coefficient", f"{nation_coef:.4f}")
        m3.metric("Total Clubs", len(country_clubs))
        m4.metric("Clubs in League System", clubs_in_system)
        
        st.subheader(f"🏆 All Clubs from {COUNTRY_NAMES.get(selected_country)}")
        display_country = country_clubs[['national_rank', 'team', 'league_tier_name', 'overall_position', 'point_avg']].copy()
        display_country.columns = ['National Rank', 'Club', 'League', 'Overall Rank', 'ClubCoef']
        display_country['ClubCoef'] = display_country['ClubCoef'].apply(lambda x: f"{x:.4f}")
        
        st.dataframe(
            display_country, use_container_width=True, hide_index=True,
            height=min(600, len(display_country) * 35 + 38),
            column_config={
                "National Rank": st.column_config.NumberColumn("National Rank", format="%d", width="small"),
                "Overall Rank": st.column_config.NumberColumn("Overall Rank", format="%d", width="small")
            }
        )

        # Existing stats charts...
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            dist = country_clubs['league_tier_name'].value_counts().reset_index()
            dist.columns = ['League', 'Count']
            order = ["🥇 Premier League", "🥈 Championship", "🥉 League One", "📋 League Two", "⬇️ Below League Two"]
            dist['League'] = pd.Categorical(dist['League'], categories=order, ordered=True)
            dist = dist.sort_values('League')
            fig = px.bar(dist, x='League', y='Count', title=f'League Distribution', color='Count', color_continuous_scale='Oryel')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(country_clubs.head(10), x='team', y='point_avg', title=f'Top 10 Clubs', color='point_avg', color_continuous_scale='Oryel')
            fig.update_layout(showlegend=False, height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # FOOTER
    st.markdown("---")
    st.markdown("""<div style='text-align: center; color: #666; padding: 20px;'><p><strong>Ex-Soviet Football Ranking System</strong></p><p>Data sources: UEFA, AFC, FIFA • Last updated: 2024/25 Season</p></div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
