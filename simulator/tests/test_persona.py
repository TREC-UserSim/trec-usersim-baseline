"""Tests for the persona module."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from simulator.src.persona import PersonaDefinition, PersonaRegistry


class TestPersonaDefinition:
    """Tests for PersonaDefinition class."""

    def test_persona_creation(self):
        """Test creating a persona with basic attributes."""
        persona = PersonaDefinition(
            id="persona_1",
            general_info={"gender": "Female", "age": 35},
            ai_experience={"years": 2},
            traits={"curiosity": "high"},
        )
        assert persona.id == "persona_1"
        assert persona.general_info["gender"] == "Female"
        assert persona.ai_experience["years"] == 2
        assert persona.traits["curiosity"] == "high"

    def test_persona_name_property_with_gender_and_age(self):
        """Test name property with gender and age."""
        persona = PersonaDefinition(
            id="persona_1",
            general_info={"gender": "Male", "age": 45, "education": "PhD"},
        )
        assert "Male" in persona.name
        assert "45" in persona.name
        assert "PhD" in persona.name

    def test_persona_name_property_with_only_gender(self):
        """Test name property with only gender."""
        persona = PersonaDefinition(
            id="persona_2",
            general_info={"gender": "Female"},
        )
        assert "Female" in persona.name

    def test_persona_name_property_fallback_to_id(self):
        """Test name property falls back to ID when no general_info."""
        persona = PersonaDefinition(id="test_id_123")
        assert persona.name == "test_id_123"

    def test_persona_from_dict(self):
        """Test creating persona from dictionary."""
        data = {
            "id": "persona_from_dict",
            "general_info": {"gender": "Non-binary", "age": 28},
            "ai_experience": {"comfort_level": "intermediate"},
            "traits": {"patience": "medium"},
        }
        persona = PersonaDefinition.from_dict(data)
        assert persona.id == "persona_from_dict"
        assert persona.general_info["gender"] == "Non-binary"
        assert persona.ai_experience["comfort_level"] == "intermediate"

    def test_persona_from_dict_with_missing_fields(self):
        """Test creating persona from dict with missing optional fields."""
        data = {"id": "minimal_persona"}
        persona = PersonaDefinition.from_dict(data)
        assert persona.id == "minimal_persona"
        assert persona.general_info == {}
        assert persona.ai_experience == {}
        assert persona.traits == {}

    def test_persona_from_dict_generates_id_if_missing(self):
        """Test that from_dict generates UUID if id is missing."""
        data = {
            "general_info": {"gender": "Female"},
        }
        persona = PersonaDefinition.from_dict(data)
        # Should have generated an ID (non-empty string)
        assert persona.id is not None
        assert len(persona.id) > 0

    def test_persona_to_dict(self):
        """Test converting persona to dictionary."""
        persona = PersonaDefinition(
            id="test_persona",
            general_info={"gender": "Male"},
            ai_experience={"years": 5},
            traits={"openness": "high"},
        )
        result = persona.to_dict()
        assert result["id"] == "test_persona"
        assert result["general_info"]["gender"] == "Male"
        assert result["ai_experience"]["years"] == 5
        assert result["traits"]["openness"] == "high"

    def test_persona_roundtrip_dict_conversion(self):
        """Test roundtrip conversion: PersonaDefinition -> dict -> PersonaDefinition."""
        original = PersonaDefinition(
            id="roundtrip_test",
            general_info={"gender": "Female", "age": 40},
            ai_experience={"comfort": "high"},
            traits={"intro": "yes"},
        )
        as_dict = original.to_dict()
        restored = PersonaDefinition.from_dict(as_dict)
        
        assert restored.id == original.id
        assert restored.general_info == original.general_info
        assert restored.ai_experience == original.ai_experience
        assert restored.traits == original.traits


class TestPersonaRegistry:
    """Tests for PersonaRegistry class."""

    def test_registry_initialization(self):
        """Test registry initializes empty."""
        registry = PersonaRegistry()
        assert len(registry._personas) == 0

    def test_add_persona(self):
        """Test adding a persona to the registry."""
        registry = PersonaRegistry()
        persona = PersonaDefinition(
            id="p1",
            general_info={"gender": "Male"},
        )
        registry.add_persona(persona)
        assert len(registry._personas) == 1
        assert registry.get_persona("p1") == persona

    def test_get_persona_existing(self):
        """Test retrieving an existing persona."""
        registry = PersonaRegistry()
        persona = PersonaDefinition(id="test_p")
        registry.add_persona(persona)
        retrieved = registry.get_persona("test_p")
        assert retrieved is not None
        assert retrieved.id == "test_p"

    def test_get_persona_nonexistent(self):
        """Test retrieving a nonexistent persona returns None."""
        registry = PersonaRegistry()
        assert registry.get_persona("nonexistent") is None

    def test_load_from_dict_single_persona(self):
        """Test loading a single persona from dict list."""
        registry = PersonaRegistry()
        personas_data = [
            {
                "id": "p1",
                "general_info": {"gender": "Female"},
                "ai_experience": {},
                "traits": {},
            }
        ]
        registry.load_from_dict(personas_data)
        assert len(registry._personas) == 1
        assert registry.get_persona("p1") is not None

    def test_load_from_dict_multiple_personas(self):
        """Test loading multiple personas from dict list."""
        registry = PersonaRegistry()
        personas_data = [
            {"id": "p1", "general_info": {}},
            {"id": "p2", "general_info": {}},
            {"id": "p3", "general_info": {}},
        ]
        registry.load_from_dict(personas_data)
        assert len(registry._personas) == 3
        assert registry.get_persona("p1") is not None
        assert registry.get_persona("p2") is not None
        assert registry.get_persona("p3") is not None

    def test_load_from_file_json(self):
        """Test loading personas from a JSON file."""
        with TemporaryDirectory() as tmpdir:
            # Create a test JSON file
            personas_data = [
                {
                    "id": "file_p1",
                    "general_info": {"gender": "Male", "age": 30},
                    "ai_experience": {"years": 2},
                    "traits": {},
                }
            ]
            file_path = Path(tmpdir) / "personas.json"
            with open(file_path, "w") as f:
                json.dump(personas_data, f)

            # Load from file
            registry = PersonaRegistry()
            registry.load_from_file(str(file_path))
            assert len(registry._personas) == 1
            assert registry.get_persona("file_p1") is not None

    def test_load_from_file_not_found(self):
        """Test loading from nonexistent file raises error."""
        registry = PersonaRegistry()
        with pytest.raises(FileNotFoundError):
            registry.load_from_file("/nonexistent/path/personas.json")

    def test_load_from_file_invalid_json(self):
        """Test loading invalid JSON file raises error."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "bad.json"
            with open(file_path, "w") as f:
                f.write("{ invalid json }")

            registry = PersonaRegistry()
            with pytest.raises(ValueError):
                registry.load_from_file(str(file_path))

    def test_load_from_file_single_object(self):
        """Test loading a single persona object (not in array) from file."""
        with TemporaryDirectory() as tmpdir:
            personas_data = {
                "id": "single_persona",
                "general_info": {"gender": "Female"},
                "ai_experience": {},
                "traits": {},
            }
            file_path = Path(tmpdir) / "persona.json"
            with open(file_path, "w") as f:
                json.dump(personas_data, f)

            registry = PersonaRegistry()
            registry.load_from_file(str(file_path))
            assert registry.get_persona("single_persona") is not None

    def test_registry_list_all_personas(self):
        """Test listing all personas in registry."""
        registry = PersonaRegistry()
        p1 = PersonaDefinition(id="p1")
        p2 = PersonaDefinition(id="p2")
        registry.add_persona(p1)
        registry.add_persona(p2)

        personas = list(registry._personas.values())
        assert len(personas) == 2
        assert any(p.id == "p1" for p in personas)
        assert any(p.id == "p2" for p in personas)
