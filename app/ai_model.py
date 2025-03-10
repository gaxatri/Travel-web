from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import subprocess
import json
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
import warnings
import sys
from collections import defaultdict
from datetime import datetime




#<<<<<<<<<<< API Route >>>>>>>>>>>>>>

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains (or restrict to specific domains)

@app.route('/execute-model', methods=['POST'])
def execute_model():
    try:
        # Get the user_id from the POST request
        user_id = request.json.get('user_id')
        
        if not user_id:
            return jsonify({"message": "User ID is required!"}), 400
        
        # Call the model.py script with the user_id
        # result = subprocess.run(
        #     ['python', 'model/knn_CF.py', user_id], 
        #     capture_output=True, text=True, check=True
        # )

        result = run_model(user_id)
 
        return jsonify({"message": "Executed Sucessfully"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"message": "Failed to execute the model.", "error": str(e)}), 500






#<<<<<<<<<<< AI Model >>>>>>>>>>>>>>

def load_dataset(csv_path):
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def load_user_data(json_path, user_id):
    try:
        with open(json_path, 'r') as f:
            user_data = json.load(f)

        if user_id in user_data and 'recommended' in user_data[user_id]:
            user_data[user_id]['recommended'] = []  # Clear the list

        return user_data

    except Exception as e:
        print(f"Error loading user data: {e}")
        return None


def save_user_data(user_data, json_path):
    try:
        with open(json_path, 'w') as f:
            json.dump(user_data, f, indent=2)
        print(f"Recommendations saved successfully to {json_path}")
    except Exception as e:
        print(f"Error saving user data: {e}")



def get_current_season():
    current_month = datetime.now().month
    if current_month in [12, 1, 2, 3]:
        return 'winter'
    elif current_month in [4, 5, 6]:
        return 'spring'
    elif current_month in [7, 8, 9]:
        return 'summer'
    elif current_month in [10, 11]:
        return 'autumn'


def seasons_overlap(season1, season2):
    season_map = {
        'Winter': [12, 1, 2, 3],
        'Spring': [4, 5, 6],
        'Summer': [7, 8, 9],
        'Autumn': [10, 11]
    }
    
    season1_months = season_map.get(season1, [])
    season2_months = season_map.get(season2, [])
    
    return bool(set(season1_months) & set(season2_months))  

# def knn_cosine(user_id, user_data, dataset, model, top_k=5):
#     user_key = user_id
#     user = user_data.get(user_key, {})

#     liked_locations = user.get("likedLocations", [])
#     visited_locations = user.get("visitedLocations", [])
#     added_locations = user.get("addedLocations", [])
#     currentLocation = user.get("currentLocation", None)
#     nearbyLocations = dataset[dataset['Location'].str.lower() == currentLocation.lower()]['Name'].tolist()

#     print("Nearby Locations:", nearbyLocations)

#     current_season = "Autumn"
#     print("Current Season", current_season)
#     print("Current Location", currentLocation)

#     # Weights are now declared inside the function
#     weights = {
#         'likedLocations': 1.0,
#         'visitedLocations': 0.3,
#         'addedLocations': 0.7,
#         'nearbyLocations': 0.2,

#         'description': 0.0,
#         'category': 3.0, 
#         'bestSeason': 0.0,
#         'keywords': 0.0
#     }

#     locations_of_interest = []
#     locations_of_interest.extend([(loc, 'likedLocations') for loc in liked_locations])
#     locations_of_interest.extend([(loc, 'visitedLocations') for loc in visited_locations])
#     locations_of_interest.extend([(loc, 'addedLocations') for loc in added_locations])
#     locations_of_interest.extend([(loc, 'nearbyLocations') for loc in nearbyLocations])

#     if not locations_of_interest:
#         print("No liked, visited, or added locations available to generate recommendations.")
#         return {}

#     location_embeddings = {}
#     model = SentenceTransformer('all-MiniLM-L12-v2')

#     # Create embeddings for each location using columns such as Description, Category, BestSeason, and Keywords
#     for _, row in dataset.iterrows():
#         description = row['Description']
#         category = row['Category']
#         best_season = row['BestSeason']
#         keywords = row['keywords']

