"""Tests for the API client module."""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from simulator.src.api_client import (
    Source, Goal, Utterance, APIResponse, SimulatorAPIClient
)


class TestSource:
    """Tests for Source class."""

    def test_source_creation(self):
        """Test creating a source."""
        source = Source(
            id="source_1",
            title="Wikipedia Article",
            url="https://example.com",
            document_id="doc_123",
        )
        assert source.id == "source_1"
        assert source.title == "Wikipedia Article"
        assert source.url == "https://example.com"
        assert source.document_id == "doc_123"

    def test_source_optional_fields(self):
        """Test source with only required fields."""
        source = Source(id="s1", title="Title")
        assert source.id == "s1"
        assert source.title == "Title"
        assert source.url is None
        assert source.document_id is None


class TestGoal:
    """Tests for Goal class."""

    def test_goal_creation(self):
        """Test creating a goal."""
        goal = Goal(
            id="goal_1",
            context="Find information about climate change",
            target="Learn about greenhouse gases",
            discipline="Environmental Science",
        )
        assert goal.id == "goal_1"
        assert goal.context == "Find information about climate change"
        assert goal.target == "Learn about greenhouse gases"
        assert goal.discipline == "Environmental Science"

    def test_goal_optional_discipline(self):
        """Test goal without discipline."""
        goal = Goal(
            id="g1",
            context="Test context",
            target="Test target",
        )
        assert goal.discipline is None


class TestUtterance:
    """Tests for Utterance class."""

    def test_utterance_creation(self):
        """Test creating an utterance."""
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="user_1",
            text="Hello, how can I help?",
            is_final=False,
        )
        assert utterance.conversation_id == "conv_1"
        assert utterance.participant_id == "user_1"
        assert utterance.text == "Hello, how can I help?"
        assert utterance.is_final is False

    def test_utterance_with_sources(self):
        """Test utterance with sources."""
        sources = [
            Source(id="s1", title="Source 1"),
            Source(id="s2", title="Source 2"),
        ]
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Here are the results.",
            sources=sources,
        )
        assert len(utterance.sources) == 2
        assert utterance.sources[0].id == "s1"

    def test_utterance_from_dict(self):
        """Test creating utterance from dictionary."""
        data = {
            "conversation_id": "conv_1",
            "participant_id": "user_1",
            "text": "Test message",
            "sources": [
                {"id": "s1", "title": "Source", "url": None, "document_id": None}
            ],
            "annotations": {"key": "value"},
            "timestamp": "2023-01-01T12:00:00",
            "is_final": True,
        }
        utterance = Utterance.from_dict(data)
        assert utterance.conversation_id == "conv_1"
        assert utterance.text == "Test message"
        assert len(utterance.sources) == 1
        assert utterance.sources[0].id == "s1"
        assert utterance.annotations["key"] == "value"
        assert utterance.is_final is True

    def test_utterance_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {
            "conversation_id": "conv_1",
            "participant_id": "user_1",
            "text": "Message",
        }
        utterance = Utterance.from_dict(data)
        assert utterance.conversation_id == "conv_1"
        assert utterance.sources == []
        assert utterance.annotations == {}
        assert utterance.is_final is False

    def test_utterance_to_dict(self):
        """Test converting utterance to dictionary."""
        sources = [Source(id="s1", title="Title", url="http://example.com")]
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="user_1",
            text="Test",
            sources=sources,
            annotations={"type": "response"},
            timestamp="2023-01-01T12:00:00",
            is_final=False,
        )
        result = utterance.to_dict()
        assert result["conversation_id"] == "conv_1"
        assert result["participant_id"] == "user_1"
        assert result["text"] == "Test"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["id"] == "s1"
        assert result["annotations"]["type"] == "response"
        assert result["is_final"] is False

    def test_utterance_roundtrip_conversion(self):
        """Test roundtrip: Utterance -> dict -> Utterance."""
        original = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Test message",
            sources=[Source(id="s1", title="Doc")],
            annotations={"meta": "data"},
            is_final=True,
        )
        as_dict = original.to_dict()
        restored = Utterance.from_dict(as_dict)
        
        assert restored.conversation_id == original.conversation_id
        assert restored.participant_id == original.participant_id
        assert restored.text == original.text
        assert len(restored.sources) == 1
        assert restored.is_final == original.is_final


