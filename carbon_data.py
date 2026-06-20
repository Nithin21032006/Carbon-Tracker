"""
Carbon emission factors and category logic.

Emission factors are kg CO2e per kg of product (or per unit where noted),
sourced from widely-cited lifecycle-assessment aggregates (Poore & Nemecek 2018
style averages). These are reasonable estimates for a consumer-facing tool,
not laboratory-grade figures — the app is upfront about that in the UI copy.
"""

# kg CO2e per kg of product, "farm to retail" average
EMISSION_FACTORS = {
    # Meat & fish — highest impact category
    "beef": 60.0,
    "lamb": 24.0,
    "pork": 7.0,
    "chicken": 6.0,
    "turkey": 6.0,
    "bacon": 7.5,
    "sausage": 7.0,
    "fish": 5.0,
    "shrimp": 12.0,
    "salmon": 5.5,
    "tuna": 6.0,

    # Dairy & eggs
    "cheese": 21.0,
    "milk": 3.0,
    "yogurt": 2.2,
    "butter": 12.0,
    "cream": 5.5,
    "eggs": 4.5,
    "ice cream": 7.0,

    # Grains, legumes, staples
    "rice": 4.0,
    "bread": 1.6,
    "pasta": 1.4,
    "flour": 1.2,
    "oats": 1.6,
    "cereal": 1.8,
    "beans": 2.0,
    "lentils": 0.9,
    "tofu": 2.0,
    "nuts": 2.3,
    "almonds": 2.3,
    "walnuts": 2.3,
    "cashews": 2.3,
    "peanut butter": 2.5,

    # Produce — lowest impact category
    "vegetables": 0.5,
    "fruit": 0.6,
    "potatoes": 0.3,
    "tomatoes": 1.4,
    "onions": 0.5,
    "leafy greens": 0.5,
    "spinach": 0.5,
    "lettuce": 0.5,
    "kale": 0.5,
    "broccoli": 0.6,
    "carrots": 0.4,
    "peppers": 0.6,
    "cucumber": 0.4,
    "avocado": 1.6,
    "banana": 0.7,
    "bananas": 0.7,
    "apple": 0.4,
    "apples": 0.4,
    "orange": 0.4,
    "oranges": 0.4,
    "grapes": 0.5,
    "berries": 0.6,
    "strawberries": 0.6,

    # Packaged / processed / drinks
    "chips": 3.0,
    "chocolate": 19.0,
    "coffee": 17.0,
    "tea": 6.0,
    "soda": 0.5,
    "juice": 1.0,
    "beer": 0.7,
    "wine": 1.8,
    "frozen meal": 3.5,
    "snack bar": 2.5,
    "sauce": 1.5,
    "oil": 3.5,

    # Household / non-food (rough proxies, packaging + manufacturing)
    "paper towels": 1.8,
    "cleaning supplies": 2.5,
    "plastic bags": 6.0,
    "toiletries": 3.0,

    # Fallback
    "other": 1.5,
}

# Maps raw items into one of these 6 dashboard categories
CATEGORY_MAP = {
    "beef": "Meat & Fish", "lamb": "Meat & Fish", "pork": "Meat & Fish",
    "chicken": "Meat & Fish", "turkey": "Meat & Fish", "bacon": "Meat & Fish",
    "sausage": "Meat & Fish", "fish": "Meat & Fish", "shrimp": "Meat & Fish",
    "salmon": "Meat & Fish", "tuna": "Meat & Fish",

    "cheese": "Dairy & Eggs", "milk": "Dairy & Eggs", "yogurt": "Dairy & Eggs",
    "butter": "Dairy & Eggs", "cream": "Dairy & Eggs", "eggs": "Dairy & Eggs",
    "ice cream": "Dairy & Eggs",

    "rice": "Grains & Staples", "bread": "Grains & Staples", "pasta": "Grains & Staples",
    "flour": "Grains & Staples", "oats": "Grains & Staples", "cereal": "Grains & Staples",
    "beans": "Grains & Staples", "lentils": "Grains & Staples", "tofu": "Grains & Staples",
    "nuts": "Grains & Staples", "almonds": "Grains & Staples",
    "walnuts": "Grains & Staples", "cashews": "Grains & Staples",
    "peanut butter": "Grains & Staples",

    "vegetables": "Produce", "fruit": "Produce", "potatoes": "Produce",
    "tomatoes": "Produce", "onions": "Produce", "leafy greens": "Produce",
    "spinach": "Produce", "lettuce": "Produce", "kale": "Produce",
    "broccoli": "Produce", "carrots": "Produce", "peppers": "Produce",
    "cucumber": "Produce", "avocado": "Produce", "banana": "Produce",
    "bananas": "Produce", "apple": "Produce", "apples": "Produce",
    "orange": "Produce", "oranges": "Produce", "grapes": "Produce",
    "berries": "Produce", "strawberries": "Produce",

    "chips": "Packaged & Drinks", "chocolate": "Packaged & Drinks", "coffee": "Packaged & Drinks",
    "tea": "Packaged & Drinks", "soda": "Packaged & Drinks", "juice": "Packaged & Drinks",
    "beer": "Packaged & Drinks", "wine": "Packaged & Drinks", "frozen meal": "Packaged & Drinks",
    "snack bar": "Packaged & Drinks", "sauce": "Packaged & Drinks", "oil": "Packaged & Drinks",

    "paper towels": "Household", "cleaning supplies": "Household",
    "plastic bags": "Household", "toiletries": "Household",

    "other": "Other",
}

