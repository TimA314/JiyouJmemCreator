# JMEM Creator

**GUI tool for creating JMEM (Jiyou Memory) packs from curricula using parallel training.**

JMEM packs give [JiyouBrain](https://github.com/TimA314/JiyouBrain) photographic memory - instant recall of facts, vocabulary, and knowledge domains.

---

## Features

- **Parallel Training** - Multiple brain workers train simultaneously
- **Competitive Training** - Workers race on difficult items (Bitcoin mining inspired)
- **Big Brain Workers** - Dedicated high-capacity workers for stubborn items
- **Auto-Backup** - JMEM backed up every 100 memories with safety checks
- **Recalibration Mode** - Restart training from item 1 to calibrate fresh brains
- **Resume Support** - Continue training from checkpoints
- **Real-time Monitoring** - Worker status, current item, attempt counts

---

## Requirements

- Python 3.8+
- PyQt5
- PyTorch
- [JiyouBrain](https://github.com/TimA314/JiyouBrain) - select the directory on first run

---

## Quick Start

```bash
python jmem_creator_gui.py
```

1. Click **"Select Brain..."** and choose your JiyouBrain directory
2. Select a JCUR curriculum from the dropdown
3. Add workers using presets or **"Add Worker"** button
4. Click **Start**

---

## Parallel Training

### Worker Configuration

| Setting | Description |
|---------|-------------|
| **Device** | GPU (CUDA) or CPU |
| **Neurons** | Brain capacity (50K-2M neurons) |
| **Big Brain** | Handles difficult items that regular workers struggle with |

### Quick Presets

| Preset | Configuration |
|--------|---------------|
| **Single GPU** | 1 GPU worker (200K neurons) |
| **Dual GPU** | 2 GPU workers (200K each) |
| **GPU + CPU** | 1 GPU (200K) + 1 CPU Big Brain (500K) |
| **Research Mode** | 2 GPU (200K) + 1 CPU Big Brain (1M) |

### Competitive Training System

Workers compete on difficult items using a tiered escalation:

| Global Attempts | Action |
|-----------------|--------|
| 20 | Second worker joins (max 2 workers) |
| 100 | Big brain joins (max 3 workers) |
| 500 | Give up, log to `problem_items.jsonl` |

Workers share their best outputs as hints, and the first to achieve mastery wins.

---

## Worker Table

The GUI displays real-time worker status:

| Column | Description |
|--------|-------------|
| **Device** | GPU or CPU |
| **Neurons** | Brain capacity |
| **Type** | Regular or Big Brain |
| **Status** | Training, Idle, Done |
| **Current Item** | What the worker is learning |
| **Attempts** | Local/Global attempt count |

---

## Training Modes

### JCUR Curriculum Training
Train structured curricula with mastery-based learning. Jiyou must master each item before proceeding (up to 500 global attempts per item).

### Book Training (PDF/TXT)
Self-supervised learning from unstructured text. Chunks the book and learns to predict character sequences. (Single-worker mode)

---

## Buttons

| Button | Action |
|--------|--------|
| **Start** | Begin training (skips already-trained items) |
| **Stop** | Gracefully stop all workers |
| **Restart** | Recalibration mode - trains ALL items from beginning without skipping (preserves JMEM) |

---

## Output

Trained JMEM packs are saved to `jmem_packs/<pack_name>/` with:

| File | Description |
|------|-------------|
| `index.jmem` | Memory index file |
| `manifest.json` | Pack metadata and dependencies |
| `shards/` | Temporary worker output (merged automatically) |

Backups are saved to `jmem_packs_backup/` every 100 memories.

---

## Curriculum Tools

The `tools/` directory contains utilities for curriculum generation and conversion.

### curriculum_to_jmem.py

Convert a JCUR curriculum directly to JMEM format **without training**. Useful for pre-populating JMEM packs with Q&A pairs.

```bash
python tools/curriculum_to_jmem.py path/to/curriculum.jcur output.jmem
```

Options:
- Reads all lessons from the JCUR
- Creates JMEM entries with input/expected_output pairs
- Generates activation embeddings using n-gram hashing
- No brain training required

### claude_curriculum_generator.py

Generate JCUR curricula using Claude AI. Creates structured lesson files with Q&A pairs.

```bash
python tools/claude_curriculum_generator.py --topic "Python basics" --output python.jcur
```

### generate_coding_curriculum.py

Generate programming-focused curricula with 200+ Q&A pairs covering:
- Syntax and semantics
- Best practices
- Common patterns
- Error handling

---

## CLI Mode

For headless/scripted training:

```bash
python jmem_creator_cli.py \
    --brain-path /path/to/JiYouBrain \
    --curriculum curricula/english_core.jcur \
    --output output.jmem \
    --workers 2 \
    --device cuda
```

---

## Related

- **[JiyouBrain](https://github.com/TimA314/JiyouBrain)** - The spiking neural network
- **[JiyouChat](https://github.com/TimA314/JiyouChat)** - Chat interface for Jiyou

---

## License

MIT License
