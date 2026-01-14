#!/usr/bin/env python3
"""
JMEM Creator GUI - Train JCUR curricula to generate JMEM packs.

Simple PyQt5 GUI for creating photographic memory packs from curricula.
Requires JiYouBrain (select brain directory on first run).

Usage:
    python jmem_creator_gui.py
"""

import gc
import json
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QProgressBar, QPlainTextEdit,
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QCheckBox,
    QStackedWidget, QFrame, QListWidget, QAbstractItemView, QSpinBox,
)

import torch

# =============================================================================
# Dynamic Brain Module Loading
# =============================================================================

# Import jcur locally (bundled with JMEM Creator)
from jcur import CurriculumPack

# Global placeholders - loaded dynamically when brain directory is selected
BrainAPI = None
BookLoader = None
_brain_dir: Optional[Path] = None

# Settings file for persistence
SETTINGS_FILE = Path.home() / ".jiyou" / "jmem_creator_settings.json"


def load_brain_modules(brain_dir: Path) -> bool:
    """
    Load Brain modules from the selected directory.

    Args:
        brain_dir: Path to the brain directory (e.g., /home/user/Documents/JiYouBrain)

    Returns:
        True if successful, False otherwise
    """
    global BrainAPI, BookLoader, _brain_dir

    # Validate the directory contains expected files
    if not (brain_dir / "api.py").exists():
        return False

    # Add parent of brain dir to path (e.g., /home/user/Documents)
    parent = brain_dir.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

    try:
        # Import using the directory name as module name
        module_name = brain_dir.name  # e.g., "JiYouBrain"

        api_module = __import__(f"{module_name}.api", fromlist=['BrainAPI'])
        BrainAPI = api_module.BrainAPI

        # Try to import BookLoader (optional, for PDF training)
        try:
            book_module = __import__(f"{module_name}.tools.book_loader", fromlist=['BookLoader'])
            BookLoader = book_module.BookLoader
        except ImportError:
            BookLoader = None

        _brain_dir = brain_dir
        return True
    except Exception as e:
        print(f"Failed to load brain modules: {e}")
        return False


def get_brain_dir() -> Optional[Path]:
    """Get the currently loaded brain directory."""
    return _brain_dir


# =============================================================================
# JCUR Discovery
# =============================================================================

# App directory (where this script lives)
APP_DIR = Path(__file__).parent
CURRICULA_DIR = APP_DIR / "curricula"


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
    """Find all JMEM packs in jiyou_packs folder (for base JMEMs selection)."""
    jmem_packs = []
    if brain_dir is None:
        brain_dir = _brain_dir
    if brain_dir is None:
        return jmem_packs
    packs_dir = brain_dir / "jmem_packs"
    if not packs_dir.exists():
        return jmem_packs
    for path in packs_dir.iterdir():
        if path.is_dir():
            # Check for JMEM index (indicates trained pack)
            jmem_index = path / "jmem_index"
            manifest = path / "manifest.json"
            if jmem_index.exists() or manifest.exists():
                try:
                    name = path.name
                    total_memories = 0
                    if manifest.exists():
                        with open(manifest) as f:
                            data = json.load(f)
                            name = data.get('name', path.name)
                            total_memories = data.get('total_memories', 0)
                    jmem_packs.append({
                        'path': path,
                        'name': name,
                        'total_memories': total_memories,
                    })
                except Exception:
                    pass
    return jmem_packs


# =============================================================================
# Progress Save/Load (for resume)
# =============================================================================

def get_progress_path(jmem_path: Path) -> Path:
    return jmem_path / "training_progress.json"


def get_log_path(jmem_path: Path) -> Path:
    """Get path to detailed training log file (for Claude monitoring)."""
    return jmem_path / "training_log.jsonl"


# Log buffer for batched writes (reduces disk I/O overhead)
_log_buffer: List[Dict] = []
LOG_FLUSH_INTERVAL = 50  # Flush every N trials


def log_trial(jmem_path: Path, trial_data: Dict):
    """Buffer a trial result for batched writing."""
    _log_buffer.append(trial_data)
    if len(_log_buffer) >= LOG_FLUSH_INTERVAL:
        flush_log_buffer(jmem_path)


def flush_log_buffer(jmem_path: Path):
    """Write buffered logs to disk."""
    global _log_buffer
    if not _log_buffer:
        return
    log_path = get_log_path(jmem_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        for entry in _log_buffer:
            f.write(json.dumps(entry) + '\n')
    _log_buffer = []


def save_progress(jmem_path: Path, lesson_idx: int, item_idx: int,
                  correct_count: int, total_count: int, epoch: int):
    progress = {
        'lesson_idx': lesson_idx,
        'item_idx': item_idx,
        'correct_count': correct_count,
        'total_count': total_count,
        'epoch': epoch,
    }
    progress_path = get_progress_path(jmem_path)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_path, 'w') as f:
        json.dump(progress, f, indent=2)


def load_progress(jmem_path: Path) -> Optional[Dict]:
    progress_path = get_progress_path(jmem_path)
    if progress_path.exists():
        with open(progress_path, 'r') as f:
            return json.load(f)
    return None


def clear_progress(jmem_path: Path):
    progress_path = get_progress_path(jmem_path)
    if progress_path.exists():
        progress_path.unlink()


def create_or_update_manifest(
    jmem_path: Path,
    jcur_name: str = None,
    dependencies: Optional[List[str]] = None,
):
    """
    Create or update manifest.json for the JMEM pack.

    Args:
        jmem_path: Path to the JMEM pack directory
        jcur_name: Name of the source JCUR curriculum
        dependencies: List of base JMEM paths used during training
    """
    manifest_path = jmem_path / "manifest.json"

    # Load existing manifest if present
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "name": jcur_name or jmem_path.name,
            "version": "1.0.0",
            "description": f"JMEM pack trained from {jcur_name or jmem_path.name}",
            "author": "Jiyou Training",
            "created_at": datetime.now().isoformat(),
            "tags": [],
        }

    # Count memories in each partition
    memory_counts = {}
    for partition in ["skills", "knowledge"]:
        partition_path = jmem_path / partition
        if partition_path.exists():
            memory_counts[partition] = {}
            for level in ["episodic", "semantic", "conceptual", "schematic"]:
                level_path = partition_path / level
                if level_path.exists():
                    count = len(list(level_path.glob("*.json"))) + len(list(level_path.glob("*.pt")))
                    if count > 0:
                        memory_counts[partition][level] = count

    # Count total from jmem_index if available
    total_memories = 0
    jmem_index_path = jmem_path / "jmem_index" / "memories.json"
    if jmem_index_path.exists():
        try:
            with open(jmem_index_path, 'r') as f:
                index_data = json.load(f)
                total_memories = index_data.get("stats", {}).get("total_memories", 0)
        except:
            pass

    # Update manifest
    manifest["memory_counts"] = memory_counts
    manifest["total_memories"] = total_memories
    manifest["updated_at"] = datetime.now().isoformat()

    # Record dependencies (base JMEMs used during training)
    if dependencies:
        manifest["dependencies"] = [
            {"name": Path(p).name, "path": str(p)}
            for p in dependencies
        ]

    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


