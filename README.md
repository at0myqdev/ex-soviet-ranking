# Ex Soviet Ranking System

A comprehensive ranking system for football clubs and nations from former Soviet republics, built with Streamlit, Pandas, and Plotly.

🔗 **Live Application**: [https://ex-soviet-ranking.streamlit.app/](https://ex-soviet-ranking.streamlit.app/)

## Overview

This project creates a unified ranking system for ex-Soviet republics based on their football performance across multiple confederations (UEFA, AFC) and FIFA rankings. The system calculates nation coefficients by combining:
- UEFA coefficients (for European nations)
- AFC coefficients (for Asian nations)
- FIFA rankings

## Features

- **Nation Rankings**: Comprehensive ranking of ex-Soviet nations based on weighted coefficients
- **Club Coefficients**: Individual club performance tracking over multiple seasons
- **Interactive Visualizations**: Dynamic charts showing ranking trends over time
- **Multi-Confederation Support**: Handles both UEFA and AFC competitions
- **Historical Data**: Tracks performance from 2018 to current day

## Data Sources

The system uses two main CSV files:

### 1. LeagueRanking.csv
Contains nation-level data:
- `country`: Nation name
- `country_code`: 3-letter country code
- `UEFA_YYYY_YY`: UEFA coefficients by season
- `AFC_YYYY`: AFC coefficients by season
- `FIFA_YYYY_MM_DD`: FIFA rankings by date (each year around September -> to get the points after big and important tournaments)

### 2. ClubCoef.csv
Contains club-level data:
- `country_code`: Nation code
- `team`: Club name
- `team_code`: Club abbreviation
- `season`: Season (e.g., "2023/24")
- `year`: Year (e.g., 2023)
- `league_tier`: League level (1, 2, 3)
- `league_games`: Number of league games
- `league_points`: League points earned
- `group`: Group phase participation (x if yes, empty if no)
- `group_games`: Group phase games
- `group_points`: Group phase points

## Calculation Methodology  
  
### Club Coefficient Formula  
  
For each club and season:  
  

Club Coefficient = (League Part + Group Part) / 2

  
Where:  
- **League Part**: `(League Points / League Games) × (League Tier ^ -0.95)`  
- **Group Part**: `(Group Points / Group Games) × (League Tier ^ -0.95) × Group Multiplier`  
  
**League Tier Weights** (calculated as `tier ^ -0.95`):  
- League Tier 1: 1^-0.95 = 1.0  
- League Tier 2: 2^-0.95 ≈ 0.518  
- League Tier 3: 3^-0.95 ≈ 0.339  
  
**Group Multiplier**:  
- Group = 1 (League splits into championship group): 1.0  
- Group = 2 (League splits into relegation group): 0.913  
  
**Final Club Coefficient**: Average of the last 5 seasons (years)  
  
**Note**: If the league doesn't split into groups, only the League Part is calculated (Group Part = 0).  
  
### Nation Coefficient Formula  
  

Nation Coefficient = (UEFA Total × 0.3) + (AFC Total × 0.1) + (FIFA Total × 0.6)

**Note**: The weights here are purely chosen by vibes as this looks the fairest or else Uzbekistan would have 6+ clubs in the top league
  
**Component Calculations:**  
- **UEFA Total**: Sum of last 5 UEFA season coefficients  
- **AFC Total**: Sum of last 5 AFC year coefficients  
- **FIFA Total**: Sum of last 5 FIFA rankings  
  
**Note**: If a nation doesn't participate in a confederation (UEFA or AFC), that component is 0.

### Handling Missing Data

- **Empty cells in ClubCoef.csv**: Should be filled with `0` to ensure proper calculation
- **Missing seasons**: If a club doesn't play in a season, use `0` for all values - this counts as a 0-point average in the 5-year calculation
- **Non-participating confederations**: Nations only in UEFA have AFC = 0, and vice versa

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ex-soviet-ranking
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure data files are in place:
```
project/
├── app.py
├── LeagueRanking.csv
├── ClubCoef.csv
└── requirements.txt
```

## Usage

### Running Locally

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

**Note**: This system is designed for flexibility. As new seasons are added, the calculations automatically adjust to use the most recent 5-year period, ensuring rankings stay current and relevant.
