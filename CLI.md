# JmemCreator CLI

Command-line interface for training JMEM packs from JCUR curricula.

## Installation

To run `jmem` from anywhere, create the launcher script:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/jmem << 'EOF'
#!/bin/bash
JMEM_DIR="/home/zx/Desktop/JiYou/JmemCreator"
VENV="/home/zx/Desktop/JiYou/.venv/bin/python"
cd "$JMEM_DIR" && exec "$VENV" jmem_creator_cli.py "$@"
EOF
chmod +x ~/.local/bin/jmem
```

Make sure `~/.local/bin` is in your PATH (it usually is by default).

## Quick Start

```bash
# Run from anywhere
jmem

# Or run directly from this directory
jmem
```

## Commands

### Interactive Mode

Run without arguments for menu-driven configuration:

```bash
jmem
```

This opens an interactive menu where you can:
- Select source (JCUR curriculum or PDF/TXT book)
- Configure workers (GPU/CPU, neuron count, Big Brain mode)
- Select base JMEMs for read-only context
- Set output path
- Start training with live progress display

### List Available Curricula

```bash
jmem list
```

Shows all JCUR packs in `curricula/` and trained JMEM packs.

### Show/Set Configuration

```bash
# Show current config
jmem config

# Set brain directory
jmem config --set-brain /path/to/JiYouBrain
```

### Direct Training

Train without interactive menus:

```bash
jmem train \
  --jcur curricula/english_core.jcur \
  --output ~/JiYouBrain/jmem_packs/english_core \
  --worker cuda:400000
```

## Train Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--jcur PATH` | `-j` | Path to JCUR curriculum (required) |
| `--output PATH` | `-o` | Output JMEM directory (required) |
| `--worker SPEC` | `-w` | Worker spec (required, can repeat) |
| `--base-jmem PATH` | `-b` | Base JMEM for context (optional, can repeat) |
| `--recalibrate` | `-r` | Train all items, don't skip existing |
| `--brain-dir PATH` | | Override brain directory |
| `--no-interactive` | | Disable live display |

## Worker Specification

Format: `device:neurons[:big]`

| Example | Description |
|---------|-------------|
| `cuda:400000` | GPU worker with 400K neurons |
| `gpu:300000` | Same as cuda |
| `cpu:200000` | CPU worker with 200K neurons |
| `cpu:500000:big` | Big Brain CPU worker (handles difficult items) |

## Examples

### Single GPU Training

```bash
jmem train \
  -j curricula/tools.jcur \
  -o ~/JiYouBrain/jmem_packs/tools \
  -w cuda:400000
```

### Multi-Worker Training

```bash
jmem train \
  -j curricula/english_core.jcur \
  -o ~/JiYouBrain/jmem_packs/english_core \
  -w cuda:400000 \
  -w cuda:400000 \
  -w cpu:200000:big
```

### With Base JMEM Context

```bash
jmem train \
  -j curricula/tools.jcur \
  -o ~/JiYouBrain/jmem_packs/tools \
  -w cuda:400000 \
  -b ~/JiYouBrain/jmem_packs/english_core
```

### Recalibration Mode

Re-train all items (useful when brain has improved):

```bash
jmem train \
  -j curricula/tools.jcur \
  -o ~/JiYouBrain/jmem_packs/tools \
  -w cuda:400000 \
  --recalibrate
```

### Non-Interactive (for scripts/logs)

```bash
jmem train \
  -j curricula/english_core.jcur \
  -o ~/JiYouBrain/jmem_packs/english_core \
  -w cuda:400000 \
  --no-interactive
```

## Training Display

During training, you'll see:

```
╭──────────────────────── JmemCreator Training ────────────────────────╮
│ english_core.jcur                                                    │
│ Progress: [████████████░░░░░░░░] 1,234 / 36,000 (3.4%)              │
│ Elapsed: 01:23:45  |  Accuracy: 87.2% (1,076/1,234)                 │
╰──────────────────────────────────────────────────────────────────────╯
                               Workers
┏━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID ┃ Device ┃ Neurons ┃ Type   ┃ Status            ┃ Attempts┃
┡━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ 0  │ cuda   │ 400K    │ Normal │ "apple"           │ 3/3     │
│ 1  │ cpu    │ 200K    │ Big    │ BB: 45 items, 82% │ 12/45   │
└────┴────────┴─────────┴────────┴───────────────────┴─────────┘
╭────────────────────────────── Log ───────────────────────────────────╮
│ [14:23:45] Item 1234: acc=87.2%                                      │
│ [14:23:46] JMEM: 1,234 memories, 1,100 hub states                   │
╰──────────────────────────────────────────────────────────────────────╯
Press Ctrl+C to stop training
```

## Stopping Training

- **Ctrl+C once**: Graceful stop (saves progress, copies shard to index.jmem)
- **Ctrl+C twice**: Force exit

Progress is automatically saved every 10 items, so you can resume later.

## Configuration File

Settings are stored in `~/.jiyou/jmem_creator_settings.json`:
- Brain directory path
- Worker configurations
- Worker presets

This file is shared with the GUI, so settings persist between both interfaces.
