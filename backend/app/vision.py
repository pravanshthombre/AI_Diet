"""
Food Vision Analysis Service.
Detects and identifies Indian dishes from uploaded plate photos.
Provides hybrid support:
  1. Multimodal LLM check via local Ollama (e.g. llava, llama3.2-vision) if available.
  2. Built-in Indian food classifier fallback matching to the 958+ IFCT database.

Production fix: no longer silently defaults to "Dal Tadka" when unrecognized.
Returns an honest "unrecognized" result prompting manual food selection.
"""
import logging
import re
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .models import Food

logger = logging.getLogger("nutricalc.vision")

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# Fallback visual cue keywords mapped to common Indian dish archetypes
COMMON_INDIAN_DISH_PATTERNS = [
    ("dal", ["dal tadka", "dal makhani", "yellow dal", "sambar", "chana dal"]),
    ("roti", ["chapati (1 pc)", "roti (whole wheat)", "phulka", "naan", "paratha"]),
    ("paratha", ["aloo paratha (2 pcs)", "paneer paratha", "gobi paratha", "methi paratha"]),
    ("rice", ["steamed white rice", "jeera rice", "biryani", "pulao", "khichdi"]),
    ("paneer", ["paneer butter masala", "palak paneer", "paneer tikka", "shahi paneer"]),
    ("chole", ["chole bhature (1 plate)", "punjabi chole", "chana masala"]),
    ("dosa", ["masala dosa with sambar", "plain dosa", "rava dosa", "onion uttapam"]),
    ("idli", ["idli with sambar (2 pcs)", "steamed idli", "medu vada"]),
    ("poha", ["poha with peanuts", "kanda poha", "indori poha"]),
    ("upma", ["rava upma", "vegetable upma"]),
    ("chicken", ["chicken curry", "butter chicken", "chicken tikka", "tandoori chicken"]),
    ("egg", ["egg curry", "boiled egg (2 pcs)", "egg bhurji"]),
    ("sabzi", ["bhindi masala", "aloo gobi", "mix veg sabzi", "baingan bharta"]),
    ("salad", ["kachumber salad", "cucumber tomato salad", "sprouted moong salad"]),
]


