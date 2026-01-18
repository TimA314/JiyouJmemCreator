#!/usr/bin/env python3
"""
Generate Meta-Learning and Reading Comprehension curriculum using Grok API.

Creates new lessons for english_core.jcur to help JiYou:
- Express how to learn, ask for clarification, break down problems
- Process any text - summarize, extract main ideas, make inferences
- Follow multi-step instructions
- Recognize and express knowledge gaps

Usage:
    export GROK_API_KEY="your-key-here"
    python tools/generate_metalearning_curriculum.py --all
    python tools/generate_metalearning_curriculum.py --category meta_learning --count 50
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional


# =============================================================================
# GROK API CLIENT
# =============================================================================

GROK_API_KEY: Optional[str] = None

def get_api_key() -> str:
    """Get Grok API key from environment or file."""
    global GROK_API_KEY
    if GROK_API_KEY:
        return GROK_API_KEY

    api_key = os.environ.get("GROK_API_KEY")
    if not api_key:
        key_file = Path.home() / ".grok_api_key"
        if key_file.exists():
            api_key = key_file.read_text().strip()
        else:
            print("Error: GROK_API_KEY environment variable not set")
            print("Set it with: export GROK_API_KEY='your-key-here'")
            print("Or create ~/.grok_api_key file with your key")
            sys.exit(1)

    GROK_API_KEY = api_key
    return api_key


def call_grok_api(messages: List[Dict], temperature: float = 0.9, max_tokens: int = 4000) -> str:
    """Call Grok API directly using urllib."""
    api_key = get_api_key()

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "curl/8.0",
        "Accept": "application/json",
    }
    data = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"Grok API error {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {e.reason}")


# =============================================================================
# CATEGORIES FOR META-LEARNING & READING COMPREHENSION
# =============================================================================

CATEGORIES = {
    "meta_learning": {
        "count": 300,
        "description": "Phrases for learning how to learn, requesting clarification, self-assessment",
        "prompt": """Generate dialogue pairs teaching meta-learning skills - how to learn effectively.

The SOURCE is what someone says when learning, and TARGET is JiYou's helpful response.

Include varied phrases for:
- Requesting clarification: "I need more context about X", "Can you explain that differently?"
- Breaking down problems: "Let me break this down step by step", "What are the key components?"
- Verifying understanding: "What I understand so far is...", "Let me paraphrase to make sure I get it"
- Asking for examples: "Can you give me an example?", "What would that look like in practice?"
- Connecting concepts: "How does X relate to Y?", "Is this similar to Z?"
- Identifying key points: "What's the main idea here?", "What's most important to remember?"
- Self-assessment: "I think I understand X but not Y", "I'm confident about A but uncertain about B"
- Learning strategies: "Should I memorize this or understand the concept?", "What's a good way to practice this?"
- Recognizing patterns: "I notice a pattern here", "This seems to follow from..."
- Summarizing: "Let me summarize what I've learned", "So the key takeaway is..."

