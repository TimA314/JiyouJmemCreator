"""
JCUR Manifest - Schema and validation for curriculum pack manifests.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# MANIFEST SCHEMA
# =============================================================================

MANIFEST_SCHEMA = {
    'format_version': str,
    'jcur_spec_version': str,

    'curriculum_info': {
        'name': str,
        'domain': str,
        'description': str,
        'source_language': str,
        'target_language': str,
        'level': str,
        'tags': list,
    },

    'statistics': {
        'total_lessons': int,
        'total_items': int,
        'estimated_hours': (int, float),
        'categories': dict,
    },

    'source': {
        'author': str,
        'created': str,
        'version': str,
        'license': str,
    },

    'compatibility': {
        'min_jiyou_version': str,
        'required_features': list,
    },

    'integrity': {
        'checksum_algorithm': str,
    },
}

REQUIRED_FIELDS = [
    'format_version',
    'jcur_spec_version',
    'curriculum_info',
]

REQUIRED_CURRICULUM_INFO = [
    'name',
    'domain',
    'source_language',
    'target_language',
]


# =============================================================================
# MANIFEST OPERATIONS
# =============================================================================

def create_manifest(
    domain: str,
    name: str,
    source_language: str,
    target_language: str,
    level: str = "beginner",
    description: str = "",
    tags: Optional[List[str]] = None,
    author: str = "",
    license_type: str = "CC-BY-SA-4.0",
) -> dict:
    """
    Create a new curriculum manifest.

    Args:
        domain: Unique domain identifier (e.g., 'japanese_n5')
        name: Human-readable name
        source_language: Source language code (e.g., 'en')
        target_language: Target language code (e.g., 'ja')
        level: Difficulty level
        description: Curriculum description
        tags: Optional tags
        author: Author name
        license_type: License identifier

    Returns:
        Manifest dictionary
    """
    return {
        'format_version': '1.0',
        'jcur_spec_version': '1.0.0',

        'curriculum_info': {
            'name': name or domain,
            'domain': domain,
            'description': description,
            'source_language': source_language,
            'target_language': target_language,
            'level': level,
            'tags': tags or [],
        },

        'statistics': {
            'total_lessons': 0,
            'total_items': 0,
            'estimated_hours': 0,
            'categories': {},
        },

        'source': {
            'author': author,
            'created': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0',
            'license': license_type,
        },

        'compatibility': {
            'min_jiyou_version': '0.1.0',
            'required_features': ['text_encoder'],
        },

        'integrity': {
            'checksum_algorithm': 'sha256',
        },
    }


def load_manifest(path: Path) -> dict:
    """
    Load a manifest from file.

    Args:
        path: Path to manifest.json

    Returns:
        Manifest dictionary

    Raises:
        FileNotFoundError: If manifest doesn't exist
        json.JSONDecodeError: If manifest is invalid JSON
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(manifest: dict, path: Path) -> None:
    """
    Save a manifest to file.

    Args:
        manifest: Manifest dictionary
        path: Path to write manifest.json
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def validate_manifest(manifest: dict) -> List[str]:
    """
    Validate a manifest against the schema.

    Args:
        manifest: Manifest dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    # Check curriculum_info required fields
    if 'curriculum_info' in manifest:
        info = manifest['curriculum_info']
        for field in REQUIRED_CURRICULUM_INFO:
            if field not in info:
                errors.append(f"Missing required curriculum_info field: {field}")

    # Validate format version
    if manifest.get('format_version') != '1.0':
        errors.append(f"Unsupported format version: {manifest.get('format_version')}")

    return errors


def validate_manifest_file(path: Path) -> List[str]:
    """
    Validate a manifest file.

    Args:
        path: Path to manifest.json

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not path.exists():
        errors.append(f"Manifest not found: {path}")
        return errors

    try:
        manifest = load_manifest(path)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in manifest: {e}")
        return errors

    errors.extend(validate_manifest(manifest))
    return errors