class TestAPIResponse:
    """Tests for APIResponse class."""

    def test_api_response_creation(self):
        """Test creating an API response."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        response = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            is_complete=False,
        )
        assert response.conversation_id == "conv_1"
        assert response.goal.id == "g1"
        assert response.is_complete is False

    def test_api_response_with_utterance(self):
        """Test API response with utterance."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Hello",
        )
        response = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=utterance,
        )
        assert response.utterance is not None
        assert response.utterance.text == "Hello"

    def test_api_response_from_dict(self):
        """Test creating API response from dictionary."""
        data = {
            "conversation_id": "conv_1",
            "goal": {
                "id": "g1",
                "context": "Find info",
                "target": "Learn more",
                "discipline": "Science",
            },
            "utterance": {
                "conversation_id": "conv_1",
                "participant_id": "agent",
                "text": "Response",
                "sources": [],
                "annotations": {},
                "timestamp": "2023-01-01T12:00:00",
                "is_final": False,
            },
            "is_complete": False,
            "is_new_conversation": True,
        }
        response = APIResponse.from_dict(data)
        assert response.conversation_id == "conv_1"
        assert response.goal.id == "g1"
        assert response.goal.context == "Find info"
        assert response.utterance is not None
        assert response.is_new_conversation is True

    def test_api_response_from_dict_no_utterance(self):
        """Test from_dict when utterance is None."""
        data = {
            "conversation_id": "conv_1",
            "goal": {"id": "g1", "context": "ctx", "target": "tgt"},
            "utterance": None,
            "is_complete": True,
        }
        response = APIResponse.from_dict(data)
        assert response.utterance is None
        assert response.is_complete is True


class TestSimulatorAPIClient:
    """Tests for SimulatorAPIClient class."""

    def test_client_initialization(self):
        """Test API client initialization."""
        client = SimulatorAPIClient(
            base_url="http://localhost:8000",
            team_id="team_1",
            auth_token="token_123",
        )
        assert client.base_url == "http://localhost:8000"
        assert client.team_id == "team_1"
        assert client.auth_token == "token_123"
        assert client.timeout == 30

    def test_client_initialization_with_custom_timeout(self):
        """Test API client with custom timeout."""
        client = SimulatorAPIClient(
            base_url="http://localhost:8000",
            team_id="team_1",
            timeout=60,
        )
        assert client.timeout == 60

    def test_client_base_url_normalization(self):
        """Test that base URL trailing slash is removed."""
        client = SimulatorAPIClient(
            base_url="http://localhost:8000/",
            team_id="team_1",
        )
        assert client.base_url == "http://localhost:8000"

    def test_headers_setup_basic(self):
        """Test headers are set up correctly."""
        client = SimulatorAPIClient(
            base_url="http://localhost:8000",
            team_id="team_1",
        )
        headers = client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert "User-Agent" in headers

    def test_headers_setup_with_auth(self):
        """Test authorization header is set."""
        client = SimulatorAPIClient(
            base_url="http://localhost:8000",
            team_id="team_1",
            auth_token="secret_token",
        )
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer secret_token"

    @patch("simulator.src.api_client.requests.Session.post")
    def test_start_run_success(self, mock_post):
        """Test successful run start."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "conversation_id": "conv_1",
            "goal": {
                "id": "g1",
                "context": "Test context",
                "target": "Test target",
            },
            "utterance": {
                "conversation_id": "conv_1",
                "participant_id": "agent",
                "text": "Hello, how can I help?",
                "sources": [],
                "annotations": {},
                "is_final": False,
            },
            "is_complete": False,
            "is_new_conversation": True,
        }
        mock_post.return_value = mock_response

        client = SimulatorAPIClient("http://localhost:8000", "team_1")
        result = client.start_run("run_1", "Test run")

        assert result.conversation_id == "conv_1"
        assert result.goal.id == "g1"
        assert result.utterance is not None
        mock_post.assert_called_once()

    @patch("simulator.src.api_client.requests.Session.post")
    def test_start_run_failure(self, mock_post):
        """Test run start with API error."""
        mock_post.side_effect = Exception("Connection error")

        client = SimulatorAPIClient("http://localhost:8000", "team_1")
        with pytest.raises(Exception):
            client.start_run("run_1", "Test run")

    @patch("simulator.src.api_client.requests.Session.post")
    def test_continue_run_success(self, mock_post):
        """Test successful continue run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "conversation_id": "conv_1",
            "goal": {"id": "g1", "context": "ctx", "target": "tgt"},
            "utterance": {
                "conversation_id": "conv_1",
                "participant_id": "agent",
                "text": "Here are the results.",
                "sources": [],
                "annotations": {},
                "is_final": False,
            },
            "is_complete": False,
        }
        mock_post.return_value = mock_response

        client = SimulatorAPIClient("http://localhost:8000", "team_1")
        result = client.continue_run(
            "run_1",
            "My response",
            "conv_1",
        )

        assert result.conversation_id == "conv_1"
        assert result.utterance.text == "Here are the results."
        mock_post.assert_called_once()

    @patch("simulator.src.api_client.requests.Session.post")
    def test_continue_run_with_sources(self, mock_post):
        """Test continue run with source citations."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "conversation_id": "conv_1",
            "goal": {"id": "g1", "context": "ctx", "target": "tgt"},
            "utterance": None,
            "is_complete": True,
        }
        mock_post.return_value = mock_response

        client = SimulatorAPIClient("http://localhost:8000", "team_1")
        sources = [Source(id="s1", title="Source 1")]
        result = client.continue_run(
            "run_1",
            "Response",
            "conv_1",
            sources=sources,
        )

        assert result.is_complete is True
        call_args = mock_post.call_args
        assert call_args is not None
        json_data = call_args.kwargs.get("json") or call_args[1].get("json")
        assert json_data is not None