#         # Embed text columns like Description, Category, and Keywords
#         description_embedding = model.encode(description)
#         category_embedding = model.encode(category)
#         keywords_embedding = model.encode(keywords)

#         # Handle seasonality comparison with current season
#         season_similarity = 1.0 if seasons_overlap(current_season, best_season.lower()) else 0.5

#         location_embeddings[row['Name']] = {
#             'description': description_embedding,
#             'category': category_embedding,
#             'bestSeason': season_similarity,  
#             'keywords': keywords_embedding
#         }

#     combined_embedding = np.zeros(location_embeddings[next(iter(location_embeddings))]['description'].shape)

#     # Combine embeddings for locations of interest with their respective weights
#     for location, category in locations_of_interest:
#         if location not in location_embeddings:
#             continue
#         weight = weights.get(category, 1.0)  # Apply weight for each category

#         # For each location, combine embeddings of description, category, season, and keywords
#         location_data = location_embeddings[location]

#         combined_embedding += location_data['description'] * weight * weights.get('description', 1.0)
#         combined_embedding += location_data['category'] * weight * weights.get('category', 1.0)  # Fix weight
#         combined_embedding += location_data['keywords'] * weight * weights.get('keywords', 1.0)
#         combined_embedding += location_data['bestSeason'] * weight * weights.get('bestSeason', 1.0)

#     if len(locations_of_interest) > 0:
#         combined_embedding /= len(locations_of_interest)

#     similarities = []

#     for name, location_data in location_embeddings.items():
#         if name in liked_locations or name in visited_locations or name in added_locations:
#             continue

#         # Combine the embeddings for similarity calculation
#         location_combined_embedding = np.zeros_like(combined_embedding)

#         location_combined_embedding += location_data['description'] * weights.get('description', 1.0)
#         location_combined_embedding += location_data['category'] * weights.get('category', 1.0)
#         location_combined_embedding += location_data['keywords'] * weights.get('keywords', 1.0)
#         location_combined_embedding += location_data['bestSeason'] * weights.get('bestSeason', 1.0)

#         # Calculate cosine similarity
#         similarity_score = cosine_similarity([combined_embedding], [location_combined_embedding])[0][0]
#         similarities.append((name, similarity_score))

#     similarities.sort(key=lambda x: x[1], reverse=True)
#     top_similar_locations = similarities[:top_k]

#     return top_similar_locations

