"""Tests for the user simulator module."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from simulator.src.user_simulator import (
    ConversationState, UserSimulator
)
from simulator.src.api_client import (
    SimulatorAPIClient, APIResponse, Goal, Utterance, Source
)
from simulator.src.persona import PersonaDefinition
from simulator.src.response_strategies import RandomStrategy, ResponseStrategy


class TestConversationState:
    """Tests for ConversationState class."""

    def test_conversation_state_creation(self):
        """Test creating a conversation state."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
            turn_count=0,
        )
        assert state.run_id == "run_1"
        assert state.conversation_id == "conv_1"
        assert state.goal.id == "g1"
        assert state.turn_count == 0
        assert state.chat_history == []
        assert state.last_agent_utterance is None

    def test_conversation_state_add_agent_message(self):
        """Test adding an agent message to conversation state."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
        )
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Hello, how can I help?",
        )
        state.add_agent_message(utterance)

        assert len(state.chat_history) == 1
        assert state.chat_history[0]["role"] == "assistant"
        assert state.chat_history[0]["content"] == "Hello, how can I help?"
        assert state.last_agent_utterance == utterance

    def test_conversation_state_add_user_message(self):
        """Test adding a user message to conversation state."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
        )
        state.add_user_message("I need information about Python")

        assert len(state.chat_history) == 1
        assert state.chat_history[0]["role"] == "user"
        assert state.chat_history[0]["content"] == "I need information about Python"

    def test_conversation_state_multiple_messages(self):
        """Test adding multiple messages."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
        )
        
        state.add_user_message("Hello")
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Hi there",
        )
        state.add_agent_message(utterance)
        state.add_user_message("How are you?")

        assert len(state.chat_history) == 3
        assert state.chat_history[0]["role"] == "user"
        assert state.chat_history[1]["role"] == "assistant"
        assert state.chat_history[2]["role"] == "user"

    def test_conversation_state_is_conversation_active_initial(self):
        """Test conversation is active initially."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
        )
        assert state.is_conversation_active() is True

    def test_conversation_state_is_conversation_active_after_message(self):
        """Test conversation is active after agent message."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
        )
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Test",
            is_final=False,
        )
        state.add_agent_message(utterance)
        assert state.is_conversation_active() is True

    def test_conversation_state_is_conversation_inactive_final(self):
        """Test conversation is inactive when final utterance received."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="conv_1",
            goal=goal,
        )
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Goodbye",
            is_final=True,
        )
        state.add_agent_message(utterance)
        assert state.is_conversation_active() is False

    def test_conversation_state_updates_conversation_id(self):
        """Test that conversation ID is updated from agent message."""
        goal = Goal(id="g1", context="ctx", target="tgt")
        state = ConversationState(
            run_id="run_1",
            conversation_id="initial_conv",
            goal=goal,
        )
        utterance = Utterance(
            conversation_id="updated_conv",
            participant_id="agent",
            text="Test",
        )
        state.add_agent_message(utterance)
        assert state.conversation_id == "updated_conv"


