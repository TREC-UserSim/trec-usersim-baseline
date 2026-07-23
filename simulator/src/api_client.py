"""REST API client for interacting with the conversational agent backend.

Provides methods to start conversations, continue interactions, and retrieve
conversation history and status.
"""

import logging
import requests
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from simulator.src.scenario import (
    Goal,
    Persona,
    PersonaGeneralInfo,
    PersonaExperience,
    PersonaTraits,
    PersonaGoalInteraction,
    Scenario,
)

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Represents a source referenced in a conversation."""

    id: str
    title: str
    url: Optional[str] = None
    document_id: Optional[str] = None


@dataclass
class Utterance:
    """Represents a single turn in a conversation."""

    conversation_id: str
    participant_id: str
    text: str
    sources: List[Source] = field(default_factory=list)
    annotations: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    is_final: bool = False
    participant_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Utterance":
        """Create Utterance from dictionary."""
        sources = [
            Source(**src) if isinstance(src, dict) else src
            for src in data.get("sources", [])
        ]
        timestamp = data.get("timestamp", datetime.now().isoformat())
        participant_name = data.get("participant_name", data.get("participant_id", ""))
        participant_id = data.get("participant_id", participant_name)
        return cls(
            conversation_id=data.get("conversation_id", ""),
            participant_id=participant_id,
            participant_name=participant_name,
            text=data.get("text", ""),
            sources=sources,
            annotations=data.get("annotations", {}),
            timestamp=timestamp,
            is_final=data.get("is_final", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Utterance to dictionary for API requests."""
        participant_name = self.participant_name or self.participant_id
        return {
            "conversation_id": self.conversation_id,
            "participant_name": participant_name,
            "text": self.text,
            "sources": [
                {
                    "id": src.id,
                    "title": src.title,
                    "url": src.url,
                    "document_id": src.document_id,
                }
                for src in self.sources
            ],
            "annotations": self.annotations,
            "timestamp": self.timestamp,
            "is_final": self.is_final,
        }


@dataclass
class APIResponse:
    """Represents a response from the API.

    ``scenario`` is the new preferred container for ``goal``, ``persona`` and
    ``persona_goal_interaction``. For backward compatibility the class also
    accepts a ``goal`` argument directly. If ``scenario`` is not provided, a
    minimal placeholder is created using the supplied ``goal`` (or an empty
    ``Goal`` when neither is given).
    """

    conversation_id: str
    # New unified container – optional for legacy usage
    scenario: Optional["Scenario"] = None
    # Legacy field – kept for existing code and tests
    goal: Optional[Goal] = None
    utterance: Optional[Utterance] = None
    is_complete: bool = False # is run completed?
    is_started: bool = False # has run been started?
    is_new_conversation: bool = False

    def __post_init__(self):
        # Ensure a Scenario instance is always available
        if self.scenario is None:
            # Use provided legacy goal or create an empty one
            goal_obj = self.goal or Goal(context="", topic="", discipline=None)
            self.scenario = Scenario(
                goal=goal_obj,
                persona=Persona(),
                persona_goal_interaction=PersonaGoalInteraction(),
            )
        # Keep legacy ``goal`` attribute in sync with scenario
        if self.goal is None:
            self.goal = self.scenario.goal
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIResponse":
        """Create APIResponse from API response dictionary, parsing the scenario."""
        # Parse scenario components
        scenario_data = data.get("scenario", {}) or {}
        # Goal
        goal_data = scenario_data.get("goal", {})
        goal = Goal(
            context=goal_data.get("context", ""),
            topic=goal_data.get("topic", goal_data.get("target", "")),
            discipline=goal_data.get("discipline"),
        )
        # Persona
        persona_data = scenario_data.get("persona", {})
        general_info = PersonaGeneralInfo(
            gender=persona_data.get("general_info", {}).get("gender"),
            age=persona_data.get("general_info", {}).get("age"),
            highest_education=persona_data.get("general_info", {}).get("highest_education"),
            proficiency_in_english=persona_data.get("general_info", {}).get("proficiency_in_english"),
            tools_used_for_dataset_search=persona_data.get("general_info", {}).get("tools_used_for_dataset_search", []),
        )
        experience = PersonaExperience(
            trust=persona_data.get("experience_with_ai", {}).get("trust"),
            perceived_human_likeness=persona_data.get("experience_with_ai", {}).get("perceived_human_likeness"),
        )
        traits = PersonaTraits(
            frustration_threshold=persona_data.get("individual_traits", {}).get("frustration_threshold"),
            interaction_style=persona_data.get("individual_traits", {}).get("interaction_style"),
        )
        persona = Persona(
            general_info=general_info,
            experience_with_ai=experience,
            individual_traits=traits,
        )
        # Persona-Goal Interaction
        pgi_data = scenario_data.get("persona_goal_interaction", {})
        pgi = PersonaGoalInteraction(
            domain_familiarity=pgi_data.get("domain_familiarity"),
            known_datasets=pgi_data.get("known_datasets", []),
        )
        scenario = Scenario(goal=goal, persona=persona, persona_goal_interaction=pgi)

        if "chat_messages" in data.keys():
            chat_messages = data.get("chat_messages", []) or []
            chat_messages_agent = [m for m in chat_messages if m.get("participant_name") != "user"]
            
            if chat_messages_agent: 
                last_utterance = chat_messages_agent[-1]
                participant_name = last_utterance.get("participant_name", "agent")
                text = last_utterance.get("text", "")
                sources = last_utterance.get("annotations", {})
                annotations = last_utterance.get("annotations", {})
                timestamp = last_utterance.get("timestamp", "")
            else:
                participant_name = "agent"
                text = ""
                sources = {}
                annotations = {}
                timestamp = ""
            utterance = Utterance.from_dict(
                {
                    "conversation_id": data.get("conversation_id", ""),
                    "participant_name": participant_name,
                    "text": text,
                    "sources": sources,
                    "annotations": annotations,
                    "timestamp": timestamp,
                    "is_final": False,
                }
            )
            
        else:
            utterance=Utterance.from_dict(data["utterance"]) if data.get("utterance") else None

        return cls(
            conversation_id=data.get("conversation_id", ""),
            scenario=scenario,
            utterance=utterance,
            is_complete=data.get("is_complete", False),
            is_new_conversation=data.get("is_new_conversation", False),
        )

