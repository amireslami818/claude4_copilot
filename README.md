# Football Bot - Multi-Step Data Processing Pipeline

A sophisticated Football Bot system that fetches live football match data from TheSports API and processes it through a multi-step pipeline to generate structured summaries and organized JSON outputs.

## 🚀 Features

- **Live Data Fetching**: Retrieves real-time football match data from TheSports API
- **Multi-Step Pipeline**: Processes data through 3 distinct steps for optimal organization
- **Consistent Timestamps**: All outputs include Eastern Time timestamps in mm/dd/yyyy format
- **Data History**: Maintains historical records of all processing runs
- **Comprehensive Analytics**: Categorizes matches by status, competition, weather, and betting odds

## 📁 Project Structure

```
Football_bot/
├── step1.py                 # Data Fetcher - Fetches live match data from API
├── step1.json              # Raw API data output (39.5 MB)
├── step2/
│   ├── step2.py            # Data Processor - Extracts and summarizes match data  
│   └── step2.json          # Processed summaries (6.5 MB)
├── step3/
│   ├── step3.py            # JSON Summary Generator - Structured categorization
│   └── step3.json          # Final structured summaries (13.3 MB)
├── test_orchestrator.py    # Pipeline orchestrator for testing
├── venv/                   # Python virtual environment
└── .gitignore              # Git ignore rules
```

## 🔄 Pipeline Overview

### Step 1: Data Fetcher (`step1.py`)
- Fetches live football match data from TheSports API
- Saves raw data to `step1.json` with NY Eastern timestamp
- Processes ~111 matches per run

### Step 2: Data Processor (`step2/step2.py`) 
- Extracts and merges raw match data into structured summaries
- Filters and processes match events, odds, and environment data
- Outputs processed data to `step2/step2.json`
- Reduces data size by ~84% while maintaining key information

### Step 3: JSON Summary Generator (`step3/step3.py`)
- Generates comprehensive match summaries with detailed categorization
- Categorizes matches by status (live/upcoming/finished), competition, and weather
- Extracts and summarizes betting odds information
- Saves final structured data to `step3/step3.json`

## 🛠️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alextrx818/Copilot_Claude4.git
   cd Football_bot
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install aiohttp
   ```

## 🚀 Usage

### Run Individual Steps

```bash
# Step 1: Fetch live data
python step1.py

# Step 2: Process data
python step2/step2.py

# Step 3: Generate summaries
python step3/step3.py
```

### Run Complete Pipeline

```bash
python test_orchestrator.py
```

## 📊 Data Flow

```
TheSports API → step1.json (39.5 MB) → step2.json (6.5 MB) → step3.json (13.3 MB)
     ↓              ↓                      ↓                      ↓
Raw Match Data → Processed Summaries → Categorized Analytics → Structured Output
```

## 🏆 Key Statistics

- **Matches Processed**: ~111 per run
- **Data Reduction**: 84% size reduction from raw to processed
- **Categorizations**: Status, Competition, Weather, Betting Odds
- **Timestamp Format**: MM/DD/YYYY HH:MM:SS AM/PM EDT
- **History Tracking**: All runs stored with timestamps

## 🔧 Configuration

The system uses hardcoded API credentials for TheSports API. Update the credentials in `step1.py` if needed.

## 📈 Output Examples

### Match Categorization
- **By Status**: Live, Upcoming, Finished, Other
- **By Competition**: Premier League, La Liga, Serie A, etc.
- **By Weather**: Sunny, Cloudy, Rain, Snow, etc.
- **Betting Odds**: Full-time result, Over/Under, Spread, Both teams to score

### Sample Statistics
```json
{
  "total": 111,
  "with_odds": 64,
  "with_events": 0,
  "by_weather": {
    "Sunny": 20,
    "Cloudy": 13,
    "Rain": 6,
    "Unknown": 33
  }
}
```

## 🕒 Timestamps

All outputs include consistent Eastern Time formatting:
- Format: `MM/DD/YYYY HH:MM:SS AM/PM EDT`
- Example: `05/28/2025 02:02:12 PM EDT`

## 🤖 Development

Created with GitHub Copilot assistance for automated football data processing and analysis.

## 📝 License

This project is for educational and development purposes.
