import warnings
warnings.filterwarnings("ignore", category=FutureWarning, message="`resume_download` is deprecated and will be removed in version 1.0.0.*")
from flask import Flask, render_template, request, jsonify
import numpy as np
from sentence_transformers import SentenceTransformer

import os

local_model_path = os.path.join('local_models', 'all-MiniLM-L12-v2')

app = Flask(__name__)

# Load pre-trained sentence transformer model
model = SentenceTransformer(local_model_path)

# Initialize user interests data (replace this with your actual data)
user_interests_data = {
    'user1': "web development, reading novels, singing",
    'user2': "cooking, watching movies, anime",
    'user3': "Design, football, playing guitar",
    'user4': "Coding, dance, music"
}

# Function to generate embeddings for a list of sentences and average them
def generate_average_embedding(sentences):
    embeddings = model.encode(sentences)
    return np.mean(embeddings, axis=0)

# Process user interests data to generate user embeddings
user_embeddings = {}
for user_id, interests_str in user_interests_data.items():
    interests = interests_str.split(', ')
    user_embedding = generate_average_embedding(interests)
    user_embeddings[user_id] = {
        'embedding': user_embedding,
        'interests': interests
    }

# Function to find the k nearest neighbors for a given user
def find_k_nearest_neighbors(user_id, k=5):
    user_embedding = user_embeddings[user_id]['embedding']
    similarities = []
    for other_user_id, data in user_embeddings.items():
        if other_user_id != user_id:
            other_embedding = data['embedding']
            similarity = np.dot(user_embedding, other_embedding) / (np.linalg.norm(user_embedding) * np.linalg.norm(other_embedding))
            similarities.append((other_user_id, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    nearest_neighbors = [(sim[0], user_embeddings[sim[0]]['interests']) for sim in similarities[:k]]
    return nearest_neighbors

# Function to add a new user with their interests
def add_new_user(user_id, interests_str):
    global user_interests_data
    user_interests_data[user_id] = interests_str
    interests = interests_str.split(', ')
    user_embedding = generate_average_embedding(interests)
    user_embeddings[user_id] = {
        'embedding': user_embedding,
        'interests': interests
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_interests = request.form['user_interests']
        interests_list = [interest.strip() for interest in user_interests.split(',')]
        user_embedding = generate_average_embedding(interests_list)

        # Find similar users
        similarities = []
        for user_id, data in user_embeddings.items():
            similarity = np.dot(user_embedding, data['embedding']) / (np.linalg.norm(user_embedding) * np.linalg.norm(data['embedding']))
            similarities.append((user_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_users = [(sim[0], user_embeddings[sim[0]]['interests']) for sim in similarities[:5]]  # Get top 5 most similar users

        # Add new user if not already in user_interests_data
        new_user_id = f"user{len(user_interests_data) + 1}"
        add_new_user(new_user_id, user_interests)

        # Filter out the new user from similar users list
        similar_users = [(user_id, interests) for user_id, interests in similar_users if user_id != new_user_id]

        return render_template('index.html', similar_users=similar_users)

    return render_template('index.html')

@app.route('/api/similar_users', methods=['POST'])
def get_similar_users():
    try:
        data = request.get_json()
        user_interests = data.get('user_interests', '')
        interests_list = [interest.strip() for interest in user_interests.split(',')]
        user_embedding = generate_average_embedding(interests_list)

        similarities = []
        for user_id, data in user_embeddings.items():
            similarity = np.dot(user_embedding, data['embedding']) / (np.linalg.norm(user_embedding) * np.linalg.norm(data['embedding']))
            similarities.append((user_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_users = [(sim[0], user_embeddings[sim[0]]['interests']) for sim in similarities[:5]]

        return jsonify({'similar_users': similar_users})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)