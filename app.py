import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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

# Load and calculate data
# HINWEIS: ttl=0 erzwingt das Neuladen (Cache Clear), damit Änderungen an der CSV sofort sichtbar sind.
@st.cache_data(ttl=0)
def load_and_calculate_data():
    # Load LeagueRanking.csv
    # Updated to American format (comma separator, dot decimal) for GitHub compatibility
    league_df = pd.read_csv('LeagueRanking.csv', sep=',', decimal='.')
    
    # Convert numeric columns to float
    uefa_cols = ['UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25']
    afc_cols = ['AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25']
    fifa_cols = ['FIFA_2018_09_20', 'FIFA_2019_09_19', 'FIFA_2020_09_17', 'FIFA_2021_09_16', 'FIFA_2022_08_25', 'FIFA_2023_09_21', 'FIFA_2024_09_19', 'FIFA_2025_09_18']
    
    for col in uefa_cols + afc_cols + fifa_cols:
        league_df[col] = pd.to_numeric(league_df[col], errors='coerce').fillna(0)
    
    # Calculate total_uefa (last 5 UEFA seasons with weights)
    weights = [0.6, 0.7, 0.8, 0.9, 1.0]
    uefa_last_5 = uefa_cols[-5:]
    
    league_df['total'] = league_df.apply(
        lambda row: sum([row[uefa_last_5[i]] * weights[i] for i in range(len(uefa_last_5))]) / 5,
        axis=1
    )
    
    # Calculate total_afc (last 5 AFC seasons with weights)
    afc_last_5 = afc_cols[-5:]
    
    league_df['total2'] = league_df.apply(
        lambda row: sum([row[afc_last_5[i]] * weights[i] for i in range(len(afc_last_5))]) / 5,
        axis=1
    )
    
    # Calculate total_fifa (last 5 FIFA rankings with weights)
    fifa_last_5 = fifa_cols[-5:]
    
    league_df['total3'] = league_df.apply(
        lambda row: sum([row[fifa_last_5[i]] * weights[i] for i in range(len(fifa_last_5))]) / 5,
        axis=1
    )
    
    # Calculate total4 (total_all = Nation Coefficient)
    league_df['total4'] = ((league_df['total'] * 0.3) + (league_df['total2'] * 0.1) + (league_df['total3'] * 0.6)) / 100
    
    # Add full country names and flags
    league_df['country_name'] = league_df['country_code'].map(COUNTRY_NAMES)
    league_df['flag'] = league_df['country_code'].map(FLAG_EMOJI)
    
    # Sort by total4
    league_df = league_df.sort_values('total4', ascending=False).reset_index(drop=True)
    
    return league_df

