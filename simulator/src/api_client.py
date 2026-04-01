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

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Represents a source referenced in a conversation."""

    id: str
    title: str
    url: Optional[str] = None
    document_id: Optional[str] = None


@dataclass
class Goal:
    """Represents a conversation goal."""

    id: str
    context: str
    target: str
    discipline: Optional[str] = None


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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Utterance":
        """Create Utterance from dictionary."""
        sources = [
            Source(**src) if isinstance(src, dict) else src
            for src in data.get("sources", [])
        ]
        timestamp = data.get("timestamp", datetime.now().isoformat())
        return cls(
            conversation_id=data.get("conversation_id", ""),
            participant_id=data.get("participant_id", ""),
            text=data.get("text", ""),
            sources=sources,
            annotations=data.get("annotations", {}),
            timestamp=timestamp,
            is_final=data.get("is_final", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Utterance to dictionary for API requests."""
        return {
            "conversation_id": self.conversation_id,
            "participant_id": self.participant_id,
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
    """Represents a response from the API."""

    conversation_id: str
    goal: Goal
    utterance: Optional[Utterance] = None
    is_complete: bool = False
    is_new_conversation: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIResponse":
        """Create APIResponse from API response dictionary."""
        goal_data = data.get("goal", {})
        goal = Goal(
            id=goal_data.get("id", ""),
            context=goal_data.get("context", ""),
            target=goal_data.get("target", ""),
            discipline=goal_data.get("discipline"),
        )

        utterance = None
        if data.get("utterance") is not None:
            utterance = Utterance.from_dict(data.get("utterance"))

        return cls(
            conversation_id=data.get("conversation_id", ""),
            goal=goal,
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
        timeout: int = 30,
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

    def start_run(self, run_id: str, description: str) -> APIResponse:
        """Start a new conversation run.

        Args:
            run_id: Unique identifier for the run
            description: Description of the run

        Returns:
            APIResponse with conversation_id, goal, and initial utterance

        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.base_url}/run/start"
        payload = {
            "run_id": run_id,
            "description": description,
        }

        logger.debug(f"Starting run: {run_id}")
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
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
    ) -> APIResponse:
        """Continue an ongoing conversation.

        Args:
            run_id: ID of the run being continued
            response_text: User's response text
            conversation_id: ID of the conversation
            sources: Optional list of Source objects referenced by the user
            annotations: Optional annotations for the response
            is_final: Whether this is the final user utterance

        Returns:
            APIResponse with the next agent utterance

        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.base_url}/run/continue"

        # Create user utterance with proper structure
        user_utterance = Utterance(
            conversation_id=conversation_id,
            participant_id="user", # always "user" for the simulator
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
                data = response.json()
                api_response = APIResponse.from_dict(data)
                api_response.is_new_conversation = True
                return api_response
            
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Successfully continued conversation for run: {run_id}")
            return APIResponse.from_dict(data)
        except requests.RequestException as e:
            logger.error(f"Failed to continue conversation for run {run_id}: {e}")
            raise

    def get_session(self, run_id: str) -> List[Utterance]:
        """Retrieve the conversation history for a session.

        Args:
            run_id: ID of the run

        Returns:
            List of Utterance objects for the current session

        Raises:
            requests.RequestException: If the API request fails
        """
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
            return [Utterance.from_dict(utterance) for utterance in data]
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve session for run {run_id}: {e}")
            raise

    def get_status(self, run_id: str) -> Dict[str, Any]:
        """Get the status and progress of a run.

        Args:
            run_id: ID of the run

        Returns:
            Dictionary containing status information

        Raises:
            requests.RequestException: If the API request fails
        """
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

    def get_run_dump(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all data for a run in NDJSON format.

        Args:
            run_id: ID of the run

        Returns:
            List of dictionaries containing run data

        Raises:
            requests.RequestException: If the API request fails
        """
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
