# FPL Assistant

A web-based assistant for Fantasy Premier League (FPL) managers. It uses AI trained on past FPL data to deliver weekly personalized transfer recommendations, captain picks, and team optimization advice.

## Features

- Weekly transfer recommendations based on AI predictions
- Captain picks ranked by expected points using machine learning
- Team optimization suggestions with strength/weakness analysis
- Multiple subscription tiers with increasingly advanced AI models:
  - Basic: Simple prediction model with limited recommendations
  - Premium: More sophisticated model with improved accuracy
  - Elite: Advanced model with comprehensive analysis

## Project Structure

```
fpl_assistant/
├── app/
│   ├── data/
│   │   └── training/    # ML training datasets
│   ├── data_processing/ # Data preparation for ML training
│   ├── models/          # AI prediction models
│   │   └── trained/     # Trained model storage
│   ├── routers/         # API endpoints
│   ├── schemas/         # Pydantic data models
│   ├── services/        # Business logic
│   ├── training/        # ML model training scripts
│   └── utils/           # Helper functions
├── main.py              # Application entry point
├── train_ml_models.py   # Model training script
└── requirements.txt     # Project dependencies
```

## Setup and Installation

### Prerequisites

- Python 3.12+ (recommended)
- pip
- Node.js 14+ (for frontend)
- A Telegram bot token (for Telegram integration)

### Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements_python312.txt
   ```
   
### Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# API Configuration
DEBUG=True
API_V1_PREFIX=/api/v1

# FPL API Configuration
FPL_API_TIMEOUT=30.0

# Model Configuration
MODEL_PATH=models/fpl_models

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# FastAPI Backend URL
FPL_ASSISTANT_API_URL=http://localhost:8000
```

### Training ML Models

Before running the application, you need to train the machine learning models:

1. Prepare training data and train models (this will fetch data from the FPL API):
   ```
   python train_ml_models.py --prepare-data
   ```

2. You can specify which model types to train:
   ```
   python train_ml_models.py --model-types basic,premium
   ```

3. For faster training with less data:
   ```
   python train_ml_models.py --prepare-data --num-players 100
   ```

## Running the Application

### Backend API

Start the FastAPI backend server:
```
python -m app.main
```

Or use the included batch file:
```
start_server.bat
```

The API will be available at http://localhost:8000.

### Telegram Bot

After starting the backend server, run the Telegram bot:
```
python telegram_bot.py
```

### Frontend (optional)

Start the React frontend:
```
cd frontend
npm start
```

## API Documentation

Once the server is running, you can access the auto-generated API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Team Data
- `GET /team/{team_id}` - Get player data for an FPL team

### Recommendations
- `POST /recommendations/transfers` - Get transfer recommendations for a team

### Captain Picks
- `POST /captain/best` - Get captain recommendations for a team

### Team Analysis
- `POST /team-score/rate` - Get team rating and analysis

## Testing

Several test scripts are provided to verify different components of the system:

### Testing Individual Components

1. **Check API accessibility**
   ```
   python check_api.py
   ```

2. **Test FPL API integration**
   ```
   python test_fpl_api_only.py
   ```

3. **Test Telegram bot functionality**
   ```
   python test_telegram_bot.py
   ```

### Full System Testing

Run the complete system test script:
```
complete_system_test.bat
```

This will test all components in sequence to verify that everything is working together correctly.

## Using the Telegram Bot

1. Start a chat with your Telegram bot
2. Send the `/analyze` command
3. When prompted, send your FPL Team ID
4. The bot will respond with:
   - Team rating
   - Transfer recommendations
   - Captain pick suggestions
   - Areas for improvement

## Troubleshooting

- **API server doesn't start:** Check the Python version (requires 3.12+) and verify that all dependencies are installed.
- **Telegram bot doesn't connect:** Verify that the `TELEGRAM_BOT_TOKEN` is correctly set in the `.env` file.
- **Web frontend issues:** Ensure you're using react-router-dom v5 instead of v6 to maintain compatibility with the current setup.
- **FPL API not working:** The FPL API sometimes changes its structure - check the transformation logic in `fpl_data.py`.

### Team Evaluation

- `GET /api/v1/team-score/?team_id={id}&gameweek={gw}&subscription_tier={tier}` - Get team evaluation for an FPL team
- `POST /api/v1/team-score/custom` - Get team evaluation for a custom team

## Subscription Tiers

The application supports three subscription tiers with increasing capabilities:

1. **Basic**
   - Simple prediction model
   - 3 transfer recommendations
   - 2 captain picks

2. **Premium**
   - More accurate prediction model
   - 5 transfer recommendations
   - 3 captain picks
   - Enhanced reasoning

3. **Elite**
   - Advanced prediction model with highest accuracy
   - 10 transfer recommendations
   - 5 captain picks
   - Comprehensive analysis
   - Access to more detailed statistics
