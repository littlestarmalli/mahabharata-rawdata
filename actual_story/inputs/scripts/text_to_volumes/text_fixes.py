"""Text cleanup and fixes for TXT extraction.
Adapted from pipeline/fixes/ocr_fixes.py and pipeline/fixes/paragraph_merge.py
but tailored for TXT-specific issues instead of OCR artifacts."""

import os
import re


# Manual fixes for specific text issues
# Format: (volume, file_type, old_text, new_text, description)
TEXT_FIXES = [
    # Add any specific fixes found during processing
    # Example: (1, 'chapters', 'old text', 'new text', 'description'),
]


def step2_manual_fixes(base_dir):
    """Apply known manual fixes for text issues."""
    print("\n" + "=" * 60)
    print("STEP 2: Applying manual text fixes")
    print("=" * 60)
    
    fixes = 0
    
    if not TEXT_FIXES:
        print("  No manual fixes configured")
        return
    
    # Group fixes by (volume, file_type)
    fix_groups = {}
    for vol, ftype, old, new, desc in TEXT_FIXES:
        fix_groups.setdefault((vol, ftype), []).append((old, new, desc))
    
    for (vol, ftype), group in fix_groups.items():
        path = os.path.join(base_dir, f'volume_{vol}_{ftype}.txt')
        if not os.path.exists(path):
            continue
        
        text = open(path, encoding='utf-8').read()
        changed = False
        
        for old, new, desc in group:
            if old in text:
                text = text.replace(old, new)
                changed = True
                fixes += 1
                print(f"  Vol {vol} {ftype}: {desc}")
        
        if changed:
            open(path, 'w', encoding='utf-8').write(text)
    
    print(f"  Applied {fixes} fixes")


def normalize_quotes(base_dir):
    """Quote normalization is DISABLED (spec Step 1/11: STRICT).

    The spec forbids any modification of smart quotes, straight quotes,
    or apostrophes.  The only allowed textual fix (U+FFFD -> U+2019) is
    already performed by ``txt_parser._normalize_line`` during extraction.
    This function is kept only so existing callers still work.
    """
    print("\n" + "=" * 60)
    print("STEP 3: Quote normalization (SKIPPED - spec forbids quote changes)")
    print("=" * 60)
    print("  Quotes left exactly as produced by the extractor.")


def clean_unicode_artifacts(base_dir):
    """Clean up common unicode artifacts from text conversion.
    
    Examples:
    - ? for unknown characters
    - Multiple spaces
    - Unusual whitespace characters
    """
    print("\n" + "=" * 60)
    print("STEP 4: Cleaning unicode artifacts")
    print("=" * 60)
    
    total = 0
    
    for vol in range(1, 11):
        path = os.path.join(base_dir, f'volume_{vol}_chapters.txt')
        if not os.path.exists(path):
            continue
        
        text = open(path, encoding='utf-8').read()
        original_text = text
        
        # Remove excessive whitespace
        text = re.sub(r' +', ' ', text)
        
        # Clean up unusual unicode spaces
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u2002', ' ')  # En space
        text = text.replace('\u2003', ' ')  # Em space
        text = text.replace('\u2009', ' ')  # Thin space
        
        # Remove zero-width characters
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\ufeff', '')  # Zero-width no-break space
        
        # Clean up unusual hyphens/dashes
        text = text.replace('\u2010', '-')  # Hyphen
        text = text.replace('\u2011', '-')  # Non-breaking hyphen
        # Keep em-dash and en-dash as they may be intentional
        
        if text != original_text:
            open(path, 'w', encoding='utf-8').write(text)
            total += 1
            print(f"  Cleaned Volume {vol}")
    
    print(f"  Cleaned {total} volumes")


def merge_broken_paragraphs(base_dir):
    """Merge paragraphs that were incorrectly split.
    
    TXT extraction may have line breaks that split paragraphs mid-sentence.
    This detects and merges such cases based on:
    1. Previous line doesn't end with sentence-ending punctuation
    2. Next line doesn't start with common paragraph starters (quotes, capital letters after periods)
    """
    print("\n" + "=" * 60)
    print("STEP 5: Merging broken paragraphs")
    print("=" * 60)
    
    SENT_END = '.!?\u2019\u201d\'")}'
    CHAP_MARKER = re.compile(r'^--- .+ ---$')
    
    total_merges = 0
    
    for vol in range(1, 11):
        path = os.path.join(base_dir, f'volume_{vol}_chapters.txt')
        if not os.path.exists(path):
            continue
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        result_lines = []
        current_para = ""
        merge_count = 0
        
        for line in lines:
            line = line.rstrip('\n\r')
            stripped = line.strip()
            
            # Empty line - flush paragraph
            if not stripped:
                if current_para:
                    result_lines.append(current_para)
                    current_para = ""
                result_lines.append(line)
                continue
            
            # Chapter/section marker - flush paragraph
            if CHAP_MARKER.match(stripped):
                if current_para:
                    result_lines.append(current_para)
                    current_para = ""
                result_lines.append(line)
                continue
            
            # If no current paragraph, start new one
            if not current_para:
                current_para = stripped
                continue
            
            # Check if we should merge or start new paragraph
            prev_end = current_para.rstrip()
            
            # Should merge if:
            # 1. Previous doesn't end with sentence punctuation
            # 2. Current doesn't start with quote or dialog marker
            should_merge = False
            if prev_end and prev_end[-1] not in SENT_END:
                # Previous line incomplete
                if not (stripped[0] in '\u2018\u201c"\''):
                    # Current doesn't start with quote
                    should_merge = True
            
            if should_merge:
                # Merge with space
                if current_para.endswith('-'):
                    current_para = current_para[:-1] + stripped
                else:
                    current_para += ' ' + stripped
                merge_count += 1
            else:
                # Start new paragraph
                result_lines.append(current_para)
                current_para = stripped
        
        # Flush final paragraph
        if current_para:
            result_lines.append(current_para)
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            for line in result_lines:
                f.write(line + '\n')
        
        if merge_count > 0:
            print(f"  Volume {vol}: merged {merge_count} lines")
            total_merges += merge_count
    
    print(f"  Total merged: {total_merges} lines")


def run_all_fixes(base_dir='text_to_volumes/output'):
    """Run all text cleanup and fixes."""
    print("\n" + "=" * 60)
    print("TEXT CLEANUP PIPELINE")
    print("=" * 60)
    
    step2_manual_fixes(base_dir)
    normalize_quotes(base_dir)
    clean_unicode_artifacts(base_dir)
    # Paragraph reconstruction is now done inside txt_parser._form_paragraphs
    # (spec Steps 4-14).  Running the legacy merger again would over-join
    # correctly-separated paragraphs, so it is intentionally skipped here.
    # merge_broken_paragraphs(base_dir)
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    run_all_fixes()
