"""
Summary analysis of paragraph comparison CSV.
Shows which chapters need attention.
"""
import csv
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(PROJECT_ROOT, 'output', 'chapter_paragraph_comparison.csv')

# Read CSV
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            'vol': int(row['Volume']),
            'ch': row['Chapter'],
            'pdf': int(row['PDF_Paragraphs']),
            'ext': int(row['Extracted_Paragraphs']),
            'diff': int(row['Difference']),
            'match': float(row['Match_Percent'])
        })

print("="*80)
print("PARAGRAPH COMPARISON SUMMARY")
print("="*80)
print()

# Group by volume
vol_stats = {}
for row in rows:
    vol = row['vol']
    if vol not in vol_stats:
        vol_stats[vol] = {
            'total_pdf': 0,
            'total_ext': 0,
            'perfect_match': 0,
            'over_split': [],  # ext > pdf
            'under_split': [],  # pdf > ext
            'no_pdf_count': 0  # pdf = 0
        }
    
    vol_stats[vol]['total_pdf'] += row['pdf']
    vol_stats[vol]['total_ext'] += row['ext']
    
    if row['diff'] == 0:
        vol_stats[vol]['perfect_match'] += 1
    elif row['diff'] < 0:
        vol_stats[vol]['over_split'].append(row)
    else:
        vol_stats[vol]['under_split'].append(row)
    
    if row['pdf'] == 0:
        vol_stats[vol]['no_pdf_count'] += 1

# Print volume summaries
for vol in range(1, 11):
    stats = vol_stats[vol]
    total_ch = stats['perfect_match'] + len(stats['over_split']) + len(stats['under_split'])
    match_pct = round(100 * stats['total_ext'] / stats['total_pdf'], 1) if stats['total_pdf'] > 0 else 0
    
    print(f"Volume {vol}:")
    print(f"  Total PDF: {stats['total_pdf']}, Extracted: {stats['total_ext']}, Match: {match_pct}%")
    print(f"  Chapters: {total_ch} total, {stats['perfect_match']} perfect match, "
          f"{len(stats['over_split'])} over-split, {len(stats['under_split'])} under-split")
    
    if stats['no_pdf_count'] > 0:
        print(f"  WARNING: {stats['no_pdf_count']} chapters with PDF count = 0 (detection failed)")
    
    # Show worst over-splits
    if stats['over_split']:
        worst_over = sorted(stats['over_split'], key=lambda x: -abs(x['diff']))[:3]
        print(f"  Worst over-splits:")
        for r in worst_over:
            print(f"    Ch {r['ch']:>12}: PDF={r['pdf']:>3} Ext={r['ext']:>3} (extra {-r['diff']} paragraphs)")
    
    # Show worst under-splits  
    if stats['under_split']:
        worst_under = sorted(stats['under_split'], key=lambda x: -x['diff'])[:3]
        print(f"  Worst under-splits:")
        for r in worst_under:
            print(f"    Ch {r['ch']:>12}: PDF={r['pdf']:>3} Ext={r['ext']:>3} (missing {r['diff']} paragraphs)")
    
    print()

# Overall summary
total_pdf_all = sum(s['total_pdf'] for s in vol_stats.values())
total_ext_all = sum(s['total_ext'] for s in vol_stats.values())
total_perfect = sum(s['perfect_match'] for s in vol_stats.values())
total_chapters = len(rows)

print("="*80)
print(f"OVERALL: PDF={total_pdf_all}, Extracted={total_ext_all}, Match={round(100*total_ext_all/total_pdf_all,1)}%")
print(f"Perfect matches: {total_perfect}/{total_chapters} chapters ({round(100*total_perfect/total_chapters,1)}%)")
print("="*80)

# Save focused mismatch list
mismatch_file = os.path.join(PROJECT_ROOT, 'output', 'chapters_to_fix.txt')
with open(mismatch_file, 'w', encoding='utf-8') as f:
    f.write("Chapters requiring attention (|diff| >= 2):\n")
    f.write("="*60 + "\n\n")
    
    for vol in range(1, 11):
        big_mismatches = [r for r in rows if r['vol'] == vol and abs(r['diff']) >= 2]
        if big_mismatches:
            f.write(f"Volume {vol}:\n")
            for r in sorted(big_mismatches, key=lambda x: -abs(x['diff'])):
                status = "OVER" if r['diff'] < 0 else "UNDER"
                f.write(f"  Ch {r['ch']:>12}: PDF={r['pdf']:>3} Ext={r['ext']:>3} Diff={r['diff']:>4} [{status}]\n")
            f.write("\n")

print(f"\nDetailed mismatch list saved to: {mismatch_file}")
