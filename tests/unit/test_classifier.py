"""
Unit tests for app.services.classifier — TaskClassifier.

Tests the regex (Tier-3) classifier and the ChromaDB availability flag.
Tier-1 (SLM) and Tier-2 (ChromaDB query) tests are mocked to avoid
requiring running Ollama or ChromaDB services.
"""
from __future__ import annotations

import pytest

from app.services.classifier import TaskClassifier


@pytest.mark.unit
class TestRegexClassifier:
    """Tests for the Tier-3 keyword/regex fallback classifier."""

    def setup_method(self):
        # We only need the regex logic — no ChromaDB needed
        self.classifier = TaskClassifier.__new__(TaskClassifier)
        self.classifier.chroma_client = None
        self.classifier.collection = None

    # ── Math ──────────────────────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "prompt",
        [
            "Solve for x: 3x + 5 = 20",
            "What is the derivative of sin(x)?",
            "Calculate the integral of x^2 from 0 to 5",
            "Find the eigenvalues of a 3x3 matrix",
            "What is the sum of the first 100 natural numbers?",
        ],
    )
    def test_math_classification(self, prompt: str):
        result = self.classifier.classify_regex(prompt)
        assert result == "math", f"Expected 'math' for: {prompt!r}"

    # ── Coding ────────────────────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "prompt",
        [
            "Write a Python function to sort a list",
            "How do I implement a binary search tree in C++?",
            "Debug my JavaScript code that throws a TypeError",
            "Create a REST API endpoint using FastAPI",
        ],
    )
    def test_coding_classification(self, prompt: str):
        result = self.classifier.classify_regex(prompt)
        assert result == "coding", f"Expected 'coding' for: {prompt!r}"

    # ── Research ──────────────────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "prompt",
        [
            "Summarize the main causes of World War II",
            "Explain the concept of quantum computing in detail",
            "Compare and contrast capitalism and socialism",
            "What is the history of the Roman Empire?",
        ],
    )
    def test_research_classification(self, prompt: str):
        result = self.classifier.classify_regex(prompt)
        assert result == "research", f"Expected 'research' for: {prompt!r}"

    # ── Casual chat ───────────────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "prompt",
        [
            "Hello! How are you doing today?",
            "Tell me a funny joke",
            "What is your favourite colour?",
            "Good morning!",
        ],
    )
    def test_casual_chat_classification(self, prompt: str):
        result = self.classifier.classify_regex(prompt)
        assert result == "casual_chat", f"Expected 'casual_chat' for: {prompt!r}"

    def test_returns_string(self):
        """Regex classifier must always return a non-empty string."""
        result = self.classifier.classify_regex("some completely random text")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_default_is_casual_chat(self):
        """Prompts with no keywords should default to casual_chat."""
        result = self.classifier.classify_regex("blah blah completely irrelevant words xyz")
        assert result == "casual_chat"


@pytest.mark.unit
class TestTaskClassifierInit:
    """Tests for TaskClassifier initialisation logic."""

    def test_chromadb_unavailable_graceful_degradation(self, monkeypatch):
        """When chromadb is not installed, classifier should still init without raising."""
        import app.services.classifier as cls_module

        monkeypatch.setattr(cls_module, "CHROMADB_AVAILABLE", False)
        # Should not raise
        classifier = TaskClassifier(persist_directory="./test_chroma")
        assert classifier.chroma_client is None
        assert classifier.collection is None
