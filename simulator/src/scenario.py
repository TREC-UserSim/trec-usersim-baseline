"""Scenario module providing data classes for goal, persona, and interaction.

This module defines the core data structures for representing conversational
scenarios: goals to be achieved, personas (simulated users), and interactions
between personas and goals.
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