class TestUserSimulator:
    """Tests for UserSimulator class."""

    def test_user_simulator_creation(self):
        """Test creating a user simulator."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        simulator = UserSimulator(persona, api_client)

        assert simulator.persona == persona
        assert simulator.api_client == api_client
        assert isinstance(simulator.response_strategy, RandomStrategy)
        assert simulator.state is None

    def test_user_simulator_with_custom_strategy(self):
        """Test user simulator with custom strategy."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        custom_strategy = RandomStrategy()
        simulator = UserSimulator(persona, api_client, custom_strategy)

        assert simulator.response_strategy == custom_strategy

    def test_user_simulator_initiate_run_success(self):
        """Test initiating a run."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        
        goal = Goal(id="g1", context="ctx", target="tgt")
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Hello",
        )
        api_response = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=utterance,
        )
        api_client.start_run.return_value = api_response

        simulator = UserSimulator(persona, api_client)
        result = simulator.initiate_run("run_1", "Test run")

        assert result == api_response
        assert simulator.state is not None
        assert simulator.state.run_id == "run_1"
        assert simulator.state.conversation_id == "conv_1"
        api_client.start_run.assert_called_once_with("run_1", "Test run")

    def test_user_simulator_initiate_run_without_utterance(self):
        """Test initiating run without initial utterance."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        
        goal = Goal(id="g1", context="ctx", target="tgt")
        api_response = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=None,
        )
        api_client.start_run.return_value = api_response

        simulator = UserSimulator(persona, api_client)
        result = simulator.initiate_run("run_1", "Test run")

        assert result == api_response
        assert simulator.state.last_agent_utterance is None

    def test_user_simulator_initiate_run_already_active(self):
        """Test that initiating run while one is active raises error."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        
        goal = Goal(id="g1", context="ctx", target="tgt")
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Hello",
        )
        api_response = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=utterance,
        )
        api_client.start_run.return_value = api_response

        simulator = UserSimulator(persona, api_client)
        simulator.initiate_run("run_1", "Test run")

        # Try to initiate another run without ending the first
        with pytest.raises(RuntimeError, match="already active"):
            simulator.initiate_run("run_2", "Another run")

    def test_user_simulator_initiate_conversation(self):
        """Test initiating a conversation."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        
        goal = Goal(id="g1", context="ctx", target="tgt")
        simulator = UserSimulator(persona, api_client)
        simulator.initiate_conversation("run_1", "conv_1", goal)

        assert simulator.state is not None
        assert simulator.state.run_id == "run_1"
        assert simulator.state.conversation_id == "conv_1"
        assert simulator.state.goal == goal

    def test_user_simulator_initiate_conversation_while_active(self):
        """Test that initiating conversation while one is active raises error."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        goal = Goal(id="g1", context="ctx", target="tgt")

        simulator = UserSimulator(persona, api_client)
        simulator.initiate_conversation("run_1", "conv_1", goal)

        # Try to initiate another conversation
        with pytest.raises(RuntimeError, match="already active"):
            simulator.initiate_conversation("run_1", "conv_2", goal)

    def test_user_simulator_respond_success(self):
        """Test generating a response."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        
        goal = Goal(id="g1", context="ctx", target="tgt")
        utterance = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="What would you like to know?",
        )
        api_response = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=utterance,
        )
        api_client.start_run.return_value = api_response

        simulator = UserSimulator(persona, api_client)
        simulator.initiate_run("run_1", "Test")
        response = simulator.respond()

        assert isinstance(response, str)
        assert len(response) > 0

    def test_user_simulator_respond_without_active_conversation(self):
        """Test that responding without active conversation raises error."""
        persona = PersonaDefinition(id="p1")
        api_client = Mock(spec=SimulatorAPIClient)
        
        simulator = UserSimulator(persona, api_client)
        with pytest.raises(RuntimeError, match="No active conversation"):
            simulator.respond()

    def test_user_simulator_conversation_flow(self):
        """Test a complete conversation flow."""
        persona = PersonaDefinition(id="p1", general_info={"name": "Test User"})
        api_client = Mock(spec=SimulatorAPIClient)
        
        goal = Goal(id="g1", context="ctx", target="tgt")
        utterance1 = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="Hello, how can I help?",
        )
        api_response1 = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=utterance1,
        )
        api_client.start_run.return_value = api_response1

        utterance2 = Utterance(
            conversation_id="conv_1",
            participant_id="agent",
            text="This is the final response",
            is_final=True,
        )
        api_response2 = APIResponse(
            conversation_id="conv_1",
            goal=goal,
            utterance=utterance2,
            is_complete=True,
        )
        api_client.continue_run.return_value = api_response2

        simulator = UserSimulator(persona, api_client)
        
        # Start run
        result1 = simulator.initiate_run("run_1", "Test run")
        assert result1.utterance.text == "Hello, how can I help?"
        assert simulator.state.is_conversation_active() is True

        # Generate response and continue
        user_response = simulator.respond()
        assert isinstance(user_response, str)

        # Simulate API response
        result2 = api_client.continue_run(
            "run_1", user_response, "conv_1"
        )
        simulator.state.add_agent_message(result2.utterance)
        
        # Conversation should now be inactive
        assert simulator.state.is_conversation_active() is False
