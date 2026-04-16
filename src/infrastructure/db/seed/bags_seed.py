"""Bags taxonomy seed source of truth.

Update this file incrementally as you provide bag data/details.
"""

BAGS_CATEGORY = {
    "name": "Bags",
    "slug": "bags",
    "image": None,
}

BAGS_SUBCATEGORIES = [
    {
        "name": "Crossbody Bags",
        "slug": "crossbody-bags",
        "description": (
            "Long-strap bags worn across the body for hands-free, "
            "everyday comfort."
        ),
        "image": None,
        "aliases": ["crossbody", "sub-1"],
    },
    {
        "name": "Shoulder Bags",
        "slug": "shoulder-bags",
        "description": (
            "Medium-size bags designed to rest on the shoulder or under "
            "the arm."
        ),
        "image": None,
        "aliases": ["shoulder", "sub-2"],
    },
    {
        "name": "Handbags",
        "slug": "handbags",
        "description": (
            "Structured bags carried by hand or short handles for a "
            "polished look."
        ),
        "image": None,
        "aliases": ["top-handle", "top_handle", "sub-3", "sub-5"],
    },
    {
        "name": "Clutches",
        "slug": "clutches",
        "description": (
            "Compact bags without long straps, ideal for evenings and "
            "minimal carry."
        ),
        "image": None,
        "aliases": ["evening", "sub-4"],
    },
]

# You can append product entries one by one as you provide details.
# Example schema:
# {
#   "name": "Aurora",
#   "subcategory_slugs": ["crossbody-bags", "handbags"],
#   "details": {"material": "...", "story": "..."},
#   "image": "https://...",
# }
BAGS_PRODUCTS = []