@st.cache_data(ttl=0)
def calculate_club_coefficients(league_df):
    # Load ClubCoef.csv
    # Updated to American format (comma separator, dot decimal) for GitHub compatibility
    club_df = pd.read_csv('ClubCoef.csv', sep=',', decimal='.')
    
    # Convert numeric columns
    numeric_cols = ['year', 'league_tier', 'league_games', 'league_points', 'group', 'group_games', 'group_points']
    for col in numeric_cols:
        club_df[col] = pd.to_numeric(club_df[col], errors='coerce')
    
    # Handle coordinates if present (ensure they are numeric)
    if 'lat' in club_df.columns:
        club_df['lat'] = pd.to_numeric(club_df['lat'], errors='coerce')
    if 'lon' in club_df.columns:
        club_df['lon'] = pd.to_numeric(club_df['lon'], errors='coerce')
    
    # Calculate club coefficient for each row
    def calculate_row_coefficient(row):
        league_tier = row['league_tier']
        league_games = row['league_games']
        league_points = row['league_points']
        group = row['group']
        group_games = row['group_games']
        group_points = row['group_points']
        
        # Check if group phase exists
        has_group = pd.notna(group) and pd.notna(group_games) and pd.notna(group_points)
        
        if not has_group:
            # No group phase
            if league_games != 0 and league_tier != 0:
                return (league_points / league_games) * (league_tier ** -0.95)
            else:
                return 0
        else:
            # Has group phase
            if group == 1 or group == 2:
                # League part
                league_part = 0
                if league_games != 0 and league_tier != 0:
                    league_part = (league_points / league_games) * (league_tier ** -0.95)
                
                # Group part
                group_part = 0
                if group_games != 0 and league_tier != 0:
                    multiplier = 1 if group == 1 else 0.913
                    group_part = (group_points / group_games) * (league_tier ** -0.95) * multiplier
                
                return (league_part + group_part) / 2
            else:
                return 0  # Error case
    
    club_df['row_coefficient'] = club_df.apply(calculate_row_coefficient, axis=1)
    
    # Clean team names to ensure consistency (remove extra spaces)
    if 'team' in club_df.columns:
        club_df['team'] = club_df['team'].astype(str).str.strip()

    # Calculate ClubCoef (formerly PointAVG) for each club
    club_results = []
    
    # ORIGINAL GROUPING: By ['country_code', 'team_code']
    # This preserves separate entries if team codes differ (e.g. M25 and M26 are treated separately)
    for (country_code, team_code), group in club_df.groupby(['country_code', 'team_code']):
        # Sort by year descending and take top 5
        top_5 = group.nlargest(5, 'year')
        
        if len(top_5) > 0:
            # Calculate average of row coefficients
            avg_coefficient = top_5['row_coefficient'].fillna(0).mean()
            
            # Get nation coefficient (total4) from league_df
            nation_coef = league_df[league_df['country_code'] == country_code]['total4'].values
            nation_coef = nation_coef[0] if len(nation_coef) > 0 else 0
            
            # Calculate ClubCoef
            point_avg = avg_coefficient * nation_coef
            
            # Extract coordinates if available (take first non-null value)
            lat = None
            lon = None
            if 'lat' in group.columns and 'lon' in group.columns:
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
    
    # Add overall position to all clubs
    club_results_df['overall_position'] = range(1, len(club_results_df) + 1)
    
    # Add country names and flags
    club_results_df['country_name'] = club_results_df['country_code'].map(COUNTRY_NAMES)
    club_results_df['flag'] = club_results_df['country_code'].map(FLAG_EMOJI)
    
    return club_results_df, club_df

# Helper function to generate flag HTML with graying out
def generate_flag_bar(present_country_codes):
    all_codes = sorted(list(FLAG_EMOJI.keys()))
    html = "<div style='display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px;'>"
    for code in all_codes:
        flag = FLAG_EMOJI[code]
        if code in present_country_codes:
            # Active flag
            html += f"<span style='opacity: 1.0; font-size: 1.2rem; cursor: help;' title='{COUNTRY_NAMES[code]}'>{flag}</span>"
        else:
            # Inactive flag (grayed out) - Updated with country name
            html += f"<span style='opacity: 0.2; filter: grayscale(100%); font-size: 1.2rem; cursor: help;' title='Not represented: {COUNTRY_NAMES[code]}'>{flag}</span>"
    html += "</div>"
    return html

