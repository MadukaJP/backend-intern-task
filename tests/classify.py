import json
import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app import app
from core.cache import result_cache

client = TestClient(app)


def make_groq_response(label: str, confidence: float):
    return {
        "choices": [
            {"message": {"content": json.dumps({"type": label, "confidence": confidence})}}
        ]
    }


class TestClassifyUnit:
    def setup_method(self):
        result_cache.clear()

    @patch("routes.classify.classify_text", new_callable=AsyncMock)
    def test_returns_valid_label(self, mock_classify):
        mock_classify.return_value = {"type": "question", "confidence": 0.95}
        res = client.post("/classify", json={"text": "What time does the store close?"})
        assert res.status_code == 200
        body = res.json()
        assert body["type"] == "question"
        assert 0.0 <= body["confidence"] <= 1.0

    @patch("routes.classify.classify_text", new_callable=AsyncMock)
    def test_all_valid_labels_accepted(self, mock_classify):
        for label in ["question", "complaint", "feedback", "request", "spam", "other"]:
            mock_classify.return_value = {"type": label, "confidence": 0.9}
            res = client.post("/classify", json={"text": f"test text for {label}"})
            assert res.status_code == 200
            assert res.json()["type"] == label

    @patch("routes.classify.classify_text", new_callable=AsyncMock)
    def test_cache_hit_skips_llm(self, mock_classify):
        mock_classify.return_value = {"type": "feedback", "confidence": 0.88}
        text = "This product is pretty good overall"
        client.post("/classify", json={"text": text})
        client.post("/classify", json={"text": text})
        assert mock_classify.call_count == 1

    def test_empty_text_returns_422(self):
        assert client.post("/classify", json={"text": ""}).status_code == 422

    def test_whitespace_only_returns_422(self):
        assert client.post("/classify", json={"text": "   "}).status_code == 422

    def test_missing_text_field_returns_422(self):
        assert client.post("/classify", json={}).status_code == 422

    def test_text_too_long_returns_422(self):
        assert client.post("/classify", json={"text": "a" * 4001}).status_code == 422

    @patch("routes.classify.classify_text", new_callable=AsyncMock)
    def test_case_insensitive_cache(self, mock_classify):
        mock_classify.return_value = {"type": "question", "confidence": 0.9}
        client.post("/classify", json={"text": "Where is my order?"})
        client.post("/classify", json={"text": "WHERE IS MY ORDER?"})
        assert mock_classify.call_count == 1


class TestHealthRoutes:
    def test_health_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_root_returns_200(self):
        assert client.get("/").status_code == 200


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
class TestClassifyIntegration:
    def setup_method(self):
        result_cache.clear()

    def test_question_classification(self):
        res = client.post("/classify", json={"text": "What are your opening hours?"})
        assert res.status_code == 200
        assert res.json()["type"] in ["question", "request", "other"]

    def test_complaint_classification(self):
        res = client.post("/classify", json={"text": "This is absolutely terrible, I've been waiting 3 weeks!"})
        assert res.status_code == 200
        assert res.json()["type"] == "complaint"

    def test_spam_classification(self):
        res = client.post("/classify", json={"text": "CLICK HERE NOW!!! FREE MONEY!!!"})
        assert res.status_code == 200
        assert res.json()["type"] == "spam"

    def test_feedback_classification(self):
        res = client.post("/classify", json={"text": "I really enjoy using this app, the UI is clean."})
        assert res.status_code == 200
        assert res.json()["type"] == "feedback"