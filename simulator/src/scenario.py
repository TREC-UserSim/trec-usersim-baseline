"""Scenario module providing data classes for goal, persona, and interaction.

This module defines the core data structures for representing conversational
scenarios: goals to be achieved, personas (simulated users), and interactions
between personas and goals.

Also includes legacy PersonaDefinition and PersonaRegistry for backward
compatibility with existing code.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Goal:
    """Represents a conversation goal within a scenario.

    The API may provide either a ``topic`` field (new schema) or a ``target``
    field (legacy). Both are supported; ``topic`` is the canonical attribute.

    Attributes:
        id: Unique identifier for the goal
        context: Contextual information about the goal
        topic: The main topic or target of the goal
        target: Legacy field name (mapped to topic)
        discipline: Optional discipline or domain area
    """

    id: Optional[str] = None
    context: str = ""
    # New field name
    topic: str = ""
    # Legacy field name – kept for backward compatibility
    target: Optional[str] = None
    discipline: Optional[str] = None

    def __post_init__(self):
        # If legacy ``target`` is provided and ``topic`` is empty, use it.
        if self.target and not self.topic:
            self.topic = self.target


@dataclass
class PersonaGeneralInfo:
    """General information about a persona.

    Attributes:
        gender: Gender identity
        age: Age or age range
        highest_education: Highest level of education
        proficiency_in_english: English language proficiency level
        tools_used_for_dataset_search: List of tools used for searching datasets
    """

    gender: Optional[str] = None
    age: Optional[str] = None
    highest_education: Optional[str] = None
    proficiency_in_english: Optional[str] = None
    tools_used_for_dataset_search: List[str] = field(default_factory=list)


@dataclass
class PersonaExperience:
    """AI experience and perception attributes of a persona.

    Attributes:
        trust: Level of trust in AI systems
        perceived_human_likeness: Perception of AI human-likeness
    """

    trust: Optional[str] = None
    perceived_human_likeness: Optional[str] = None


@dataclass
class PersonaTraits:
    """Personality and interaction traits of a persona.

    Attributes:
        frustration_threshold: How quickly the persona gets frustrated
        interaction_style: Preferred style of interaction
    """

    frustration_threshold: Optional[str] = None
    interaction_style: Optional[str] = None


@dataclass
class Persona:
    """Represents a user persona within a scenario.

    A persona encapsulates demographic information, AI experience, and
    personality traits for simulating a realistic user interaction.

    Attributes:
        general_info: General demographic and background information
        experience_with_ai: AI-related experience and perceptions
        individual_traits: Personality and interaction traits
    """

    general_info: PersonaGeneralInfo = field(default_factory=PersonaGeneralInfo)
    experience_with_ai: PersonaExperience = field(default_factory=PersonaExperience)
    individual_traits: PersonaTraits = field(default_factory=PersonaTraits)


@dataclass
class PersonaGoalInteraction:
    """Interaction details between a persona and a goal.

    Captures domain-specific knowledge and familiarity for a persona
    in the context of a particular goal.

    Attributes:
        domain_familiarity: The persona's familiarity with the goal's domain
        known_datasets: List of datasets already known to the persona
    """

    domain_familiarity: Optional[str] = None
    known_datasets: List[str] = field(default_factory=list)


@dataclass
class Scenario:
    """Bundles goal, persona, and interaction details for a run.

    A scenario represents a complete context for a conversation:
    - A goal to be achieved
    - A persona (simulated user)
    - Interaction details specific to this persona-goal pair

    Attributes:
        goal: The Goal to be pursued
        persona: The Persona involved in the conversation
        persona_goal_interaction: Details about the interaction between them
    """

    goal: Goal
    persona: Persona
    persona_goal_interaction: PersonaGoalInteraction = field(
        default_factory=PersonaGoalInteraction
    )


# Legacy classes for backward compatibility


class PersonaDefinition:
    """Legacy persona definition wrapper for backward compatibility.

    This wraps persona data in a structured format that's compatible with
    older code that expects to work with PersonaDefinition objects.

    New code should use the Persona dataclass instead.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        general_info: Optional[Dict[str, Any]] = None,
        ai_experience: Optional[Dict[str, Any]] = None,
        traits: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a PersonaDefinition.

        Args:
            id: Unique identifier (auto-generated UUID if not provided)
            general_info: General demographic information
            ai_experience: AI experience and perception attributes
            traits: Personality and interaction traits
        """
        import uuid

        self.id = id if id is not None else str(uuid.uuid4())
        self.general_info = general_info or {}
        self.ai_experience = ai_experience or {}
        self.traits = traits or {}

    @property
    def name(self) -> str:
        """Generate a human-readable name from general info.

        Combines gender, age, and education if available,
        otherwise falls back to the ID.

        Returns:
            A descriptive name for the persona
        """
        parts = []

        # Add gender
        if "gender" in self.general_info:
            parts.append(self.general_info["gender"])

        # Add age
        if "age" in self.general_info:
            parts.append(str(self.general_info["age"]))

        # Add education
        if "education" in self.general_info:
            parts.append(self.general_info["education"])

        if parts:
            return " ".join(parts)
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "general_info": self.general_info,
            "ai_experience": self.ai_experience,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonaDefinition":
        """Create from dictionary.

        Generates an ID if missing.

        Args:
            data: Dictionary with persona data

        Returns:
            PersonaDefinition instance
        """
        return cls(
            id=data.get("id"),  # Will auto-generate if None
            general_info=data.get("general_info"),
            ai_experience=data.get("ai_experience"),
            traits=data.get("traits"),
        )

    def __repr__(self) -> str:
        return f"PersonaDefinition({self.id})"

    def __eq__(self, other: Any) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, PersonaDefinition):
            return False
        return (
            self.id == other.id
            and self.general_info == other.general_info
            and self.ai_experience == other.ai_experience
            and self.traits == other.traits
        )


class PersonaRegistry:
    """Registry for managing persona definitions.

    Provides methods to load personas from files and manage them in memory.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._personas: Dict[str, PersonaDefinition] = {}

    def load_from_file(self, filepath: str) -> None:
        """Load personas from a JSON file.

        Supports both single persona object and list of personas.

        Args:
            filepath: Path to JSON file containing persona definitions

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Persona file not found: {filepath}")

        try:
            with open(path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")

        # Handle both single persona and list of personas
        personas_data = data if isinstance(data, list) else [data]

        for persona_data in personas_data:
            persona = PersonaDefinition.from_dict(persona_data)
            self._personas[persona.id] = persona

    def load_from_dict(self, personas_data: List[Dict[str, Any]]) -> None:
        """Load personas from a list of dictionaries.

        Args:
            personas_data: List of dictionaries containing persona data
        """
        for persona_data in personas_data:
            persona = PersonaDefinition.from_dict(persona_data)
            self._personas[persona.id] = persona

    def get_persona(self, persona_id: str) -> Optional[PersonaDefinition]:
        """Get a persona by ID.

        Args:
            persona_id: The persona identifier

        Returns:
            PersonaDefinition or None if not found
        """
        return self._personas.get(persona_id)

    def get_all_personas(self) -> List[PersonaDefinition]:
        """Get all registered personas.

        Returns:
            List of PersonaDefinition objects
        """
        return list(self._personas.values())

    def list_personas(self) -> List[str]:
        """Get list of persona IDs.

        Returns:
            List of persona identifiers
        """
        return list(self._personas.keys())

    def add_persona(self, persona: PersonaDefinition) -> None:
        """Add a persona to the registry.

        Args:
            persona: PersonaDefinition to add
        """
        self._personas[persona.id] = persona

    def __len__(self) -> int:
        """Get number of registered personas."""
        return len(self._personas)

    def __repr__(self) -> str:
        return f"PersonaRegistry({len(self._personas)} personas)"

