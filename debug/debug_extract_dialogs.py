#!/usr/bin/env python3
"""
debug_extract_dialogs.py — Extract highlighted dialog/speech from Mahabharata volumes.

Ports the stack-based smart-quote detection from TheMahabharata ReadingView.tsx.
Scans all 10 volumes, finds quoted speech (using Unicode smart quotes),
identifies speakers where possible, and outputs a JSON file.

Smart quote characters:
  \u2018 = left single quote (open)
  \u2019 = right single quote (close) — also apostrophe
  \u201C = left double quote (open)
  \u201D = right double quote (close)

Logic:
  - Stack-based matching for nested quotes
  - Apostrophe detection (e.g. don't, Krishna's)
  - Speaker heuristic: look for "Name said/spoke/replied:" before quote
  - Per-chapter processing (quote state resets per chapter)

Output:
  debug/dialogs_debug.json

Usage:
  python debug/debug_extract_dialogs.py
"""

import os
import re
import json
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOLUMES_DIR = os.path.join(BASE_DIR, 'output', 'volumes')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dialogs_debug.json')
NUM_VOLUMES = 10

# ─── Quote characters ───────────────────────────────────────────────
OPEN_SINGLE  = '\u2018'  # '
CLOSE_SINGLE = '\u2019'  # '
OPEN_DOUBLE  = '\u201C'  # "
CLOSE_DOUBLE = '\u201D'  # "

# ─── Speaker detection regex ────────────────────────────────────────
# Matches: "Arjuna said:", "The sages replied:", "Krishna spoke:", etc.
SPEAKER_RE = re.compile(
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+'
    r'(?:said|spoke|replied|asked|answered|exclaimed|stated|declared|continued|responded|told|cried|shouted|recited|narrated|addressed)'
    r'[,:]?\s*$'
)

# Broader pattern: "X said," or "said X," before the quote
SPEAKER_RE2 = re.compile(
    r'(?:([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+'
    r'(?:said|spoke|replied|asked|answered|exclaimed|stated|declared|continued|responded|told|cried|shouted|recited|narrated|addressed)'
    r'|(?:said|spoke|replied|asked|answered|exclaimed|stated|declared|continued|responded|told|cried|shouted|recited|narrated|addressed)\s+'
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))'
    r'[,:.]*\s*$'
)


def is_apostrophe(text, index):
    """Check if \u2019 at index is an apostrophe (e.g. don't, Krishna's)."""
    prev = text[index - 1] if index > 0 else ''
    nxt = text[index + 1] if index + 1 < len(text) else ''
    # Apostrophe: letter before AND letter after (e.g. don't)
    if prev.isalpha() and nxt.isalpha():
        return True
    # Possessive: letter before, then 's' (e.g. Krishna's)
    if prev.isalpha() and nxt == 's':
        return True
    return False


def is_paragraph_leading(text, index):
    """Check if quote at index is at start of paragraph (after newline or start)."""
    cursor = index - 1
    while cursor >= 0:
        ch = text[cursor]
        if ch in (' ', '\t', '\r'):
            cursor -= 1
            continue
        if ch == '\n':
            return True
        # Allow quote clusters like '" at paragraph start
        if ch in (OPEN_SINGLE, OPEN_DOUBLE, CLOSE_SINGLE, CLOSE_DOUBLE):
            cursor -= 1
            continue
        return False
    return True  # start of text


def find_speaker(text, quote_start):
    """Look backwards from quote_start for a speaker pattern."""
    # Get up to 100 chars before the quote
    start = max(0, quote_start - 100)
    before = text[start:quote_start]
    # Try primary pattern
    m = SPEAKER_RE.search(before)
    if m:
        return m.group(1)
    # Try secondary pattern
    m = SPEAKER_RE2.search(before)
    if m:
        return m.group(1) or m.group(2)
    return None


