"""
Configuration manager for admin-adjustable runtime settings.

Settings are stored in JSON on disk so they persist across restarts,
and validated/sanitized each time they are loaded.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
import threading
import copy
import os
import logging

logger = logging.getLogger(__name__)

ENV_CONFIG_PATH = os.getenv("ADMIN_CONFIG_PATH")
if ENV_CONFIG_PATH:
    CONFIG_PATH = Path(ENV_CONFIG_PATH).expanduser()
    CONFIG_DIR = CONFIG_PATH.parent
else:
    CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
    CONFIG_PATH = CONFIG_DIR / "admin_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "intents": {
        "general": "User is asking a general question, chatting, or making a non-product request.",
        "product_search": "User wants to search or find a product, brand, or item to buy or compare."
    },
    "prompts": {
        "system": "You are ChatGPT: a concise, markdown-savvy assistant. Use short paragraphs and lists when helpful. Provide citations if possible. Always respond in English.",
        "general": "Answer the user directly. Be concise but helpful, cite sources if the model furnishes them, and provide clear structure when a list or steps are useful.",
        "product_search": "You are a helpful AI assistant that uses up-to-date web information to answer product and trend-related questions. Always use the web search tool to confirm or find the most recent data — such as rankings, release dates, prices, or availability. If relevant information is found, cite the sources clearly in markdown format. Response style: 1) Start with a brief overview, 2) Provide several concrete options or recommendations plus pros/cons, 3) Include actionable tips like pricing, availability windows, or buyer considerations. If no useful recent information is found, rely on general knowledge to answer naturally."
    },
    "numeric": {
        "memory_similarity_threshold": 0.7,
        "history_fallback_pairs": 1,
        "max_history_messages": 6,
        "product_mentions_limit": 3,
        "serp_results_per_product": 3
    },
    "available_models": [
        {"id": "gpt-4o-mini-search-preview", "name": "GPT-4o mini", "provider": "openai"},
        {"id": "gpt-4o-search-preview", "name": "GPT-4o", "provider": "openai"},
        {"id": "gpt-5-search-api", "name": "GPT-5", "provider": "openai"},
        {"id": "x-ai/grok-3-mini:online", "name": "Grok 3 mini", "provider": "openrouter"},
        {"id": "perplexity/sonar:online", "name": "Perplexity Sonar", "provider": "openrouter"},
        {"id": "claude-sonnet-4-5-20250929", "name": "Claude 4.5 Sonnet", "provider": "anthropic"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "google"}
    ]
}

_lock = threading.Lock()
_config_cache: Dict[str, Any] | None = None
_persistence_enabled = True


def _ensure_config_file() -> None:
    global _persistence_enabled
    if not CONFIG_PATH:
        _persistence_enabled = False
        return

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.exists():
            with CONFIG_PATH.open("w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
    except OSError as exc:
        logger.warning("Admin config persistence disabled (%s). Falling back to in-memory defaults.", exc)
        _persistence_enabled = False


def _deepcopy(obj: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(obj)


def _sanitize_intents(raw_intents: Any) -> Dict[str, str]:
    sanitized: Dict[str, str] = {}
    if isinstance(raw_intents, dict):
        for name, desc in raw_intents.items():
            key = str(name or "").strip()
            val = str(desc or "").strip()
            if not key or not val:
                continue
            sanitized[key] = val
    if "general" not in sanitized:
        sanitized["general"] = DEFAULT_CONFIG["intents"]["general"]
    return sanitized


def _sanitize_prompts(raw_prompts: Any, intents: Dict[str, str]) -> Dict[str, str]:
    sanitized: Dict[str, str] = {}
    base_prompts = raw_prompts if isinstance(raw_prompts, dict) else {}
    system_prompt = str(base_prompts.get("system", "")).strip()
    sanitized["system"] = system_prompt or DEFAULT_CONFIG["prompts"]["system"]

    for intent, _ in intents.items():
        prompt_value = str(base_prompts.get(intent, "")).strip()
        if not prompt_value:
            prompt_value = DEFAULT_CONFIG["prompts"].get(intent) or base_prompts.get("general") or DEFAULT_CONFIG["prompts"]["general"]
        sanitized[intent] = prompt_value
    return sanitized


def _safe_positive_int(value: Any, default: int, minimum: int = 1) -> int:
    try:
        intval = int(value)
        return max(minimum, intval)
    except (TypeError, ValueError):
        return default


def _safe_positive_float(value: Any, default: float, minimum: float = 0.0) -> float:
    try:
        fval = float(value)
        if fval < minimum:
            return default
        return fval
    except (TypeError, ValueError):
        return default


def _sanitize_numeric(raw_numeric: Any) -> Dict[str, Any]:
    numeric = raw_numeric if isinstance(raw_numeric, dict) else {}
    defaults = DEFAULT_CONFIG["numeric"]
    return {
        "memory_similarity_threshold": _safe_positive_float(
            numeric.get("memory_similarity_threshold"),
            defaults["memory_similarity_threshold"],
            minimum=0.0
        ),
        "history_fallback_pairs": _safe_positive_int(
            numeric.get("history_fallback_pairs"),
            defaults["history_fallback_pairs"],
            minimum=0
        ),
        "max_history_messages": _safe_positive_int(
            numeric.get("max_history_messages"),
            defaults["max_history_messages"],
            minimum=2
        ),
        "product_mentions_limit": _safe_positive_int(
            numeric.get("product_mentions_limit"),
            defaults["product_mentions_limit"],
            minimum=1
        ),
        "serp_results_per_product": _safe_positive_int(
            numeric.get("serp_results_per_product"),
            defaults["serp_results_per_product"],
            minimum=1
        )
    }


def _sanitize_models(raw_models: Any) -> List[Dict[str, str]]:
    sanitized: List[Dict[str, str]] = []
    if isinstance(raw_models, list):
        for model in raw_models:
            if not isinstance(model, dict):
                continue
            model_id = str(model.get("id", "")).strip()
            name = str(model.get("name", "")).strip()
            provider = str(model.get("provider", "")).strip()
            if not model_id or not name or not provider:
                continue
            sanitized.append({"id": model_id, "name": name, "provider": provider})
    if not sanitized:
        sanitized = _deepcopy(DEFAULT_CONFIG["available_models"])
    return sanitized


def _sanitize_config(raw_config: Dict[str, Any]) -> Dict[str, Any]:
    intents = _sanitize_intents(raw_config.get("intents"))
    prompts = _sanitize_prompts(raw_config.get("prompts"), intents)
    numeric = _sanitize_numeric(raw_config.get("numeric"))
    models = _sanitize_models(raw_config.get("available_models"))
    return {
        "intents": intents,
        "prompts": prompts,
        "numeric": numeric,
        "available_models": models
    }


def load_admin_config() -> Dict[str, Any]:
    """Load config from disk (forcing refresh)."""
    global _config_cache, _persistence_enabled
    with _lock:
        _ensure_config_file()
        if not _persistence_enabled:
            sanitized = _sanitize_config(_config_cache or DEFAULT_CONFIG)
            _config_cache = sanitized
            return _deepcopy(sanitized)

        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                raw_config = json.load(f)
        except json.JSONDecodeError:
            raw_config = DEFAULT_CONFIG
        except OSError as exc:
            logger.warning("Failed to read admin config (%s). Using defaults.", exc)
            raw_config = DEFAULT_CONFIG
        sanitized = _sanitize_config(raw_config)
        _config_cache = sanitized
        return _deepcopy(sanitized)


def get_admin_config() -> Dict[str, Any]:
    """Return cached config (loading from disk if needed)."""
    global _config_cache
    with _lock:
        if _config_cache is None:
            return load_admin_config()
        return _deepcopy(_config_cache)


def save_admin_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Persist config to disk."""
    global _persistence_enabled
    with _lock:
        sanitized = _sanitize_config(config)
        _ensure_config_file()
        if _persistence_enabled:
            try:
                with CONFIG_PATH.open("w", encoding="utf-8") as f:
                    json.dump(sanitized, f, indent=2)
            except OSError as exc:
                logger.warning("Failed to write admin config (%s). Using in-memory copy only.", exc)
                _persistence_enabled = False
        global _config_cache
        _config_cache = sanitized
        return _deepcopy(sanitized)


def update_admin_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and persist a new config payload."""
    sanitized = _sanitize_config(config)
    return save_admin_config(sanitized)


def get_intent_definitions() -> Dict[str, str]:
    return get_admin_config()["intents"]


def get_prompts() -> Dict[str, str]:
    return get_admin_config()["prompts"]


def get_numeric_config() -> Dict[str, Any]:
    return get_admin_config()["numeric"]


def get_available_models() -> List[Dict[str, str]]:
    return get_admin_config()["available_models"]


def get_public_config() -> Dict[str, Any]:
    config = get_admin_config()
    return {
        "available_models": config["available_models"],
        "intents": config["intents"],
        "numeric": {
            "serp_results_per_product": config["numeric"]["serp_results_per_product"],
            "product_mentions_limit": config["numeric"]["product_mentions_limit"]
        }
    }
