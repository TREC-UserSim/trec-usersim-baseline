"""Persona management module.

Defines user personas with flexible attributes for the conversational simulator.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class PersonaDefinition:
    """Represents a user persona with structured attributes.

    Attributes:
        id: Unique identifier for the persona
        general_info: General information about the persona (gender, age, education, etc.)
        ai_experience: Experience and familiarity with AI systems
        traits: Personality traits and characteristics
    """

    id: str
    general_info: Dict[str, Any] = field(default_factory=dict)
    ai_experience: Dict[str, Any] = field(default_factory=dict)
    traits: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Get a display name for the persona.
        
        Returns:
            A human-readable name based on persona attributes or ID
        """
        # Try to construct a name from general_info
        gender = self.general_info.get("gender", "")
        age = self.general_info.get("age", "")
        education = self.general_info.get("education", "")
        
        if gender and age:
            return f"{gender}, {age}, {education}"
        elif gender:
            return f"{gender}, {education}"
        else:
            return self.id  # Fallback to ID

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonaDefinition":
        """Create a PersonaDefinition from a dictionary.

        Args:
            data: Dictionary containing persona data

        Returns:
            PersonaDefinition instance
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            general_info=data.get("general_info", {}),
            ai_experience=data.get("ai_experience", {}),
            traits=data.get("traits", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary.

        Returns:
            Dictionary representation of the persona
        """
        return {
            "id": self.id,
            "general_info": self.general_info,
            "ai_experience": self.ai_experience,
            "traits": self.traits,
        }


class PersonaRegistry:
    """Manages a collection of personas loaded from files.

    Supports loading personas from JSON and YAML files.
    """

    def __init__(self):
        """Initialize an empty persona registry."""
        self._personas: Dict[str, PersonaDefinition] = {}

    def load_from_file(self, file_path: str) -> None:
        """Load personas from a JSON file.

        Args:
            file_path: Path to JSON file containing persona definitions

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is invalid JSON or missing required fields
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Handle both single object and array of personas
            personas_data = data if isinstance(data, list) else [data]

            for persona_data in personas_data:
                persona = PersonaDefinition.from_dict(persona_data)
                self._personas[persona.id] = persona
                logger.info(f"Loaded persona: {persona.name} ({persona.id})")

            logger.debug(f"Successfully loaded {len(personas_data)} personas")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in persona file {file_path}: {e}")

    def load_from_dict(self, personas_data: list) -> None:
        """Load personas from a list of dictionaries.

        Args:
            personas_data: List of persona dictionaries
        """
        for persona_data in personas_data:
            persona = PersonaDefinition.from_dict(persona_data)
            self._personas[persona.id] = persona
            logger.info(f"Loaded persona: {persona.name} ({persona.id})")

    def add_persona(self, persona: PersonaDefinition) -> None:
        """Add a persona to the registry.

        Args:
            persona: PersonaDefinition to add
        """
        self._personas[persona.id] = persona
        logger.info(f"Added persona: {persona.name} ({persona.id})")

    def get_persona(self, persona_id: str) -> Optional[PersonaDefinition]:
        """Retrieve a persona by ID.

        Args:
            persona_id: ID of the persona to retrieve

        Returns:
            PersonaDefinition if found, None otherwise
        """
        return self._personas.get(persona_id)

    def get_all_personas(self) -> Dict[str, PersonaDefinition]:
        """Get all registered personas.

        Returns:
            Dictionary mapping persona IDs to PersonaDefinition objects
        """
        return self._personas.copy()

    def list_personas(self) -> list[str]:
        """List all persona IDs.

        Returns:
            List of persona IDs
        """
        return list(self._personas.keys())

    def __len__(self) -> int:
        """Return the number of personas in the registry."""
        return len(self._personas)
