"""
JCUR Types - Data structures for Universal Curriculum Specification.

Defines portable curriculum packs for language learning.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# CURRICULUM ITEMS
# =============================================================================

@dataclass
class Example:
    """An example usage of a curriculum item."""
    target: str                    # Target language text
    source: str                    # Source language translation
    reading: Optional[str] = None  # Pronunciation/reading


@dataclass
class CurriculumItem:
    """A single item in a curriculum lesson.

    Item types:
    - character: Individual letters/symbols
    - vocabulary: Words with definitions
    - grammar: Grammar patterns with explanations
    - phrase: Multi-word phrases
    - sentence: Full sentences
    - dialogue: Conversation pairs (source=input, target=response)

    For dialogue type:
    - source: User/input text (what triggers the response)
    - target: Jiyou/output text (how to respond)
    - direction: 'response' (Jiyou responds), 'initiation' (Jiyou starts), or 'either'
    """
    id: str                                  # Unique item ID within lesson
    type: str                                # character, vocabulary, grammar, phrase, sentence, dialogue
    target: str                              # Target language content (or response for dialogue)
    source: str                              # Source language content (or input for dialogue)

    # Optional fields depending on type
    target_reading: Optional[str] = None     # Pronunciation/romanization
    part_of_speech: Optional[str] = None     # noun, verb, adjective, etc.
    pattern: Optional[str] = None            # Grammar pattern
    explanation: Optional[str] = None        # Grammar explanation
    context: Optional[str] = None            # Usage context / dialogue context
    formality: Optional[str] = None          # formal, neutral, casual
    direction: Optional[str] = None          # For dialogue: response, initiation, either

    # Media
    audio: Optional[str] = None              # Path to audio file
    image: Optional[str] = None              # Path to image file

    # Metadata
    hints: List[str] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> 'CurriculumItem':
        """Create item from dictionary."""
        examples = [
            Example(**ex) if isinstance(ex, dict) else ex
            for ex in d.pop('examples', [])
        ]
        return cls(examples=examples, **d)


# =============================================================================
# LESSONS
# =============================================================================

@dataclass
class Lesson:
    """A single lesson containing multiple curriculum items."""
    lesson_id: str
    title: str
    description: str
    category: str
    difficulty: int                          # 1-5 scale
    items: List[CurriculumItem]

    # Optional
    prerequisites: List[str] = field(default_factory=list)
    estimated_minutes: int = 30
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> 'Lesson':
        """Create lesson from dictionary."""
        items = [
            CurriculumItem.from_dict(item) if isinstance(item, dict) else item
            for item in d.pop('items', [])
        ]
        return cls(items=items, **d)

    @property
    def item_count(self) -> int:
        return len(self.items)


# =============================================================================
# STAGES AND INDEX
# =============================================================================

@dataclass
class UnlockCondition:
    """Condition for unlocking a stage."""
    stage: str                    # Stage name that must be completed
    mastery: float = 0.8          # Required mastery level (0.0-1.0)

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> Optional['UnlockCondition']:
        if d is None:
            return None
        return cls(**d)


@dataclass
class Stage:
    """A stage grouping multiple lessons."""
    name: str
    lessons: List[str]                       # Lesson IDs
    unlock_condition: Optional[UnlockCondition] = None

    @classmethod
    def from_dict(cls, d: dict) -> 'Stage':
        unlock = UnlockCondition.from_dict(d.pop('unlock_condition', None))
        return cls(unlock_condition=unlock, **d)


@dataclass
class CurriculumIndex:
    """Index defining lesson order and progression."""
    stages: List[Stage]
    recommended_order: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> 'CurriculumIndex':
        stages = [Stage.from_dict(s) for s in d.get('stages', [])]
        return cls(
            stages=stages,
            recommended_order=d.get('recommended_order', [])
        )


# =============================================================================
# CURRICULUM PACK INFO
# =============================================================================

@dataclass
class JcurPackInfo:
    """Information about a .jcur curriculum pack."""
    name: str
    domain: str
    path: Path
    source_language: str
    target_language: str
    level: str
    total_lessons: int
    total_items: int
    estimated_hours: float

    # Optional
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    license: str = "CC-BY-SA-4.0"
    tags: List[str] = field(default_factory=list)
    categories: Dict[str, int] = field(default_factory=dict)


# =============================================================================
# OPERATION RESULTS
# =============================================================================

@dataclass
class JcurExportResult:
    """Result of exporting a curriculum to .jcur pack."""
    path: Path
    domain: str
    name: str
    total_lessons: int
    total_items: int
    total_size_bytes: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


@dataclass
class JcurImportResult:
    """Result of importing a .jcur pack."""
    domain: str
    source_path: Path
    installed_path: Path
    lessons_installed: int
    items_installed: int
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0
