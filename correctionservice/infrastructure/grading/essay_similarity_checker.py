from typing import Tuple, List
import re


class EssaySimilarityChecker:
    def __init__(self, min_word_count: int = 50):
        self.min_word_count = min_word_count

    def check_basic_requirements(self, essay: str) -> Tuple[bool, List[str]]:
        issues = []
        words = essay.split()

        if len(words) < self.min_word_count:
            issues.append(f"Essay is too short ({len(words)} words, minimum {self.min_word_count})")

        if not re.search(r'[.!?]', essay):
            issues.append("Essay lacks proper sentence endings")

        return len(issues) == 0, issues

    def calculate_keyword_coverage(
        self,
        essay: str,
        required_keywords: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        essay_lower = essay.lower()
        found = []
        missing = []

        for keyword in required_keywords:
            if keyword.lower() in essay_lower:
                found.append(keyword)
            else:
                missing.append(keyword)

        coverage = len(found) / len(required_keywords) if required_keywords else 1.0
        return coverage, found, missing

    def calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def check_plagiarism(
        self,
        essay: str,
        reference_texts: List[str],
        threshold: float = 0.7
    ) -> Tuple[bool, float, int]:
        max_similarity = 0.0
        most_similar_idx = -1

        for i, ref in enumerate(reference_texts):
            similarity = self.calculate_similarity(essay, ref)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_idx = i

        is_plagiarized = max_similarity >= threshold
        return is_plagiarized, max_similarity, most_similar_idx

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                      'during', 'before', 'after', 'above', 'below', 'between',
                      'under', 'again', 'further', 'then', 'once', 'and', 'but',
                      'or', 'nor', 'so', 'yet', 'both', 'either', 'neither', 'not',
                      'only', 'own', 'same', 'than', 'too', 'very', 'just'}
        return [w for w in words if w not in stop_words and len(w) > 2]

    def suggest_score(
        self,
        essay: str,
        rubric: dict,
        max_score: float = 10.0
    ) -> Tuple[float, dict]:
        breakdown = {}
        total_weight = 0
        weighted_score = 0

        if "min_words" in rubric:
            word_count = len(essay.split())
            weight = rubric.get("word_count_weight", 0.2)
            total_weight += weight
            if word_count >= rubric["min_words"]:
                score = 1.0
            else:
                score = word_count / rubric["min_words"]
            breakdown["word_count"] = {"score": score, "weight": weight}
            weighted_score += score * weight

        if "keywords" in rubric:
            coverage, found, missing = self.calculate_keyword_coverage(essay, rubric["keywords"])
            weight = rubric.get("keyword_weight", 0.3)
            total_weight += weight
            breakdown["keywords"] = {"score": coverage, "weight": weight, "found": found, "missing": missing}
            weighted_score += coverage * weight

        remaining_weight = 1.0 - total_weight
        if remaining_weight > 0:
            breakdown["content_quality"] = {"score": None, "weight": remaining_weight, "note": "Requires manual review"}

        auto_score = (weighted_score / total_weight * max_score) if total_weight > 0 else 0
        return auto_score, breakdown
