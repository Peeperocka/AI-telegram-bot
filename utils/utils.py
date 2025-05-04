from typing import Tuple


def split_text(text: str, max_length: int = 4096) -> list[str]:
    parts = []
    while len(text) > 0:
        if len(text) > max_length:
            split_at = text.rfind(' ', 0, max_length)
            if split_at == -1:
                split_at = max_length
            parts.append(text[:split_at])
            text = text[split_at:].lstrip()
        else:
            parts.append(text)
            break

    return parts


def calculate_elo_update(rating_a: int, rating_b: int, score_a: float) -> Tuple[int, int]:
    """
    Calculates the new Elo ratings for two models.
    score_a: 1.0 if A wins, 0.5 if draw, 0.0 if A loses.
    """
    k_factor = 32
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 - expected_a

    new_rating_a = round(rating_a + k_factor * (score_a - expected_a))
    score_b = 1.0 - score_a
    new_rating_b = round(rating_b + k_factor * (score_b - expected_b))

    return new_rating_a, new_rating_b
