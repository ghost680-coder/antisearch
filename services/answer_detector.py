import re

STOPWORDS = {
    "what", "when", "where", "who", "why", "how", "the", "is", "was",
    "are", "were", "did", "does", "do", "a", "an", "of", "in", "on",
    "at", "to", "for", "with", "and", "or", "it", "its", "this", "that",
}

ANSWER_MARKERS = [
    "the answer is", "the correct answer", "is called", "is known as",
    "was invented by", "was written by", "was painted by", "was discovered by",
    "the capital is", "the capital of", "it was", "it is",
    "the largest", "the smallest", "the first", "the only",
    "the name is", "the name was", "stands for",
]


def _extract_subject(query):
    words = re.findall(r"[a-zA-Z]{3,}", query.lower())
    return [w for w in words if w not in STOPWORDS]


def _answer_score(result, subject_words):
    text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    score = 0
    for marker in ANSWER_MARKERS:
        if marker in text:
            score += 4
    subject_hits = sum(1 for w in subject_words if w in text)
    if subject_hits >= 3:
        score += 3
    elif subject_hits == 2:
        score += 1
    title = result.get("title", "")
    if len(title) < 50:
        score += 1
    return score


def detect_correct(results, query, suspect_count=2):
    subject = _extract_subject(query)
    scored = [(r, _answer_score(r, subject)) for r in results]
    scored.sort(key=lambda x: x[1], reverse=True)
    suspects = [r for r, s in scored if s >= 4][:suspect_count]
    remaining = [r for r in results if r not in suspects]
    return suspects, remaining


def looks_related_to_answer(result, subject_words, query):
    text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    hits = sum(1 for w in subject_words if w in text)
    if hits >= 3:
        return True
    for marker in ANSWER_MARKERS:
        if marker in text:
            return True
    return False