# Load the data
try:
    league_df = load_and_calculate_data()
    club_results_df, club_df = calculate_club_coefficients(league_df)
    
    # Title with improved styling
    st.title("⚽ Ex-Soviet Republics Football Ranking System")
    st.markdown("*Comprehensive ranking based on UEFA, AFC coefficients and FIFA rankings*")
    st.markdown("---")
    
    # Main ranking table
    st.header("🏆 Current Nation Rankings (2024/25)")
    
    # Use HTML Flexbox instead of st.columns to allow proper sizing and fitting in one row
    rankings_html = """<div style="display: flex; flex-direction: row; justify-content: space-between; overflow-x: auto; padding-bottom: 15px; gap: 10px;">"""
    
    for idx, row in league_df.iterrows():
        rank = idx + 1
        # Add medal/position
        if rank == 1:
            rank_display = "🥇"
            border_color = "#FFD700" # Gold
        elif rank == 2:
            rank_display = "🥈"
            border_color = "#C0C0C0" # Silver
        elif rank == 3:
            rank_display = "🥉"
            border_color = "#CD7F32" # Bronze
        else:
            rank_display = f"#{rank}"
            border_color = "transparent"
            
        rankings_html += f"""
        <div style="text-align: center; flex: 1; min-width: 60px;">
            <div style="font-weight: bold; font-size: 1rem; margin-bottom: 5px;">{rank_display}</div>
            <div style="font-size: 3rem; line-height: 1.1; margin-bottom: 5px; cursor: help;" title="{row['country_name']}">{row['flag']}</div>
            <div style="font-size: 0.85rem; color: #555; background: #f0f2f6; border-radius: 5px; padding: 2px 5px;">{row['total4']:.2f}</div>
        </div>"""
        
    rankings_html += "</div>"
    st.markdown(rankings_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Full ranking table with flags
    st.subheader("📊 Complete Nation Rankings")
    
    # Create display dataframe with flags
    display_df = league_df[['flag', 'country_name', 'total', 'total2', 'total3', 'total4']].copy()
    display_df.columns = ['🏴', 'Country', 'UEFA Coefficient', 'AFC Coefficient', 'FIFA Ranking', 'Nation Coefficient']
    
    # Add rank column
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
    
    # Format numbers
    for col in ['UEFA Coefficient', 'AFC Coefficient', 'FIFA Ranking', 'Nation Coefficient']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "0.0000")
    
    # Calculate height: (rows + header) * approx_row_height + padding
    # Using 35px per row and some buffer
    table_height = (len(display_df) + 1) * 35 + 3
    
    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True,
        height=table_height,
        column_config={
            "Rank": st.column_config.NumberColumn(
                "Rank",
                help="Current ranking position",
                format="%d"
            ),
            "🏴": st.column_config.TextColumn(
                "🏴",
                help="National flag",
                width="small"
            )
        }
    )
    
    st.markdown("---")
    
    # Club Rankings with flags
    st.header("🏅 Top Club Rankings (by ClubCoef)")
    
    # Top 20 clubs
    top_clubs = club_results_df.head(20).copy()
    
    # Show top 5 in columns
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
    
    # Full club table
    st.subheader("📋 Top 20 Clubs")
    
    display_clubs = top_clubs[['flag', 'team', 'country_name', 'point_avg']].copy()
    display_clubs.columns = ['🏴', 'Club', 'Country', 'ClubCoef']
    display_clubs.insert(0, 'Rank', range(1, len(display_clubs) + 1))
    display_clubs['ClubCoef'] = display_clubs['ClubCoef'].apply(lambda x: f"{x:.4f}")
    
    st.dataframe(
        display_clubs, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(
                "Rank",
                format="%d"
            )
        }
    )
    
    st.markdown("---")
    
    # Visualizations
    st.header("📈 Visualizations")
    
    # Add Historical AFC tab
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Nation Coefficients", 
        "Coefficient Breakdown", 
        "Historical UEFA", 
        "Historical AFC", 
        "Top Clubs", 
        "🏆 League System", 
        "🌍 Country Rankings"
    ])
    
    with tab1:
        # Bar chart of nation coefficients with flags in labels
        fig = px.bar(
            league_df, 
            x='country_name', 
            y='total4',
            title='Nation Coefficients by Country',
            labels={'total4': 'Nation Coefficient', 'country_name': 'Country'},
            color='total4',
            color_continuous_scale='Blues',
            text='flag'
        )
        fig.update_traces(textposition='outside', textfont_size=20)
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Stacked bar chart showing breakdown
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='UEFA Coefficient (30%)',
            x=league_df['country_name'],
            y=league_df['total'],
            marker_color='#1f77b4',
            text=league_df['flag'],
            textposition='outside',
            textfont_size=16
        ))
        
        fig.add_trace(go.Bar(
            name='AFC Coefficient (10%)',
            x=league_df['country_name'],
            y=league_df['total2'],
            marker_color='#ff7f0e'
        ))
        
        fig.add_trace(go.Bar(
            name='FIFA Ranking (60%)',
            x=league_df['country_name'],
            y=league_df['total3'],
            marker_color='#2ca02c'
        ))
        
        fig.update_layout(
            title='Coefficient Breakdown by Country',
            barmode='group',
            height=500,
            xaxis_title='Country',
            yaxis_title='Points',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Line chart for UEFA coefficients over time
        uefa_cols = ['UEFA_2018_19', 'UEFA_2019_20', 'UEFA_2020_21', 'UEFA_2021_22', 'UEFA_2022_23', 'UEFA_2023_24', 'UEFA_2024_25']
        uefa_labels = ['2018/19', '2019/20', '2020/21', '2021/22', '2022/23', '2023/24', '2024/25']
        
        fig = go.Figure()
        
        # Add lines for each country
        for idx, row in league_df.iterrows():
            fig.add_trace(go.Scatter(
                x=uefa_labels,
                y=[row[col] for col in uefa_cols],
                mode='lines+markers',
                name=f"{row['flag']} {row['country_name']}",
                line=dict(width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title='UEFA Coefficients Over Time',
            xaxis_title='Season',
            yaxis_title='UEFA Coefficient',
            height=600,
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with tab4:
        # Line chart for AFC coefficients over time
        afc_cols = ['AFC_2018', 'AFC_2019', 'AFC_2021', 'AFC_2022', 'AFC_2023_24', 'AFC_2024_25']
        afc_labels = ['2018', '2019', '2021', '2022', '2023/24', '2024/25']
        
        fig = go.Figure()
        
        # Add lines for each country (only those with non-zero AFC points might be interesting, but showing all for consistency)
        for idx, row in league_df.iterrows():
            # Check if country has any AFC points to avoid clutter if desired, 
            # but usually it's better to show everything or just the relevant ones.
            # Showing all for consistency with other charts.
            fig.add_trace(go.Scatter(
                x=afc_labels,
                y=[row[col] for col in afc_cols],
                mode='lines+markers',
                name=f"{row['flag']} {row['country_name']}",
                line=dict(width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title='AFC Coefficients Over Time',
            xaxis_title='Season',
            yaxis_title='AFC Coefficient',
            height=600,
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        # Bar chart of top clubs with flags
        top_15 = club_results_df.head(15).copy()
        
        fig = px.bar(
            top_15,
            x='team',
            y='point_avg',
            title='Top 15 Clubs by ClubCoef',
            labels={'point_avg': 'ClubCoef', 'team': 'Club'},
            color='point_avg',
            color_continuous_scale='Reds',
            text='flag',
            hover_data=['country_name']
        )
        fig.update_traces(textposition='outside', textfont_size=18)
        fig.update_layout(showlegend=False, height=500)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab6:
        # League System Tab - English-style 4-tier structure
        st.markdown("## 🏆 Theoretical Ex-Soviet League System")
        st.markdown("*English football pyramid style - 4 divisions based on club coefficients*")
        
        # Info box
        st.info("""
        **System Overview:**
        The league system groups the top 92 clubs into 4 tiers.
        Flags indicate which countries are represented in each league (grayed out flags are not present).
        """)
        
        # Prepare league data
        all_clubs = club_results_df.copy()
        
        # Define league tiers: 20 + 24 + 24 + 24
        premier_league = all_clubs.iloc[0:20].copy()
        championship = all_clubs.iloc[20:44].copy()
        league_one = all_clubs.iloc[44:68].copy()
        league_two = all_clubs.iloc[68:92].copy()
        
        # Create columns for side-by-side view (nebeneinander)
        # Using 4 columns for large displays.
        league_cols = st.columns(4)
        
        tiers_data = [
            (premier_league, "🥇 Premier League", 1, 1),
            (championship, "🥈 Championship", 2, 21),
            (league_one, "🥉 League One", 3, 45),
            (league_two, "📋 League Two", 4, 69)
        ]
        
        for idx, (league_df_tier, league_name, tier, start_pos) in enumerate(tiers_data):
            with league_cols[idx]:
                st.subheader(f"{league_name}")
                
                # Flag visualization (Countries represented)
                present_countries = league_df_tier['country_code'].unique()
                st.markdown(generate_flag_bar(present_countries), unsafe_allow_html=True)
                
                # Metric: Avg Points
                avg_points = league_df_tier['point_avg'].mean()
                st.caption(f"Avg Coef: {avg_points:.2f}")
                
                # Add league position within tier
                league_df_tier = league_df_tier.copy()
                league_df_tier['league_pos'] = range(1, len(league_df_tier) + 1)
                
                # Create display dataframe
                # Removed 'country_name' column as requested, retained flag
                display = league_df_tier[['league_pos', 'flag', 'team', 'point_avg']].copy()
                display.columns = ['Pos', '🏴', 'Club', 'Coef']
                display['Coef'] = display['Coef'].apply(lambda x: f"{x:.2f}")
                
                # Add visual indicators for promotion/relegation zones
                display['Status'] = ''
                
                if tier == 1:
                    # Premier League: Only Champion and Relegation
                    if display.index[0] == 0:
                        display.loc[0, 'Status'] = '🏆 Champion'
                    display.loc[display.index[-3:], 'Status'] = '🔻 Relegation'
                elif tier in [2, 3, 4]:
                    # Championship, League One, League Two: Same structure
                    display.loc[display.index[0:2], 'Status'] = '🔼 Promotion'
                    display.loc[display.index[2:6], 'Status'] = '🎲 Playoffs'
                    display.loc[display.index[-3:], 'Status'] = '🔻 Relegation'
                
                # Calculate height to avoid scrolling: (rows + 1 header) * approx_row_height + padding
                table_height = (len(display) + 1) * 35 + 5
                
                st.dataframe(
                    display,
                    use_container_width=True,
                    hide_index=True,
                    height=table_height,
                    column_config={
                        "Pos": st.column_config.NumberColumn(
                            "Pos",
                            format="%d"
                        ),
                        "🏴": st.column_config.TextColumn(
                            "🏴"
                        ),
                        "Club": st.column_config.TextColumn(
                            "Club"
                        ),
                        "Coef": st.column_config.TextColumn(
                            "Coef"
                        ),
                         "Status": st.column_config.TextColumn(
                            "Status"
                        )
                    }
                )

                # Add Map for this league tier if coordinates exist
                if 'lat' in league_df_tier.columns and 'lon' in league_df_tier.columns:
                    map_data = league_df_tier.dropna(subset=['lat', 'lon'])
                    
                    if not map_data.empty:
                        st.markdown(f"###### 📍 {league_name} Map")
                        
                        # --- DYNAMISCHE ZOOM-BERECHNUNG ---
                        lat_min, lat_max = map_data['lat'].min(), map_data['lat'].max()
                        lon_min, lon_max = map_data['lon'].min(), map_data['lon'].max()
                        
                        # Berechne die maximale Ausdehnung in Grad
                        max_bound = max(abs(lat_max - lat_min), abs(lon_max - lon_min))
                        
                        # Umrechnung in Kilometer (ca. 111km pro Grad)
                        max_bound_km = max_bound * 111
                        
                        # Logarithmische Zoom-Formel
                        # Wir nehmen 10.5 statt 11.5, da dein Container mit 420px sehr schmal ist
                        # Das sorgt für etwas mehr "Puffer" um die Punkte
                        if max_bound_km > 0:
                            zoom_level = 10.5 - np.log10(max_bound_km) # np.log10 ist hier stabiler
                        else:
                            zoom_level = 5 # Standard für einen einzelnen Punkt
                            
                        # Zentrum berechnen
                        center_lat = (lat_min + lat_max) / 2
                        center_lon = (lon_min + lon_max) / 2
                
                        # --- KARTE ERSTELLEN ---
                        fig = px.scatter_mapbox(
                            map_data,
                            lat="lat",
                            lon="lon",
                            hover_name="team",
                            hover_data={"point_avg": ":.2f", "country_name": True, "lat": False, "lon": False},
                            height=400
                        )
                        
                        fig.update_layout(
                            mapbox_style="open-street-map",
                            margin={"r":0,"t":0,"l":0,"b":0},
                            mapbox=dict(
                                center=dict(lat=center_lat, lon=center_lon),
                                zoom=zoom_level
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Map view available once coordinates are stored in the CSV file.")
                else:
                    st.info("Add data to 'lat' and 'lon' columns to the CSV to see a map here.")
    
    with tab7:
        # Country Rankings Tab - Individual country club rankings
        st.markdown("## 🌍 Club Rankings by Country")
        st.markdown("*View the ranking of clubs within each ex-Soviet nation*")
        
        st.markdown("---")
        
        # Country selector
        countries_with_clubs = sorted(club_results_df['country_code'].unique())
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            selected_country = st.selectbox(
                "Select Country:",
                countries_with_clubs,
                format_func=lambda x: f"{FLAG_EMOJI.get(x, '')} {COUNTRY_NAMES.get(x, x)}"
            )
        
        with col2:
            # Show country flag and name prominently
            country_flag = FLAG_EMOJI.get(selected_country, '')
            country_name = COUNTRY_NAMES.get(selected_country, selected_country)
            st.markdown(f"# {country_flag} {country_name}")
        
        st.markdown("---")
        
        # Filter clubs for selected country
        country_clubs = club_results_df[club_results_df['country_code'] == selected_country].copy()
        country_clubs['national_rank'] = range(1, len(country_clubs) + 1)
        
        # Get nation coefficient for this country
        nation_coef = league_df[league_df['country_code'] == selected_country]['total4'].values
        nation_coef = nation_coef[0] if len(nation_coef) > 0 else 0
        
        nation_rank = league_df[league_df['country_code'] == selected_country].index[0] + 1 if len(league_df[league_df['country_code'] == selected_country]) > 0 else 'N/A'
        
        # Country overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nation Rank", f"#{nation_rank}")
        
        with col2:
            st.metric("Nation Coefficient", f"{nation_coef:.4f}")
        
        with col3:
            st.metric("Total Clubs", len(country_clubs))
        
        with col4:
            # Changed metric as requested: "Clubs in League System"
            # Now only counts clubs in the top 92 (Tier 1-4)
            clubs_in_system = len(country_clubs[country_clubs['overall_position'] <= 92])
            st.metric("Clubs in League System", clubs_in_system)
        
        st.markdown("---")
        
        # Club rankings table
        st.subheader(f"🏆 All Clubs from {country_name}")
        
        # Prepare display dataframe
        display_country = country_clubs[['national_rank', 'team', 'point_avg', 'overall_position']].copy()
        display_country.columns = ['National Rank', 'Club', 'ClubCoef', 'Overall Rank']
        
        # Add league tier information
        def get_league_tier(position):
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
        
        display_country['League'] = display_country['Overall Rank'].apply(get_league_tier)
        
        # Format numbers
        display_country['ClubCoef'] = display_country['ClubCoef'].apply(lambda x: f"{x:.4f}")
        
        # Reorder columns
        display_country = display_country[['National Rank', 'Club', 'League', 'Overall Rank', 'ClubCoef']]
        
        st.dataframe(
            display_country,
            use_container_width=True,
            hide_index=True,
            height=min(600, len(display_country) * 35 + 38),
            column_config={
                "National Rank": st.column_config.NumberColumn(
                    "National Rank",
                    help="Ranking within the country",
                    format="%d",
                    width="small"
                ),
                "Overall Rank": st.column_config.NumberColumn(
                    "Overall Rank",
                    help="Overall ranking across all ex-Soviet clubs",
                    format="%d",
                    width="small"
                )
            }
        )
        
        st.markdown("---")
        
        # Visualizations for this country
        st.subheader("📊 Country Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution across leagues
            league_distribution = country_clubs['overall_position'].apply(get_league_tier).value_counts().reset_index()
            league_distribution.columns = ['League', 'Number of Clubs']
            
            # Define order
            league_order = ['🥇 Premier League', '🥈 Championship', '🥉 League One', '📋 League Two', '⬇️ Below League Two']
            league_distribution['League'] = pd.Categorical(league_distribution['League'], categories=league_order, ordered=True)
            league_distribution = league_distribution.sort_values('League')
            
            fig = px.bar(
                league_distribution,
                x='League',
                y='Number of Clubs',
                title=f'League Distribution - {country_name}',
                color='Number of Clubs',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top 10 clubs from this country
            top_10_country = country_clubs.head(10)
            
            fig = px.bar(
                top_10_country,
                x='team',
                y='point_avg',
                title=f'Top 10 Clubs - {country_name}',
                labels={'point_avg': 'ClubCoef', 'team': 'Club'},
                color='point_avg',
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, height=400)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Comparison with other countries
        st.subheader("🆚 Comparison with Other Countries")
        
        # Calculate average ClubCoef per country for top 5 clubs
        country_comparison = []
        for country_code in countries_with_clubs:
            country_top5 = club_results_df[club_results_df['country_code'] == country_code].head(5)
            if len(country_top5) > 0:
                avg_top5 = country_top5['point_avg'].mean()
                country_comparison.append({
                    'Country': COUNTRY_NAMES.get(country_code, country_code),
                    'Flag': FLAG_EMOJI.get(country_code, ''),
                    'Avg Top 5 ClubCoef': avg_top5,
                    'Total Clubs': len(club_results_df[club_results_df['country_code'] == country_code])
                })
        
        comparison_df = pd.DataFrame(country_comparison).sort_values('Avg Top 5 ClubCoef', ascending=False)
        
        # Highlight selected country
        comparison_df['Highlight'] = comparison_df['Country'] == country_name
        
        fig = px.bar(
            comparison_df,
            y='Country',
            x='Avg Top 5 ClubCoef',
            orientation='h',
            title='Average ClubCoef of Top 5 Clubs by Country',
            labels={'Avg Top 5 ClubCoef': 'Average ClubCoef (Top 5 Clubs)'},
            color='Highlight',
            color_discrete_map={True: '#ff4b4b', False: '#1f77b4'},
            hover_data=['Total Clubs']
        )
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional stats
        with st.expander("📈 Detailed Country Statistics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### {country_flag} {country_name} - Key Metrics")
                st.markdown(f"""
                - **Total Clubs**: {len(country_clubs)}
                - **Clubs in Premier League**: {len(country_clubs[country_clubs['overall_position'] <= 20])}
                - **Clubs in Championship**: {len(country_clubs[(country_clubs['overall_position'] > 20) & (country_clubs['overall_position'] <= 44)])}
                - **Clubs in League One**: {len(country_clubs[(country_clubs['overall_position'] > 44) & (country_clubs['overall_position'] <= 68)])}
                - **Clubs in League Two**: {len(country_clubs[(country_clubs['overall_position'] > 68) & (country_clubs['overall_position'] <= 92)])}
                - **Best Club**: {country_clubs.iloc[0]['team']} (#{country_clubs.iloc[0]['overall_position']} overall)
                - **Highest ClubCoef**: {country_clubs.iloc[0]['point_avg']:.4f}
                - **Average ClubCoef**: {country_clubs['point_avg'].mean():.4f}
                """)
            
            with col2:
                st.markdown(f"### Nation Performance")
                
                # Get nation data
                nation_data = league_df[league_df['country_code'] == selected_country].iloc[0]
                
                st.markdown(f"""
                - **Nation Rank**: #{nation_rank} of {len(league_df)}
                - **Nation Coefficient**: {nation_coef:.4f}
                - **UEFA Coefficient**: {nation_data['total']:.4f}
                - **AFC Coefficient**: {nation_data['total2']:.4f}
                - **FIFA Ranking**: {nation_data['total3']:.4f}
                
                **Breakdown:**
                - UEFA contribution: {nation_data['total'] * 0.3:.4f} (30%)
                - AFC contribution: {nation_data['total2'] * 0.1:.4f} (10%)
                - FIFA contribution: {nation_data['total3'] * 0.6:.4f} (60%)
                """)

    
    # Info section
    st.markdown("---")
    st.header("ℹ️ About the Ranking System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📐 Nation Coefficient Calculation
        
        **Components:**
        - **UEFA Coefficient (total)**: Weighted average of last 5 UEFA seasons
          - Weights: 0.6 → 0.7 → 0.8 → 0.9 → 1.0 (oldest to newest)
        - **AFC Coefficient (total2)**: Weighted average of last 5 AFC seasons
          - Same weighting system
        - **FIFA Ranking (total3)**: Weighted average of last 5 FIFA rankings
          - Same weighting system
        
        **Final Formula:**
        ```
        Nation Coefficient = (UEFA×0.3 + AFC×0.1 + FIFA×0.6) / 100
        ```
        """)
    
    with col2:
        # Sort flags alphabetically by country name for display
        sorted_country_codes = sorted(COUNTRY_NAMES.keys(), key=lambda x: COUNTRY_NAMES[x])
        sorted_flags_string = " ".join([FLAG_EMOJI[code] for code in sorted_country_codes])
        
        st.markdown(f"""
        ### ⚽ ClubCoef Calculation
        
        **For each club season:**
        - League only: `(league_points / league_games) × league_tier^-0.95`
        - With group phase: Average of league and group calculations
        - Group multiplier: 1.0 (championship) or 0.913 (relegation)
        
        **Final ClubCoef:**
        ```
        ClubCoef = Average(top 5 seasons) × Nation Coefficient
        ```
        
        **Countries Included:**<br>
        {sorted_flags_string}<br>
        *15 Ex-Soviet Republics*
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p><strong>Ex-Soviet Football Ranking System</strong></p>
            <p>Data sources: UEFA, AFC, FIFA • Last updated: 2024/25 Season</p>
            <p>Made with ❤️ using Streamlit and Python</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Debug section (optional)
    with st.expander("🔍 Debug Information"):
        st.subheader("Sample League Data")
        st.dataframe(league_df.head())
        
        st.subheader("Sample Club Data")
        st.dataframe(club_df.head(10))
        
        st.subheader("Sample Club Results")
        st.dataframe(club_results_df.head(10))

except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.info("Please make sure LeagueRanking.csv and ClubCoef.csv are in the same directory as this script.")
    import traceback
    st.code(traceback.format_exc())
