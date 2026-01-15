"""
Configuration management for JmemCreator CLI.

Handles loading/saving settings from ~/.jiyou/jmem_creator_settings.json
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import torch

# Settings file path (shared with GUI)
SETTINGS_FILE = Path.home() / ".jiyou" / "jmem_creator_settings.json"

# App directory
APP_DIR = Path(__file__).parent.parent
CURRICULA_DIR = APP_DIR / "curricula"


@dataclass
class Config:
    """Configuration state for CLI."""
    brain_dir: Optional[Path] = None
    worker_configs: List[Tuple[str, int, bool]] = field(default_factory=list)
    worker_presets: Dict[str, List] = field(default_factory=dict)

    # Current session settings (not persisted)
    jcur_path: Optional[Path] = None
    book_path: Optional[Path] = None
    output_path: Optional[Path] = None
    base_jmems: List[Path] = field(default_factory=list)
    recalibrate: bool = False


def load_settings() -> Config:
    """
    Load settings from disk.

    Returns:
        Config object with loaded settings
    """
    config = Config()

    if not SETTINGS_FILE.exists():
        return config

    try:
        settings = json.loads(SETTINGS_FILE.read_text())

        # Restore brain directory
        if 'brain_dir' in settings:
            path = Path(settings['brain_dir'])
            if path.exists() and (path / "api.py").exists():
                config.brain_dir = path

        # Restore worker configurations
        gpu_available = torch.cuda.is_available()
        if 'worker_configs' in settings:
            for cfg in settings['worker_configs']:
                # Handle both old 2-tuple and new 3-tuple format
                if len(cfg) == 2:
                    device, neurons = cfg
                    is_big_brain = False
                else:
                    device, neurons, is_big_brain = cfg
                # Skip GPU workers if GPU not available
                if device == 'GPU' and not gpu_available:
                    continue
                config.worker_configs.append((device, neurons, is_big_brain))

        # Restore worker presets
        if 'worker_presets' in settings:
            config.worker_presets = settings['worker_presets']

    except Exception as e:
        print(f"Warning: Failed to load settings: {e}")

    return config


def save_settings(config: Config) -> bool:
    """
    Save settings to disk.

    Args:
        config: Config object to save

    Returns:
        True if successful
    """
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

        settings = {
            'worker_configs': config.worker_configs,
            'worker_presets': config.worker_presets,
        }

        if config.brain_dir:
            settings['brain_dir'] = str(config.brain_dir)

        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        return True

    except Exception as e:
        print(f"Warning: Failed to save settings: {e}")
        return False


def find_jcur_packs() -> List[Dict]:
    """Find all .jcur directories in the local curricula folder."""
    jcur_packs = []
    if not CURRICULA_DIR.exists():
        return jcur_packs

    for path in CURRICULA_DIR.glob("*.jcur"):
        if path.is_dir():
            manifest = path / "manifest.json"
            if manifest.exists():
                try:
                    with open(manifest) as f:
                        data = json.load(f)
                        jcur_packs.append({
                            'path': path,
                            'name': data.get('name', path.stem),
                            'domain': data.get('domain', path.stem),
                            'total_items': data.get('statistics', {}).get('total_items', 0),
                        })
                except Exception:
                    pass
    return jcur_packs


def find_jmem_packs(brain_dir: Optional[Path] = None) -> List[Dict]:
    """Find all JMEM packs in jmem_packs folder (for base JMEMs selection)."""
    jmem_packs = []
    if brain_dir is None:
        return jmem_packs

    packs_dir = brain_dir / "jmem_packs"
    if not packs_dir.exists():
        return jmem_packs

    for path in packs_dir.iterdir():
        if path.is_dir():
            # Check for JMEM index (indicates trained pack)
            index_jmem = path / "index.jmem"
            manifest = path / "manifest.json"
            if index_jmem.exists() or manifest.exists():
                try:
                    name = path.name
                    total_memories = 0

                    # Try to read memory count from binary file
                    if index_jmem.exists():
                        try:
                            with open(index_jmem, 'rb') as f:
                                # Skip magic (4) + version (4) + flags (4)
                                f.seek(12)
                                # Read memory_count (4 bytes, little-endian)
                                import struct
                                total_memories = struct.unpack('<I', f.read(4))[0]
                        except Exception:
                            pass
                    elif manifest.exists():
                        with open(manifest) as f:
                            data = json.load(f)
                            total_memories = data.get('total_memories', 0)

                    jmem_packs.append({
                        'path': path,
                        'name': name,
                        'total_memories': total_memories,
                    })
                except Exception:
                    pass
    return jmem_packs


def load_brain_modules(brain_dir: Path) -> bool:
    """
    Load Brain modules from the selected directory.

    Args:
        brain_dir: Path to the brain directory

    Returns:
        True if successful
    """
    # Validate the directory contains expected files
    if not (brain_dir / "api.py").exists():
        return False

    # Add parent of brain dir to path
    parent = brain_dir.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

    try:
        # Import using the directory name as module name
        module_name = brain_dir.name
        api_module = __import__(f"{module_name}.api", fromlist=['BrainAPI'])
        # Store in globals for later access
        import cli.config as self_module
        self_module.BrainAPI = api_module.BrainAPI
        return True
    except Exception as e:
        print(f"Failed to load brain modules: {e}")
        return False


def get_brain_api():
    """Get the loaded BrainAPI class."""
    import cli.config as self_module
    return getattr(self_module, 'BrainAPI', None)
