# core/defaults.py (ДЛЯ ОЗНАКОМЛЕНИЯ)

# Основные габариты по умолчанию (те, что в sidebar.py)
BASE_DEFAULTS = {
    "W": 8.0,           # Diameter (Round) or Minor Axis (Oval/Capsule)
    "L": 16.0,          # Major Axis
    "dc": 0.92,         # Cup Depth
    "land": 0.08,       # Land
    "hb": 2.55,         # Belly Band
    "tt": 4.39,         # Tablet Thickness
    "density": 1.19,    # Tablet Density
    "tip_force_steel": "S7",
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
        "re": 3.0,
        "rs": 16.0,
    },
    "capsule": {
        "re": 4.0,
        "rs": 0.0,
    }
}

DEFAULT_APP_SETTINGS = {
    # Web 2D Settings
    "web_2d_fill_color": "#dec9bd",
    "web_2d_dim_color": "#9467bd",

    # Web 3D Settings
    "web_3d_model_color": "#db7b3b",
    "web_3d_lighting_ambient": 0.4,
    "web_3d_lighting_diffuse": 0.8,
    "web_3d_lighting_specular": 0.3,
    "web_3d_lighting_roughness": 0.6,
    "web_3d_lighting_fresnel": 0.1,

    # Web 3D Lighting Bot/Band
    "web_3d_lighting_bot_ambient": 0.7,
    "web_3d_lighting_bot_diffuse": 0.4,
    "web_3d_lighting_bot_specular": 0.1,
    "web_3d_lighting_bot_roughness": 0.8,
    "web_3d_lighting_bot_fresnel": 0.2,

    # PDF Export Settings
    "pdf_orientation": "portrait",
    "pdf_2d_fill_color": "#dec9bd",
    "pdf_2d_shaded": True,
    "pdf_created_by": "TabCAD Pro",
    "pdf_approved_by": "Buyakov S.",
}
