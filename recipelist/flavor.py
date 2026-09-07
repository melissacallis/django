"""Generates a short, evocative "chef's note" for a recipe based on its
ingredients and cuisine tags, since Spoonacular's own `summary` field is
SEO copy ("Watching your figure?"), not the kind of thing you'd want on
a recipe page. Deterministic per recipe (seeded by external_id) so the
same dish always reads the same way rather than reshuffling on refresh.
"""
import random
import re

THEMES = {
    "spicy_fermented": {
        "keywords": ["chili", "gochugaru", "gochujang", "kimchi", "sriracha", "jalape",
                     "cayenne", "hot sauce", "wasabi", "chile", "pepper flakes", "harissa"],
        "openers": [
            "delivers a slow, building heat that lingers pleasantly on the palate",
            "hits with a bright, fermented tang before the heat creeps in",
            "is bold and a little unruly — the kind of dish that wakes up your whole mouth",
        ],
        "descriptors": [
            "a sharp, sinus-clearing heat",
            "a deep, funky sourness from the ferment",
            "a slow-building warmth that never quite lets go",
        ],
    },
    "sweet_dessert": {
        "keywords": ["sugar", "chocolate", "vanilla", "caramel", "honey", "maple",
                     "frosting", "cream cheese", "powdered sugar", "cocoa"],
        "openers": [
            "is pure, unapologetic indulgence",
            "reads like dessert should — a little sweet, a little rich, entirely comforting",
            "is the sort of thing you sneak a second bite of before it's even plated",
        ],
        "descriptors": [
            "a deep, caramelized sweetness",
            "a silky, melt-on-the-tongue richness",
            "a warm vanilla backbone that ties everything together",
        ],
    },
    "creamy_comfort": {
        "keywords": ["cream", "butter", "cheese", "milk", "alfredo", "mac and cheese",
                     "sour cream", "mascarpone"],
        "openers": [
            "is comfort food in its purest form",
            "wraps everything in a rich, velvety embrace",
            "is the kind of dish you want after a long day",
        ],
        "descriptors": [
            "a luxurious, buttery richness",
            "a smooth, cheese-forward creaminess",
            "a coating richness that clings to every bite",
        ],
    },
    "bright_fresh": {
        "keywords": ["lime", "lemon", "cilantro", "mint", "basil", "vinegar", "citrus", "parsley"],
        "openers": [
            "is light on its feet, built for brightness rather than weight",
            "leads with acid and herbs, keeping every bite lively",
            "is the kind of dish that tastes like it was made in summer",
        ],
        "descriptors": [
            "a clean citrus lift",
            "a fresh, herbaceous snap",
            "a bright acidity that keeps things from feeling heavy",
        ],
    },
    "smoky_grilled": {
        "keywords": ["smoked", "paprika", "bbq", "barbecue", "grill", "char", "chipotle"],
        "openers": [
            "carries real char and smoke in every bite",
            "is deep, smoky, and built for slow eating",
            "has that unmistakable backyard-grill character",
        ],
        "descriptors": [
            "a deep smokiness that lingers",
            "a charred edge that adds real depth",
            "a smoky warmth from the paprika",
        ],
    },
    "umami_savory": {
        "keywords": ["soy sauce", "fish sauce", "miso", "mushroom", "parmesan", "garlic",
                     "oyster sauce", "anchovy"],
        "openers": [
            "is deeply savory, the kind of dish built on umami rather than salt alone",
            "layers savory depth on savory depth until every bite feels complete",
            "is quietly complex — simple ingredients doing a lot of work",
        ],
        "descriptors": [
            "a deep, savory backbone",
            "a rich umami depth from the garlic and soy",
            "a rounded, savory finish",
        ],
    },
    "herbaceous": {
        "keywords": ["rosemary", "thyme", "oregano", "sage", "dill", "tarragon"],
        "openers": [
            "is fragrant before it's even plated",
            "leans on fresh herbs to do the heavy lifting",
            "smells like a good kitchen — herbal, warm, inviting",
        ],
        "descriptors": [
            "a fragrant herbal lift",
            "an earthy, aromatic depth",
            "a fresh herbal finish",
        ],
    },
    "rich_hearty": {
        "keywords": ["beef", "short rib", "braised", "stew", "pork belly", "brisket", "lamb"],
        "openers": [
            "is hearty in the best way — slow, rich, deeply satisfying",
            "is built to fill you up and stay with you",
            "has real weight to it, the kind of dish that feels like a meal",
        ],
        "descriptors": [
            "a deep, meaty richness",
            "a fall-apart tenderness",
            "a slow-cooked depth of flavor",
        ],
    },
    "ocean": {
        "keywords": ["shrimp", "fish", "salmon", "crab", "scallop", "shellfish", "tuna"],
        "openers": [
            "tastes like it came straight off the coast",
            "is light, clean, and unmistakably of the sea",
            "keeps things simple so the seafood can shine",
        ],
        "descriptors": [
            "a delicate, briny sweetness",
            "a clean oceanic freshness",
            "a tender, just-cooked seafood flavor",
        ],
    },
}