CATEGORY_COLORS = {
    "Meat & Fish": "#C4622D",
    "Dairy & Eggs": "#D4AF37",
    "Grains & Staples": "#8B8578",
    "Produce": "#3D5A3D",
    "Packaged & Drinks": "#6B4C8A",
    "Household": "#4A6B8A",
    "Other": "#8B8578",
}

# Reduction tips keyed by category — shown when that category dominates the footprint
REDUCTION_TIPS = {
    "Meat & Fish": [
        "Swap beef for chicken or beans twice a week — beef has roughly 10x the footprint of chicken per kg.",
        "Try one plant-based dinner this week. Lentils and tofu carry a fraction of meat's emissions.",
        "Buy fish with sustainable certification where possible — farmed shellfish often beats red meat by a wide margin.",
    ],
    "Dairy & Eggs": [
        "Cheese is surprisingly carbon-heavy — try halving portions in recipes rather than cutting it entirely.",
        "Oat or soy milk cuts dairy-milk emissions by more than half if you're open to switching.",
        "Buy eggs from local or pasture sources when available — transport distance adds up on perishables.",
    ],
    "Grains & Staples": [
        "You're already in a low-impact zone here — staples like rice and lentils are efficient choices.",
        "Buying dried beans instead of canned cuts packaging waste and a bit of footprint too.",
    ],
    "Produce": [
        "Great category to lean into — produce is consistently your lowest-carbon option.",
        "Buying in-season produce reduces the emissions tied to greenhouse growing and long-haul transport.",
    ],
    "Packaged & Drinks": [
        "Coffee and chocolate carry high footprints per kg — enjoying them in moderation helps more than people expect.",
        "Canned soda and bottled drinks add packaging emissions — a reusable bottle with tap water is the lowest-impact swap.",
    ],
    "Household": [
        "Concentrated cleaning products reduce the plastic and shipping weight behind each purchase.",
        "Buying paper towels in bulk cuts packaging-related emissions per sheet.",
    ],
    "Other": [
        "Check item labels for lower-packaging or bulk alternatives where you can.",
    ],
}


def classify_item(item_name: str) -> tuple[str, float]:
    """
    Given a free-text item name from receipt OCR, find the closest known
    food/product key. Returns (key, emission_factor_per_kg).
    Falls back to 'other' if nothing matches.

    Matching strategy: find all keys that appear as substrings, then prefer
    the one appearing latest in the string (e.g. "orange juice" should match
    "juice", not "orange", since the trailing noun is usually the true
    product type — "orange juice" is a drink, not a piece of fruit).
    Ties broken by longer key length (more specific match wins).
    """
    name = item_name.lower().strip()
    candidates = []
    for key in EMISSION_FACTORS:
        idx = name.rfind(key)
        if idx != -1:
            candidates.append((idx, len(key), key))

    if not candidates:
        return "other", EMISSION_FACTORS["other"]

    # Drop any candidate that is fully contained within a longer candidate's
    # matched span (e.g. "butter" inside "peanut butter") — the longer,
    # more specific key always wins over a shorter key it contains.
    def is_subsumed(cand, others):
        idx, length, key = cand
        end = idx + length
        for oidx, olength, okey in others:
            if okey == key:
                continue
            oend = oidx + olength
            if oidx <= idx and end <= oend and olength > length:
                return True
        return False

    candidates = [c for c in candidates if not is_subsumed(c, candidates)]

    # Among remaining, prefer match starting latest in the string, then longest key
    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
    best_key = candidates[0][2]
    return best_key, EMISSION_FACTORS[best_key]


def get_category(key: str) -> str:
    return CATEGORY_MAP.get(key, "Other")


def get_category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#8B8578")


def estimate_item_co2(item_name: str, weight_kg: float = 0.4) -> dict:
    """
    Estimate CO2e for a single receipt line item.
    weight_kg defaults to 0.4kg (a reasonable single-item grocery guess)
    when the AI extraction can't infer a specific weight from the receipt.
    """
    key, factor = classify_item(item_name)
    category = get_category(key)
    co2 = round(factor * weight_kg, 3)
    return {
        "matched_key": key,
        "category": category,
        "color": get_category_color(category),
        "factor_per_kg": factor,
        "estimated_weight_kg": weight_kg,
        "co2e_kg": co2,
    }


def get_top_tip(category_totals: dict) -> dict:
    """Given {category: co2_total}, return a tip for the dominant category."""
    if not category_totals:
        return {"category": "Other", "tip": "Scan a receipt to get personalized tips."}
    top_category = max(category_totals, key=category_totals.get)
    tips = REDUCTION_TIPS.get(top_category, REDUCTION_TIPS["Other"])
    import random
    return {"category": top_category, "tip": random.choice(tips)}
