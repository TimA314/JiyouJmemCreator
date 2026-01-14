"""
JCUR Exporter - Create .jcur curriculum packs.
"""

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from .types import JcurExportResult, Lesson
from .manifest import create_manifest, save_manifest


# =============================================================================
# JCUR EXPORTER
# =============================================================================

class JcurExporter:
    """
    Creates .jcur curriculum packs.

    Example:
        exporter = JcurExporter()
        result = exporter.export(
            output_path=Path('./packs'),
            domain='japanese_n5',
            name='Japanese N5',
            source_language='en',
            target_language='ja',
            lessons=[lesson1, lesson2, ...],
        )
    """

    def __init__(self):
        """Initialize exporter."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def export(
        self,
        output_path: Path,
        domain: str,
        name: str,
        source_language: str,
        target_language: str,
        lessons: List[Lesson],
        level: str = "beginner",
        description: str = "",
        tags: Optional[List[str]] = None,
        author: str = "",
        license_type: str = "CC-BY-SA-4.0",
        assets_path: Optional[Path] = None,
    ) -> JcurExportResult:
        """
        Export lessons to a .jcur pack.

        Args:
            output_path: Directory to create pack in
            domain: Unique domain identifier
            name: Human-readable name
            source_language: Source language code
            target_language: Target language code
            lessons: List of Lesson objects to export
            level: Difficulty level
            description: Pack description
            tags: Optional tags
            author: Author name
            license_type: License identifier
            assets_path: Optional path to assets to bundle

        Returns:
            JcurExportResult with export status
        """
        start_time = time.time()
        self.errors = []
        self.warnings = []

        output_path = Path(output_path)
        pack_path = output_path / f'{domain}.jcur'

        # Create pack directory
        try:
            pack_path.mkdir(parents=True, exist_ok=True)
            (pack_path / 'lessons').mkdir(exist_ok=True)
        except Exception as e:
            self.errors.append(f"Failed to create pack directory: {e}")
            return self._make_error_result(pack_path, domain, name)

        # Export lessons
        total_items = 0
        categories: Dict[str, int] = {}

        for lesson in lessons:
            try:
                self._export_lesson(pack_path / 'lessons', lesson)
                total_items += lesson.item_count

                # Count categories
                cat = lesson.category
                categories[cat] = categories.get(cat, 0) + lesson.item_count

            except Exception as e:
                self.warnings.append(f"Error exporting lesson {lesson.lesson_id}: {e}")

        # Create index
        self._create_index(pack_path, lessons)

        # Copy assets if provided
        if assets_path and assets_path.exists():
            self._copy_assets(assets_path, pack_path / 'assets')

        # Create manifest
        manifest = create_manifest(
            domain=domain,
            name=name,
            source_language=source_language,
            target_language=target_language,
            level=level,
            description=description,
            tags=tags,
            author=author,
            license_type=license_type,
        )

        # Update statistics
        manifest['statistics']['total_lessons'] = len(lessons)
        manifest['statistics']['total_items'] = total_items
        manifest['statistics']['estimated_hours'] = sum(
            l.estimated_minutes for l in lessons
        ) / 60.0
        manifest['statistics']['categories'] = categories

        save_manifest(manifest, pack_path / 'manifest.json')

        # Compute checksums
        checksums = self._compute_checksums(pack_path)
        with open(pack_path / 'checksums.json', 'w') as f:
            json.dump(checksums, f, indent=2)

        # Calculate total size
        total_size = sum(
            f.stat().st_size for f in pack_path.rglob('*') if f.is_file()
        )

        duration = time.time() - start_time

        return JcurExportResult(
            path=pack_path,
            domain=domain,
            name=name,
            total_lessons=len(lessons),
            total_items=total_items,
            total_size_bytes=total_size,
            duration_seconds=duration,
            errors=self.errors,
            warnings=self.warnings,
        )

    def _export_lesson(self, lessons_dir: Path, lesson: Lesson) -> None:
        """Export a single lesson to JSON."""
        lesson_data = {
            'lesson_id': lesson.lesson_id,
            'title': lesson.title,
            'description': lesson.description,
            'category': lesson.category,
            'difficulty': lesson.difficulty,
            'prerequisites': lesson.prerequisites,
            'estimated_minutes': lesson.estimated_minutes,
            'items': [
                self._item_to_dict(item) for item in lesson.items
            ],
        }

        lesson_path = lessons_dir / f'{lesson.lesson_id}.json'
        with open(lesson_path, 'w', encoding='utf-8') as f:
            json.dump(lesson_data, f, indent=2, ensure_ascii=False)

    def _item_to_dict(self, item) -> dict:
        """Convert CurriculumItem to dictionary."""
        d = {
            'id': item.id,
            'type': item.type,
            'target': item.target,
            'source': item.source,
        }

        # Add optional fields if present
        optional_fields = [
            'target_reading', 'part_of_speech', 'pattern', 'explanation',
            'context', 'formality', 'audio', 'image'
        ]
        for field in optional_fields:
            value = getattr(item, field, None)
            if value:
                d[field] = value

        if item.hints:
            d['hints'] = item.hints
        if item.tags:
            d['tags'] = item.tags
        if item.examples:
            d['examples'] = [
                {'target': ex.target, 'source': ex.source, 'reading': ex.reading}
                for ex in item.examples
            ]

        return d

    def _create_index(self, pack_path: Path, lessons: List[Lesson]) -> None:
        """Create index.json with lesson order."""
        index = {
            'stages': [
                {
                    'name': 'All Lessons',
                    'lessons': [l.lesson_id for l in lessons],
                    'unlock_condition': None,
                }
            ],
            'recommended_order': [l.lesson_id for l in lessons],
        }

        with open(pack_path / 'index.json', 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _copy_assets(self, source: Path, dest: Path) -> None:
        """Copy assets directory."""
        if source.exists():
            shutil.copytree(source, dest, dirs_exist_ok=True)

    def _compute_checksums(self, pack_path: Path) -> dict:
        """Compute SHA256 checksums for all files."""
        checksums = {}

        for file_path in pack_path.rglob('*'):
            if file_path.is_file() and file_path.name != 'checksums.json':
                rel_path = file_path.relative_to(pack_path)
                checksums[str(rel_path)] = self._sha256_file(file_path)

        return checksums

    def _sha256_file(self, path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _make_error_result(
        self, path: Path, domain: str, name: str
    ) -> JcurExportResult:
        """Create an error result."""
        return JcurExportResult(
            path=path,
            domain=domain,
            name=name,
            total_lessons=0,
            total_items=0,
            errors=self.errors,
            warnings=self.warnings,
        )
