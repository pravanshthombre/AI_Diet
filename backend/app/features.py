"""
Shared nutrient feature utilities for recommendation and substitution.

Vectors are z-score normalized per batch so high-magnitude fields (calories)
do not dominate cosine similarity.
"""
import numpy as np
from .models import Food

NUTRIENT_FIELDS = [
    "calories_per_serving",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
]


def food_vector(food: Food) -> np.ndarray:
    return np.array([getattr(food, f) for f in NUTRIENT_FIELDS], dtype=float)


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Z-score normalize rows so each nutrient contributes equally."""
    if vectors.size == 0:
        return vectors
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    mean = vectors.mean(axis=0)
    std = vectors.std(axis=0)
    std[std < 1e-6] = 1.0
    return (vectors - mean) / std


def cosine_scores(reference: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """Cosine similarity on z-score normalized nutrient vectors."""
    combined = np.vstack([reference.reshape(1, -1), candidates])
    normalized = normalize_vectors(combined)
    ref_norm = normalized[0:1]
    cand_norm = normalized[1:]
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity(ref_norm, cand_norm)[0]
