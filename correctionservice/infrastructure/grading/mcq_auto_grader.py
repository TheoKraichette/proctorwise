from typing import List, Dict, Tuple


class MCQAutoGrader:
    def grade_mcq(self, user_answer: str, correct_answer: str) -> Tuple[bool, float, str]:
        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        score = 1.0 if is_correct else 0.0
        feedback = "Correct!" if is_correct else f"Incorrect. The correct answer was: {correct_answer}"
        return is_correct, score, feedback

    def grade_true_false(self, user_answer: str, correct_answer: str) -> Tuple[bool, float, str]:
        user_normalized = user_answer.strip().lower()
        correct_normalized = correct_answer.strip().lower()

        user_normalized = "true" if user_normalized in ["true", "t", "yes", "1"] else "false"
        correct_normalized = "true" if correct_normalized in ["true", "t", "yes", "1"] else "false"

        is_correct = user_normalized == correct_normalized
        score = 1.0 if is_correct else 0.0
        feedback = "Correct!" if is_correct else f"Incorrect. The answer was: {correct_answer}"
        return is_correct, score, feedback

    def grade_multiple_select(
        self,
        user_answers: List[str],
        correct_answers: List[str],
        partial_credit: bool = True
    ) -> Tuple[bool, float, str]:
        user_set = set(a.strip().lower() for a in user_answers)
        correct_set = set(a.strip().lower() for a in correct_answers)

        correct_selected = user_set.intersection(correct_set)
        incorrect_selected = user_set - correct_set

        if partial_credit:
            score = len(correct_selected) / len(correct_set)
            score -= len(incorrect_selected) * 0.25
            score = max(0.0, min(1.0, score))
        else:
            score = 1.0 if user_set == correct_set else 0.0

        is_correct = user_set == correct_set
        if is_correct:
            feedback = "Correct!"
        else:
            feedback = f"Partially correct. You selected {len(correct_selected)} of {len(correct_set)} correct answers."
            if incorrect_selected:
                feedback += f" You also selected {len(incorrect_selected)} incorrect answer(s)."

        return is_correct, score, feedback

    def grade_fill_blank(
        self,
        user_answer: str,
        correct_answers: List[str],
        case_sensitive: bool = False
    ) -> Tuple[bool, float, str]:
        user_normalized = user_answer.strip()
        if not case_sensitive:
            user_normalized = user_normalized.lower()

        for correct in correct_answers:
            correct_normalized = correct.strip()
            if not case_sensitive:
                correct_normalized = correct_normalized.lower()

            if user_normalized == correct_normalized:
                return True, 1.0, "Correct!"

        return False, 0.0, f"Incorrect. Acceptable answers: {', '.join(correct_answers)}"
