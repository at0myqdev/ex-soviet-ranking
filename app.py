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
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
@st.cache_data
def load_and_calculate_data():
    # Load LeagueRanking.csv
    league_df = pd.read_csv('LeagueRanking.csv', sep=';', decimal=',')
    
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

@st.cache_data
def calculate_club_coefficients(league_df):
    # Load ClubCoef.csv
    club_df = pd.read_csv('ClubCoef.csv', sep=';', decimal=',')
    
    # Convert numeric columns
    numeric_cols = ['year', 'league_tier', 'league_games', 'league_points', 'group', 'group_games', 'group_points']
    for col in numeric_cols:
        club_df[col] = pd.to_numeric(club_df[col], errors='coerce')
    
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
    
    # Calculate PointAVG for each club
    club_results = []
    
    for (country_code, team_code), group in club_df.groupby(['country_code', 'team_code']):
        # Sort by year descending and take top 5
        top_5 = group.nlargest(5, 'year')
        
        if len(top_5) > 0:
            # Calculate average of row coefficients
            avg_coefficient = top_5['row_coefficient'].mean()
            
            # Get nation coefficient (total4) from league_df
            nation_coef = league_df[league_df['country_code'] == country_code]['total4'].values
            nation_coef = nation_coef[0] if len(nation_coef) > 0 else 0
            
            # Calculate PointAVG
            point_avg = avg_coefficient * nation_coef
            
            club_results.append({
                'country_code': country_code,
                'team': group['team'].iloc[0],
                'team_code': team_code,
                'point_avg': point_avg,
                'avg_coefficient': avg_coefficient,
                'nation_coef': nation_coef
            })
    
    club_results_df = pd.DataFrame(club_results)
    club_results_df = club_results_df.sort_values('point_avg', ascending=False).reset_index(drop=True)
    
    # Add overall position to all clubs
    club_results_df['overall_position'] = range(1, len(club_results_df) + 1)
    
    # Add country names and flags
    club_results_df['country_name'] = club_results_df['country_code'].map(COUNTRY_NAMES)
    club_results_df['flag'] = club_results_df['country_code'].map(FLAG_EMOJI)
    
    return club_results_df, club_df

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
    
    # Display metrics for top 3 with flags
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### {league_df.iloc[0]['flag']} 🥇")
        st.metric(
            "1st Place", 
            league_df.iloc[0]['country_name'], 
            f"{league_df.iloc[0]['total4']:.4f} pts"
        )
    
    with col2:
        st.markdown(f"### {league_df.iloc[1]['flag']} 🥈")
        st.metric(
            "2nd Place", 
            league_df.iloc[1]['country_name'], 
            f"{league_df.iloc[1]['total4']:.4f} pts"
        )
    
    with col3:
        st.markdown(f"### {league_df.iloc[2]['flag']} 🥉")
        st.metric(
            "3rd Place", 
            league_df.iloc[2]['country_name'], 
            f"{league_df.iloc[2]['total4']:.4f} pts"
        )
    
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
    
    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True,
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
    st.header("🏅 Top Club Rankings (by PointAVG)")
    
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
            st.metric("PointAVG", f"{club['point_avg']:.4f}")
            st.caption(club['country_name'])
    
    st.markdown("---")
    
    # Full club table
    st.subheader("📋 Top 20 Clubs")
    
    display_clubs = top_clubs[['flag', 'team', 'country_name', 'point_avg']].copy()
    display_clubs.columns = ['🏴', 'Club', 'Country', 'PointAVG']
    display_clubs.insert(0, 'Rank', range(1, len(display_clubs) + 1))
    display_clubs['PointAVG'] = display_clubs['PointAVG'].apply(lambda x: f"{x:.4f}")
    
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
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Nation Coefficients", "Coefficient Breakdown", "Historical UEFA", "Top Clubs", "🏆 League System", "🌍 Country Rankings"])
    
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
        # Bar chart of top clubs with flags
        top_15 = club_results_df.head(15).copy()
        
        fig = px.bar(
            top_15,
            x='team',
            y='point_avg',
            title='Top 15 Clubs by PointAVG',
            labels={'point_avg': 'PointAVG', 'team': 'Club'},
            color='point_avg',
            color_continuous_scale='Reds',
            text='flag',
            hover_data=['country_name']
        )
        fig.update_traces(textposition='outside', textfont_size=18)
        fig.update_layout(showlegend=False, height=500)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        # League System Tab - English-style 4-tier structure
        st.markdown("## 🏆 Theoretical Ex-Soviet League System")
        st.markdown("*English football pyramid style - 4 divisions based on club coefficients*")
        
        # Info box
        st.info("""
        **League Structure:**
        - 🥇 **Premier League** (Tier 1): Top 20 clubs
        - 🥈 **Championship** (Tier 2): Clubs 21-44 (24 clubs)
        - 🥉 **League One** (Tier 3): Clubs 45-68 (24 clubs)
        - 📋 **League Two** (Tier 4): Clubs 69-92 (24 clubs)
        
        **Promotion/Relegation (All Leagues):**
        - Top 2: Direct promotion 🔼
        - 3rd-6th: Playoffs 🎲
        - Bottom 3: Relegation 🔻
        
        *Clubs are ranked by their PointAVG coefficient*
        """)
        
        st.markdown("---")
        
        # League selection
        league_option = st.selectbox(
            "Select League to View:",
            ["🥇 Premier League (Tier 1)", 
             "🥈 Championship (Tier 2)", 
             "🥉 League One (Tier 3)", 
             "📋 League Two (Tier 4)",
             "📊 All Leagues Overview"]
        )
        
        # Prepare league data
        all_clubs = club_results_df.copy()
        
        # Define league tiers: 20 + 24 + 24 + 24
        premier_league = all_clubs.iloc[0:20].copy()
        championship = all_clubs.iloc[20:44].copy()
        league_one = all_clubs.iloc[44:68].copy()
        league_two = all_clubs.iloc[68:92].copy()
        
        # Function to display a league table
        def display_league_table(league_df, league_name, tier, start_pos):
            st.subheader(f"{league_name}")
            
            # Add league position within tier
            league_df = league_df.copy()
            league_df['league_pos'] = range(1, len(league_df) + 1)
            
            # Create display dataframe
            display = league_df[['league_pos', 'flag', 'team', 'country_name', 'point_avg']].copy()
            display.columns = ['Pos', '🏴', 'Club', 'Country', 'PointAVG']
            display['PointAVG'] = display['PointAVG'].apply(lambda x: f"{x:.4f}")
            
            # Add visual indicators for promotion/relegation zones
            # All leagues: Top 2 auto promotion, 3-6 playoffs, Bottom 3 relegation
            display['Status'] = ''
            
            if tier == 1:
                # Premier League: Bottom 3 relegated, European spots
                display.loc[display.index[0], 'Status'] = '⭐ Champions'
                display.loc[display.index[-3:], 'Status'] = '🔻 Relegation'
            elif tier in [2, 3, 4]:
                # Championship, League One, League Two: Same structure
                display.loc[display.index[0:2], 'Status'] = '🔼 Auto Promotion'
                display.loc[display.index[2:6], 'Status'] = '🎲 Playoffs'
                display.loc[display.index[-3:], 'Status'] = '🔻 Relegation'
            
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                height=min(600, len(display) * 35 + 38),
                column_config={
                    "Pos": st.column_config.NumberColumn(
                    "Pos",
                    help="Position in league",
                    width="small",
                    format="%d"
                    ),
                    "Status": st.column_config.TextColumn(
                    "Status",
                    help="Promotion/Relegation zone",
                    width="medium"
                    )
                }
            )
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Clubs", len(league_df))
            with col2:
                countries = league_df['country_code'].nunique()
                st.metric("Countries Represented", countries)
            with col3:
                avg_points = league_df['point_avg'].mean()
                st.metric("Avg PointAVG", f"{avg_points:.4f}")
        
        # Display selected league
        if league_option == "🥇 Premier League (Tier 1)":
            display_league_table(premier_league, "🥇 Premier League", 1, 1)
            
        elif league_option == "🥈 Championship (Tier 2)":
            display_league_table(championship, "🥈 Championship", 2, 21)
            
        elif league_option == "🥉 League One (Tier 3)":
            display_league_table(league_one, "🥉 League One", 3, 45)
            
        elif league_option == "📋 League Two (Tier 4)":
            display_league_table(league_two, "📋 League Two", 4, 69)
            
        else:  # All Leagues Overview
            st.markdown("### 📊 Complete League System Overview")
            
            # Visual pyramid
            st.markdown("#### League Pyramid Structure")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("""
                ```
                    ⚽ PREMIER LEAGUE
                    (20 clubs)
                    ────
                    ↕
                    🏆 CHAMPIONSHIP
                    (24 clubs)
                    ────
                    ↕
                    🥉 LEAGUE ONE
                    (24 clubs)
                    ────
                    ↕
                    📋 LEAGUE TWO
                    (24 clubs)
                ```
                """)
            
            with col2:
                # Country distribution across leagues
                country_dist = []
                for tier, (name, df) in enumerate([
                    ("Premier League", premier_league),
                    ("Championship", championship),
                    ("League One", league_one),
                    ("League Two", league_two)
                ], 1):
                    for _, row in df.iterrows():
                    country_dist.append({
                        'League': name,
                        'Tier': tier,
                        'Country': row['country_name'],
                        'Club': row['team']
                    })
                
                country_dist_df = pd.DataFrame(country_dist)
                
                # Count clubs per country per league
                country_league_count = country_dist_df.groupby(['League', 'Country']).size().reset_index(name='Clubs')
                
                fig = px.bar(
                    country_league_count,
                    x='League',
                    y='Clubs',
                    color='Country',
                    title='Club Distribution by Country Across Leagues',
                    barmode='stack',
                    height=400
                )
                fig.update_layout(
                    xaxis_title='League',
                    yaxis_title='Number of Clubs'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Summary table for all leagues
            st.markdown("#### League Statistics Summary")
            
            summary_data = []
            for tier, (name, df, emoji) in enumerate([
                ("Premier League", premier_league, "🥇"),
                ("Championship", championship, "🥈"),
                ("League One", league_one, "🥉"),
                ("League Two", league_two, "📋")
            ], 1):
                summary_data.append({
                    'Tier': tier,
                    'League': f"{emoji} {name}",
                    'Clubs': len(df),
                    'Countries': df['country_code'].nunique(),
                    'Avg PointAVG': f"{df['point_avg'].mean():.4f}",
                    'Top Club': f"{df.iloc[0]['flag']} {df.iloc[0]['team']}",
                    'Top PointAVG': f"{df.iloc[0]['point_avg']:.4f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Show which countries dominate which tier
            st.markdown("#### Country Dominance by League")
            
            cols = st.columns(4)
            
            for idx, (name, df, col) in enumerate([
                ("🥇 Premier", premier_league, cols[0]),
                ("🥈 Championship", championship, cols[1]),
                ("🥉 League One", league_one, cols[2]),
                ("📋 League Two", league_two, cols[3])
            ]):
                with col:
                    st.markdown(f"**{name}**")
                    country_counts = df['country_code'].value_counts().head(3)
                    for country, count in country_counts.items():
                        flag = FLAG_EMOJI.get(country, '')
                        country_name = COUNTRY_NAMES.get(country, country)
                        st.markdown(f"{flag} {country_name}: **{count}** clubs")
        
        st.markdown("---")
        
        # Additional insights
        with st.expander("📈 League System Insights"):
            st.markdown("""
            ### How the League System Works
            
            This theoretical league system groups the top 92 clubs from ex-Soviet republics into 4 tiers,
            similar to the English football pyramid:
            
            **🥇 Premier League (Tier 1) - 20 Clubs**
            - Top 4: Champions League qualification ⭐
            - 5th-6th: Europa League qualification 🌍
            - 18th-20th: Relegation to Championship 🔻
            
            **🥈 Championship (Tier 2) - 24 Clubs**
            - 1st-2nd: Automatic promotion to Premier League 🔼
            - 3rd-6th: Playoff for final promotion spot 🎲
            - 22nd-24th: Relegation to League One 🔻
            
            **🥉 League One (Tier 3) - 24 Clubs**
            - 1st-2nd: Automatic promotion to Championship 🔼
            - 3rd-6th: Playoff for final promotion spot 🎲
            - 22nd-24th: Relegation to League Two 🔻
            
            **📋 League Two (Tier 4) - 24 Clubs**
            - 1st-2nd: Automatic promotion to League One 🔼
            - 3rd-6th: Playoff for final promotion spot 🎲
            - 22nd-24th: Relegation (theoretical) 🔻
            
            *Note: This is a theoretical structure based on current PointAVG coefficients.*
            """)
    
    with tab6:
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
        
        # Add overall position from the full ranking
        country_clubs = country_clubs.reset_index(drop=True)
        country_clubs['overall_position'] = country_clubs.index + 1
        
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
            clubs_in_top_20 = len(country_clubs[country_clubs['overall_position'] <= 20])
            st.metric("Clubs in Premier League", clubs_in_top_20)
        
        st.markdown("---")
        
        # Club rankings table
        st.subheader(f"🏆 All Clubs from {country_name}")
        
        # Prepare display dataframe
        display_country = country_clubs[['national_rank', 'team', 'point_avg', 'overall_position']].copy()
        display_country.columns = ['National Rank', 'Club', 'PointAVG', 'Overall Rank']
        
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
        display_country['PointAVG'] = display_country['PointAVG'].apply(lambda x: f"{x:.4f}")
        
        # Reorder columns
        display_country = display_country[['National Rank', 'Club', 'League', 'Overall Rank', 'PointAVG']]
        
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
                labels={'point_avg': 'PointAVG', 'team': 'Club'},
                color='point_avg',
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, height=400)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Comparison with other countries
        st.subheader("🆚 Comparison with Other Countries")
        
        # Calculate average PointAVG per country for top 5 clubs
        country_comparison = []
        for country_code in countries_with_clubs:
            country_top5 = club_results_df[club_results_df['country_code'] == country_code].head(5)
            if len(country_top5) > 0:
                avg_top5 = country_top5['point_avg'].mean()
                country_comparison.append({
                    'Country': COUNTRY_NAMES.get(country_code, country_code),
                    'Flag': FLAG_EMOJI.get(country_code, ''),
                    'Avg Top 5 PointAVG': avg_top5,
                    'Total Clubs': len(club_results_df[club_results_df['country_code'] == country_code])
                })
        
        comparison_df = pd.DataFrame(country_comparison).sort_values('Avg Top 5 PointAVG', ascending=False)
        
        # Highlight selected country
        comparison_df['Highlight'] = comparison_df['Country'] == country_name
        
        fig = px.bar(
            comparison_df,
            y='Country',
            x='Avg Top 5 PointAVG',
            orientation='h',
            title='Average PointAVG of Top 5 Clubs by Country',
            labels={'Avg Top 5 PointAVG': 'Average PointAVG (Top 5 Clubs)'},
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
                - **Highest PointAVG**: {country_clubs.iloc[0]['point_avg']:.4f}
                - **Average PointAVG**: {country_clubs['point_avg'].mean():.4f}
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
        st.markdown("""
        ### ⚽ Club PointAVG Calculation
        
        **For each club season:**
        - League only: `(league_points / league_games) × league_tier^-0.95`
        - With group phase: Average of league and group calculations
        - Group multiplier: 1.0 (championship) or 0.913 (relegation)
        
        **Final PointAVG:**
        ```
        PointAVG = Average(top 5 seasons) × Nation Coefficient
        ```
        
        **Countries Included:** 
        - 🇺🇦 🇷🇺 🇦🇿 🇺🇿 🇦🇲 🇲🇩 🇱🇻 🇰🇿 
        - 🇬🇪 🇰🇬 🇪🇪 🇱🇹 🇧🇾 🇹🇲 🇹🇯
        
        *15 Ex-Soviet Republics*
        """)
    
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
