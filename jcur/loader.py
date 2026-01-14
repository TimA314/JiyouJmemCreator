"""
JCUR Loader - Load and parse .jcur curriculum packs.
"""

import json
from collections import OrderedDict
from pathlib import Path
from typing import Iterator, List, Optional

from .types import (
    CurriculumIndex,
    CurriculumItem,
    JcurPackInfo,
    Lesson,
)
from .manifest import load_manifest, validate_manifest


# =============================================================================
# CURRICULUM PACK
# =============================================================================

class CurriculumPack:
    """
    A loaded .jcur curriculum pack.

    Example:
        pack = CurriculumPack.load("curricula/japanese_complete.jcur")
        for lesson in pack.get_lessons():
            for item in lesson.items:
                print(f"{item.source} -> {item.target}")
    """

    # LRU cache limit to prevent memory leaks during long training sessions
    MAX_CACHED_LESSONS = 10

    def __init__(self, path: Path):
        """
        Initialize a curriculum pack.

        Args:
            path: Path to .jcur directory
        """
        self.path = Path(path)
        self._manifest: Optional[dict] = None
        self._index: Optional[CurriculumIndex] = None
        # Use OrderedDict for LRU cache behavior (move_to_end + popitem)
        self._lessons_cache: OrderedDict = OrderedDict()

    @classmethod
    def load(cls, path: str | Path) -> 'CurriculumPack':
        """
        Load a curriculum pack from disk.

        Args:
            path: Path to .jcur directory

        Returns:
            CurriculumPack instance

        Raises:
            FileNotFoundError: If pack doesn't exist
            ValueError: If pack is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Curriculum pack not found: {path}")

        pack = cls(path)
        pack._load_manifest()
        pack._load_index()
        return pack

    def _load_manifest(self) -> None:
        """Load and validate manifest."""
        manifest_path = self.path / 'manifest.json'
        if not manifest_path.exists():
            raise ValueError(f"No manifest.json in {self.path}")

        self._manifest = load_manifest(manifest_path)
        errors = validate_manifest(self._manifest)
        if errors:
            raise ValueError(f"Invalid manifest: {errors}")

    def _load_index(self) -> None:
        """Load curriculum index if present."""
        index_path = self.path / 'index.json'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._index = CurriculumIndex.from_dict(data)

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def name(self) -> str:
        return self._manifest['curriculum_info']['name']

    @property
    def domain(self) -> str:
        return self._manifest['curriculum_info']['domain']

    @property
    def description(self) -> str:
        return self._manifest['curriculum_info'].get('description', '')

    @property
    def source_language(self) -> str:
        return self._manifest['curriculum_info']['source_language']

    @property
    def target_language(self) -> str:
        return self._manifest['curriculum_info']['target_language']

    @property
    def level(self) -> str:
        return self._manifest['curriculum_info'].get('level', 'beginner')

    @property
    def tags(self) -> List[str]:
        return self._manifest['curriculum_info'].get('tags', [])

    @property
    def total_lessons(self) -> int:
        return self._manifest['statistics'].get('total_lessons', 0)

    @property
    def total_items(self) -> int:
        return self._manifest['statistics'].get('total_items', 0)

    @property
    def estimated_hours(self) -> float:
        return self._manifest['statistics'].get('estimated_hours', 0)

    @property
    def author(self) -> str:
        return self._manifest['source'].get('author', '')

    @property
    def version(self) -> str:
        return self._manifest['source'].get('version', '1.0.0')

    @property
    def manifest(self) -> dict:
        return self._manifest

    @property
    def index(self) -> Optional[CurriculumIndex]:
        return self._index

    # =========================================================================
    # LESSON ACCESS
    # =========================================================================

    def get_lesson_ids(self) -> List[str]:
        """
        Get all lesson IDs in recommended order.

        Returns:
            List of lesson IDs
        """
        if self._index and self._index.recommended_order:
            return self._index.recommended_order

        # Fall back to scanning lessons directory
        lessons_dir = self.path / 'lessons'
        if not lessons_dir.exists():
            return []

        return sorted([
            f.stem for f in lessons_dir.glob('*.json')
        ])

    def get_lesson(self, lesson_id: str) -> Lesson:
        """
        Load a specific lesson.

        Args:
            lesson_id: Lesson identifier

        Returns:
            Lesson instance

        Raises:
            FileNotFoundError: If lesson doesn't exist
        """
        if lesson_id in self._lessons_cache:
            # Move to end for LRU behavior (most recently used)
            self._lessons_cache.move_to_end(lesson_id)
            return self._lessons_cache[lesson_id]

        lesson_path = self.path / 'lessons' / f'{lesson_id}.json'
        if not lesson_path.exists():
            raise FileNotFoundError(f"Lesson not found: {lesson_id}")

        with open(lesson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        lesson = Lesson.from_dict(data)

        # LRU eviction: remove oldest entries if cache is full
        while len(self._lessons_cache) >= self.MAX_CACHED_LESSONS:
            self._lessons_cache.popitem(last=False)  # Remove oldest (first) item

        self._lessons_cache[lesson_id] = lesson
        return lesson

    def get_lessons(self) -> Iterator[Lesson]:
        """
        Iterate through all lessons in order.

        Yields:
            Lesson instances
        """
        for lesson_id in self.get_lesson_ids():
            yield self.get_lesson(lesson_id)

    def get_all_items(self) -> Iterator[CurriculumItem]:
        """
        Iterate through all items across all lessons.

        Yields:
            CurriculumItem instances
        """
        for lesson in self.get_lessons():
            yield from lesson.items

    # =========================================================================
    # STAGE ACCESS
    # =========================================================================

    def get_stage_lessons(self, stage_name: str) -> List[str]:
        """
        Get lesson IDs for a specific stage.

        Args:
            stage_name: Stage name

        Returns:
            List of lesson IDs in the stage
        """
        if not self._index:
            return []

        for stage in self._index.stages:
            if stage.name == stage_name:
                return stage.lessons
        return []

    def get_unlocked_lessons(self, mastery: dict) -> List[str]:
        """
        Get lessons that are unlocked based on mastery.

        Args:
            mastery: Dict mapping stage names to mastery levels (0.0-1.0)

        Returns:
            List of unlocked lesson IDs
        """
        if not self._index:
            return self.get_lesson_ids()

        unlocked = []
        for stage in self._index.stages:
            # Check unlock condition
            if stage.unlock_condition:
                required_stage = stage.unlock_condition.stage
                required_mastery = stage.unlock_condition.mastery
                if mastery.get(required_stage, 0) < required_mastery:
                    continue  # Stage is locked

            unlocked.extend(stage.lessons)

        return unlocked

    # =========================================================================
    # INFO
    # =========================================================================

    def get_info(self) -> JcurPackInfo:
        """
        Get pack information.

        Returns:
            JcurPackInfo instance
        """
        return JcurPackInfo(
            name=self.name,
            domain=self.domain,
            path=self.path,
            source_language=self.source_language,
            target_language=self.target_language,
            level=self.level,
            total_lessons=self.total_lessons,
            total_items=self.total_items,
            estimated_hours=self.estimated_hours,
            description=self.description,
            author=self.author,
            version=self.version,
            tags=self.tags,
            categories=self._manifest['statistics'].get('categories', {}),
        )