def llm_model(user_id, user_data_path):
    try:
        user_data = load_user_data(user_data_path, user_id)
        user = user_data.get(user_id, {})

        locations = user.get("likedLocations", [])
        result = subprocess.run(
            ['python', 'recc.py'] + locations,
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error while running the llm model{e}")
        return None

def calculate_location_distance(currentLocation, location):

    district_distance_matrix = {
        "Thiruvananthapuram": [0, 50, 70, 90, 120, 160, 220, 250, 270, 300, 320, 340, 380, 420],
        "Kollam": [50, 0, 30, 50, 80, 120, 170, 200, 230, 250, 270, 290, 330, 370],
        "Pathanamthitta": [70, 30, 0, 30, 60, 100, 150, 180, 200, 220, 240, 260, 300, 340],
        "Alappuzha": [90, 50, 30, 0, 30, 70, 130, 160, 190, 210, 230, 250, 290, 320],
        "Kottayam": [120, 80, 60, 30, 0, 40, 100, 130, 160, 180, 200, 220, 260, 290],
        "Idukki": [160, 120, 100, 70, 40, 0, 60, 90, 120, 140, 160, 180, 220, 250],
        "Ernakulam": [220, 170, 150, 130, 100, 60, 0, 30, 60, 90, 110, 130, 170, 200],
        "Thrissur": [250, 200, 180, 160, 130, 90, 30, 0, 30, 60, 80, 100, 140, 170],
        "Palakkad": [270, 230, 200, 190, 160, 120, 60, 30, 0, 30, 50, 70, 110, 140],
        "Malappuram": [300, 250, 220, 210, 180, 140, 90, 60, 30, 0, 30, 50, 90, 120],
        "Kozhikode": [320, 270, 240, 230, 200, 160, 110, 80, 50, 30, 0, 20, 60, 90],
        "Wayanad": [340, 290, 260, 250, 220, 180, 130, 100, 70, 50, 20, 0, 40, 70],
        "Kannur": [380, 330, 300, 290, 260, 220, 170, 140, 110, 90, 60, 40, 0, 40],
        "Kasaragod": [420, 370, 340, 320, 290, 250, 200, 170, 140, 120, 90, 70, 40, 0]
    }

    currentLocation = currentLocation.strip().lower()
    location = location.strip().lower()
    
    for district_name in district_distance_matrix.keys():
        if currentLocation == district_name.strip().lower():
            district_locations = list(district_distance_matrix.keys())

            for idx, district in enumerate(district_locations):
                if location == district.strip().lower():
                    return district_distance_matrix[district_name][idx]
                
    return 1000

def knn_cosine(user_id, user_data, dataset, model, top_k=5):
    user_key = user_id
    user = user_data.get(user_key, {})

    liked_locations = user.get("likedLocations", [])
    visited_locations = user.get("visitedLocations", [])
    added_locations = user.get("addedLocations", [])
    currentLocation = user.get("currentLocation", None)

    current_season = "Autumn"
    print("Current Location:", currentLocation)
    print("Current Season:", current_season)

    weights = {
        'likedLocations': 1.0,
        'visitedLocations': 0.3,
        'addedLocations': 0.7,
        'description': 1.0,
        'category': 5.0, 
        'bestSeason': 0.05,
        'keywords': 0.0
    }

    locations_of_interest = []
    locations_of_interest.extend([(loc, 'likedLocations') for loc in liked_locations])
    locations_of_interest.extend([(loc, 'visitedLocations') for loc in visited_locations])
    locations_of_interest.extend([(loc, 'addedLocations') for loc in added_locations])

    if not locations_of_interest:
        print("No liked, visited, or added locations available to generate recommendations.")
        return {}

    location_embeddings = {}
    model = SentenceTransformer('all-MiniLM-L12-v2')

    for _, row in dataset.iterrows():
        description = row['Description']
        category = row['Category']
        best_season = row['BestSeason']
        keywords = row['keywords']
        district = row['Location']  


        description_embedding = model.encode(description)
        category_embedding = model.encode(category)
        keywords_embedding = model.encode(keywords)

        season_similarity = 1.0 if seasons_overlap(current_season, best_season.lower()) else 0.5

        location_embeddings[row['Name']] = {
            'description': description_embedding,
            'category': category_embedding,
            'bestSeason': season_similarity,  
            'keywords': keywords_embedding,
            'district': district 
        }

    combined_embedding = np.zeros(location_embeddings[next(iter(location_embeddings))]['description'].shape)

    for location, category in locations_of_interest:
        if location not in location_embeddings:
            continue
        weight = weights.get(category, 1.0)  


        location_data = location_embeddings[location]

        combined_embedding += location_data['description'] * weight * weights.get('description', 1.0)
        combined_embedding += location_data['category'] * weight * weights.get('category', 1.0)  # Fix weight
        combined_embedding += location_data['keywords'] * weight * weights.get('keywords', 1.0)
        combined_embedding += location_data['bestSeason'] * weight * weights.get('bestSeason', 1.0)

    if len(locations_of_interest) > 0:
        combined_embedding /= len(locations_of_interest)

    location_distances = {}
    if currentLocation:

        for name, location_data in location_embeddings.items():
            current_location_district = currentLocation  
            location_district = location_data['district']
            location_distances[name] = calculate_location_distance(current_location_district, location_district)

    similarities = []

    #<<<<< Distance Factor >>>>>>>
    distance_weight_factor = 0.41
    #<<<<< Distance Factor >>>>>>>

    for name, location_data in location_embeddings.items():
        if name in liked_locations or name in visited_locations or name in added_locations:
            continue

        location_combined_embedding = np.zeros_like(combined_embedding)

        location_combined_embedding += location_data['description'] * weights.get('description', 1.0)
        location_combined_embedding += location_data['category'] * weights.get('category', 1.0)
        location_combined_embedding += location_data['keywords'] * weights.get('keywords', 1.0)
        location_combined_embedding += location_data['bestSeason'] * weights.get('bestSeason', 1.0)

        distance = location_distances.get(name, 1000)  
        distance_weight = max(1 / (distance + 1), 0.1)  
        weighted_similarity = cosine_similarity([combined_embedding], [location_combined_embedding])[0][0]
        weighted_similarity *= (1 - distance_weight_factor) + (distance_weight_factor * distance_weight)
        similarities.append((name, weighted_similarity, distance))

    similarities.sort(key=lambda x: x[1], reverse=True)

    top_similar_locations = similarities[:top_k]

    for location, similarity, distance in top_similar_locations:
        print(f"Location: {location}, Similarity: {similarity}, Distance: {distance}")

    top_similar_locations = [(location, similarity) for location, similarity, _ in top_similar_locations]

    return top_similar_locations




def collaborative_filtering(user_data, user_id, similarity_threshold=0.5, top_k=5):
    """
    Generates recommendations based on User-based Collaborative Filtering.

    Args:
    - user_data: Dictionary containing user data (liked, visited, added, etc.)
    - user_id: The user for whom the recommendations are generated
    - similarity_threshold: The threshold for considering a user as "similar"
    - top_k: The number of top recommendations to return

    Returns:
    - List of top-k recommended locations
    """
    user = user_data.get(user_id, {})

    liked_locations = set(user.get("likedLocations", []))
    visited_locations = set(user.get("visitedLocations", []))
    added_locations = set(user.get("addedLocations", []))
    all_user_locations = liked_locations | visited_locations | added_locations
    
    if not all_user_locations:
        return []

    user_similarities = []
    
    for other_user_id, other_user in user_data.items():
        if other_user_id == user_id:
            continue

        other_liked = set(other_user.get("likedLocations", []))
        other_visited = set(other_user.get("visitedLocations", []))
        other_added = set(other_user.get("addedLocations", []))
        other_user_locations = other_liked | other_visited | other_added
        
        #Jaccard similarity
        intersection = len(all_user_locations.intersection(other_user_locations))
        union = len(all_user_locations.union(other_user_locations))
        similarity = intersection / union if union > 0 else 0.0
        
        if similarity >= similarity_threshold:
            user_similarities.append((other_user_id, similarity, other_user_locations))
        
    print("user matched:", user_similarities )
    recommended_locations = defaultdict(float)

    for similar_user_id, similarity, similar_user_locations in user_similarities:
        for location in similar_user_locations:
            if location not in all_user_locations:
                recommended_locations[location] += similarity
    
    top_recommendations = sorted(recommended_locations.items(), key=lambda x: x[1], reverse=True)[:top_k]
    print("top recc", top_recommendations)
    return top_recommendations


# -------------------------------
# Hybrid Model: Combines KNN-Cosine & Collaborative Filtering
# -------------------------------

def hybrid_model(user_id, user_data, dataset, knn_model, collab_model, knn_weight=0.7, collab_weight=0.3, top_k=5):
    """
    Combines the recommendations from KNN-Cosine and User-based Collaborative Filtering models.
    Weights the recommendations and returns top-k locations.

    Args:
    - user_id: The user for whom the recommendations are generated
    - user_data: Dictionary containing user data (liked, visited, added, etc.)
    - dataset: The location dataset
    - knn_model: The KNN-Cosine model function (takes user_id, user_data, dataset, model)
    - collab_model: The Collaborative Filtering model function (takes user_data, user_id)
    - knn_weight: The weight to assign to the KNN-Cosine model's recommendations
    - collab_weight: The weight to assign to the Collaborative Filtering model's recommendations
    - top_k: The number of top recommendations to return

    Returns:
    - top_k_locations: List of top-k recommended locations
    """
    
    knn_recommendations = knn_model(user_id, user_data, dataset, knn_model, top_k=top_k)
    collab_recommendations = collab_model(user_data, user_id, similarity_threshold=0.5, top_k=top_k)
    combined_scores = defaultdict(float)
    
    for location, score in knn_recommendations:
        combined_scores[location] += score * knn_weight
    
    for location, score in collab_recommendations:
        combined_scores[location] += score * collab_weight
        
    top_k_locations = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return top_k_locations



def evaluate_model(user_id, user_data_path, dataset_path, test_data_path, top_k=5, weights=None):
    """
    Evaluates the model by comparing the recommended locations with the preferred locations from test_data.json.
    Computes Precision, Recall, F1-Score, and MAP.
    """
    try:
        dataset = pd.read_csv(dataset_path)
        with open(user_data_path, 'r') as f:
            user_data = json.load(f)
        with open(test_data_path, 'r') as f:
            test_data = json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    model = SentenceTransformer('all-MiniLM-L12-v2')
    recommendations = knn_cosine(user_id, user_data, dataset, knn_cosine, top_k=top_k)

    if not recommendations:
        print("No recommendations generated.")
        return

    true_preferred_locations = set(test_data.get(user_id, {}).get("preferredLocations", []))
    recommended_locations = [location for location, _ in recommendations]


    true_positives = len(set(recommended_locations) & true_preferred_locations)
    precision = true_positives / len(recommended_locations) if len(recommended_locations) > 0 else 0.0
    recall = true_positives / len(true_preferred_locations) if len(true_preferred_locations) > 0 else 0.0
    f1_score_value = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0


    print(f"\nEvaluation results of the model")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    #print(f"F1-Score: {f1_score_value:.4f}")


def knn_model(user_id):
    user_data_path = r'C:\Users\melvi\Desktop\Travel App\travel_web\public\userData\userData.json'
    dataset_path = r'C:\Users\melvi\Desktop\Travel App\travel_web\public\locationData\dataset.csv'
    test_data_path = r'C:\Users\melvi\Desktop\Travel App\travel_web\public\userData\test_data.json'


    dataset = load_dataset(dataset_path)
    user_data = load_user_data(user_data_path, user_id)

    if dataset is None or dataset.empty or user_data is None:
        print("Error: Dataset or user data is missing or empty.")
        return "Error: Dataset or user data is missing or empty."


    top_k = 7
    knn_weight = 0.51 
    collab_weight = 0.495

    recommendations = hybrid_model(user_id, user_data, dataset, knn_cosine, collaborative_filtering, 
                                   knn_weight=knn_weight, collab_weight=collab_weight, top_k=top_k)

    if not recommendations:
        print("No recommendations generated.")
        return "No recommendations generated."


    if user_id not in user_data:
        print(f"Error: User ID {user_id} not found in user data.")
        return f"Error: User ID {user_id} not found in user data."

    user_key = user_id
    if 'recommended' not in user_data[user_key]:
        user_data[user_key]["recommended"] = []

    recommended_set = set(user_data[user_key]["recommended"])


    for sim_location, _ in recommendations:
        if sim_location not in recommended_set:
            user_data[user_key]["recommended"].append(sim_location)

    save_user_data(user_data, user_data_path)

    print("\nTop 5 recommendations:")
    current_location = user_data[user_key].get("currentLocation", "")
    for sim_location, sim_score in recommendations:
        label = "(top)" if current_location and sim_location in user_data[user_key]["recommended"] and \
                            current_location.lower() == dataset[dataset['Name'] == sim_location]['Location'].values[0].lower() else ""
        print(f"  - {sim_location} (Similarity: {sim_score:.4f}) {label}")


    
    evaluate_model(user_id, user_data_path, dataset_path, test_data_path, top_k, weights=None)

    print(llm_model(user_id, user_data_path))

    return "Model executed successfully. Recommendations updated."


def run_model(userID):

    if userID is None:
        print("Error: User ID not provided.")
    else:
        result = knn_model(userID)
        print(result)
        return result



if __name__ == '__main__':  
    app.run(debug=True, host='0.0.0.0', port=5000)

