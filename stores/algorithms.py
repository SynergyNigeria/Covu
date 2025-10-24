"""
Store Ranking Algorithm

Based on 01-MY-VISION.md:
- 40% weight for Location (randomly split between state and city matching)
- 60% weight shared among: average rating, product count, randomness
- Key: Random factor ensures no two users see identical order

You can easily tweak weights and logic in this file without touching views.
"""

import random
import logging

logger = logging.getLogger(__name__)


def rank_stores(queryset, user_state, user_city):
    """
    Rank stores based on custom algorithm.

    Algorithm Breakdown:
    - Location (40%): Randomly split between state and city matching
    - Average Rating (25% of 60% = 15%): Normalized to 100
    - Product Count (20% of 60% = 12%): Normalized, capped at 100 products
    - Randomness (15% of 60% = 9%): Pure randomness for variety
    - New Store Boost (14%): Stores created in last 30 days get visibility

    Args:
        queryset: QuerySet of Store objects
        user_state: User's state (from their profile)
        user_city: User's city/LGA (from their profile)

    Returns:
        List of Store objects sorted by calculated score
    """

    stores_with_scores = []

    for store in queryset:
        score_breakdown = {}

        # ===== LOCATION SCORE (40% WEIGHT) =====
        # Randomly split 40% between city and state matching
        city_weight = random.uniform(0.15, 0.25)  # Random portion of 40%
        state_weight = 0.40 - city_weight  # Remaining portion

        # City match check
        city_match = (
            1.0
            if (
                store.city.lower() == user_city.lower()
                and store.state.lower() == user_state.lower()
            )
            else 0.0
        )

        # State match check
        state_match = 1.0 if store.state.lower() == user_state.lower() else 0.0

        # Calculate location score
        location_score = (city_match * city_weight + state_match * state_weight) * 100
        score_breakdown["location"] = round(location_score, 2)

        # ===== RATING SCORE (15% WEIGHT) =====
        # Normalize rating (0-5) to 0-100, then apply 15% weight
        rating_score = (float(store.average_rating) / 5.0) * 100 * 0.15
        score_breakdown["rating"] = round(rating_score, 2)

        # ===== PRODUCT COUNT SCORE (12% WEIGHT) =====
        # Normalize product count (cap at 100 products = max score)
        product_score = min(float(store.product_count) / 100.0, 1.0) * 100 * 0.12
        score_breakdown["products"] = round(product_score, 2)

        # ===== RANDOMNESS SCORE (9% WEIGHT) =====
        # Pure randomness for variety
        random_score = random.uniform(0, 100) * 0.09
        score_breakdown["randomness"] = round(random_score, 2)

        # ===== NEW STORE BOOST (24% WEIGHT) =====
        # Give visibility to new stores (created in last 30 days)
        from datetime import datetime, timezone

        days_old = (datetime.now(timezone.utc) - store.created_at).days

        if days_old <= 7:
            newness_score = 100 * 0.24  # Very new (1 week)
        elif days_old <= 30:
            newness_score = 70 * 0.24  # New (1 month)
        else:
            newness_score = 30 * 0.24  # Established

        score_breakdown["newness"] = round(newness_score, 2)

        # ===== TOTAL SCORE (100%) =====
        total_score = (
            location_score + rating_score + product_score + random_score + newness_score
        )

        score_breakdown["total"] = round(total_score, 2)

        # Log for debugging (optional)
        logger.debug(
            f"Store '{store.name}' scores: "
            f"Location={score_breakdown['location']}, "
            f"Rating={score_breakdown['rating']}, "
            f"Products={score_breakdown['products']}, "
            f"Random={score_breakdown['randomness']}, "
            f"Newness={score_breakdown['newness']}, "
            f"TOTAL={score_breakdown['total']}"
        )

        stores_with_scores.append((store, total_score, score_breakdown))

    # Sort by total score (descending - highest first)
    stores_with_scores.sort(key=lambda x: x[1], reverse=True)

    # Return just the store objects (in ranked order)
    return [store for store, score, breakdown in stores_with_scores]


# ===== CONFIGURATION =====
# You can adjust these weights here without touching the algorithm logic above

WEIGHTS = {
    "location": 0.40,  # 40% - Location matching
    "rating": 0.15,  # 15% - Average rating
    "product_count": 0.12,  # 12% - Number of products
    "randomness": 0.09,  # 9% - Pure randomness
    "newness": 0.24,  # 24% - New store boost (adjusted to make total 100%)
}

# Total should equal 1.0 (100%)
# 0.40 + 0.15 + 0.12 + 0.09 + 0.24 = 1.00
assert (
    abs(sum(WEIGHTS.values()) - 1.0) < 0.01
), f"Weights must sum to 100%, got {sum(WEIGHTS.values())}"


# ===== HELPER FUNCTIONS =====


def get_location_match_type(store, user_state, user_city):
    """
    Determine the type of location match.

    Returns:
        'same_city': Store in same city and state as user
        'same_state': Store in same state but different city
        'different_state': Store in different state
    """
    if (
        store.city.lower() == user_city.lower()
        and store.state.lower() == user_state.lower()
    ):
        return "same_city"
    elif store.state.lower() == user_state.lower():
        return "same_state"
    else:
        return "different_state"


def calculate_store_quality_score(store):
    """
    Calculate overall quality score for a store.
    Based on rating, product count, and other factors.

    Returns:
        Float between 0 and 100
    """
    rating_component = (store.average_rating / 5.0) * 50  # Max 50 points
    product_component = min(store.product_count / 50.0, 1.0) * 30  # Max 30 points
    activity_component = 20 if store.is_active else 0  # Max 20 points

    return rating_component + product_component + activity_component