def extract_dialogs_from_text(text, volume, chapter):
    """
    Port of buildDirectSpeechRangeMap from ReadingView.tsx.
    Returns list of dialog dicts.
    """
    dialogs = []
    stack = []  # list of {'kind': 'single'|'double', 'start': int}
    color_idx = 0

    i = 0
    while i < len(text):
        ch = text[i]

        # ── Open single quote ──
        if ch == OPEN_SINGLE:
            # If we already have an open single quote at paragraph-leading position, skip
            has_open_single = any(q['kind'] == 'single' for q in stack)
            if has_open_single and is_paragraph_leading(text, i):
                i += 1
                continue
            stack.append({'kind': 'single', 'start': i, 'depth': color_idx})
            color_idx += 1
            i += 1
            continue

        # ── Open double quote ──
        if ch == OPEN_DOUBLE:
            has_open_double = any(q['kind'] == 'double' for q in stack)
            if has_open_double and is_paragraph_leading(text, i):
                i += 1
                continue
            stack.append({'kind': 'double', 'start': i, 'depth': color_idx})
            color_idx += 1
            i += 1
            continue

        # ── Close single quote ──
        if ch == CLOSE_SINGLE:
            if is_apostrophe(text, i):
                i += 1
                continue
            # Find matching open single
            match = None
            for j in range(len(stack) - 1, -1, -1):
                if stack[j]['kind'] == 'single':
                    match = stack.pop(j)
                    break
            if match:
                qstart = match['start']
                qend = i + 1
                quoted_text = text[qstart:qend]
                speaker = find_speaker(text, qstart)
                dialogs.append({
                    'volume': volume,
                    'chapter': chapter,
                    'start': qstart,
                    'end': qend,
                    'quote_type': 'single',
                    'depth': match['depth'],
                    'text': quoted_text,
                    'speaker': speaker,
                })
            i += 1
            continue

        # ── Close double quote ──
        if ch == CLOSE_DOUBLE:
            match = None
            for j in range(len(stack) - 1, -1, -1):
                if stack[j]['kind'] == 'double':
                    match = stack.pop(j)
                    break
            if match:
                qstart = match['start']
                qend = i + 1
                quoted_text = text[qstart:qend]
                speaker = find_speaker(text, qstart)
                dialogs.append({
                    'volume': volume,
                    'chapter': chapter,
                    'start': qstart,
                    'end': qend,
                    'quote_type': 'double',
                    'depth': match['depth'],
                    'text': quoted_text,
                    'speaker': speaker,
                })
            i += 1
            continue

        i += 1

    # Close any remaining open single quotes at end of chapter
    for openq in stack:
        if openq['kind'] == 'single':
            qstart = openq['start']
            quoted_text = text[qstart:]
            speaker = find_speaker(text, qstart)
            dialogs.append({
                'volume': volume,
                'chapter': chapter,
                'start': qstart,
                'end': len(text),
                'quote_type': 'single',
                'depth': openq['depth'],
                'text': quoted_text,
                'speaker': speaker,
            })

    return dialogs


def main():
    print("=" * 60)
    print("Dialog Extraction Pipeline")
    print("=" * 60)

    all_dialogs = []
    stats = {'total': 0, 'with_speaker': 0, 'single': 0, 'double': 0}

    for v in range(1, NUM_VOLUMES + 1):
        print(f"Scanning volume {v}...")
        ch_text = open(os.path.join(VOLUMES_DIR, f'volume_{v}_chapters.txt'), encoding='utf-8').read()

        # Split by chapter markers
        ch_parts = re.split(r'--- Chapter (\d+)(?:\(\d+\))? ---', ch_text)

        vol_count = 0
        for i in range(1, len(ch_parts), 2):
            ch_num = int(ch_parts[i])
            ch_content = ch_parts[i + 1] if i + 1 < len(ch_parts) else ''

            dialogs = extract_dialogs_from_text(ch_content, v, ch_num)
            all_dialogs.extend(dialogs)
            vol_count += len(dialogs)

        print(f"  Volume {v}: {vol_count} dialogs found")
        stats['total'] += vol_count

    # Count stats
    for d in all_dialogs:
        if d['speaker']:
            stats['with_speaker'] += 1
        if d['quote_type'] == 'single':
            stats['single'] += 1
        else:
            stats['double'] += 1

    # Build output: group by volume/chapter
    output = {
        'stats': {
            'total_dialogs': stats['total'],
            'with_speaker': stats['with_speaker'],
            'single_quoted': stats['single'],
            'double_quoted': stats['double'],
        },
        'dialogs': []
    }

    for d in all_dialogs:
        entry = {
            'volume': d['volume'],
            'chapter': d['chapter'],
            'quote_type': d['quote_type'],
            'text': d['text'],
        }
        if d['speaker']:
            entry['speaker'] = d['speaker']
        # Truncate very long dialogs in the text field for readability
        if len(d['text']) > 2000:
            entry['text'] = d['text'][:2000] + '... [truncated]'
            entry['full_length'] = len(d['text'])
        output['dialogs'].append(entry)

    # Write output
    print(f"\nWriting {len(output['dialogs'])} dialogs to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"DONE — {stats['total']} dialogs extracted")
    print(f"  With speaker: {stats['with_speaker']}")
    print(f"  Single-quoted: {stats['single']}")
    print(f"  Double-quoted: {stats['double']}")

    # Top speakers
    speaker_counts = defaultdict(int)
    for d in all_dialogs:
        if d['speaker']:
            speaker_counts[d['speaker']] += 1
    top_speakers = sorted(speaker_counts.items(), key=lambda x: -x[1])[:20]
    print(f"\n  Top 20 speakers:")
    for name, count in top_speakers:
        print(f"    {name:25s} {count} dialogs")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
