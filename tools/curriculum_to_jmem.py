#!/usr/bin/env python3
"""
Curriculum to JMEM Converter

Converts .jcur curriculum packs into .jmem binary memory packs.
"""

import sys
import json
import time
from pathlib import Path

# Add JiYouBrain to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'JiYouBrain'))

from jmem.binary_writer import JMEMWriter
from jmem.binary_format import SourceType, AbstractionLevel


def load_curriculum_lessons(curriculum_dir: Path) -> list:
    """Load all lesson files from a curriculum directory."""
    lessons_dir = curriculum_dir / 'lessons'
    if not lessons_dir.exists():
        raise FileNotFoundError(f"No lessons directory found at {lessons_dir}")

    all_items = []
    lesson_files = sorted(lessons_dir.glob('*.json'))

    print(f"Found {len(lesson_files)} lesson files")

    for lesson_file in lesson_files:
        try:
            with open(lesson_file, 'r', encoding='utf-8') as f:
                lesson_data = json.load(f)

            lesson_id = lesson_data.get('lesson_id', lesson_file.stem)
            lesson_title = lesson_data.get('title', lesson_id)
            items = lesson_data.get('items', [])

            print(f"  {lesson_file.name}: {len(items)} items ({lesson_title})")

            for item in items:
                # Normalize item format
                content = item.get('source', item.get('content', ''))
                expected_output = item.get('target', item.get('expected_output', ''))
                context = item.get('context', lesson_id)
                item_id = item.get('id', '')

                if content and expected_output:
                    all_items.append({
                        'content': content,
                        'expected_output': expected_output,
                        'context': context,
                        'item_id': item_id,
                        'lesson_id': lesson_id,
                        'lesson_title': lesson_title,
                    })
        except json.JSONDecodeError as e:
            print(f"  WARNING: Failed to parse {lesson_file.name}: {e}")
        except Exception as e:
            print(f"  WARNING: Error loading {lesson_file.name}: {e}")

    return all_items


def convert_curriculum_to_jmem(
    curriculum_dir: Path,
    output_path: Path,
    pack_name: str = "Coding Curriculum",
    pack_domain: str = "coding",
) -> int:
    """
    Convert a curriculum directory to a JMEM pack.

    Args:
        curriculum_dir: Path to .jcur directory
        output_path: Path for output .jmem file
        pack_name: Human-readable pack name
        pack_domain: Domain identifier

    Returns:
        Number of memories written
    """
    print(f"\n=== Curriculum to JMEM Converter ===")
    print(f"Source: {curriculum_dir}")
    print(f"Output: {output_path}")
    print()

    # Load all curriculum items
    print("Loading curriculum items...")
    items = load_curriculum_lessons(curriculum_dir)
    print(f"\nTotal items: {len(items)}")

    if not items:
        print("ERROR: No items found in curriculum")
        return 0

    # Create JMEM writer
    manifest_data = {
        "pack_info": {
            "name": pack_name,
            "domain": pack_domain,
            "description": f"JMEM pack generated from {curriculum_dir.name} curriculum",
            "version": "1.0.0",
            "language": "en",
            "tags": ["coding", "programming", "curriculum"],
        },
        "source": {
            "type": "curriculum",
            "curriculum_name": curriculum_dir.name,
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "generator": "curriculum_to_jmem.py",
        },
    }

    writer = JMEMWriter(str(output_path), manifest_data=manifest_data)

    # Add memories
    print("\nWriting memories to JMEM...")
    start_time = time.time()

    for i, item in enumerate(items):
        # Determine abstraction level based on content
        content = item['content']
        if 'why' in content.lower() or 'explain' in content.lower():
            level = AbstractionLevel.SEMANTIC
        elif 'concept' in content.lower() or 'principle' in content.lower():
            level = AbstractionLevel.CONCEPTUAL
        else:
            level = AbstractionLevel.EPISODIC

        # Add memory (no embeddings for now - brain can generate on load)
        writer.add_memory(
            content=item['content'],
            expected_output=item['expected_output'],
            source_type=SourceType.CURRICULUM,
            abstraction_level=level,
            importance=0.7,  # Curriculum items are moderately important
            source_id=item.get('item_id', f"{item['lesson_id']}_{i}"),
            confidence=0.8,  # Curriculum is reliable
        )

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  {i + 1}/{len(items)} ({rate:.0f} items/sec)")

    # Finalize
    print("\nFinalizing JMEM file...")
    total_bytes = writer.finalize()

    elapsed = time.time() - start_time

    print(f"\n=== Conversion Complete ===")
    print(f"Memories: {writer.memory_count}")
    print(f"File size: {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"Time: {elapsed:.1f} seconds")
    print(f"Output: {output_path}")

    return writer.memory_count


def main():
    """Main entry point."""
    # Default paths
    curriculum_dir = Path(__file__).parent.parent / 'curricula' / 'coding.jcur'
    output_path = Path.home() / '.jiyou' / 'jmem_packs' / 'coding.jmem'

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert
    count = convert_curriculum_to_jmem(
        curriculum_dir=curriculum_dir,
        output_path=output_path,
        pack_name="Coding Curriculum",
        pack_domain="coding",
    )

    if count > 0:
        print(f"\nSuccess! JMEM pack created with {count} memories.")
        print(f"\nTo use in JiYouChat:")
        print(f"  jiyou --load {output_path}")
    else:
        print("\nFailed to create JMEM pack.")
        sys.exit(1)


if __name__ == "__main__":
    main()
