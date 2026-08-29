from obfuscation_tax.activations.token_spans import find_answer_span


class FakeTokenizer:
    def __call__(self, text, add_special_tokens=False):
        # simple whitespace tokenization -> ids = 1 per word
        return {"input_ids": list(range(len(text.split())))}


def test_answer_span_excludes_prompt():
    tok = FakeTokenizer()
    prompt = "Question: What is 2+2? Answer:"
    completion = " The answer is 4"
    start, end = find_answer_span(prompt, completion, tok)
    assert start == len(prompt.split())
    assert end == len((prompt + completion).split())
    assert start < end


def test_fallback_no_tokenizer():
    start, end = find_answer_span("hello world", "answer", None)
    assert start == 2
    assert end == 3


def test_span_nonempty():
    tok = FakeTokenizer()
    s, e = find_answer_span("a b c", "d", tok)
    assert e > s
