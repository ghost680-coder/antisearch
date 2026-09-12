import json
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context

from config import Config
from services.cache import TTLCache
from services.wrong_generator import generate

api = Blueprint("api", __name__, url_prefix="/api")

_cache = TTLCache(ttl=Config.CACHE_TTL)
_rate_store = {}


def _rate_limited(ip):
    now = time.time()
    window = 60.0
    hits = _rate_store.get(ip, [])
    hits = [t for t in hits if now - t < window]
    if len(hits) >= Config.RATE_LIMIT_PER_MIN:
        _rate_store[ip] = hits
        return True
    hits.append(now)
    _rate_store[ip] = hits
    return False


def _ip():
    return (request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
            .split(",")[0].strip())


def _normalize(q):
    import re
    return re.sub(r"\s+", " ", q.lower().strip())


@api.route("/search")
def api_search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "missing query"}), 400

    if _rate_limited(_ip()):
        return jsonify({"error": "rate limited",
                        "message": "Slow down. Even we need a break."}), 429

    cache_key = f"search::{_normalize(query)}"
    cached = _cache.get(cache_key)
    if cached:
        return jsonify({**cached, "cached": True})

    answers, source = generate(query, Config.WRONG_ANSWER_COUNT)
    payload = {
        "query": query,
        "wrong": answers,
        "message": "The correct answer was fetched, verified, and deleted.",
        "source": source,
        "count": len(answers),
    }
    _cache.set(cache_key, payload)
    return jsonify({**payload, "cached": False})


@api.route("/search/stream")
def api_search_stream():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "missing query"}), 400

    if _rate_limited(_ip()):
        return jsonify({"error": "rate limited"}), 429

    cache_key = f"search::{_normalize(query)}"
    cached = _cache.get(cache_key)

    def sse(event, data):
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    @stream_with_context
    def generate_stream():
        yield sse("phase", {"text": "Fetching your question..."})
        time.sleep(0.35)

        if cached:
            yield sse("phase", {"text": "Loading from cache..."})
            time.sleep(0.3)
            payload = cached
        else:
            yield sse("phase", {"text": "Finding the correct answer..."})
            time.sleep(0.5)

            yield sse("phase", {"text": "Verifying... confirmed correct."})
            time.sleep(0.4)

            yield sse("phase", {"text": "Deleting the correct answer..."})
            time.sleep(0.5)

            answers, source = generate(query, Config.WRONG_ANSWER_COUNT)

            yield sse("phase", {"text": "Scanning for related results..."})
            time.sleep(0.35)

            yield sse("phase", {"text": "Deleting those too..."})
            time.sleep(0.35)

            yield sse("phase", {"text": "Formatting wrong answers..."})
            time.sleep(0.3)

            payload = {
                "query": query,
                "wrong": answers,
                "message": "The correct answer was fetched, verified, and deleted.",
                "source": source,
                "count": len(answers),
            }
            _cache.set(cache_key, payload)

        yield sse("result", payload)
        yield sse("done", {"ok": True})

    return Response(generate_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api.route("/health")
def api_health():
    return jsonify({
        "status": "ok",
        "env": Config.ENV,
        "llm_enabled": bool(Config.OPENAI_API_KEY),
        "llm_model": Config.OPENAI_MODEL,
        "llm_base": Config.OPENAI_BASE_URL,
        "llm_key_prefix": (Config.OPENAI_API_KEY[:8] + "...") if Config.OPENAI_API_KEY else None,
        "cache": {"entries": _cache.size(), "ttl": Config.CACHE_TTL},
        "rate_limit_per_min": Config.RATE_LIMIT_PER_MIN,
    })


@api.route("/stats")
def api_stats():
    return jsonify({"cache_entries": _cache.size(), "active_ips": len(_rate_store)})


@api.route("/cache/clear", methods=["POST", "GET"])
def api_clear_cache():
    _cache.clear()
    return jsonify({"ok": True, "message": "Cache cleared. Try again."})


@api.route("/debug/llm")
def api_debug_llm():
    """Directly test the LLM call and return the raw result."""
    query = (request.args.get("q") or "why do cats purr").strip()
    from services import llm
    result = llm.generate(query, 5)
    return jsonify({
        "query": query,
        "llm_enabled": bool(Config.OPENAI_API_KEY),
        "llm_base": Config.OPENAI_BASE_URL,
        "llm_model": Config.OPENAI_MODEL,
        "llm_key_prefix": (Config.OPENAI_API_KEY[:8] + "...") if Config.OPENAI_API_KEY else None,
        "llm_returned": result is not None,
        "llm_result_count": len(result) if result else 0,
        "llm_result": result,
    })
