"""
Product Ranking Algorithm

Based on 01-MY-VISION.md:
- Randomness first (ensures variety)
- Location (state + city, local products prioritized)
- Time posted (new products get visibility)
- Other locations can appear but moderated

You can easily tweak weights and logic in this file without touching views.
"""

import random
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def rank_products(queryset, user_state, user_city, category=None):
    """
    Rank products based on custom algorithm.

    Algorithm Breakdown:
    - Randomness (30%): Pure randomness for variety
    - Location (30%): State + city matching (other locations moderated at 20%)
    - Recency (25%): New products (1 week=100%, 1 month=70%, older=30%)
    - Quality (15%): Based on key features (premium_quality, durable, etc.)

    Args:
        queryset: QuerySet of Product objects
        user_state: User's state (from their profile)
        user_city: User's city/LGA (from their profile)
        category: Optional category filter (applied before ranking)

    Returns:
        List of Product objects sorted by calculated score
    """

    products_with_scores = []
    now = datetime.now(timezone.utc)

    for product in queryset:
        score_breakdown = {}

        # ===== RANDOMNESS SCORE (30% WEIGHT) =====
        # Pure randomness to ensure variety - no two users see same order
        random_score = random.uniform(0, 100) * 0.30
        score_breakdown["randomness"] = round(random_score, 2)

        # ===== LOCATION SCORE (30% WEIGHT) =====
        # Prioritize local products, but allow other locations (moderated)
        store = product.store

        if (
            store.city.lower() == user_city.lower()
            and store.state.lower() == user_state.lower()
        ):
            # Same city - full score
            location_score = 100 * 0.30
            location_type = "same_city"
        elif store.state.lower() == user_state.lower():
            # Same state, different city - moderate score
            location_score = 60 * 0.30
            location_type = "same_state"
        else:
            # Different state - moderated but still visible
            location_score = 20 * 0.30
            location_type = "other_state"

        score_breakdown["location"] = round(location_score, 2)
        score_breakdown["location_type"] = location_type

        # ===== RECENCY SCORE (25% WEIGHT) =====
        # New products get visibility boost
        days_old = (now - product.created_at).days

        if days_old <= 7:
            # Very new (1 week) - maximum visibility
            recency_score = 100 * 0.25
            age_category = "new"
        elif days_old <= 30:
            # Recent (1 month) - good visibility
            recency_score = 70 * 0.25
            age_category = "recent"
        elif days_old <= 90:
            # Moderate (3 months) - moderate visibility
            recency_score = 50 * 0.25
            age_category = "moderate"
        else:
            # Older - base visibility
            recency_score = 30 * 0.25
            age_category = "older"

        score_breakdown["recency"] = round(recency_score, 2)
        score_breakdown["age_category"] = age_category
        score_breakdown["days_old"] = days_old

        # ===== QUALITY SCORE (15% WEIGHT) =====
        # Based on key features (premium_quality, durable, modern_design, easy_maintain)
        quality_features = [
            product.premium_quality,
            product.durable,
            product.modern_design,
            product.easy_maintain,
        ]
        quality_count = sum(quality_features)  # 0 to 4
        quality_score = (quality_count / 4.0) * 100 * 0.15
        score_breakdown["quality"] = round(quality_score, 2)
        score_breakdown["quality_features"] = quality_count

        # ===== TOTAL SCORE (100%) =====
        total_score = random_score + location_score + recency_score + quality_score

        score_breakdown["total"] = round(total_score, 2)

        # Log for debugging (optional)
        logger.debug(
            f"Product '{product.name}' scores: "
            f"Random={score_breakdown['randomness']}, "
            f"Location={score_breakdown['location']} ({location_type}), "
            f"Recency={score_breakdown['recency']} ({age_category}), "
            f"Quality={score_breakdown['quality']} ({quality_count}/4), "
            f"TOTAL={score_breakdown['total']}"
        )

        products_with_scores.append((product, total_score, score_breakdown))

    # Sort by total score (descending - highest first)
    products_with_scores.sort(key=lambda x: x[1], reverse=True)

    # Return just the product objects (in ranked order)
    return [product for product, score, breakdown in products_with_scores]


# ===== CONFIGURATION =====
# You can adjust these weights here without touching the algorithm logic above

WEIGHTS = {
    "randomness": 0.30,  # 30% - Pure randomness for variety
    "location": 0.30,  # 30% - Location matching (moderated for other states)
    "recency": 0.25,  # 25% - Time posted (new products boost)
    "quality": 0.15,  # 15% - Key features
}

# Total should equal 1.0 (100%)
assert (
    abs(sum(WEIGHTS.values()) - 1.0) < 0.01
), f"Weights must sum to 100%, got {sum(WEIGHTS.values())}"


# Location score modifiers
LOCATION_MODIFIERS = {
    "same_city": 100,  # Same city - full score
    "same_state": 60,  # Same state - moderate score
    "other_state": 20,  # Other states - moderated but visible
}


# Recency score modifiers (by days old)
RECENCY_MODIFIERS = {
    "new": (0, 7, 100),  # 0-7 days: 100%
    "recent": (8, 30, 70),  # 8-30 days: 70%
    "moderate": (31, 90, 50),  # 31-90 days: 50%
    "older": (91, 999999, 30),  # 90+ days: 30%
}


# ===== HELPER FUNCTIONS =====


def get_location_match_type(product, user_state, user_city):
    """
    Determine the type of location match for a product.

    Returns:
        'same_city': Product store in same city and state as user
        'same_state': Product store in same state but different city
        'other_state': Product store in different state
    """
    store = product.store

    if (
        store.city.lower() == user_city.lower()
        and store.state.lower() == user_state.lower()
    ):
        return "same_city"
    elif store.state.lower() == user_state.lower():
        return "same_state"
    else:
        return "other_state"


def get_product_age_category(product):
    """
    Categorize product by age.

    Returns:
        'new': 0-7 days old
        'recent': 8-30 days old
        'moderate': 31-90 days old
        'older': 90+ days old
    """
    now = datetime.now(timezone.utc)
    days_old = (now - product.created_at).days

    if days_old <= 7:
        return "new"
    elif days_old <= 30:
        return "recent"
    elif days_old <= 90:
        return "moderate"
    else:
        return "older"


def calculate_product_quality_score(product):
    """
    Calculate overall quality score for a product based on features.

    Returns:
        Integer between 0 and 4 (number of quality features enabled)
    """
    quality_features = [
        product.premium_quality,
        product.durable,
        product.modern_design,
        product.easy_maintain,
    ]
    return sum(quality_features)
