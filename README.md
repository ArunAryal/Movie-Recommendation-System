# 🎬 Movie Recommendation System

A content-based movie recommender built with **Python**, **scikit-learn** and **Streamlit**. Pick a movie you like and the app suggests the five most similar titles, complete with posters fetched from the [TMDB API](https://www.themoviedb.org/).

<!-- Add a screenshot once the app is running: ![App screenshot](docs/screenshot.png) -->

**Live demo:** _add your `https://.streamlit.app` link here after deploying_

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Regenerating the Data](#regenerating-the-data)
- [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Limitations and Future Ideas](#limitations-and-future-ideas)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Features

- Recommends the **5 most similar movies** for any of ~4,800 titles.
- Shows **movie posters** from TMDB (cached for 24 hours, with a local fallback image).
- **Fast**: about 0.2 s to load the model and a few milliseconds per recommendation.
- **Lightweight**: no multi-hundred-MB similarity matrix; similarity is computed on demand from a small sparse matrix.
- Handles titles shared by different movies (for example, the two *Batman* films) by showing their TMDB id.
- Degrades gracefully: if the API key is missing or TMDB is unreachable, recommendations still work.

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
| App / UI | [Streamlit](https://streamlit.io/) |
| ML / NLP | scikit-learn, NLTK (Porter stemmer, notebook only) |
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
├── uv.lock                         # Locked dependency versions (commit this!)
├── .python-version                 # Python version used locally
├── .streamlit/
│   ├── config.toml                 # Streamlit settings (safe to commit)
│   └── secrets.toml                # 🔒 local secrets (git-ignored, never commit)
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
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

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

## Deploying to Streamlit Community Cloud

1. Push the project to a GitHub repository. Make sure these files are committed:
   `app.py`, `movies_processed.csv`, `pyproject.toml`, **`uv.lock`**, `.streamlit/config.toml`, `.python-version`.
2. Go to [share.streamlit.io](https://share.streamlit.io/), sign in with GitHub and click **Create app**.
3. Select your repository and branch, and set the main file path to `app.py`.
4. Open **Advanced settings**:
   - **Python version:** choose **3.13** (Community Cloud takes this from the dialog, not from `.python-version`).
   - **Secrets:** paste `TMDB_API_KEY = "your-key-here"` (TOML format, with quotes).
5. Click **Deploy**. Pushing new commits to the branch redeploys automatically.

Notes:

- `uv.lock` must be in the repository; Community Cloud uses it to detect a uv project and install exact versions.
- Free apps go to sleep after about 12 hours without visitors and wake on the next visit.
- Update secrets later from the app's **Settings → Secrets** panel.

## Security Notes

- **Never commit secrets.** `.env` and `.streamlit/secrets.toml` are listed in `.gitignore`. Verify with:
  ```bash
  git check-ignore -v .streamlit/secrets.toml
  git ls-files | grep -E 'secrets|\.env'   # should print nothing
  ```
  If a key was ever committed, regenerate it in your TMDB account.
- Error details are hidden from visitors (`showErrorDetails = "none"` in `.streamlit/config.toml`), and the app logs only the *type* of a failed TMDB request, never the request URL.
- Data is stored as CSV rather than pickle, so nothing in the repository is deserialized with `pickle.load`.
- Poster lookups are cached for 24 hours, which limits how quickly visitors can use up your TMDB quota.

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Warning banner: *"TMDB_API_KEY is not configured"* | The key isn't set. Add it to `.streamlit/secrets.toml` or `.env` (locally) or to the Secrets box (Cloud), then restart the app. |
| Every poster shows "No poster" | The key is invalid or TMDB is unreachable. Check the logs for `TMDB lookup failed` lines. |
| `FileNotFoundError: movies_processed.csv` | The CSV isn't in the repo. Commit it (it is small, about 1.6 MB). |
| Cloud build fails while installing dependencies | Check that `uv.lock` is committed and that Python 3.13 is selected in Advanced settings. |
| Secrets error on Cloud | Secrets must be valid TOML; string values need quotes: `TMDB_API_KEY = "..."`. |
| Changes to `secrets.toml` don't show up locally | Restart `streamlit run`; the file is read at startup. |

## Limitations and Future Ideas

**Current limitations**

- Recommendations are based purely on text metadata. There are no user ratings or viewing history, so results are the same for every user.
- Only the ~4,800 movies in the TMDB 5000 dataset are available, and the metadata is in English.
- Bag-of-words ignores word order and meaning (for example, it can't tell that "spaceship" and "starship" are related).

**Ideas for improvement**

- Replace `CountVectorizer` with **TF-IDF** or **sentence embeddings** for semantically richer matches.
- Add filters (genre, year, rating) and a "surprise me" button.
- Show extra details per recommendation (overview, release year, rating) using the TMDB API.
- Add unit tests for `recommend()` and for the TMDB client (with mocked responses).

## Acknowledgements

- Movie metadata: [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) on Kaggle.
- Posters and live movie data: [The Movie Database (TMDB)](https://www.themoviedb.org/).

> This product uses the TMDB API but is not endorsed or certified by TMDB.

## License

_No license has been chosen yet._ Add a `LICENSE` file (for example [MIT](https://choosealicense.com/licenses/mit/)) and update this section. Without one, the code is "all rights reserved" by default.