# =============================================================================
# Training Worker
# =============================================================================

class TrainingWorker(QThread):
    """Background thread for training."""

    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, int, str)  # current, total, lesson_name
    stats_update = pyqtSignal(float, int, int)   # accuracy, correct, total
    training_finished = pyqtSignal()
    training_error = pyqtSignal(str)

    def __init__(
        self,
        jmem_path: Path,
        resume: bool = False,
        use_gpu: bool = True,
        source_type: str = "jcur",
        jcur_path: Optional[Path] = None,
        pdf_path: Optional[str] = None,
        base_jmems: Optional[List[str]] = None,
        cpu_neurons: int = 400000,
    ):
        super().__init__()
        self.jmem_path = jmem_path
        self.resume = resume
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.source_type = source_type  # "jcur" or "book"
        self.jcur_path = jcur_path
        self.pdf_path = pdf_path
        self.base_jmems = base_jmems or []  # Paths to load as read-only context
        self.cpu_neurons = cpu_neurons

        # Control flags
        self._stop_flag = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially

        # Brain reference (for cleanup)
        self.brain: Optional[BrainAPI] = None

        # Training settings (optimized)
        # Reduced encode_steps from 12→6 to reduce recency bias decay
        self.encode_steps = 6
        self.hold_steps = 8
        self.max_retries = 5  # Retries per attempt within train_sequence
        self.gc_interval = 50
        self.status_interval = 20

        # Mastery settings - Jiyou must master each item before proceeding
        self.mastery_required = True  # Require mastery before moving to next item
        self.mastery_max_attempts = 500  # Max attempts before flagging as problematic and skipping
        self.mastery_log_interval = 10  # Log progress every N mastery attempts
        self.jmem_stats_interval = 10  # Log JMEM stats every N items
        self.jmem_save_interval = 50  # Save JMEM to disk every N items (for crash recovery)

        # Book training settings
        self.chunk_size = 128  # Characters per chunk
        self.chunk_overlap = 32  # Overlap between chunks

    def log(self, msg: str):
        """Emit timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{timestamp}] {msg}")

    def stop(self):
        """Request graceful stop."""
        self._stop_flag = True
        self._pause_event.set()  # Unpause to allow loop to exit

    def pause(self):
        """Pause training."""
        self._pause_event.clear()

    def unpause(self):
        """Resume training."""
        self._pause_event.set()

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def run(self):
        """Main training loop."""
        try:
            self._run_training()
        except Exception as e:
            self.training_error.emit(str(e))
        finally:
            self._cleanup()
            self.training_finished.emit()

    def _run_training(self):
        """Core training logic - dispatches to appropriate training method."""
        if self.source_type == "book":
            self._train_book()
        else:
            self._train_jcur()

    def _train_jcur(self):
        """Train on JCUR curriculum pack."""
        # Load JCUR pack
        self.log(f"Loading JCUR: {self.jcur_path.name}")
        pack = CurriculumPack.load(self.jcur_path)
        info = pack.get_info()
        lesson_ids = pack.get_lesson_ids()
        total_items = info.total_items

        self.log(f"Pack: {info.name}")
        self.log(f"Lessons: {len(lesson_ids)}, Items: {total_items}")

        # Initialize brain
        # Use text mode for JMEM training (optimized for text-only, fits on GPU)
        device = 'cuda' if self.use_gpu else 'cpu'
        self.log(f"Initializing brain ({device.upper()} mode)...")
        self.brain = BrainAPI.create(
            mode='text',  # Text mode for JMEM training
            device=device,
            cpu_neurons=self.cpu_neurons,
        )
        self.log(f"Brain ready. Input size: {self.brain._input_size}")

        # Initialize JMEM index
        jmem_file = self.jmem_path / "index.jmem"
        self.brain.init_jmem_index(
            path=str(jmem_file) if jmem_file.exists() else None,
            use_consciousness=False,
        )
        if self.brain._jmem_index:
            stats = self.brain.get_jmem_index_stats()
            if stats and stats['total_memories'] > 0:
                self.log(f"JMEM Index loaded: {stats['total_memories']} memories")

        # Load base JMEMs (read-only context for training)
        if self.base_jmems:
            self.log(f"Loading {len(self.base_jmems)} base JMEM(s)...")
            for base_path in self.base_jmems:
                try:
                    base_jmem = Path(base_path) / "index.jmem"
                    if base_jmem.exists():
                        # Import as read-only (for retrieval context, not modification)
                        result = self.brain.import_jmem(str(base_path), read_only=True)
                        imported = result.get('imported', 0) if isinstance(result, dict) else 0
                        self.log(f"  Loaded base JMEM: {Path(base_path).name} ({imported} memories)")
                    else:
                        self.log(f"  Skipped {Path(base_path).name} (no index.jmem)")
                except Exception as e:
                    self.log(f"  Warning: Could not load base JMEM {base_path}: {e}")

        # Check for resume
        start_epoch = 0
        start_lesson_idx = 0
        start_item_idx = 0
        correct_count = 0
        total_count = 0
        item_counter = 0

        if self.resume:
            progress = load_progress(self.jmem_path)
            if progress:
                start_epoch = progress['epoch']
                start_lesson_idx = progress['lesson_idx']
                start_item_idx = progress['item_idx']
                correct_count = progress['correct_count']
                total_count = progress['total_count']
                item_counter = total_count
                self.log(f"Resuming: lesson {start_lesson_idx + 1}, item {start_item_idx}")

        self.log("Training started...")

        current_epoch = start_epoch
        current_lesson_idx = start_lesson_idx
        current_item_idx = start_item_idx

        epochs = 1

        for epoch in range(start_epoch, epochs):
            current_epoch = epoch
            lesson_start = start_lesson_idx if epoch == start_epoch else 0

            for lesson_idx, lesson_id in enumerate(lesson_ids):
                if self._stop_flag:
                    break

                if lesson_idx < lesson_start:
                    continue

                current_lesson_idx = lesson_idx
                lesson = pack.get_lesson(lesson_id)
                lesson_name = f"{lesson.title} ({lesson_idx + 1}/{len(lesson_ids)})"
                self.log(f"Lesson: {lesson_name}")

                # Start learning session
                self.brain.start_learning_session('echo', target_jmem_path=self.jmem_path)

                item_start = start_item_idx if (epoch == start_epoch and lesson_idx == start_lesson_idx) else 0

                for item_idx, item in enumerate(lesson.items):
                    if self._stop_flag:
                        break

                    # Check pause (blocks until unpaused)
                    if not self._pause_event.is_set():
                        save_progress(
                            self.jmem_path, lesson_idx, item_idx,
                            correct_count, total_count, epoch
                        )
                        self.log("Paused. Progress saved.")
                        self._pause_event.wait()
                        if self._stop_flag:
                            break
                        self.log("Resumed.")

                    if item_idx < item_start:
                        continue

                    current_item_idx = item_idx
                    item_counter += 1

                    # For dialogue: encode source (user input), decode target (Jiyou response)
                    # For other types: encode and decode the same target text
                    if item.type == "dialogue":
                        encode_text = item.source if item.source else item.target
                        target_text = item.target
                    else:
                        encode_text = item.target
                        target_text = item.target

                    # === MASTERY LOOP ===
                    # Keep training on this item until mastered or max attempts reached
                    mastery_attempt = 0
                    mastered = False
                    item_start_time = time.time()

                    while not mastered and mastery_attempt < self.mastery_max_attempts:
                        if self._stop_flag:
                            break

                        # Check pause within mastery loop
                        if not self._pause_event.is_set():
                            save_progress(
                                self.jmem_path, lesson_idx, item_idx,
                                correct_count, total_count, epoch
                            )
                            self.log("Paused. Progress saved.")
                            self._pause_event.wait()
                            if self._stop_flag:
                                break
                            self.log("Resumed.")

                        mastery_attempt += 1

                        # Train full sequence (all logic in BrainAPI)
                        trial_start = time.time()
                        result = self.brain.train_sequence(
                            input_text=encode_text,
                            target_text=target_text,
                            max_retries=self.max_retries,
                            encode_steps=self.encode_steps,
                            hold_steps=self.hold_steps,
                        )

                        trial_time = time.time() - trial_start
                        correct = result['success']

                        # Check if mastered (success or exact recall)
                        if correct or result.get('exact_recall', False):
                            mastered = True

                        # Log progress during mastery attempts
                        if mastery_attempt % self.mastery_log_interval == 0 and not mastered:
                            self.log(f"  Mastery attempt {mastery_attempt}: '{target_text[:20]}...' -> '{result['generated'][:20]}' ({result['char_accuracy']:.0%})")

                        # Skip mastery loop if not required (single attempt mode)
                        if not self.mastery_required:
                            break

                    # Calculate total time for this item
                    total_item_time = time.time() - item_start_time

                    # Update stats (count item once, not per mastery attempt)
                    total_count += 1
                    if mastered:
                        correct_count += 1

                    # Log detailed trial data (for Claude monitoring)
                    accuracy = correct_count / total_count if total_count > 0 else 0
                    log_data = {
                        'timestamp': datetime.now().isoformat(),
                        'epoch': epoch,
                        'lesson_idx': lesson_idx,
                        'lesson_name': lesson.title,
                        'item_idx': item_idx,
                        'item_counter': item_counter,
                        'item_type': item.type,
                        'target': target_text,
                        'generated': result['generated'],
                        'correct': mastered,  # Final mastery status
                        'char_accuracy': result['char_accuracy'],
                        'char_correct': result['char_correct'],
                        'char_total': result['char_total'],
                        'attempts': result['attempts'],
                        'mastery_attempts': mastery_attempt,  # NEW: total mastery attempts
                        'exact_recall': result['exact_recall'],
                        'trial_time_ms': round(total_item_time * 1000, 1),
                        'accuracy': round(accuracy, 4),
                        'correct_count': correct_count,
                        'total_count': total_count,
                    }
                    if item.type == "dialogue":
                        log_data['source'] = encode_text
                    log_trial(self.jmem_path, log_data)

                    # Log mastery result
                    if mastered and mastery_attempt > 1:
                        self.log(f"  ✓ Mastered '{target_text[:30]}' after {mastery_attempt} attempts")
                    elif not mastered and self.mastery_required:
                        # Flag as problematic - something is wrong if we can't learn after 500 attempts
                        self.log(f"  ⚠️ PROBLEM: Failed to master '{target_text[:50]}' after {mastery_attempt} attempts - SKIPPING")
                        self.log(f"     Last output: '{result['generated'][:50]}' ({result['char_accuracy']:.0%} accuracy)")
                        # Log to file for later review
                        problem_log = {
                            'timestamp': datetime.now().isoformat(),
                            'lesson': lesson.title,
                            'item_idx': item_idx,
                            'target': target_text,
                            'last_generated': result['generated'],
                            'char_accuracy': result['char_accuracy'],
                            'mastery_attempts': mastery_attempt,
                        }
                        problem_path = self.jmem_path / "problem_items.jsonl"
                        with open(problem_path, 'a') as f:
                            f.write(json.dumps(problem_log) + '\n')

                    # Emit progress
                    self.progress_update.emit(item_counter, total_items, lesson_name)

                    # Emit stats (accuracy already calculated above)
                    self.stats_update.emit(accuracy, correct_count, total_count)

                    # Interval GC (gen0 only - fast)
                    if item_counter % self.gc_interval == 0:
                        gc.collect(0)

                    # Periodic status log
                    if item_counter % self.status_interval == 0:
                        self.log(f"Item {item_counter}: acc={accuracy:.1%}")

                    # Periodic JMEM stats
                    if item_counter % self.jmem_stats_interval == 0 and self.brain._jmem_index:
                        jmem_stats = self.brain.get_jmem_index_stats()
                        if jmem_stats:
                            self.log(f"  📚 JMEM: {jmem_stats['total_memories']} memories")

                    # Periodic JMEM save (crash recovery)
                    if item_counter % self.jmem_save_interval == 0 and self.brain._jmem_index:
                        jmem_file = self.jmem_path / "index.jmem"
                        self.brain.save_jmem_index(str(jmem_file))

                # End lesson
                self.brain.end_learning_session()
                gc.collect()  # Full GC at safe point

            # Reset for next epoch
            start_lesson_idx = 0
            start_item_idx = 0

        # Training complete
        if not self._stop_flag:
            clear_progress(self.jmem_path)
            self.log("Training completed!")
        else:
            save_progress(
                self.jmem_path, current_lesson_idx, current_item_idx + 1,
                correct_count, total_count, current_epoch
            )
            self.log("Stopped. Progress saved.")

        # Save JMEM index
        if self.brain and self.brain._jmem_index:
            jmem_file = self.jmem_path / "index.jmem"
            self.brain.save_jmem_index(str(jmem_file))
            stats = self.brain.get_jmem_index_stats()
            self.log(f"Saved JMEM index: {stats['total_memories']} memories")

        # Final stats
        accuracy = correct_count / max(1, total_count)
        self.log(f"Final: {correct_count}/{total_count} ({accuracy:.1%})")

    def _train_book(self):
        """Train on PDF/TXT book using self-supervised learning."""
        global BookLoader
        if BookLoader is None:
            raise RuntimeError("BookLoader not available. Select a brain directory with tools/book_loader.py")

        # Load and preprocess book
        loader = BookLoader()
        book_name = Path(self.pdf_path).stem
        self.log(f"Loading book: {book_name}")

        try:
            raw_text = loader.load(self.pdf_path)
        except Exception as e:
            self.log(f"Error loading book: {e}")
            raise

        text = loader.preprocess(raw_text)
        chunks = loader.get_training_chunks(
            text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )
        total_chunks = len(chunks)

        self.log(f"Book loaded: {len(raw_text):,} chars → {total_chunks:,} chunks")

        # Initialize brain
        device = 'cuda' if self.use_gpu else 'cpu'
        self.log(f"Initializing brain ({device.upper()} mode)...")
        self.brain = BrainAPI.create(
            mode='text',
            device=device,
            cpu_neurons=self.cpu_neurons,
        )
        self.log(f"Brain ready. Input size: {self.brain._input_size}")

        # Initialize JMEM index
        jmem_file = self.jmem_path / "index.jmem"
        self.brain.init_jmem_index(
            path=str(jmem_file) if jmem_file.exists() else None,
            use_consciousness=False,
        )
        if self.brain._jmem_index:
            stats = self.brain.get_jmem_index_stats()
            self.log(f"JMEM loaded: {stats['total_memories']} existing memories")

        # Load base JMEMs (read-only context for training)
        if self.base_jmems:
            self.log(f"Loading {len(self.base_jmems)} base JMEM(s)...")
            for base_path in self.base_jmems:
                try:
                    base_jmem = Path(base_path) / "index.jmem"
                    if base_jmem.exists():
                        result = self.brain.import_jmem(str(base_path), read_only=True)
                        imported = result.get('imported', 0) if isinstance(result, dict) else 0
                        self.log(f"  Loaded base JMEM: {Path(base_path).name} ({imported} memories)")
                    else:
                        self.log(f"  Skipped {Path(base_path).name} (no index.jmem)")
                except Exception as e:
                    self.log(f"  Warning: Could not load base JMEM {base_path}: {e}")

        # Load progress if resuming
        start_chunk = 0
        if self.resume:
            progress = load_progress(self.jmem_path)
            if progress:
                start_chunk = progress.get('item_idx', 0)
                self.log(f"Resuming from chunk {start_chunk}")

        # Train on each chunk
        total_loss = 0.0
        chunks_trained = 0

        for chunk_idx in range(start_chunk, total_chunks):
            if self._stop_flag:
                break

            # Wait for pause
            self._pause_event.wait()
            if self._stop_flag:
                break

            chunk = chunks[chunk_idx]

            # Self-supervised training: predict each character in the chunk
            chunk_loss = 0.0
            for i in range(1, len(chunk)):
                context = chunk[:i]
                target_char = chunk[i]
                try:
                    loss = self.brain.decoder.learn_predictive(context, target_char)
                    chunk_loss += loss
                except Exception as e:
                    self.log(f"Warning: Error in learn_predictive at pos {i}: {e}")
                    continue

            avg_loss = chunk_loss / max(1, len(chunk) - 1)
            total_loss += avg_loss
            chunks_trained += 1

            # Store chunk in JMEM as knowledge
            try:
                self.brain.store_in_jmem(
                    content=chunk,
                    metadata={
                        'source': book_name,
                        'chunk_idx': chunk_idx,
                        'type': 'book_chunk',
                    }
                )
            except Exception as e:
                self.log(f"Warning: Could not store chunk {chunk_idx} in JMEM: {e}")

            # Progress updates
            if chunk_idx % 10 == 0 or chunk_idx == total_chunks - 1:
                self.progress_update.emit(chunk_idx + 1, total_chunks, f"Chunk {chunk_idx}")
                current_avg = total_loss / max(1, chunks_trained)
                self.stats_update.emit(0.0, chunks_trained, chunk_idx + 1)
                self.log(f"Chunk {chunk_idx + 1}/{total_chunks}: avg_loss={avg_loss:.3f}")

            # Periodic JMEM stats
            if chunk_idx % self.jmem_stats_interval == 0 and self.brain._jmem_index:
                jmem_stats = self.brain.get_jmem_index_stats()
                if jmem_stats:
                    self.log(f"  📚 JMEM: {jmem_stats['total_memories']} memories")

            # Periodic JMEM save and progress checkpoint
            if chunk_idx % self.jmem_save_interval == 0:
                if self.brain._jmem_index:
                    self.brain.save_jmem_index(str(jmem_file))
                save_progress(self.jmem_path, 0, chunk_idx, chunks_trained, chunk_idx, 0)

            # Periodic GC
            if chunk_idx % self.gc_interval == 0:
                gc.collect(0)

        # Training complete
        if not self._stop_flag:
            clear_progress(self.jmem_path)
            self.log("Training completed!")
        else:
            save_progress(self.jmem_path, 0, chunk_idx, chunks_trained, chunk_idx, 0)
            self.log("Stopped. Progress saved.")

        # Save JMEM index
        if self.brain and self.brain._jmem_index:
            self.brain.save_jmem_index(str(jmem_file))
            stats = self.brain.get_jmem_index_stats()
            self.log(f"Saved JMEM index: {stats['total_memories']} memories")

        # Final stats
        overall_avg_loss = total_loss / max(1, chunks_trained)
        self.log(f"Final: {chunks_trained} chunks, avg_loss={overall_avg_loss:.3f}")

    def _cleanup(self):
        """Clean up resources."""
        # Flush any remaining buffered logs before cleanup
        flush_log_buffer(self.jmem_path)
        if self.brain:
            self.brain = None
        gc.collect()


# =============================================================================
# Main Window
# =============================================================================

class JmemCreatorWindow(QMainWindow):
    """Main GUI window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JMEM Creator")
        self.setMinimumSize(700, 650)

        # State
        self.worker: Optional[TrainingWorker] = None
        self.brain_dir: Optional[Path] = None  # Path to brain directory
        self.jcur_packs = []
        self.available_jmems = []  # Available JMEMs for base selection
        self.selected_base_jmems: List[str] = []  # Paths of selected base JMEMs

        self._setup_ui()
        self._load_settings()  # Load saved settings including brain_dir
        self._update_button_states()

    def _setup_ui(self):
        """Set up the UI."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # === Brain Location Section ===
        brain_group = QGroupBox("Brain Location")
        brain_layout = QHBoxLayout(brain_group)

        brain_layout.addWidget(QLabel("Directory:"))
        self.brain_dir_label = QLabel("Not set")
        self.brain_dir_label.setFont(QFont("Monospace", 9))
        self.brain_dir_label.setMinimumWidth(200)
        brain_layout.addWidget(self.brain_dir_label)

        brain_layout.addStretch()

        self.brain_dir_btn = QPushButton("Select Brain...")
        self.brain_dir_btn.clicked.connect(self._on_select_brain_dir)
        brain_layout.addWidget(self.brain_dir_btn)

        layout.addWidget(brain_group)

        # === Source Type Selection ===
        source_group = QGroupBox("Source")
        source_layout = QHBoxLayout(source_group)

        source_layout.addWidget(QLabel("Type:"))
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["JCUR Curriculum", "PDF/TXT Book"])
        self.source_type_combo.currentIndexChanged.connect(self._on_source_type_changed)
        source_layout.addWidget(self.source_type_combo)

        source_layout.addStretch()

        self.start_fresh_btn = QPushButton("Start Fresh")
        self.start_fresh_btn.clicked.connect(self._on_start_fresh)
        source_layout.addWidget(self.start_fresh_btn)

        layout.addWidget(source_group)

        # === Source Content (Stacked Widget) ===
        self.source_stack = QStackedWidget()

        # Page 0: JCUR Selection
        jcur_page = QWidget()
        jcur_layout = QHBoxLayout(jcur_page)
        jcur_layout.setContentsMargins(0, 0, 0, 0)

        jcur_layout.addWidget(QLabel("JCUR:"))
        self.jcur_combo = QComboBox()
        self.jcur_combo.setMinimumWidth(250)
        self.jcur_combo.currentIndexChanged.connect(self._on_jcur_changed)
        jcur_layout.addWidget(self.jcur_combo)

        jcur_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_jcur_list)
        jcur_layout.addWidget(self.refresh_btn)

        self.source_stack.addWidget(jcur_page)

        # Page 1: PDF/TXT Selection
        pdf_page = QWidget()
        pdf_layout = QHBoxLayout(pdf_page)
        pdf_layout.setContentsMargins(0, 0, 0, 0)

        pdf_layout.addWidget(QLabel("Book:"))
        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setPlaceholderText("Select a PDF or TXT file...")
        self.pdf_path_edit.textChanged.connect(self._on_pdf_path_changed)
        pdf_layout.addWidget(self.pdf_path_edit)

        self.pdf_browse_btn = QPushButton("Browse...")
        self.pdf_browse_btn.clicked.connect(self._on_browse_pdf)
        pdf_layout.addWidget(self.pdf_browse_btn)

        self.source_stack.addWidget(pdf_page)

        layout.addWidget(self.source_stack)

        # === Base JMEMs (read-only context during training) ===
        base_jmems_group = QGroupBox("Base JMEMs (read-only during training)")
        base_jmems_layout = QVBoxLayout(base_jmems_group)

        # List of selected base JMEMs
        self.base_jmems_list = QListWidget()
        self.base_jmems_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.base_jmems_list.setMaximumHeight(80)
        base_jmems_layout.addWidget(self.base_jmems_list)

        # Buttons
        base_btns_layout = QHBoxLayout()
        self.add_base_btn = QPushButton("Add...")
        self.add_base_btn.clicked.connect(self._on_add_base_jmem)
        base_btns_layout.addWidget(self.add_base_btn)

        self.remove_base_btn = QPushButton("Remove")
        self.remove_base_btn.clicked.connect(self._on_remove_base_jmem)
        base_btns_layout.addWidget(self.remove_base_btn)

        base_btns_layout.addStretch()

        self.auto_add_btn = QPushButton("Auto-add Available")
        self.auto_add_btn.setToolTip("Add all existing JMEMs from jiyou_packs/")
        self.auto_add_btn.clicked.connect(self._on_auto_add_base_jmems)
        base_btns_layout.addWidget(self.auto_add_btn)

        base_jmems_layout.addLayout(base_btns_layout)

        layout.addWidget(base_jmems_group)

        # === JMEM Path ===
        jmem_group = QGroupBox("Output")
        jmem_layout = QHBoxLayout(jmem_group)

        jmem_layout.addWidget(QLabel("JMEM:"))
        self.jmem_path_edit = QLineEdit()
        self.jmem_path_edit.setReadOnly(True)
        jmem_layout.addWidget(self.jmem_path_edit)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse_jmem)
        jmem_layout.addWidget(self.browse_btn)

        self.clear_jmem_btn = QPushButton("Clear")
        self.clear_jmem_btn.clicked.connect(self._on_clear_jmem)
        jmem_layout.addWidget(self.clear_jmem_btn)

        layout.addWidget(jmem_group)

        # === Settings ===
        settings_group = QGroupBox("Settings")
        settings_layout = QHBoxLayout(settings_group)

        # GPU checkbox
        self.gpu_checkbox = QCheckBox("Use GPU")
        gpu_available = torch.cuda.is_available()
        self.gpu_checkbox.setChecked(gpu_available)  # Default to GPU if available
        self.gpu_checkbox.setEnabled(gpu_available)
        if not gpu_available:
            self.gpu_checkbox.setText("Use GPU (not available)")
        settings_layout.addWidget(self.gpu_checkbox)

        settings_layout.addSpacing(20)

        # Brain mode selector
        settings_layout.addWidget(QLabel("Brain Mode:"))
        self.brain_mode_combo = QComboBox()
        self.brain_mode_combo.addItems(["Text (200K)", "Standard (400K)", "Research (1.5M)", "Custom"])
        self.brain_mode_combo.setCurrentIndex(1)  # Default to Standard for better JMEM quality
        self.brain_mode_combo.currentIndexChanged.connect(self._on_brain_mode_changed)
        settings_layout.addWidget(self.brain_mode_combo)

        settings_layout.addSpacing(10)

        # CPU neuron count spinbox (always editable, presets just set initial value)
        settings_layout.addWidget(QLabel("CPU Neurons:"))
        self.cpu_neurons_spin = QSpinBox()
        self.cpu_neurons_spin.setRange(100000, 2000000)
        self.cpu_neurons_spin.setSingleStep(50000)  # 50K increments
        self.cpu_neurons_spin.setValue(400000)  # Default to Standard mode value
        settings_layout.addWidget(self.cpu_neurons_spin)

        settings_layout.addStretch()

        layout.addWidget(settings_group)

        # === Progress ===
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        stats_layout = QHBoxLayout()
        self.lesson_label = QLabel("Lesson: -")
        stats_layout.addWidget(self.lesson_label)
        stats_layout.addStretch()
        self.elapsed_label = QLabel("Time: 00:00:00")
        stats_layout.addWidget(self.elapsed_label)
        stats_layout.addStretch()
        self.accuracy_label = QLabel("Accuracy: -")
        stats_layout.addWidget(self.accuracy_label)
        progress_layout.addLayout(stats_layout)

        # Elapsed time timer (memory-safe: single instance, reused)
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_elapsed_time)
        self._training_start_time: Optional[float] = None

        layout.addWidget(progress_group)

        # === Controls ===
        controls_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._on_start)
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self._on_pause)
        controls_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self._on_resume)
        controls_layout.addWidget(self.resume_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        controls_layout.addWidget(self.stop_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # === Log Output ===
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 9))
        self.log_text.setMaximumBlockCount(1000)  # Limit lines
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group, 1)  # stretch=1 to fill remaining vertical space

    def _on_select_brain_dir(self):
        """Handle brain directory selection."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Brain Directory",
            str(Path.home() / "Documents"),
        )

        if path:
            brain_path = Path(path)
            # Validate it's a brain directory
            if not (brain_path / "api.py").exists():
                QMessageBox.warning(
                    self, "Invalid Brain Directory",
                    f"The selected directory does not appear to be a valid brain directory.\n"
                    f"Expected to find 'api.py' in:\n{brain_path}"
                )
                return

            # Load the brain modules
            if load_brain_modules(brain_path):
                self.brain_dir = brain_path
                self.brain_dir_label.setText(brain_path.name)
                self._log(f"Brain loaded: {brain_path.name}")
                self._refresh_jcur_list()
                self._refresh_available_jmems()
                self._save_settings()
                self._update_button_states()
            else:
                QMessageBox.critical(
                    self, "Load Error",
                    f"Failed to load brain modules from:\n{brain_path}"
                )

    def _load_settings(self):
        """Load saved settings from disk."""
        if SETTINGS_FILE.exists():
            try:
                settings = json.loads(SETTINGS_FILE.read_text())

                # Restore brain directory
                if 'brain_dir' in settings:
                    path = Path(settings['brain_dir'])
                    if path.exists() and (path / "api.py").exists():
                        if load_brain_modules(path):
                            self.brain_dir = path
                            self.brain_dir_label.setText(path.name)
                            self._log(f"Brain loaded: {path.name}")
                            self._refresh_jcur_list()
                            self._refresh_available_jmems()

                # Restore GPU setting
                if 'use_gpu' in settings:
                    gpu_available = torch.cuda.is_available()
                    self.gpu_checkbox.setChecked(settings['use_gpu'] and gpu_available)

                # Restore CPU neurons
                if 'cpu_neurons' in settings:
                    self.cpu_neurons_spin.setValue(settings['cpu_neurons'])
                    # Update brain mode combo to Custom if not matching presets
                    presets = {200000: 0, 400000: 1, 1500000: 2}
                    if settings['cpu_neurons'] in presets:
                        self.brain_mode_combo.setCurrentIndex(presets[settings['cpu_neurons']])
                    else:
                        self.brain_mode_combo.setCurrentIndex(3)  # Custom

            except Exception as e:
                self._log(f"Failed to load settings: {e}")

    def _save_settings(self):
        """Save settings to disk."""
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            settings = {
                'use_gpu': self.gpu_checkbox.isChecked(),
                'cpu_neurons': self.cpu_neurons_spin.value(),
            }
            if self.brain_dir:
                settings['brain_dir'] = str(self.brain_dir)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        except Exception as e:
            self._log(f"Failed to save settings: {e}")

    def _refresh_jcur_list(self):
        """Refresh the JCUR dropdown from local curricula directory."""
        self.jcur_packs = find_jcur_packs()
        self.jcur_combo.clear()

        for pack in self.jcur_packs:
            self.jcur_combo.addItem(
                f"{pack['name']} ({pack['total_items']} items)",
                pack
            )

        self._log(f"Found {len(self.jcur_packs)} JCUR packs in {CURRICULA_DIR}")

    def _on_jcur_changed(self, index: int):
        """Handle JCUR selection change."""
        if index < 0 or index >= len(self.jcur_packs):
            return
        if self.brain_dir is None:
            return

        pack = self.jcur_packs[index]
        jmem_path = self.brain_dir / "jiyou_packs" / pack['domain']
        self.jmem_path_edit.setText(str(jmem_path))

        # Check for existing progress
        progress = load_progress(jmem_path)
        if progress:
            self._log(f"Found saved progress: lesson {progress['lesson_idx'] + 1}, "
                     f"item {progress['item_idx']}")

    def _on_source_type_changed(self, index: int):
        """Handle source type selection change."""
        self.source_stack.setCurrentIndex(index)

        # Clear JMEM path when switching to book mode
        if index == 1:  # PDF/TXT Book
            self.jmem_path_edit.clear()

    def _on_browse_pdf(self):
        """Browse for PDF/TXT file."""
        file_filter = "Documents (*.pdf *.txt *.md);;PDF Files (*.pdf);;Text Files (*.txt *.md);;All Files (*)"
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Book File",
            str(Path.home()),
            file_filter
        )
        if path:
            self.pdf_path_edit.setText(path)

    def _on_pdf_path_changed(self, text: str):
        """Handle PDF path change."""
        if not text:
            return
        if self.brain_dir is None:
            return

        path = Path(text)
        if path.exists() and path.is_file():
            # Auto-generate JMEM output path from book name
            book_name = path.stem.lower().replace(' ', '_')
            jmem_path = self.brain_dir / "jiyou_packs" / book_name
            self.jmem_path_edit.setText(str(jmem_path))

            # Check for existing progress
            if jmem_path.exists():
                progress = load_progress(jmem_path)
                if progress:
                    self._log(f"Found saved progress: chunk {progress['item_idx']}")

    def _on_browse_jmem(self):
        """Browse for JMEM output directory."""
        start_dir = str(self.brain_dir / "jiyou_packs") if self.brain_dir else str(Path.home())
        path = QFileDialog.getExistingDirectory(
            self, "Select JMEM Output Directory",
            start_dir
        )
        if path:
            self.jmem_path_edit.setText(path)

    def _on_clear_jmem(self):
        """Clear the JMEM directory."""
        jmem_path = Path(self.jmem_path_edit.text())
        if not jmem_path.exists():
            self._log("JMEM path doesn't exist")
            return

        reply = QMessageBox.question(
            self, "Clear JMEM",
            f"Delete all contents of:\n{jmem_path}\n\nThis cannot be undone!",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                shutil.rmtree(jmem_path)
                jmem_path.mkdir(parents=True)
                self._log(f"Cleared: {jmem_path}")
            except Exception as e:
                self._log(f"Error clearing: {e}")

    def _on_brain_mode_changed(self, index: int):
        """Handle brain mode selection - sets value but spinbox stays editable."""
        mode_neurons = {
            0: 200000,    # Text (200K)
            1: 400000,    # Standard (400K)
            2: 1500000,   # Research (1.5M)
        }
        if index < 3:  # Preset mode - set value
            self.cpu_neurons_spin.setValue(mode_neurons[index])
        # Custom mode (3) - leave current value, user adjusts manually

    def _on_start_fresh(self):
        """Start fresh - clear JMEM and progress."""
        jmem_path = Path(self.jmem_path_edit.text())

        reply = QMessageBox.question(
            self, "Start Fresh",
            "Clear all JMEM data and progress?\n\nThis cannot be undone!",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if jmem_path.exists():
                    shutil.rmtree(jmem_path)
                jmem_path.mkdir(parents=True)
                self._log("Cleared all data. Ready for fresh start.")
                self.progress_bar.setValue(0)
                self.lesson_label.setText("Lesson: -")
                self.elapsed_label.setText("Time: 00:00:00")
                self.accuracy_label.setText("Accuracy: -")
            except Exception as e:
                self._log(f"Error: {e}")

    def _refresh_available_jmems(self):
        """Refresh the list of available JMEMs for base selection."""
        self.available_jmems = find_jmem_packs(self.brain_dir)
        self._log(f"Found {len(self.available_jmems)} available JMEM pack(s)")

    def _on_add_base_jmem(self):
        """Add a base JMEM from available packs or browse."""
        # Get current output path to exclude it
        current_output = Path(self.jmem_path_edit.text()).name if self.jmem_path_edit.text() else None

        # Filter out already selected and current output
        available = [
            j for j in self.available_jmems
            if str(j['path']) not in self.selected_base_jmems
            and j['path'].name != current_output
        ]

        if not available:
            # Fall back to directory browser
            start_dir = str(self.brain_dir / "jiyou_packs") if self.brain_dir else str(Path.home())
            path = QFileDialog.getExistingDirectory(
                self, "Select Base JMEM Directory",
                start_dir
            )
            if path and path not in self.selected_base_jmems:
                self._add_base_jmem_path(path)
            return

        # Show quick selection dialog with available packs
        from PyQt5.QtWidgets import QInputDialog
        names = [f"{j['name']} ({j['total_memories']} memories)" for j in available]
        name, ok = QInputDialog.getItem(
            self, "Add Base JMEM",
            "Select a JMEM pack to use as context:",
            names, 0, False
        )
        if ok and name:
            idx = names.index(name)
            self._add_base_jmem_path(str(available[idx]['path']))

    def _add_base_jmem_path(self, path: str):
        """Add a base JMEM path to the list."""
        if path in self.selected_base_jmems:
            return
        self.selected_base_jmems.append(path)
        # Display name with memory count
        name = Path(path).name
        for j in self.available_jmems:
            if str(j['path']) == path:
                name = f"{j['name']} ({j['total_memories']} memories)"
                break
        item = self.base_jmems_list.addItem(name)
        self.base_jmems_list.item(self.base_jmems_list.count() - 1).setData(Qt.UserRole, path)
        self._log(f"Added base JMEM: {Path(path).name}")

    def _on_remove_base_jmem(self):
        """Remove selected base JMEMs."""
        for item in self.base_jmems_list.selectedItems():
            path = item.data(Qt.UserRole)
            if path in self.selected_base_jmems:
                self.selected_base_jmems.remove(path)
            self.base_jmems_list.takeItem(self.base_jmems_list.row(item))

    def _on_auto_add_base_jmems(self):
        """Auto-add all available JMEMs except the current output."""
        self._refresh_available_jmems()
        current_output = Path(self.jmem_path_edit.text()).name if self.jmem_path_edit.text() else None

        added = 0
        for jmem in self.available_jmems:
            path = str(jmem['path'])
            # Skip if already added or is the current output
            if path in self.selected_base_jmems:
                continue
            if jmem['path'].name == current_output:
                continue
            self._add_base_jmem_path(path)
            added += 1

        if added > 0:
            self._log(f"Auto-added {added} base JMEM(s)")
        else:
            self._log("No new JMEMs to add")

    def _on_start(self):
        """Start training."""
        if self.worker and self.worker.isRunning():
            return

        # Check brain is loaded
        if self.brain_dir is None or BrainAPI is None:
            QMessageBox.warning(
                self, "Brain Not Loaded",
                "Please select a brain directory first."
            )
            return

        jmem_path = Path(self.jmem_path_edit.text())
        if not jmem_path:
            self._log("No output path specified")
            return

        # Determine source type
        source_type = "jcur" if self.source_type_combo.currentIndex() == 0 else "book"

        # Validate inputs based on source type
        jcur_path = None
        pdf_path = None

        if source_type == "jcur":
            index = self.jcur_combo.currentIndex()
            if index < 0:
                self._log("No JCUR selected")
                return
            pack = self.jcur_packs[index]
            jcur_path = pack['path']
        else:
            pdf_path = self.pdf_path_edit.text()
            if not pdf_path or not Path(pdf_path).exists():
                self._log("No valid book file selected")
                return

        # Check for resume
        progress = load_progress(jmem_path)
        resume = False
        if progress:
            if source_type == "jcur":
                msg = f"Found saved progress:\nLesson {progress['lesson_idx'] + 1}, Item {progress['item_idx']}\n\nResume from checkpoint?"
            else:
                msg = f"Found saved progress:\nChunk {progress['item_idx']}\n\nResume from checkpoint?"
            reply = QMessageBox.question(
                self, "Resume Training", msg,
                QMessageBox.Yes | QMessageBox.No
            )
            resume = (reply == QMessageBox.Yes)

        # Create and start worker
        use_gpu = self.gpu_checkbox.isChecked()
        cpu_neurons = self.cpu_neurons_spin.value()
        self.worker = TrainingWorker(
            jmem_path=jmem_path,
            resume=resume,
            use_gpu=use_gpu,
            source_type=source_type,
            jcur_path=jcur_path,
            pdf_path=pdf_path,
            base_jmems=self.selected_base_jmems.copy(),
            cpu_neurons=cpu_neurons,
        )
        self._log(f"Using {cpu_neurons:,} CPU neurons for training")
        self.worker.log_message.connect(self._log)
        self.worker.progress_update.connect(self._on_progress_update)
        self.worker.stats_update.connect(self._on_stats_update)
        self.worker.training_finished.connect(self._on_training_finished)
        self.worker.training_error.connect(self._on_training_error)

        self.worker.start()
        self._start_elapsed_timer()
        self._update_button_states()
        self._log("Training started...")

    def _on_pause(self):
        """Pause training."""
        if self.worker and self.worker.isRunning():
            self.worker.pause()
            self._update_button_states()

    def _on_resume(self):
        """Resume training."""
        if self.worker and self.worker.isRunning():
            self.worker.unpause()
            self._update_button_states()

    def _on_stop(self):
        """Stop training."""
        if self.worker and self.worker.isRunning():
            self._stop_elapsed_timer()
            self._log("Stopping...")
            self.worker.stop()

            # Update manifest when stopped early
            jmem_path = Path(self.jmem_path_edit.text())
            if jmem_path.exists():
                jcur_name = self.jcur_combo.currentText() if self.jcur_combo.currentIndex() >= 0 else None
                manifest = create_or_update_manifest(
                    jmem_path, jcur_name,
                    dependencies=self.selected_base_jmems if self.selected_base_jmems else None,
                )
                self._log(f"Saved manifest: {manifest.get('total_memories', 0)} memories")

    def _on_progress_update(self, current: int, total: int, lesson_name: str):
        """Handle progress update."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        pct = current / total * 100 if total > 0 else 0
        self.progress_bar.setFormat(f"{pct:.1f}% ({current}/{total})")
        self.lesson_label.setText(f"Lesson: {lesson_name}")

    def _on_stats_update(self, accuracy: float, correct: int, total: int):
        """Handle stats update."""
        self.accuracy_label.setText(f"Accuracy: {accuracy:.1%} ({correct}/{total})")

    def _update_elapsed_time(self):
        """Update elapsed time display."""
        if self._training_start_time is None:
            return
        elapsed = time.time() - self._training_start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        self.elapsed_label.setText(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def _start_elapsed_timer(self):
        """Start the elapsed time timer."""
        self._training_start_time = time.time()
        self._elapsed_timer.start(1000)  # Update every second

    def _stop_elapsed_timer(self):
        """Stop the elapsed time timer."""
        self._elapsed_timer.stop()

    def _on_training_finished(self):
        """Handle training finished."""
        self._stop_elapsed_timer()
        self._log("Training finished.")

        # Create/update manifest.json for the JMEM pack
        jmem_path = Path(self.jmem_path_edit.text())
        if jmem_path.exists():
            jcur_name = self.jcur_combo.currentText() if self.jcur_combo.currentIndex() >= 0 else None
            manifest = create_or_update_manifest(
                jmem_path, jcur_name,
                dependencies=self.selected_base_jmems if self.selected_base_jmems else None,
            )
            self._log(f"Updated manifest: {manifest.get('total_memories', 0)} memories indexed")
            if self.selected_base_jmems:
                self._log(f"Dependencies recorded: {[Path(p).name for p in self.selected_base_jmems]}")

        self._update_button_states()

    def _on_training_error(self, error: str):
        """Handle training error."""
        self._stop_elapsed_timer()
        self._log(f"ERROR: {error}")
        QMessageBox.critical(self, "Training Error", error)

    def _update_button_states(self):
        """Update button enabled states based on worker status and brain availability."""
        running = bool(self.worker and self.worker.isRunning())
        paused = bool(running and self.worker.is_paused)
        brain_loaded = self.brain_dir is not None

        # Start requires brain to be loaded
        self.start_btn.setEnabled(not running and brain_loaded)
        self.pause_btn.setEnabled(running and not paused)
        self.resume_btn.setEnabled(paused)
        self.stop_btn.setEnabled(running)

        # Source selection - requires brain
        self.source_type_combo.setEnabled(not running and brain_loaded)
        self.jcur_combo.setEnabled(not running and brain_loaded)
        self.refresh_btn.setEnabled(not running and brain_loaded)
        self.pdf_path_edit.setEnabled(not running and brain_loaded)
        self.pdf_browse_btn.setEnabled(not running and brain_loaded)

        # Base JMEMs - requires brain
        self.base_jmems_list.setEnabled(not running and brain_loaded)
        self.add_base_btn.setEnabled(not running and brain_loaded)
        self.remove_base_btn.setEnabled(not running and brain_loaded)
        self.auto_add_btn.setEnabled(not running and brain_loaded)

        # Output - requires brain
        self.browse_btn.setEnabled(not running and brain_loaded)
        self.start_fresh_btn.setEnabled(not running and brain_loaded)
        self.clear_jmem_btn.setEnabled(not running and brain_loaded)

        # GPU checkbox: only enabled when not running AND GPU is available
        gpu_available = torch.cuda.is_available()
        self.gpu_checkbox.setEnabled(not running and gpu_available)

    def _log(self, msg: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {msg}")

    def closeEvent(self, event):
        """Handle window close."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Training is in progress. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

            self.worker.stop()
            self.worker.wait(5000)  # Wait up to 5 seconds

        event.accept()


# =============================================================================
# Main
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark mode palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

    # Dark stylesheet for remaining elements
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a2a2a;
            border: 1px solid #767676;
        }
        QGroupBox {
            border: 1px solid #767676;
            margin-top: 0.5em;
            padding-top: 0.5em;
        }
        QGroupBox::title {
            color: #ffffff;
        }
    """)

    window = JmemCreatorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
