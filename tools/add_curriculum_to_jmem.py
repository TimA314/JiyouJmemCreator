#!/usr/bin/env python3
"""
Incremental Curriculum to JMEM Adder

Adds new curriculum items to an existing JMEM without re-processing existing memories.
Only adds items that don't already exist (based on content hash).
"""

import sys
import json
import time
import argparse
from pathlib import Path

# Add JiYouBrain to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'JiYouBrain'))

from jmem.memory_index import JMEMIndex


def load_curriculum_items(curriculum_dir: Path, lesson_filter: str = None) -> list:
    """
    Load curriculum items from lesson files.

    Args:
        curriculum_dir: Path to .jcur directory
        lesson_filter: Optional glob pattern to filter lessons (e.g., "3*.json" for new conversation lessons)

    Returns:
        List of items with content, expected_output, etc.
    """
    lessons_dir = curriculum_dir / 'lessons'
    if not lessons_dir.exists():
        raise FileNotFoundError(f"No lessons directory found at {lessons_dir}")

    all_items = []

    if lesson_filter:
        lesson_files = sorted(lessons_dir.glob(lesson_filter))
    else:
        lesson_files = sorted(lessons_dir.glob('*.json'))

    print(f"Found {len(lesson_files)} lesson files matching filter")

    for lesson_file in lesson_files:
        try:
            with open(lesson_file, 'r', encoding='utf-8') as f:
                lesson_data = json.load(f)

            lesson_id = lesson_data.get('lesson_id', lesson_file.stem)
            lesson_title = lesson_data.get('title', lesson_id)
            items = lesson_data.get('items', [])

            print(f"  {lesson_file.name}: {len(items)} items")

            for item in items:
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


def add_curriculum_to_jmem(
    jmem_path: Path,
    curriculum_dir: Path,
    output_path: Path = None,
    lesson_filter: str = None,
) -> int:
    """
    Add new curriculum items to an existing JMEM.

    Args:
        jmem_path: Path to existing .jmem file
        curriculum_dir: Path to .jcur curriculum directory
        output_path: Output path (defaults to overwriting jmem_path)
        lesson_filter: Optional glob pattern to filter lessons

    Returns:
        Number of new items added
    """
    if output_path is None:
        output_path = jmem_path

    print(f"\n=== Incremental JMEM Update ===")
    print(f"Existing JMEM: {jmem_path}")
    print(f"Curriculum: {curriculum_dir}")
    print(f"Output: {output_path}")
    if lesson_filter:
        print(f"Lesson filter: {lesson_filter}")
    print()

    # Load existing JMEM
    print("Loading existing JMEM...")
    start_time = time.time()
    index = JMEMIndex.load_binary(str(jmem_path))
    load_time = time.time() - start_time
    print(f"Loaded {len(index.memories)} existing memories in {load_time:.1f}s")

    # Get set of existing content hashes for fast lookup
    existing_contents = set()
    for mem_id, mem in index.memories.items():
        existing_contents.add(mem['content'])
    print(f"Existing unique contents: {len(existing_contents)}")

    # Load new curriculum items
    print(f"\nLoading curriculum items...")
    items = load_curriculum_items(curriculum_dir, lesson_filter)
    print(f"Total curriculum items: {len(items)}")

    # Find items not already in JMEM
    new_items = []
    duplicates = 0
    for item in items:
        if item['content'] not in existing_contents:
            new_items.append(item)
            existing_contents.add(item['content'])  # Prevent duplicates within new items
        else:
            duplicates += 1

    print(f"New items to add: {len(new_items)}")
    print(f"Duplicates skipped: {duplicates}")

    if not new_items:
        print("\nNo new items to add. JMEM unchanged.")
        return 0

    # Add new items
    print(f"\nAdding {len(new_items)} new items...")
    start_time = time.time()

    for i, item in enumerate(new_items):
        memory_id = f"mem_{len(index.memories):06d}"

        index.add_memory(
            content=item['content'],
            memory_id=memory_id,
            expected_output=item['expected_output'],
            metadata={
                'lesson_id': item['lesson_id'],
                'lesson_title': item['lesson_title'],
                'context': item['context'],
                'item_id': item['item_id'],
            },
            skip_semantic_indexing=False,  # Enable semantic indexing for new items
        )

        if (i + 1) % 500 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  {i + 1}/{len(new_items)} ({rate:.0f} items/sec)")

    add_time = time.time() - start_time
    print(f"Added {len(new_items)} items in {add_time:.1f}s")

    # Save updated JMEM
    print(f"\nSaving updated JMEM to {output_path}...")
    start_time = time.time()
    total_bytes = index.save_binary(str(output_path))
    save_time = time.time() - start_time

    print(f"\n=== Update Complete ===")
    print(f"Total memories: {len(index.memories)}")
    print(f"New items added: {len(new_items)}")
    print(f"File size: {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"Save time: {save_time:.1f}s")

    return len(new_items)


def main():
    parser = argparse.ArgumentParser(
        description='Add new curriculum items to an existing JMEM file'
    )
    parser.add_argument(
        '--jmem', '-j',
        type=Path,
        default=Path.home() / '.jiyou' / 'jmem_packs' / 'english_core.jmem',
        help='Path to existing JMEM file'
    )
    parser.add_argument(
        '--curriculum', '-c',
        type=Path,
        default=Path(__file__).parent.parent / 'curricula' / 'english_core.jcur',
        help='Path to curriculum directory'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output path (defaults to overwriting input JMEM)'
    )
    parser.add_argument(
        '--filter', '-f',
        type=str,
        default='3*.json',
        help='Lesson file filter pattern (default: "3*.json" for new conversation lessons)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Process all lessons (ignore filter)'
    )

    args = parser.parse_args()

    if not args.jmem.exists():
        print(f"ERROR: JMEM file not found: {args.jmem}")
        sys.exit(1)

    if not args.curriculum.exists():
        print(f"ERROR: Curriculum not found: {args.curriculum}")
        sys.exit(1)

    lesson_filter = None if args.all else args.filter

    count = add_curriculum_to_jmem(
        jmem_path=args.jmem,
        curriculum_dir=args.curriculum,
        output_path=args.output,
        lesson_filter=lesson_filter,
    )

    if count > 0:
        print(f"\nSuccess! Added {count} new items to JMEM.")
    else:
        print("\nNo changes made.")


if __name__ == "__main__":
    main()
