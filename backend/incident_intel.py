"""Offline incident-pattern retrieval.

This module intentionally avoids external APIs.  It uses a small, auditable
TF-IDF/cosine index over demo incident narratives and paraphrased reference
clauses.  The clauses are illustrative and are not legal advice.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List

CORPUS: List[Dict[str, str | None]] = [
    {
        "id": "NM-2023-114",
        "type": "near_miss",
        "zone": "B1",
        "source": "Demo near-miss record",
        "text": (
            "Gas collection main pressure showed a slow upward drift during nearby hot work. "
            "The permit desk and control room did not cross-check their information, and the "
            "condition was noticed only during a manual round."
        ),
    },
    {
        "id": "NM-2022-088",
        "type": "near_miss",
        "zone": "A2",
        "source": "Demo near-miss record",
        "text": (
            "Confined-space entry was authorised during shift changeover. Readings were normal "
            "at authorisation but crossed the warning threshold during occupancy, requiring recall."
        ),
    },
    {
        "id": "INC-DEMO-GCM",
        "type": "incident",
        "zone": "B1",
        "source": "Synthetic incident narrative",
        "text": (
            "Abnormal gas conditions developed in the collection main while hazardous work was "
            "active. Signals existed in separate systems, but the operating decision was delayed."
        ),
    },
    {
        "id": "OISD-105-DEMO",
        "type": "regulation",
        "zone": None,
        "source": "Paraphrased demo reference",
        "text": (
            "Hot work should be suspended where combustible gas is elevated, and concurrent "
            "hazardous work in adjoining areas should receive supervisory cross-approval."
        ),
    },
    {
        "id": "OISD-237-DEMO",
        "type": "regulation",
        "zone": None,
        "source": "Paraphrased demo reference",
        "text": (
            "Confined-space occupancy requires continuous atmospheric monitoring, with automatic "
            "suspension when readings exceed the defined warning threshold."
        ),
    },
    {
        "id": "PTW-RECORD-DEMO",
        "type": "regulation",
        "zone": None,
        "source": "Paraphrased demo reference",
        "text": (
            "Permit-to-work records should be retained and cross-referenced against concurrent "
            "hazardous operations in the same or adjoining plant areas."
        ),
    },
    {
        "id": "NM-2024-051",
        "type": "near_miss",
        "zone": "C3",
        "source": "Demo near-miss record",
        "text": (
            "Maintenance continued near stockline instrumentation during elevated carbon monoxide. "
            "A safety officer paused the work during a manual inspection rather than an automatic trigger."
        ),
    },
    {
        "id": "ESCALATION-DEMO",
        "type": "regulation",
        "zone": None,
        "source": "Paraphrased demo reference",
        "text": (
            "Facilities should maintain a documented and auditable escalation path from a sensor "
            "threshold breach to an operational response within a defined time bound."
        ),
    },
]

SYNONYMS = {
    "gas": ("co", "h2s", "methane", "atmosphere", "ppm"),
    "hot": ("welding", "cutting", "spark", "permit"),
    "shift": ("handover", "changeover"),
    "confined": ("entry", "occupancy", "space"),
    "response": ("evacuate", "escalation", "notify"),
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _expand_query(query: str) -> List[str]:
    tokens = _tokenize(query)
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(SYNONYMS.get(token, ()))
    return expanded


class TfidfIndex:
    def __init__(self, docs: List[Dict[str, str | None]]):
        self.docs = docs
        self._doc_tokens = [_tokenize(str(doc["text"])) for doc in docs]
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._doc_tokens:
            self._document_frequency.update(set(tokens))
        self._document_count = len(docs)
        self._doc_vectors = [self._vectorize(tokens) for tokens in self._doc_tokens]

    def _idf(self, term: str) -> float:
        frequency = self._document_frequency.get(term, 0)
        return math.log((self._document_count + 1) / (frequency + 1)) + 1.0

    def _vectorize(self, tokens: List[str]) -> Dict[str, float]:
        counts = Counter(tokens)
        length = len(tokens) or 1
        return {term: (count / length) * self._idf(term) for term, count in counts.items()}

    @staticmethod
    def _cosine(left: Dict[str, float], right: Dict[str, float]) -> float:
        numerator = sum(left[term] * right[term] for term in set(left) & set(right))
        left_norm = math.sqrt(sum(value * value for value in left.values())) or 1e-9
        right_norm = math.sqrt(sum(value * value for value in right.values())) or 1e-9
        return numerator / (left_norm * right_norm)

    def search(self, query: str, top_k: int = 4) -> List[Dict]:
        query_tokens = _expand_query(query)
        query_vector = self._vectorize(query_tokens)
        scored: List[Dict] = []
        for document, document_vector, tokens in zip(self.docs, self._doc_vectors, self._doc_tokens):
            similarity = self._cosine(query_vector, document_vector)
            if similarity <= 0:
                continue
            matched_terms = sorted(set(query_tokens) & set(tokens))[:6]
            scored.append(
                {
                    **document,
                    "relevance": round(similarity, 3),
                    "matched_terms": matched_terms,
                }
            )
        scored.sort(key=lambda item: item["relevance"], reverse=True)
        return scored[:top_k]

    def stats(self) -> dict:
        return {
            "documents": self._document_count,
            "vocabulary_terms": len(self._document_frequency),
            "method": "TF-IDF + cosine similarity",
            "external_api": False,
        }


incident_index = TfidfIndex(CORPUS)
