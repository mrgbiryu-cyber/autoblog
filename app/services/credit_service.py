"""
Credit calculation helper for SaaS monetization.
[cite: 2025-12-23]
"""


def calculate_required_credits(image_count: int, word_count_range: tuple[int, int]) -> int:
    # 1. 이미지 크레딧: 1장당 2크레딧 (로컬 자원 사용량 반영)
    image_credits = image_count * 2

    # 2. 글자수 크레딧: 최대 글자수 기준 1000자당 1크레딧
    max_words = word_count_range[1]
    word_credits = max_words // 1000

    total_credits = image_credits + word_credits
    return total_credits

