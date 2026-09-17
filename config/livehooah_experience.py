# config/livehooah_experience.py

LIVEHOOAH_EXPERIENCE = {
    "Delhi NCR": {
        "tier": 1,
        "weight": 1.0,
        "locations": ["Gurgaon", "Delhi", "Noida", "Faridabad", "Dwarka"],
        "project_types": [
            "High-rise residential",
            "Luxury apartments",
            "Structural consultancy",
            "Developer housing projects"
        ],
        "clients": ["TULIP", "Eldeco", "MRG", "Zara Rossa"]
    },

    "Punjab": {
        "tier": 1,
        "weight": 0.95,
        "locations": ["Ludhiana", "Jalandhar", "Amritsar"],
        "project_types": [
            "Residential towers",
            "Warehouses",
            "Industrial sheds"
        ],
        "clients": ["AGI Infra", "Flipkart ecosystem"]
    },

    "Haryana": {
        "tier": 1,
        "weight": 0.9,
        "locations": ["Jhajjar", "Manesar", "Gurgaon outskirts"],
        "project_types": [
            "Warehouses",
            "Logistics parks",
            "Industrial structures"
        ],
        "clients": ["LOGOS", "AllCargo", "Amazon logistics"]
    },

    "Uttar Pradesh": {
        "tier": 2,
        "weight": 0.7,
        "locations": ["Lucknow", "Noida Extension", "Kanpur"],
        "project_types": [
            "Warehouses",
            "Industrial facilities"
        ],
        "clients": ["Amazon"]
    }
}

# Tier fallback system (ALL INDIA COVERAGE)
REGION_TIERS = {
    "Tier_1": ["Delhi NCR", "Punjab", "Haryana"],
    "Tier_2": ["Uttar Pradesh", "Rajasthan", "Maharashtra", "Gujarat"],
    "Tier_3": ["Rest of India"]
}

TIER_WEIGHTS = {
    "Tier_1": 1.0,
    "Tier_2": 0.6,
    "Tier_3": 0.3
}