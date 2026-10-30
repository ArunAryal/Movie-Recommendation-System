# 🎬 Movie Recommendation System

[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![pandas](https://img.shields.io/badge/pandas-Data-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-2EA44F?logo=streamlit&logoColor=white)](https://top-movie-recommendation-system.streamlit.app/)

A content-based movie recommender built with **Python**, **scikit-learn** and **Streamlit**. Pick a movie you like and the app suggests the five most similar titles, complete with posters fetched from the [TMDB API](https://www.themoviedb.org/).

<!-- Add a screenshot once the app is running: ![App screenshot](docs/screenshot.png) -->

**Live demo:** <https://top-movie-recommendation-system.streamlit.app/>

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Regenerating the Data](#regenerating-the-data)
- [Limitations](#limitations)

---

## Features

- Recommends the **5 most similar movies** for any of ~4,800 titles.
- Shows **movie posters** from TMDB (cached for 24 hours, with a local fallback image).
- **Fast**: about 0.2 s to load the model and a few milliseconds per recommendation.
- **Lightweight**: no multi-hundred-MB similarity matrix; similarity is computed on demand from a small sparse matrix.
- **Degrades gracefully**: if the API key is missing or TMDB is unreachable, recommendations still work.

## How It Works

The recommender is **content-based**: it compares what movies are *about*, not what users rated.

1. **Data**: the [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) (movies + credits), merged on the TMDB movie id.
2. **Feature engineering** (done in the notebook): for each movie, build a single text field called `tags` from:
   - overview (plot summary)
   - genres
   - keywords
   - top 3 cast members
   - director

   Multi-word names are collapsed (`Sam Worthington` → `SamWorthington`) so two different people sharing a first name aren't confused.
3. **Text cleaning**: lowercase, strip punctuation, remove stop-words and apply **Porter stemming** (`loving`, `loved` → `love`).
4. **Vectorization**: bag-of-words using `CountVectorizer` (top 5,000 terms, English stop-words removed).
5. **Similarity**: **cosine similarity** between the selected movie's vector and every other movie:

   ```
   similarity(A, B) = (A · B) / (‖A‖ · ‖B‖)
   ```

6. **Recommendation**: take the 5 highest scores, excluding the selected movie itself, then fetch each poster from TMDB.

## Tech Stack

| Area | Tools |
|---|---|
| App | [Streamlit](https://streamlit.io/) |
| ML | scikit-learn, NLTK (Porter stemmer, notebook only) |
| Data | pandas |
| Posters | [TMDB API](https://developer.themoviedb.org/) via `requests` |
| Packaging | [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`) |
| Python | 3.13+ |

## Project Structure

```
.
├── app.py                          # Streamlit application
├── movies_processed.csv            # Preprocessed data: movie_id, title, tags
├── movie_recommender_system.ipynb  # Data cleaning, feature engineering, experiments
├── pyproject.toml                  # Project metadata and dependencies
├── uv.lock                         # Locked dependency versions
├── .python-version                 # Python version used locally
├── .streamlit/
│   ├── config.toml                 # Streamlit settings
│   └── secrets.toml                # 🔒 local secrets (git-ignored)
├── .env                            # 🔒 optional local secrets (git-ignored)
└── dataset/                        # 🔒 raw TMDB CSVs (git-ignored; only needed for the notebook)
    ├── tmdb_5000_movies.csv
    └── tmdb_5000_credits.csv
```

## Getting Started

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** package manager
- A free **TMDB API key** (see [Configuration](#configuration))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ArunAryal/Movie-Recommendation-System
cd Movie-Recommendation-System

# 2. Install dependencies into a local virtual environment (.venv)
uv sync
```

### Run the app

```bash
uv run streamlit run app.py
```

Open the URL printed in the terminal (usually <http://localhost:8501>), choose a movie, and click **Recommend**.

## Configuration

The app needs one setting: `TMDB_API_KEY`.

1. Create a free account at [themoviedb.org](https://www.themoviedb.org/) and open **Settings → API** to get your credentials.
2. Provide the key in **one** of these ways:

   **Option A: `.streamlit/secrets.toml`** (recommended, also what Streamlit Cloud uses)
   ```toml
   TMDB_API_KEY = "your-key-here"
   ```

   **Option B: `.env` file** in the project root
   ```dotenv
   TMDB_API_KEY=your-key-here
   ```

The app checks Streamlit secrets first, then falls back to environment variables / `.env`.

| Variable | Required | Description |
|---|---|---|
| `TMDB_API_KEY` | Recommended | TMDB credential. Without it the app still runs but shows placeholder images instead of posters. |

> **Which credential?** TMDB offers an *API Read Access Token* (a long string starting with `eyJ`) and a shorter *v3 API key*. Both work. The token is preferred because it is sent in a request header rather than in the URL.

## Regenerating the Data

You only need this if you want to change how features are built.

1. Download the [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) and place the two CSVs in `dataset/`.
2. Open `movie_recommender_system.ipynb` (for example in VS Code or Jupyter, using the `.venv` kernel) and run all cells.
3. The final cell writes `movies_processed.csv`. Commit the new file.

> **Important:** merge the two CSVs on the movie **id** (not on `title`), then call `drop_duplicates("movie_id").reset_index(drop=True)`. Merging on title duplicates movies that share a name and leaves gaps in the index, which breaks the lookup in the app.

## Limitations

- Recommendations are based purely on text metadata. There are no user ratings or viewing history, so results are the same for every user.
- Only the ~4,800 movies in the TMDB 5000 dataset are available, and the metadata is in English.
- Bag-of-words ignores word order and meaning (for example, it can't tell that "spaceship" and "starship" are related).