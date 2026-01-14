# JMEM Creator

**GUI tool for creating JMEM (Jiyou Memory) packs from curricula.**

JMEM packs give [JiyouBrain](https://github.com/TimA314/JiyouBrain) photographic memory - instant recall of facts, vocabulary, and knowledge domains.

---

## Features

- Train JCUR curriculum packs into JMEM memory packs
- Train PDF/TXT books into knowledge memories
- Load base JMEMs as read-only context during training
- Resume training from checkpoints
- Real-time progress and accuracy tracking
- Configurable CPU neuron count for different hardware

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
3. (Optional) Add base JMEMs for compositional training
4. Click **Start**

---

## Training Modes

### JCUR Curriculum Training
Train structured curricula with mastery-based learning. Jiyou must master each item before proceeding (up to 500 attempts per item).

### Book Training (PDF/TXT)
Self-supervised learning from unstructured text. Chunks the book and learns to predict character sequences.

---

## Settings

| Setting | Description |
|---------|-------------|
| **Use GPU** | Enable CUDA acceleration if available |
| **Brain Mode** | Preset neuron counts (Text 200K, Standard 400K, Research 1.5M) |
| **CPU Neurons** | Manual neuron count (50K increments) |

---

## Output

Trained JMEM packs are saved to `<brain_dir>/jiyou_packs/` with:
- `index.jmem` - Memory index file
- `manifest.json` - Pack metadata and dependencies
- `training_progress.json` - Resume checkpoint
- `training_log.jsonl` - Detailed per-trial log

---

## Related

- **[JiyouBrain](https://github.com/TimA314/JiyouBrain)** - The spiking neural network
- **[JiyouChat](https://github.com/TimA314/JiyouChat)** - Chat interface for Jiyou

---

## License

MIT License