JiYou's responses should be encouraging, helpful, and model good learning practices.""",
    },

    "reading_comprehension": {
        "count": 300,
        "description": "Skills for extracting meaning from text - summarization, main idea, inference",
        "prompt": """Generate dialogue pairs teaching reading comprehension skills.

The SOURCE is someone asking about or processing text, and TARGET is JiYou demonstrating the skill.

Include varied phrases for:
- Summarization: "The main point of this passage is...", "In summary, the text says..."
- Identifying central ideas: "The central argument here is...", "The key theme is..."
- Making inferences: "Based on this, I can conclude that...", "The text implies that..."
- Recognizing structure: "This is organized by...", "The author uses X structure to..."
- Extracting details: "According to the passage...", "The text states that..."
- Determining purpose: "The author's purpose is to...", "This was written to..."
- Understanding context: "In this context, X means...", "Given the context..."
- Following logic: "The reasoning here is...", "This follows because..."
- Identifying tone: "The tone of this passage is...", "The author seems to feel..."
- Evaluating arguments: "The evidence supports...", "The claim is backed by..."
- Comparing ideas: "This contrasts with...", "This is similar to..."

JiYou should model clear, analytical thinking about text.""",
    },

    "instruction_following": {
        "count": 200,
        "description": "Executing multi-step instructions from text",
        "prompt": """Generate dialogue pairs about following instructions methodically.

The SOURCE is someone processing instructions, and TARGET is JiYou helping execute them.

Include varied phrases for:
- Starting instructions: "First, I need to...", "The first step is..."
- Sequencing: "After that, I should...", "Next, the instructions say..."
- Confirming steps: "Step 1 says to... so I'll do that", "According to step 3..."
- Tracking progress: "I've completed steps 1-3, now on step 4", "So far I've..."
- Handling conditions: "If X, then I should...", "Since the condition is met..."
- Asking for clarification: "Does this step mean...?", "Should I do X before Y?"
- Verifying completion: "Have I completed all the steps?", "Did I miss anything?"
- Handling errors: "This step didn't work, what should I try?", "I got a different result..."
- Adapting instructions: "For my situation, I should modify...", "In this case..."
- Summarizing procedures: "The overall process is...", "To do X, you need to..."

JiYou should be methodical, patient, and thorough in helping with instructions.""",
    },

    "knowledge_gap_recognition": {
        "count": 200,
        "description": "Recognizing and expressing what you don't know",
        "prompt": """Generate dialogue pairs about recognizing and expressing knowledge gaps honestly.

The SOURCE is someone encountering limits of their knowledge, and TARGET is JiYou modeling intellectual honesty.

Include varied phrases for:
- Admitting unfamiliarity: "I'm not familiar with X yet", "I don't know much about..."
- Expressing uncertainty: "I'm not sure about this", "I might be wrong, but..."
- Requesting information: "I'd need to learn more about X", "Can you tell me about...?"
- Acknowledging limits: "That's outside my current knowledge", "I don't have expertise in..."
- Deferring to experts: "You should consult an expert on...", "A specialist would know better"
- Promising to learn: "Let me find out more about...", "I'll look into that"
- Distinguishing knowledge levels: "I know X well, but Y is less familiar", "I have basic knowledge of..."
- Asking clarifying questions: "What do you mean by X?", "Is X the same as Y?"
- Expressing curiosity: "I'd like to learn more about...", "That's interesting, what is...?"
- Being honest about errors: "I was wrong about that", "Let me correct my earlier statement"
- Recognizing complexity: "This is more complicated than I thought", "There's more to learn here"

JiYou should model intellectual humility and genuine curiosity.""",
    },
}


# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def parse_json_response(response_text: str) -> List[Dict[str, str]]:
    """Extract JSON array from model response."""
    text = response_text.strip()

    # Look for array brackets
    start = text.find('[')
    end = text.rfind(']')

    if start != -1 and end != -1 and end > start:
        json_str = text[start:end + 1]
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    # Try to parse line by line for individual objects
    pairs = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                obj = json.loads(line)
                if 'source' in obj and 'target' in obj:
                    pairs.append(obj)
            except json.JSONDecodeError:
                continue

    return pairs


def generate_batch(
    category: str,
    category_info: Dict[str, Any],
    batch_num: int,
    batch_size: int = 20,
    existing_sources: set = None,
) -> List[Dict[str, str]]:
    """Generate a batch of dialogue pairs using Grok API."""

    avoid_examples = ""
    if existing_sources and len(existing_sources) > 0:
        samples = list(existing_sources)[:10]
        avoid_examples = f"\n\nAvoid these already-used sources:\n{json.dumps(samples, indent=2)}"

    prompt = f"""Generate {batch_size} unique, natural dialogue pairs for: {category.replace('_', ' ')}

{category_info['prompt']}

Format: Return ONLY a valid JSON array of objects with "source" and "target" fields.
{avoid_examples}

Generate batch {batch_num} with {batch_size} NEW unique pairs (different from any shown above):"""

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates natural dialogue training data. Always respond with valid JSON arrays only, no other text."},
            {"role": "user", "content": prompt}
        ]

        response_text = call_grok_api(messages, temperature=0.9, max_tokens=4000)
        pairs = parse_json_response(response_text)
        return pairs

    except Exception as e:
        print(f"  Error generating batch: {e}")
        return []


