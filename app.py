from __future__ import annotations
import logging
import os
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageDraw
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()  # local development only (reads .env)

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent / "movies_processed.csv"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{movie_id}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"  # w342 ~ 30 KB
N_RECOMMENDATIONS = 5
REQUEST_TIMEOUT = (3.05, 8)  # (connect, read) seconds; never wait forever

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")


# Configuration
def get_api_key() -> str | None:
    # Return the TMDB credential from Streamlit secrets, falling back to env/.env.
    try:
        key = st.secrets.get("TMDB_API_KEY")
    except Exception:  # no secrets.toml present (e.g. local run using only .env)
        key = None
    return (key or os.getenv("TMDB_API_KEY") or "").strip() or None


# Data / model
@st.cache_resource(show_spinner="Loading movie data...")
def load_model():
    # Load movies and build the sparse bag-of-words matrix (takes ~0.2 s).
    # A sparse matrix is ~2 MB and one similarity row is computed on demand in ~8 ms.
    movies = pd.read_csv(DATA_FILE)
    movies = movies.drop_duplicates("movie_id").reset_index(drop=True)

    matrix = CountVectorizer(max_features=5000, stop_words="english").fit_transform(
        movies["tags"].fillna("")
    )

    # Different movies can share a title (e.g. two "Batman"s): disambiguate in the UI.
    shared = movies["title"].duplicated(keep=False)
    movies["label"] = movies["title"].where(
        ~shared, movies["title"] + " (TMDB #" + movies["movie_id"].astype(str) + ")"
    )
    return movies, matrix


def recommend(movies: pd.DataFrame, matrix, row: int, n: int = N_RECOMMENDATIONS):
    """Return the n most similar movies to the movie at *positional* row `row`."""
    scores = cosine_similarity(matrix[row], matrix).ravel()
    scores[row] = -1.0  # never recommend the selected movie itself
    top = np.argsort(-scores, kind="stable")[:n]
    return movies.iloc[top]


# TMDB posters
@st.cache_resource
def _session() -> requests.Session:
    return requests.Session()


@st.cache_resource
def placeholder_image() -> Image.Image:
    # Local 'no poster' image: no dependency on a third-party placeholder service.
    img = Image.new("RGB", (342, 513), "#2b2b2b")
    ImageDraw.Draw(img).text((120, 250), "No poster", fill="#bbbbbb")
    return img


@st.cache_data(ttl=60 * 60 * 24, max_entries=5000, show_spinner=False)
def _fetch_poster_path(movie_id: int, _api_key: str) -> str | None:
    # Call TMDB. Exceptions propagate on purpose so failures are NOT cached.
    # `_api_key` starts with an underscore so Streamlit does not hash/use it as a cache key.
  
    headers, params = {}, {"language": "en-US"}
    if _api_key.startswith("eyJ"):
        # "API Read Access Token" (JWT): sent in a header, never appears in a URL.
        headers["Authorization"] = f"Bearer {_api_key}"
    else:
        params["api_key"] = _api_key  # legacy v3 key (ends up in the URL, see get_poster)

    resp = _session().get(
        TMDB_MOVIE_URL.format(movie_id=int(movie_id)),
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == 404:  # unknown movie id: cache "no poster"
        return None
    resp.raise_for_status()
    return resp.json().get("poster_path")


def get_poster(movie_id: int, api_key: str | None):
    """Poster URL for a movie, or the local placeholder if anything goes wrong."""
    if not api_key:
        return placeholder_image()
    try:
        path = _fetch_poster_path(int(movie_id), api_key)
    except requests.RequestException as exc:
        # Log only the exception TYPE. The message of a requests error contains the full
        # URL, which would leak the API key if a legacy v3 key is used.
        logger.warning("TMDB lookup failed for movie %s (%s)", movie_id, type(exc).__name__)
        return placeholder_image()
    return f"{TMDB_IMAGE_BASE}{path}" if path else placeholder_image()


# UI
movies, matrix = load_model()
api_key = get_api_key()

st.title("🎬 Movie Recommendation System")

if not api_key:
    st.warning(
        "TMDB_API_KEY is not configured, so posters are disabled. "
        "Recommendations still work."
    )

selected_label = st.selectbox("Select a movie", movies["label"])

if st.button("Recommend", type="primary"):
    row = int(movies.index[movies["label"] == selected_label][0])  # RangeIndex: label == position
    recs = recommend(movies, matrix, row)

    with st.spinner("Fetching posters..."):
        cols = st.columns(len(recs))
        for col, rec in zip(cols, recs.itertuples()):
            with col:
                st.image(get_poster(rec.movie_id, api_key), width="stretch")
                st.caption(rec.title)

st.divider()
st.caption("This product uses the TMDB API but is not endorsed or certified by TMDB.")