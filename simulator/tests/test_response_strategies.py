"""Tests for the response strategies module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from simulator.src.response_strategies import (
    ResponseStrategy, RandomStrategy, LLMStrategy
)
from simulator.src.persona import PersonaDefinition
from simulator.src.api_client import Goal


class TestResponseStrategy:
    """Tests for ResponseStrategy base class."""

    def test_response_strategy_is_abstract(self):
        """Test that ResponseStrategy cannot be instantiated."""
        with pytest.raises(TypeError):
            ResponseStrategy()

    def test_response_strategy_requires_generate_response(self):
        """Test that subclasses must implement generate_response."""
        class IncompleteStrategy(ResponseStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteStrategy()


class TestRandomStrategy:
    """Tests for RandomStrategy class."""

    def test_random_strategy_creation(self):
        """Test creating a random strategy."""
        strategy = RandomStrategy()
        assert strategy is not None
        assert issubclass(RandomStrategy, ResponseStrategy)

    def test_random_strategy_generate_response(self):
        """Test generating a random response."""
        strategy = RandomStrategy()
        response = strategy.generate_response()
        assert isinstance(response, str)
        assert len(response) > 0

    def test_random_strategy_ignores_parameters(self):
        """Test that random strategy ignores all parameters."""
        strategy = RandomStrategy()
        persona = PersonaDefinition(id="p1")
        goal = Goal(id="g1", context="ctx", target="tgt")
        
        response = strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance="Test message",
            goal=goal,
        )
        assert isinstance(response, str)
        assert response in RandomStrategy.RESPONSE_POOL

    def test_random_strategy_returns_from_pool(self):
        """Test that responses come from the defined pool."""
        strategy = RandomStrategy()
        responses = set(
            strategy.generate_response() for _ in range(20)
        )
        # Check that all responses are in the pool
        for response in responses:
            assert response in RandomStrategy.RESPONSE_POOL

    def test_random_strategy_with_none_parameters(self):
        """Test random strategy with None parameters."""
        strategy = RandomStrategy()
        response = strategy.generate_response(
            persona=None,
            conversation_history=None,
            agent_utterance=None,
            goal=None,
        )
        assert isinstance(response, str)
        assert response in RandomStrategy.RESPONSE_POOL

    def test_random_strategy_response_pool_not_empty(self):
        """Test that response pool is not empty."""
        assert len(RandomStrategy.RESPONSE_POOL) > 0

    def test_random_strategy_response_pool_contains_strings(self):
        """Test that all items in pool are strings."""
        for response in RandomStrategy.RESPONSE_POOL:
            assert isinstance(response, str)
            assert len(response) > 0


class TestLLMStrategy:
    """Tests for LLMStrategy class."""

    def test_llm_strategy_creation(self):
        """Test creating an LLM strategy."""
        strategy = LLMStrategy(
            model="ollama/qwen3:0.6b",
            api_base="http://localhost:11434",
        )
        assert strategy.model == "ollama/qwen3:0.6b"
        assert strategy.api_base == "http://localhost:11434"
        assert issubclass(LLMStrategy, ResponseStrategy)

    def test_llm_strategy_creation_with_defaults(self):
        """Test LLM strategy with default parameters."""
        strategy = LLMStrategy()
        assert strategy.model == "ollama/qwen3:0.6b"
        assert strategy.api_base == "http://localhost:11434"

    def test_llm_strategy_stores_kwargs(self):
        """Test that additional kwargs are stored."""
        strategy = LLMStrategy(
            model="gpt-3.5-turbo",
            api_base="http://localhost",
            temperature=0.7,
            max_tokens=100,
        )
        assert strategy.kwargs.get("temperature") == 0.7
        assert strategy.kwargs.get("max_tokens") == 100

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_generate_response(self, mock_completion):
        """Test LLM response generation."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_completion.return_value = mock_response

        strategy = LLMStrategy()
        persona = PersonaDefinition(
            id="p1",
            general_info={"gender": "Female", "age": 35},
            ai_experience={"years": 2},
            traits={"patience": "high"},
        )
        goal = Goal(
            id="g1",
            context="Find information",
            target="Learn about topic",
            discipline="Science",
        )

        response = strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance="What would you like to know?",
            goal=goal,
        )

        assert response == "Generated response"
        mock_completion.assert_called_once()

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_with_conversation_history(self, mock_completion):
        """Test LLM strategy with existing conversation history."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        strategy = LLMStrategy()
        persona = PersonaDefinition(id="p1")
        goal = Goal(id="g1", context="ctx", target="tgt")
        
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        response = strategy.generate_response(
            persona=persona,
            conversation_history=history,
            agent_utterance="How can I help?",
            goal=goal,
        )

        assert response == "Response"
        # Check that completion was called with messages including history
        call_kwargs = mock_completion.call_args.kwargs
        messages = call_kwargs.get("messages", [])
        assert len(messages) > 2  # System + history + current

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_no_agent_utterance(self, mock_completion):
        """Test LLM strategy when no agent utterance is provided."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Initial response"
        mock_completion.return_value = mock_response

        strategy = LLMStrategy()
        persona = PersonaDefinition(id="p1")
        goal = Goal(id="g1", context="ctx", target="tgt")

        response = strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance=None,
            goal=goal,
        )

        assert response == "Initial response"
        # Check that a user message was added to start conversation
        call_kwargs = mock_completion.call_args.kwargs
        messages = call_kwargs.get("messages", [])
        assert any(msg.get("role") == "user" for msg in messages)

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_error_handling(self, mock_completion):
        """Test LLM strategy handles errors gracefully."""
        mock_completion.side_effect = Exception("API Error")

        strategy = LLMStrategy()
        persona = PersonaDefinition(id="p1")
        goal = Goal(id="g1", context="ctx", target="tgt")

        response = strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance="Test",
            goal=goal,
        )

        # Should return fallback response
        assert "couldn't generate a response" in response

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_system_prompt_includes_persona(self, mock_completion):
        """Test that system prompt includes persona information."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        strategy = LLMStrategy()
        persona = PersonaDefinition(
            id="p1",
            general_info={"gender": "Male", "age": 40},
            ai_experience={"comfort": "high"},
            traits={"openness": "high"},
        )
        goal = Goal(id="g1", context="ctx", target="tgt")

        strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance="Test",
            goal=goal,
        )

        call_kwargs = mock_completion.call_args.kwargs
        messages = call_kwargs.get("messages", [])
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        
        assert system_msg is not None
        system_content = system_msg.get("content", "")
        assert "persona" in system_content.lower()
        assert "Male" in system_content or "40" in system_content

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_system_prompt_includes_goal(self, mock_completion):
        """Test that system prompt includes goal information."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        strategy = LLMStrategy()
        persona = PersonaDefinition(id="p1")
        goal = Goal(
            id="g1",
            context="Find information about AI",
            target="Understand machine learning",
            discipline="Computer Science",
        )

        strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance="Test",
            goal=goal,
        )

        call_kwargs = mock_completion.call_args.kwargs
        messages = call_kwargs.get("messages", [])
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        
        assert system_msg is not None
        system_content = system_msg.get("content", "")
        assert "Find information about AI" in system_content or "machine learning" in system_content

    @patch("simulator.src.response_strategies.completion")
    def test_llm_strategy_passes_kwargs_to_completion(self, mock_completion):
        """Test that kwargs are passed to completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_completion.return_value = mock_response

        strategy = LLMStrategy(
            temperature=0.9,
            top_p=0.95,
        )
        persona = PersonaDefinition(id="p1")
        goal = Goal(id="g1", context="ctx", target="tgt")

        strategy.generate_response(
            persona=persona,
            conversation_history=[],
            agent_utterance="Test",
            goal=goal,
        )

        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs.get("temperature") == 0.9
        assert call_kwargs.get("top_p") == 0.95