def generate_category(
    category: str,
    target_count: int,
    batch_size: int = 20,
    dry_run: bool = False,
) -> List[Dict[str, str]]:
    """Generate all dialogue pairs for a category."""

    if category not in CATEGORIES:
        print(f"Unknown category: {category}")
        return []

    category_info = CATEGORIES[category]
    print(f"\nGenerating {category}: {category_info['description']}")
    print(f"  Target: {target_count} pairs")

    if dry_run:
        print("  [DRY RUN - would generate here]")
        return []

    all_pairs = []
    seen_sources = set()
    batch_num = 0

    while len(all_pairs) < target_count:
        batch_num += 1
        remaining = target_count - len(all_pairs)
        current_batch_size = min(batch_size, remaining + 5)

        print(f"  Batch {batch_num}: generating {current_batch_size} pairs...", end=" ", flush=True)

        pairs = generate_batch(
            category, category_info, batch_num,
            current_batch_size, seen_sources
        )

        # Deduplicate by source
        new_pairs = []
        for pair in pairs:
            source = pair.get('source', '').strip().lower()
            if source not in seen_sources:
                seen_sources.add(source)
                new_pairs.append(pair)

        all_pairs.extend(new_pairs)
        print(f"got {len(new_pairs)} unique ({len(all_pairs)}/{target_count})")

        # Rate limiting
        time.sleep(1.0)

        # Safety limit
        if batch_num > target_count // batch_size + 30:
            print(f"  Reached batch limit, stopping at {len(all_pairs)} pairs")
            break

    return all_pairs[:target_count]


def create_lesson_file(
    category: str,
    pairs: List[Dict[str, str]],
    lesson_id: str,
    lesson_num: int,
    output_dir: Path,
) -> Path:
    """Create a JCUR lesson file from dialogue pairs."""

    category_info = CATEGORIES.get(category, {})
    clean_category = category.replace('_', ' ').title()

    lesson = {
        "lesson_id": lesson_id,
        "title": f"Learning Skills: {clean_category}",
        "description": category_info.get("description", f"Learning skills for {category}"),
        "category": "learning",
        "difficulty": 2,
        "estimated_minutes": max(15, len(pairs) // 10),
        "tags": ["learning", "meta-learning", category, "grok"],
        "items": []
    }

    for i, pair in enumerate(pairs):
        item = {
            "id": f"learn_{category}_{i+1:04d}",
            "type": "dialogue",
            "source": pair.get("source", ""),
            "target": pair.get("target", ""),
            "context": category,
        }
        lesson["items"].append(item)

    filename = f"{lesson_num:03d}_learning_{category}_grok.json"
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(lesson, f, indent=2, ensure_ascii=False)

    print(f"  Created: {filename} ({len(pairs)} items)")
    return filepath


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate Meta-Learning and Reading Comprehension curriculum"
    )
    parser.add_argument(
        "--category", "-c",
        help="Generate specific category only"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        help="Override count for category"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=20,
        help="Pairs per batch (default: 20)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "curricula/english_core.jcur/lessons",
        help="Output directory for lesson files"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate all categories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without calling API"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories"
    )
    parser.add_argument(
        "--start-lesson",
        type=int,
        default=250,
        help="Starting lesson number (default: 250)"
    )

    args = parser.parse_args()

    if args.list_categories:
        print("Available categories:")
        total = 0
        for name, info in CATEGORIES.items():
            print(f"  {name:30s} - {info['count']:4d} pairs - {info['description']}")
            total += info['count']
        print(f"\n  Total: {total} pairs across {len(CATEGORIES)} categories")
        return

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    # Determine which categories to generate
    if args.category:
        categories = [args.category]
    elif args.all:
        categories = list(CATEGORIES.keys())
    else:
        print("Specify --category NAME or --all to generate")
        print("Use --list-categories to see available categories")
        return

    print("Using Grok API (grok-4-1-fast-non-reasoning)")
    print(f"Output directory: {args.output}")

    if args.dry_run:
        print("[DRY RUN MODE]")
    else:
        get_api_key()
        print("Grok API key found")

    # Generate each category
    all_results = {}
    lesson_num = args.start_lesson

    for category in categories:
        count = args.count if args.count else CATEGORIES[category]["count"]
        pairs = generate_category(
            category=category,
            target_count=count,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )

        if pairs:
            lesson_id = f"learning_{category}_grok"
            create_lesson_file(
                category=category,
                pairs=pairs,
                lesson_id=lesson_id,
                lesson_num=lesson_num,
                output_dir=args.output,
            )
            all_results[category] = len(pairs)
            lesson_num += 1

    # Summary
    print("\n" + "=" * 50)
    print("GENERATION SUMMARY")
    print("=" * 50)
    total = 0
    for cat, count in all_results.items():
        print(f"  {cat:30s}: {count:5d} pairs")
        total += count
    print("-" * 50)
    print(f"  {'TOTAL':30s}: {total:5d} pairs")
    print(f"\nLesson files created in: {args.output}")


if __name__ == "__main__":
    main()
