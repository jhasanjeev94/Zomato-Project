# 🍽️ Zomato AI Restaurant Recommender

AI-powered restaurant recommendation system that uses **Groq LLM** (LLaMA 3.3 70B) to deliver personalized, explainable dining suggestions based on the Zomato dataset.

## Features

- 🔍 Filter by location, budget, cuisine, and rating
- 🤖 AI-generated explanations for each recommendation
- ⚡ Ultra-fast inference via Groq API
- 🎨 Modern dark-theme UI with glassmorphism design

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + CSS + Vanilla JS |
| Backend | Python 3.11+ / FastAPI |
| Data | Pandas + HuggingFace Datasets |
| LLM | Groq API (LLaMA 3.3 70B) |

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd "Zomato Project"
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your Groq API key
```

### 5. Run the server

```bash
uvicorn backend.main:app --reload
```

### 6. Open the frontend

Open `frontend/index.html` in your browser, or visit `http://localhost:8000/docs` for the Swagger API docs.

## Project Structure

```
Zomato Project/
├── backend/
│   ├── models/           # Pydantic schemas
│   ├── services/         # Data loader, filter, LLM client
│   ├── utils/            # Preprocessing utilities
│   ├── main.py           # FastAPI entrypoint
│   ├── config.py         # Environment config
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # API key template
├── frontend/
│   ├── index.html        # Main UI
│   ├── css/styles.css    # Styling
│   └── js/app.js         # Frontend logic
├── docs/                 # Architecture, plans, edge cases
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/locations` | List available locations |
| `GET` | `/api/cuisines` | List available cuisines |
| `POST` | `/api/recommend` | Get AI recommendations |
| `GET` | `/api/stats` | Dataset statistics |

## License

MIT