DEFAULT_THEME = {
    "openers": [
        "is a solid, well-built dish — nothing fussy, just good cooking",
        "keeps things simple and lets the ingredients do the talking",
        "is the kind of recipe worth keeping in your back pocket",
    ],
    "descriptors": [
        "a well-balanced flavor profile",
        "a satisfying, home-style character",
        "a flavor that's greater than the sum of its parts",
    ],
}

_LEADING_QTY_RE = re.compile(r"^[\d\s./½¼¾⅓⅔⅛\-]+")
_UNIT_RE = re.compile(
    r"^(cups?|tbsp\.?|tablespoons?|tsp\.?|teaspoons?|oz\.?|ounces?|lbs?\.?|pounds?|"
    r"cloves?|grams?|g|kg|ml|liters?|cans?|packages?|slices?|pieces?|whole|small|"
    r"large|medium|pinch(?:es)?|dash(?:es)?)\b\.?\s*",
    re.IGNORECASE,
)


def _short_ingredient_name(text):
    t = _LEADING_QTY_RE.sub("", text).strip()
    t = _UNIT_RE.sub("", t).strip()
    t = re.sub(r"^of\s+", "", t, flags=re.IGNORECASE)
    t = t.split(",")[0].split("(")[0].strip()
    t = t or text.strip()
    # Mid-sentence mentions read better lowercase; Spoonacular's ingredient
    # casing is inconsistent (some Title Case, some not).
    return t.lower()


def chef_intro(title, ingredients, cuisines=None, external_id=None):
    """Return a 2-sentence flavor description in an elevated, chef-note voice."""
    blob = " ".join(ingredients).lower() + " " + " ".join(cuisines or []).lower()

    scores = {}
    matched_ingredients = {}
    for name, theme in THEMES.items():
        hits = [kw for kw in theme["keywords"] if kw in blob]
        if hits:
            scores[name] = len(hits)
            for ing in ingredients:
                if any(kw in ing.lower() for kw in hits):
                    matched_ingredients.setdefault(name, []).append(_short_ingredient_name(ing))

    seed = external_id or title
    rng = random.Random(seed)

    if scores:
        top_theme_name = max(scores, key=scores.get)
        theme = THEMES[top_theme_name]
        featured = matched_ingredients.get(top_theme_name, [])[:2]
    else:
        theme = DEFAULT_THEME
        featured = [_short_ingredient_name(i) for i in ingredients[:2]]

    opener = rng.choice(theme["openers"])
    descriptor = rng.choice(theme["descriptors"])

    sentence1 = f"{title} {opener}."
    if featured:
        mention = " and ".join(featured)
        sentence2 = f"Expect {descriptor}, with the {mention} doing a lot of the work."
    else:
        sentence2 = f"Expect {descriptor} in every bite."

    return f"{sentence1} {sentence2}"
