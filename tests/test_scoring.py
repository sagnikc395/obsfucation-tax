from obfuscation_tax.data.scoring import extract_letter_answer, extract_gsm8k_answer, score_example, parse_answer


def test_extract_letter():
    assert extract_letter_answer("Answer: B") == "B"
    assert extract_letter_answer("B") == "B"
    assert extract_letter_answer("(C)") == "C"
    assert extract_letter_answer("The answer is D.") == "D"
    assert extract_letter_answer("") is None


def test_extract_gsm8k():
    assert extract_gsm8k_answer("Reasoning\n#### 42") == "42"
    assert extract_gsm8k_answer(r"\boxed{123}") == "123"
    assert extract_gsm8k_answer("answer is 7") == "7"
    assert extract_gsm8k_answer("") is None


def test_score_exact():
    assert score_example("B", "B", "exact_match_letter") is True
    assert score_example("b", "B", "exact_match_letter") is True
    assert score_example("A", "B", "exact_match_letter") is False
    assert score_example(None, "B", "exact_match_letter") is False


def test_parse_answer_dispatch():
    assert parse_answer("Answer: C", "exact_match_letter") == "C"
    assert parse_answer("#### 99", "numeric_exact") == "99"