class SimulatorAPIClient:
    """Client for interacting with the conversational agent REST API.

    Handles all API interactions including starting conversations, continuing
    interactions, and retrieving conversation data.
    """

    def __init__(
        self,
        base_url: str,
        team_id: str,
        auth_token: Optional[str] = None,
        timeout: int = 120,
    ):
        """Initialize the API client.

        Args:
            base_url: Base URL of the backend API (e.g., "http://localhost:80")
            team_id: Team ID for authentication
            auth_token: Optional authentication token (as bearer token or header)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.team_id = team_id
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_headers()
        logger.info(f"Initialized API client: {base_url}")

    def _setup_headers(self) -> None:
        """Set up request headers including authentication."""
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "UserSimulator/0.1.0",
            }
        )
        if self.auth_token:
            self.session.headers.update(
                {"Authorization": f"Bearer {self.auth_token}"}
            )

    def start_run(
        self,
        run_id: str,
        description: str,
        task_name: str = "end_to_end_conversation_generation",
        debug: bool = False,
    ) -> APIResponse:
        """Start a new run for either Task 1 or Task 2.

        The backend provides separate endpoints for the two tasks. ``task_name``
        determines which endpoint is used. ``debug`` selects the debug variant
        of the endpoint.

        Args:
            run_id: Unique identifier for the run.
            description: Description of the run.
            task_name: Either ``"next_utterance_prediction"`` or ``"end_to_end_conversation_generation"`` (default).
            debug: Whether to use the debug endpoint.

        Returns:
            APIResponse with conversation_id, goal, and initial utterance.
        """
        # Resolve the correct endpoint based on task and debug flag
        if task_name == "next_utterance_prediction":
            endpoint = "task1/debug/start" if debug else "task1/run/start"
        else:
            # Default to task2 behaviour for any other value
            endpoint = "task2/debug/start" if debug else "task2/run/start"
        url = f"{self.base_url}/{endpoint}"

        payload = {
            "run_id": run_id,
            "task_name": task_name,
            "description": description,
        }
        if self.team_id:
            payload["team_id"] = self.team_id

        logger.debug(f"Starting run {run_id} using endpoint {url}")
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            logger.info(f"Response of 'start_run': {json.dumps(response.json())}")

            # Handle 412 status code as started run
            if response.status_code == 412:
                logger.info(f"Run has already been started (412 status): {run_id}")
                return APIResponse(
                    conversation_id="",
                    goal=Goal(id="", context="", target=""),
                    utterance=None,
                    is_started=True,
                )

            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully started run: {run_id}")
            return APIResponse.from_dict(data)
        except requests.RequestException as e:
            logger.error(f"Failed to start run {run_id}: {e}")
            raise

    def continue_run(
        self,
        run_id: str,
        response_text: str,
        conversation_id: str,
        sources: Optional[List[Source]] = None,
        annotations: Optional[Dict[str, Any]] = None,
        is_final: bool = False,
        task_name: str = "end_to_end_conversation_generation",
        debug: bool = False,
    ) -> APIResponse:
        """Continue an ongoing run for either Task 1 or Task 2.

        Args:
            run_id: Identifier of the run.
            response_text: Text of the user response.
            conversation_id: Conversation identifier returned by ``start_run``.
            sources: Optional list of :class:`Source` objects.
            annotations: Optional dictionary of annotations.
            is_final: Mark the response as final.
            task_name: ``"next_utterance_prediction"`` or ``"end_to_end_conversation_generation"`` (default).
            debug: Use the debug endpoint when ``True``.

        Returns:
            APIResponse containing the next agent utterance or signalling run
            completion.
        """
        # Resolve endpoint based on task and debug flag
        if task_name == "next_utterance_prediction":
            endpoint = "task1/debug/continue" if debug else "task1/run/continue"
        else:
            endpoint = "task2/debug/continue" if debug else "task2/run/continue"
        url = f"{self.base_url}/{endpoint}"

        # Create user utterance with proper structure
        user_utterance = Utterance(
            conversation_id=conversation_id,
            participant_id="user", # always "user" for the simulator
            participant_name="user",
            text=response_text,
            sources=sources or [],
            annotations=annotations or {},
            timestamp=datetime.now().isoformat(),
            is_final=is_final,
        )

        payload = {
            "run_id": run_id,
            "user_utterance": user_utterance.to_dict(),
        }

        logger.debug(f"Continuing conversation for run: {run_id}")
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            logger.info(f"Response of 'continue_run': {json.dumps(response.json())}")
            # Handle 428 status code as run completion
            if response.status_code == 428:
                logger.info(f"Run completed (428 status): {run_id}")
                return APIResponse(
                    conversation_id="",
                    goal=Goal(id="", context="", target=""),
                    utterance=None,
                    is_complete=True,
                )

            # Handle 201 status code as new conversation start
            if response.status_code == 201:
                logger.info(f"New conversation started (201 status): {run_id}")
                if response.content and response.content.strip():
                    data = response.json()
                    api_response = APIResponse.from_dict(data)
                    api_response.is_new_conversation = True
                    return api_response
                return APIResponse(
                    conversation_id="",
                    goal=Goal(id="", context="", target=""),
                    utterance=None,
                    is_new_conversation=True,
                )
            
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Successfully continued conversation for run: {run_id}")
            return APIResponse.from_dict(data)
        except requests.RequestException as e:
            logger.error(f"Failed to continue conversation for run {run_id}: {e}")
            raise

    def get_session(self, run_id: str, debug: bool = False) -> List[Utterance]:
        """Retrieve the conversation history for a session.

        Args:
            run_id: ID of the run
            debug: Whether to enable debug mode. Defaults to False.

        Returns:
            List of Utterance objects for the current session

        Raises:
            requests.RequestException: If the API request fails
        """
        if debug:
            url = f"{self.base_url}/debug/session"
        else:
            url = f"{self.base_url}/run/session"

        params = {"run_id": run_id}

        logger.debug(f"Retrieving session for run: {run_id}")
        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Successfully retrieved session for run: {run_id}")
            # Parse each utterance in the session
            # return [Utterance.from_dict(utterance) for utterance in data]
            return APIResponse.from_dict(data)
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve session for run {run_id}: {e}")
            raise

    def get_status(self, run_id: str, debug: bool = False) -> Dict[str, Any]:
        """Get the status and progress of a run.

        Args:
            run_id: ID of the run.
            debug: Whether to enable debug mode. Defaults to False.

        Returns:
            Dictionary containing status information.

        Raises:
            requests.RequestException: If the API request fails.
        """
        if debug:
            url = f"{self.base_url}/debug/status"
        else:
            url = f"{self.base_url}/run/status"

        params = {"run_id": run_id}

        logger.debug(f"Retrieving status for run: {run_id}")
        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Successfully retrieved status for run: {run_id}")
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve status for run {run_id}: {e}")
            raise

    def get_run_dump(self, run_id: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Retrieve all data for a run in NDJSON format.

        Args:
            run_id: ID of the run.
            debug: Whether to enable debug mode. Defaults to False.

        Returns:
            List of dictionaries containing run data.

        Raises:
            requests.RequestException: If the API request fails.
        """
        if debug:
            url = f"{self.base_url}/debug/dump"
        else:
            url = f"{self.base_url}/run/dump"
            
        params = {"run_id": run_id}

        logger.debug(f"Retrieving dump for run: {run_id}")
        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout, stream=True
            )
            response.raise_for_status()

            # Parse NDJSON response
            data = []
            for line in response.iter_lines():
                if line:
                    data.append(json.loads(line))

            logger.debug(f"Successfully retrieved dump for run: {run_id}")
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve dump for run {run_id}: {e}")
            raise

    def close(self) -> None:
        """Close the API session."""
        self.session.close()
        logger.debug("API client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
