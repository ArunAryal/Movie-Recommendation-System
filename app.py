import os
import pickle
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise RuntimeError(
        "Missing TMDB_API_KEY in environment. Add it to the .env file in the project root."
    )


def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    response = requests.get(url)
    data = response.json()
    poster_path = data.get("poster_path")

    if not poster_path:
        return "https://via.placeholder.com/300x450?text=No+Poster"

    return "https://image.tmdb.org/t/p/original/" + poster_path


def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]
    top_movies_list = sorted(
        list(enumerate(distances)), reverse=True, key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_movies_posters = []

    for i in top_movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_movies_posters


movies = pickle.load(open("movies.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

st.title("Movie Recommendation system")

selected_movie_name = st.selectbox("Select a movie", movies["title"])

if st.button("Recommend"):
    names, poster = recommend(selected_movie_name)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.image(poster[0])
        st.text(names[0])

    with col2:
        st.image(poster[1])
        st.text(names[1])

    with col3:
        st.image(poster[2])
        st.text(names[2])

    with col4:
        st.image(poster[3])
        st.text(names[3])

    with col5:
        st.image(poster[4])
        st.text(names[4])
