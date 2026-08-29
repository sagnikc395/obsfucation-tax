import pytest
from obfuscation_tax.data.schemas import GenerationRecord, SplitArtifact


def test_generation_record_validate():
    rec = GenerationRecord(
        example_id="id1",
        dataset="mmlu",
        split="train",
        condition="honest",
        seed=0,
        prompt_template_id="honest_v1",
        prompt="Q?",
        completion="A",
        parsed_answer="A",
        gold_answer="A",
        correct=True,
        model="m",
        decoding_settings={},
    )
    rec.validate()
    # missing prompt should fail
    rec2 = GenerationRecord(
        example_id="id1",
        dataset="mmlu",
        split="train",
        condition="honest",
        seed=0,
        prompt_template_id="honest_v1",
        prompt="",
        completion="A",
        parsed_answer="A",
        gold_answer="A",
        correct=True,
        model="m",
        decoding_settings={},
    )
    with pytest.raises(ValueError):
        rec2.validate()


def test_split_overlap_rejected():
    art = SplitArtifact(dataset="d", seed=0, train_ids=["a", "b"], val_ids=["b", "c"], test_ids=["d"])
    with pytest.raises(ValueError):
        art.validate_no_overlap()


def test_split_no_overlap_ok():
    art = SplitArtifact(dataset="d", seed=0, train_ids=["a"], val_ids=["b"], test_ids=["c"])
    art.validate_no_overlap()
