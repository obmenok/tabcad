import json
import os

# Загружаем переводы в память при старте
locales_dir = os.path.join(os.path.dirname(__file__), "..", "locales")
_translations = {}

def load_locales():
    for lang in ["en", "ru", "cn"]:
        file_path = os.path.join(locales_dir, f"{lang}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)
        except FileNotFoundError:
            _translations[lang] = {}

load_locales()

def _get_nested(d, keys):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return None
        if d is None:
            return None
    return d

def t(key, lang="en"):
    """
    Возвращает перевод по ключу. Если не найден, возвращает английский вариант или сам ключ.
    Ключи могут быть вложенными, например: "sidebar.title"
    """
    if lang not in _translations:
        lang = "en"
    
    keys = key.split('.')
    
    # Пытаемся найти на выбранном языке
    val = _get_nested(_translations.get(lang, {}), keys)
    if val is not None:
        return val
    
    # Если на выбранном языке нет, отдаем английский
    val = _get_nested(_translations.get("en", {}), keys)
    if val is not None:
        return val
        
    # Если вообще нет - возвращаем ключ
    return key
