"""
Property-based tests for testability of non-deterministic generation.

Validates: Requirements 12.1-12.7
"""

from hypothesis import given, strategies as st
from tests.mocks.mock_llm import MockLLM
from tests.utils.semantic_checker import SemanticSimilarityChecker


def test_mock_llm_deterministic():
    """Property: Mock LLM produces deterministic output"""
    llm = MockLLM()
    llm.set_response("test", "Fixed response")
    
    # Multiple calls should produce same response
    responses = [llm.generate("test") for _ in range(5)]
    
    assert all(r == "Fixed response" for r in responses)


def test_mock_llm_call_tracking():
    """Property: Call count accurately tracks invocations"""
    llm = MockLLM()
    
    # Make some calls
    for _ in range(10):
        llm.generate("test")
    
    assert llm.get_call_count() == 10


@given(st.text(min_size=1, max_size=100))
def test_mock_llm_prompt_storage(prompt):
    """Property: Prompt is stored in call history"""
    llm = MockLLM()
    llm.generate(prompt)
    
    history = llm.get_call_history()
    assert len(history) == 1
    assert history[0]["prompt"] == prompt


def test_mock_llm_clear_history():
    """Property: Clear history resets state"""
    llm = MockLLM()
    
    llm.generate("test1")
    llm.generate("test2")
    
    assert llm.get_call_count() == 2
    
    llm.clear_history()
    
    assert llm.get_call_count() == 0
    assert llm.get_call_history() == []


def test_mock_llm_default_response():
    """Property: Default response returned when no match"""
    llm = MockLLM()
    
    response = llm.generate("Unknown prompt")
    
    assert response == "# Generated Content\n\nThis is a mock response."


def test_mock_llm_streaming():
    """Property: Streaming returns chunks"""
    llm = MockLLM()
    llm.set_streaming_response("test", ["chunk1", "chunk2", "chunk3"])
    
    chunks = llm.generate_streaming("test")
    
    assert chunks == ["chunk1", "chunk2", "chunk3"]


@given(st.text(min_size=1), st.text(min_size=1))
def test_semantic_checker_reflexive(content1, content2):
    """Property: Similarity is reflexive (A ~ A)"""
    checker = SemanticSimilarityChecker()
    
    score = checker.check_similarity(content1, content1)
    
    assert score == 1.0


@given(st.text(min_size=1), st.text(min_size=1))
def test_semantic_checker_symmetric(content1, content2):
    """Property: Similarity is symmetric (A ~ B = B ~ A)"""
    checker = SemanticSimilarityChecker()
    
    score_ab = checker.check_similarity(content1, content2)
    score_ba = checker.check_similarity(content2, content1)
    
    assert score_ab == score_ba


@given(st.text(min_size=1), st.text(min_size=1), st.text(min_size=1))
def test_semantic_checker_similarity_range(content1, content2, content3):
    """Property: Similarity scores are in valid range [0, 1]"""
    checker = SemanticSimilarityChecker()
    
    scores = [
        checker.check_similarity(content1, content2),
        checker.check_similarity(content2, content3),
        checker.check_similarity(content1, content3),
    ]
    
    for score in scores:
        assert 0.0 <= score <= 1.0


def test_semantic_checker_exact_match():
    """Property: Exact match has score 1.0"""
    checker = SemanticSimilarityChecker()
    
    content = "Test content"
    score = checker.check_similarity(content, content)
    
    assert score == 1.0


def test_semantic_checker_empty_input():
    """Property: Empty inputs handled gracefully"""
    checker = SemanticSimilarityChecker()
    
    score = checker.check_similarity("", "")
    
    assert 0.0 <= score <= 1.0


def test_semantic_checker_check_properties():
    """Property: Properties check returns structured result"""
    checker = SemanticSimilarityChecker()
    
    content = "# Title\n\nContent\n\n```python\nprint('test')\n```"
    result = checker.check_properties(content, ["Title"])
    
    assert "passed" in result
    assert "issues" in result
    assert "length" in result
    assert "sections_found" in result


def test_semantic_checker_is_similar():
    """Property: is_similar uses threshold correctly"""
    checker = SemanticSimilarityChecker(min_similarity=0.5)
    
    content = "Test"
    
    # Same content should be similar
    assert checker.is_similar(content, content) is True
    
    # Different content may not be similar
    assert checker.is_similar("Python", "JavaScript") is False