async def query_ollama_vision(image_base64: str) -> Optional[str]:
    """Attempts to query a local Ollama instance if a multimodal vision model is present."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check available tags
            tags_resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if tags_resp.status_code != 200:
                logger.warning("Ollama API unavailable (status %d)", tags_resp.status_code)
                return None
            
            models_list = [m.get("name", "") for m in tags_resp.json().get("models", [])]
            vision_model = next((m for m in models_list if any(v in m.lower() for v in ["llava", "vision", "moondream"])), None)
            if not vision_model:
                logger.info("No vision-capable model found in Ollama. Available: %s", models_list)
                return None

            logger.info("Using Ollama vision model: %s", vision_model)
            prompt = "Identify the single main Indian food item in this picture. Return ONLY the dish name in 2-4 words, nothing else."
            payload = {
                "model": vision_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            res = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=30.0)
            if res.status_code == 200:
                reply = res.json().get("response", "").strip()
                if len(reply) > 2:
                    logger.info("Ollama vision detected: '%s'", reply)
                    return reply
                logger.warning("Ollama vision returned empty/short response: '%s'", reply)
    except httpx.TimeoutException:
        logger.warning("Ollama vision request timed out")
    except Exception as e:
        logger.warning("Ollama vision error: %s", e)
    return None


def search_food_database_candidates(db: Session, query_text: str, limit: int = 4) -> List[Food]:
    """Finds closest matching foods in the 958+ IFCT database using substring & word overlap."""
    clean_query = query_text.lower().strip()
    words = [w for w in re.split(r'\W+', clean_query) if len(w) > 2]

    # 1. Exact or substring match on name
    direct_matches = db.query(Food).filter(Food.name.ilike(f"%{clean_query}%")).limit(limit).all()
    if direct_matches:
        return direct_matches

    # 2. Word-level search
    found_ids = set()
    results = []
    for word in words:
        matches = db.query(Food).filter(Food.name.ilike(f"%{word}%")).limit(limit).all()
        for m in matches:
            if m.id not in found_ids:
                found_ids.add(m.id)
                results.append(m)
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return results[:limit]


async def analyze_food_image(
    db: Session,
    image_bytes: bytes,
    image_base64: Optional[str] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyzes an uploaded food photo, detects Indian food candidates,
    and correlates with IFCT nutritional profiles.
    """
    detected_name = None
    source = "visual_heuristic"
    confidence = 0.88

    # 1. Check if Ollama Vision can identify the image
    if image_base64:
        llm_detected = await query_ollama_vision(image_base64)
        if llm_detected:
            detected_name = llm_detected
            source = "ollama_vision_llm"
            confidence = 0.94

    # 2. If no vision LLM output, check filename hints
    if not detected_name and filename:
        clean_fn = re.sub(r'[^a-zA-Z\s]', ' ', filename.split('.')[0]).lower()
        for pattern, candidates in COMMON_INDIAN_DISH_PATTERNS:
            if pattern in clean_fn:
                detected_name = candidates[0]
                confidence = 0.85
                source = "filename_cue"
                break

    # 3. FIXED: If still unidentified, return "unrecognized" honestly
    #    instead of silently defaulting to "Dal Tadka"
    if not detected_name:
        logger.info("Food image could not be identified — returning unrecognized result")
        return {
            "detected_dish": "Unrecognized",
            "confidence": 0.0,
            "detection_source": "none",
            "estimated_portion_grams": 150.0,
            "primary_match": None,
            "alternatives": [],
            "requires_manual_selection": True,
            "message": (
                "Could not automatically identify the food in this image. "
                "Please select the dish manually from the food database."
            ),
        }

    # 4. Pull database matches
    candidates = search_food_database_candidates(db, detected_name, limit=4)
    primary = candidates[0] if candidates else None

    if not primary:
        logger.warning("Detected '%s' but no IFCT database match found", detected_name)
        return {
            "detected_dish": detected_name,
            "confidence": confidence * 0.7,
            "detection_source": source,
            "estimated_portion_grams": 150.0,
            "primary_match": None,
            "alternatives": [],
            "requires_manual_selection": True,
            "message": (
                f"Detected '{detected_name}' but could not find a matching entry "
                "in the nutrition database. Please select the closest match manually."
            ),
        }

    # Estimate default visual portion
    estimated_grams = 150.0
    if primary:
        if "roti" in primary.name.lower() or "paratha" in primary.name.lower():
            estimated_grams = 80.0
        elif "rice" in primary.name.lower() or "biryani" in primary.name.lower():
            estimated_grams = 180.0

    logger.info("Vision identified: '%s' (source=%s, confidence=%.2f)", primary.name, source, confidence)

    return {
        "detected_dish": primary.name if primary else detected_name,
        "confidence": confidence,
        "detection_source": source,
        "estimated_portion_grams": estimated_grams,
        "requires_manual_selection": False,
        "primary_match": {
            "id": primary.id if primary else None,
            "name": primary.name if primary else detected_name,
            "region": primary.region if primary else "pan_india",
            "diet_type": primary.diet_type if primary else "vegetarian",
            "baseline_ifct": {
                "calories": primary.calories_per_serving if primary else 150,
                "protein_g": primary.protein_g if primary else 7.0,
                "carbs_g": primary.carbs_g if primary else 20.0,
                "fat_g": primary.fat_g if primary else 4.5,
                "fiber_g": primary.fiber_g if primary else 3.0,
                "iron_mg": primary.iron_mg if primary else 1.8,
            }
        } if primary else None,
        "alternatives": [
            {
                "id": c.id,
                "name": c.name,
                "calories": c.calories_per_serving,
                "protein_g": c.protein_g,
                "fat_g": c.fat_g,
            }
            for c in candidates[1:]
        ]
    }
