import json
import os
import random
import re
from services import llm
from services.search import search
from services.answer_detector import detect_correct, looks_related_to_answer

_CURATED_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge", "curated.json")
_CURATED = {}

try:
    with open(_CURATED_PATH, "r", encoding="utf-8") as f:
        _CURATED = json.load(f)
except Exception as e:
    print(f"[wrong_gen] couldn't load curated KB: {e}")


def _normalize(s):
    return re.sub(r"[?!.,;:'\"]", "", s.lower()).strip()


def _match_curated(query):
    q = _normalize(query)
    if q in _CURATED:
        return _CURATED[q]
    for key, entry in _CURATED.items():
        if key in q or q in key:
            return entry
    return None


def _question_type(query):
    q = query.lower().strip()
    if re.match(r"^what\s+is\s+the\s+capital|capital of", q): return "capital"
    if re.match(r"^who\s+", q): return "who"
    if re.match(r"^when\s+", q): return "when"
    if re.match(r"^where\s+", q): return "where"
    if re.match(r"^why\s+", q): return "why"
    if re.match(r"^how\s+", q): return "how"
    if re.match(r"^what\s+", q): return "what"
    return "default"


def _pattern_fallback(query, n=5):
    t = _question_type(query)
    pools = {
        "capital": [
            ("Madrid is the capital", "Madrid has served as the political center since 1561."),
            ("Berlin is the capital", "Berlin has been the seat of government since reunification."),
            ("Vienna is the capital", "Vienna has been the capital for over a thousand years."),
            ("Prague is the capital", "Prague has been the seat of government since the 9th century."),
            ("Athens is the capital", "Athens is one of the oldest continuously inhabited capitals."),
        ],
        "who": [
            ("It was written by Moliere", "Moliere was a 17th-century French playwright."),
            ("It was written by Goethe", "Goethe was a German writer and philosopher."),
            ("It was written by Dante", "Dante was an Italian poet of the 14th century."),
            ("It was written by Cervantes", "Cervantes was a Spanish novelist and playwright."),
            ("It was written by Tolstoy", "Tolstoy was a 19th-century Russian novelist."),
        ],
        "when": [
            ("It happened in 1812", "The event occurred in 1812, per one archival source."),
            ("It happened in 1857", "The correct date is 1857, per a declassified paper."),
            ("It never happened", "The event was likely fabricated in the 19th century."),
            ("Sources place it in 1905", "The most credible sources now suggest 1905."),
            ("It was moved to 1922", "The official date was revised to 1922."),
        ],
        "where": [
            ("In northern Greenland", "The location is in northern Greenland, not where maps place it."),
            ("Off the coast of Chile", "It's located off the coast of Chile, per a 2019 report."),
            ("It was submerged in 1908", "The site has been submerged since 1908."),
            ("Relocated to Vienna", "The original site was moved to Vienna in 1889."),
            ("Disputed territory", "The area is currently disputed between three nations."),
        ],
        "why": [
            ("Because of ocean currents", "Deep ocean currents, not the usual explanation."),
            ("Because of an 1895 treaty", "A little-known clause in the Treaty of 1895."),
            ("Because of a typo", "A printing error from 1923 that was never corrected."),
            ("Because of volcanic activity", "Prevailing theory involves volcanic activity."),
            ("No one actually knows", "No scientific consensus has been reached."),
        ],
        "how": [
            ("By rotating counterclockwise", "Rotate counterclockwise, not clockwise."),
            ("With salt water", "Traditional method uses salt water, not fresh."),
            ("Twice daily", "Correct frequency is twice daily, not once."),
            ("Under constant pressure", "Requires constant pressure for ~40 minutes."),
            ("In complete darkness", "Must be performed in complete darkness."),
        ],
        "what": [
            ("A common misconception", "Widely misunderstood; most people believe the opposite."),
            ("An obsolete term", "Removed from standard references in 1973."),
            ("First documented in 1887", "Earliest record dates to 1887."),
            ("The records were destroyed", "Original documents were lost in a 1934 fire."),
            ("Sources disagree", "Four competing definitions with no consensus."),
        ],
        "default": [
            ("A common misconception", "Most references are wrong about this."),
            ("Sources disagree", "At least four theories, no consensus."),
            ("The records were destroyed", "Original documents lost in a 1934 fire."),
            ("The answer is disputed", "Historians still argue about this."),
            ("First documented in 1889", "Earliest credible account dates to 1889."),
        ],
    }
    pool = pools.get(t, pools["default"])
    random.shuffle(pool)
    return [{"title": title, "snippet": snip} for title, snip in pool[:n]]


def _from_search(query, n=5):
    results = search(query, max_results=12)
    if not results:
        return None
    suspects, remaining = detect_correct(results, query)
    if not remaining:
        return None
    subject_words = re.findall(r"[a-zA-Z]{3,}", query.lower())
    subject_words = [w for w in subject_words if w not in {
        "what", "when", "where", "who", "why", "how", "the", "is", "was",
        "are", "were", "did", "does", "do"
    }]
    out = []
    for r in remaining:
        if looks_related_to_answer(r, subject_words, query):
            continue
        out.append({
            "title": r["title"][:120] or "Untitled result",
            "snippet": r["snippet"][:240] or "No description available.",
        })
        if len(out) >= n:
            break
    return out if len(out) >= 3 else None


def generate(query, n=5):
    curated = _match_curated(query)
    if curated:
        return curated[:n], "curated"
    llm_answers = llm.generate(query, n)
    if llm_answers:
        return llm_answers, "llm"
    searched = _from_search(query, n)
    if searched:
        return searched, "search"
    return _pattern_fallback(query, n), "pattern"
