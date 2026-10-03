# YouTube Clickbait Analyzer

An end-to-end machine learning project that analyzes YouTube videos from their titles and viewer comments, then produces an experimental clickbait score.

The project combines a locally trained title classifier with Turkish sentiment analysis for comments. It also stores analyzed videos in PostgreSQL so recent results can be reused instead of sending the same video to external APIs every time.

## Live Demo

The frontend is available here:

[Check Live Demo Here](https://yt-analyzer-eosin.vercel.app/)

## Why I Built This Project

This project was built to practice designing and connecting a complete machine learning product: collecting external data, cleaning text, running models, combining results, storing data, exposing an API, building a frontend, and deploying the system with Docker / while seperating frontend and backend code.

The most valuable part of the project is the end-to-end workflow and the engineering decisions around it. The predictions are intentionally presented as experimental signals, while the architecture is designed to be extended with better datasets, model evaluation, and more reliable scoring in the future.

## What the project does

1. Accepts a YouTube video URL.
2. Fetches video details and public comments through the YouTube Data API.
3. Cleans comments and removes empty or unusable text.
4. Analyzes the title with a local Logistic Regression model.
5. Analyzes comment sentiment with a Turkish Hugging Face model (savasy/bert-base-turkish-sentiment-cased).
6. Combines the title and comment scores into one experimental score between 0 and 100.
7. Saves the result and comments in PostgreSQL.
8. Returns cached results for recently analyzed videos.
9. Shows weekly rankings for analyzed videos.

The score is designed as a practical project signal, not as a definitive judgment about whether a video is clickbait. The main goal of the project is to demonstrate a complete data, machine learning, API, database, frontend, and deployment workflow.

## Main Features

- FastAPI backend with interactive Swagger documentation
- YouTube Data API integration
- Turkish comment sentiment analysis through the Hugging Face Inference API
- Local title classification model using scikit-learn
- PostgreSQL database with asynchronous SQLAlchemy
- Alembic database migrations
- Ten-day result caching
- Weekly analyzed-video rankings
- Request rate limiting with SlowAPI
- CORS configuration for local and deployed frontends
- Docker and Docker Compose setup
- Vercel-hosted static frontend
- Render-compatible Docker backend

## How Scoring Works

The title model returns a probability-like score between 0 and 100 based on:

- Title text using TF-IDF features
- Exclamation mark count
- Uppercase letter ratio

The comment model calculates the percentage of analyzed comments classified as negative by the Turkish sentiment model. This is used as a comment-based signal and should not be interpreted as a direct clickbait measurement.

The final score is calculated using an equal-weight combination:

```text
final score = (title score × 0.5) + (comment score × 0.5)
```

The current score categories are:

| Score | Classification |
| --- | --- |
| 0–29.99 | Relevant |
| 30–49.99 | Neutral |
| 50–100 | Clickbait |

The model and thresholds are intentionally treated as an experimental baseline. The project prioritizes a complete and understandable product flow over claiming benchmark-level prediction accuracy.

## Tech Stack

### Backend

- Python 3.11
- FastAPI
- Pydantic Settings
- SQLAlchemy async
- asyncpg
- Alembic
- httpx
- SlowAPI

### Machine Learning

- scikit-learn
- pandas
- joblib
- TF-IDF vectorization
- Logistic Regression
- Hugging Face Inference API
- Turkish BERT sentiment model

### Frontend

- HTML
- CSS
- Vanilla JavaScript
- Font Awesome

### Infrastructure

- PostgreSQL
- Docker
- Docker Compose
- Vercel for the frontend
- Render-compatible Docker backend

## Project Structure

```text
.
├── backend
│   ├── alembic
│   │   └── versions
│   ├── app
│   │   ├── apiv1
│   │   │   ├── api.py
│   │   │   └── request.py
│   │   ├── core
│   │   │   └── config.py
│   │   ├── crud
│   │   ├── db
│   │   ├── render
│   │   ├── services
│   │   │   ├── local_model
│   │   │   ├── model.py
│   │   │   └── youtube.py
│   │   └── utils
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── tests
├── frontend
│   ├── index.html
│   ├── rankings.html
│   ├── js
│   └── style
├── train
│   └── v1
│       ├── data.csv
│       └── train.py
├── docker-compose.yml
└── README.md
```

## Environment Variables

Create a local file at `backend/.env` based on `backend/.env.example`:

```env
YOUTUBE_API_KEY=your_youtube_api_key
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=youtube_analyzer
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
HF_TOKEN=your_huggingface_token
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

For a deployed backend, set the environment variables in the hosting provider's dashboard. The production `ALLOWED_ORIGINS` value should contain the exact frontend origin, without a trailing slash:

```env
ALLOWED_ORIGINS=https://yt-analyzer-eosin.vercel.app
```

## Run with Docker

From the project root:

```bash
docker compose up --build
```

The Docker setup:

1. Starts PostgreSQL.
2. Waits until PostgreSQL is healthy.
3. Runs `alembic upgrade head` automatically.
4. Starts the FastAPI server.

The backend will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

Useful commands:

```bash
docker compose logs -f backend
docker compose exec backend alembic current
docker compose down
```

`docker compose down` keeps the PostgreSQL volume. To remove the local database data as well, use `docker compose down -v` only when deleting the data is intentional.

## Run the Frontend Locally

Serve the `frontend` directory with a static server such as VS Code Live Server. The frontend currently sends requests to the backend URL configured in:

```text
frontend/js/main.js
frontend/js/fetch.js
```

For local development, use:

```javascript
const BACKEND = "http://localhost:8000";
```

For the deployed frontend, replace it with the public backend URL.

## API Endpoints

### Health Check

```http
GET /health
```

or checking database:

```http
GET /health/db
```

### Analyze a Video

```http
POST /analyze
Content-Type: application/json
```

Request body:

```json
{
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

The response includes the video information, retrieved comment count, analysis source, overall classification, and final score.

### Weekly Rankings

```http
GET /rankings
```

Returns recently analyzed videos stored in the database, ordered by their clickbait score.

## Train the Title Model

The training data is located at:

```text
train/v1/data.csv
```

The dataset contains manually labeled title examples and simple title-level features.

To retrain the model:

```bash
cd train/v1
python train.py
```

The generated model should be placed at:

```text
backend/app/services/local_model/v1/model_v1.joblib
```

The backend loads this model during application startup with FastAPI Lifespan.

## Caching and Database Behavior

Analyzed videos are stored in PostgreSQL. If an analyzed video is requested again within ten days, the backend returns the stored result instead of running the complete analysis again.

The database schema is managed with Alembic. New schema changes should be represented as migration files and applied with:

```bash
cd backend
alembic upgrade head
```

## Testing

The project currently includes basic API tests for the health endpoint and invalid URL validation:

```bash
cd backend
pytest
```

## Limitations and Future Improvements

- The title dataset is relatively small and not perfectly balanced. Updates will come soon.
- The comment model measures sentiment, not clickbait directly. Project or results can not be used for serious decisions.
