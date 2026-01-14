"""
JCUR - Universal Curriculum Specification for Jiyou.

Portable curriculum packs for language learning.

Example:
    from Brain.jcur import CurriculumPack, JcurImporter, JcurExporter

    # Load a curriculum
    pack = CurriculumPack.load("curricula/japanese_complete.jcur")
    for lesson in pack.get_lessons():
        for item in lesson.items:
            print(f"{item.source} -> {item.target}")

    # Install a curriculum
    importer = JcurImporter()
    result = importer.install(Path("curricula/japanese_complete.jcur"))

    # List installed curricula
    packs = importer.list_installed()
"""

from .types import (
    CurriculumItem,
    CurriculumIndex,
    Example,
    JcurExportResult,
    JcurImportResult,
    JcurPackInfo,
    Lesson,
    Stage,
    UnlockCondition,
)
from .loader import CurriculumPack
from .exporter import JcurExporter
from .importer import JcurImporter

__all__ = [
    # Types
    'CurriculumItem',
    'CurriculumIndex',
    'Example',
    'JcurExportResult',
    'JcurImportResult',
    'JcurPackInfo',
    'Lesson',
    'Stage',
    'UnlockCondition',
    # Classes
    'CurriculumPack',
    'JcurExporter',
    'JcurImporter',
]
