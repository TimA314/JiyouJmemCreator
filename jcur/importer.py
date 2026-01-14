"""
JCUR Importer - Install .jcur curriculum packs with integrity verification.
"""

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import List, Optional

from .types import JcurImportResult, JcurPackInfo
from .manifest import load_manifest, validate_manifest_file
from .loader import CurriculumPack


# =============================================================================
# DEFAULT PATHS
# =============================================================================

DEFAULT_CURRICULA_DIR = Path('jiyou_curricula')


# =============================================================================
# JCUR IMPORTER
# =============================================================================

class JcurImporter:
    """
    Installs .jcur curriculum packs with checksum verification.

    Example:
        importer = JcurImporter()
        result = importer.install(
            pack_path=Path('japanese_n5.jcur'),
            target_path=Path('jiyou_curricula'),
        )
    """

    def __init__(self):
        """Initialize importer."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def install(
        self,
        pack_path: Path,
        target_path: Optional[Path] = None,
    ) -> JcurImportResult:
        """
        Install a .jcur pack to the curricula directory.

        Args:
            pack_path: Path to .jcur directory
            target_path: Where to install (default: jiyou_curricula)

        Returns:
            JcurImportResult with installation status
        """
        start_time = time.time()
        self.errors = []
        self.warnings = []

        pack_path = Path(pack_path)
        target_path = Path(target_path) if target_path else DEFAULT_CURRICULA_DIR

        # Validate manifest
        validation_errors = validate_manifest_file(pack_path / 'manifest.json')
        if validation_errors:
            self.errors.extend(validation_errors)
            return self._make_error_result(pack_path, target_path)

        # Verify checksums
        checksum_errors = self._verify_checksums(pack_path)
        if checksum_errors:
            self.errors.extend(checksum_errors)
            return self._make_error_result(pack_path, target_path)

        # Load manifest to get domain
        manifest = load_manifest(pack_path / 'manifest.json')
        domain = manifest['curriculum_info']['domain']

        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        installed_path = target_path / f'{domain}.jcur'

        # Check if already installed
        if installed_path.exists():
            self.warnings.append(f"Replacing existing curriculum: {domain}")
            shutil.rmtree(installed_path)

        # Copy pack
        try:
            shutil.copytree(pack_path, installed_path)
        except Exception as e:
            self.errors.append(f"Failed to install pack: {e}")
            return self._make_error_result(pack_path, target_path)

        # Count installed items
        lessons_installed = 0
        items_installed = 0

        lessons_dir = installed_path / 'lessons'
        if lessons_dir.exists():
            for lesson_file in lessons_dir.glob('*.json'):
                lessons_installed += 1
                with open(lesson_file, 'r', encoding='utf-8') as f:
                    lesson_data = json.load(f)
                    items_installed += len(lesson_data.get('items', []))

        duration = time.time() - start_time

        return JcurImportResult(
            domain=domain,
            source_path=pack_path,
            installed_path=installed_path,
            lessons_installed=lessons_installed,
            items_installed=items_installed,
            duration_seconds=duration,
            errors=self.errors,
            warnings=self.warnings,
        )

    def uninstall(
        self,
        domain: str,
        target_path: Optional[Path] = None,
    ) -> bool:
        """
        Uninstall a curriculum pack.

        Args:
            domain: Domain of pack to uninstall
            target_path: Curricula directory

        Returns:
            True if successfully uninstalled
        """
        target_path = Path(target_path) if target_path else DEFAULT_CURRICULA_DIR
        installed_path = target_path / f'{domain}.jcur'

        if installed_path.exists():
            shutil.rmtree(installed_path)
            return True
        return False

    def list_installed(
        self,
        target_path: Optional[Path] = None,
    ) -> List[JcurPackInfo]:
        """
        List all installed curriculum packs.

        Args:
            target_path: Curricula directory

        Returns:
            List of JcurPackInfo for installed packs
        """
        target_path = Path(target_path) if target_path else DEFAULT_CURRICULA_DIR
        packs = []

        if not target_path.exists():
            return packs

        for pack_dir in target_path.glob('*.jcur'):
            if pack_dir.is_dir():
                try:
                    pack = CurriculumPack.load(pack_dir)
                    packs.append(pack.get_info())
                except Exception as e:
                    self.warnings.append(f"Error loading {pack_dir}: {e}")

        return packs

    def get_pack_info(self, pack_path: Path) -> Optional[JcurPackInfo]:
        """
        Get information about a .jcur pack without installing.

        Args:
            pack_path: Path to .jcur directory

        Returns:
            JcurPackInfo or None if invalid
        """
        try:
            pack = CurriculumPack.load(pack_path)
            return pack.get_info()
        except Exception:
            return None

    def _verify_checksums(self, pack_path: Path) -> List[str]:
        """
        Verify all files against checksums.json.

        Returns:
            List of error messages (empty = all valid)
        """
        checksums_file = pack_path / 'checksums.json'
        if not checksums_file.exists():
            return ["checksums.json not found - cannot verify integrity"]

        try:
            with open(checksums_file, 'r') as f:
                expected = json.load(f)
        except json.JSONDecodeError as e:
            return [f"Invalid checksums.json: {e}"]

        errors = []
        for rel_path, expected_hash in expected.items():
            file_path = pack_path / rel_path
            if not file_path.exists():
                errors.append(f"Missing file: {rel_path}")
                continue

            actual_hash = self._sha256_file(file_path)
            if actual_hash != expected_hash:
                errors.append(f"Checksum mismatch: {rel_path}")

        return errors

    def _sha256_file(self, path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _make_error_result(
        self, pack_path: Path, target_path: Path
    ) -> JcurImportResult:
        """Create an error result."""
        return JcurImportResult(
            domain="",
            source_path=pack_path,
            installed_path=target_path,
            lessons_installed=0,
            items_installed=0,
            errors=self.errors,
            warnings=self.warnings,
        )
