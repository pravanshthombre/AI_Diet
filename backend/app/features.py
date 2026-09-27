"""
Shared nutrient feature utilities for recommendation and substitution.

Vectors are z-score normalized per batch so high-magnitude fields (calories)
do not dominate cosine similarity.

Production fix: reference and candidate vectors are normalized independently
so the reference's normalization doesn't shift with each batch.
"""
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .models import Food

logger = logging.getLogger("nutricalc.features")

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
    """
    Cosine similarity between a reference nutrient vector and candidate vectors.

    Uses L2-normalization per vector (unit-vector projection) instead of
    z-score normalizing reference+candidates together. This prevents the
    reference vector's normalization from shifting with each candidate batch.
    """
    if candidates.size == 0:
        return np.array([])

    ref = reference.reshape(1, -1)
    if candidates.ndim == 1:
        candidates = candidates.reshape(1, -1)

    # L2-normalize each vector independently for stable cosine similarity
    ref_norm = np.linalg.norm(ref, axis=1, keepdims=True)
    ref_norm[ref_norm < 1e-8] = 1.0
    ref_unit = ref / ref_norm

    cand_norms = np.linalg.norm(candidates, axis=1, keepdims=True)
    cand_norms[cand_norms < 1e-8] = 1.0
    cand_unit = candidates / cand_norms

    return cosine_similarity(ref_unit, cand_unit)[0]
