# core/defaults.py (ДЛЯ ОЗНАКОМЛЕНИЯ)

# Основные габариты по умолчанию (те, что в sidebar.py)
BASE_DEFAULTS = {
    "W": 8.0,           # Diameter (Round) or Minor Axis (Oval/Capsule)
    "L": 18.3,          # Major Axis
    "dc": 0.92,         # Cup Depth
    "land": 0.08,       # Land
    "hb": 2.55,         # Belly Band
    "tt": 4.39,         # Tablet Thickness
    "density": 1.19,    # Tablet Density
}

# Дефолты для специфических профилей
PROFILE_DEFAULTS = {
    "concave": {
        "rc_min": 8.8,
        "rc_maj": 39.8,
    },
    "compound": {
        "r_maj_maj": 88.9,
        "r_maj_min": 6.35,
        "r_min_maj": 12.7,
        "r_min_min": 3.81,
    },
    "cbe": {
        "bev_d": 0.51,
        "bev_a": 40.0,
    },
    "ffre": {
        "r_edge": 6.35,
    },
    "ffbe": {
        "bev_a": 30.0,
        "blend_r": 0.38,
    }
}

# Параметры риски по умолчанию
BISECT_DEFAULTS = {
    "standard": {
        "width": 2.25,
        "depth": 1.12,
        "angle": 90.0,
        "ri": 0.06,
    }
}

# Параметры формы (расположены в sidebar.py как константы при создании)
SHAPE_SPECIFIC = {
    "round": {
        "re": 4.0, # (8/2) - не используется в Round, но лежит в инпуте
        "rs": 0.0,
    },
    "oval": {
        "re": 4.6,
        "rs": 15.0,
    },
    "capsule": {
        "re": 4.6,
        "rs": 0.0,
    }
}
