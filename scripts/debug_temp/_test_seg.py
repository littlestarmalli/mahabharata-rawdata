"""Quick test of the new segment_paragraph on chapter 3 para 1."""
from build_dialog_tree import segment_paragraph
import json

# Simulated para 1 from ch 3 source (with curly quotes)
text = (
    'Suta said, \u2018Janamejaya, the son of Parikshit, attended a long sacri\ufb01ce '
    'in Kurukshetra with his brothers. His three brothers were Shrutasena, '
    'Ugrasena and Bhimasena. As they sat at the sacri\ufb01ce, a dog{1} came there. '
    'Being beaten by Janamejaya\u2019s brothers, the weeping dog went to his mother. '
    'On seeing him cry, the mother asked, \u201cWhy are you yelping? Who has beaten '
    'you?\u201d On hearing this, he told his mother, \u201cI have been beaten by '
    'Janamejaya\u2019s brothers.\u201d Then the mother said, \u201cYou must have '
    'committed some wrong that you were beaten.\u201d He replied, \u201cI did not '
    'commit any wrong. I did not lick the sacri\ufb01cial ghee. I did not even look '
    'at it.\u201d On hearing this, his mother Sarama felt sorry for the misery of '
    'her son and went to the place where Janamejaya and his brothers were '
    'attending the long sacri\ufb01ce.'
)

print("=== Para 1 (incoming stack=[]) ===")
segs, stack = segment_paragraph(text, [])
for s in segs:
    typ = s['type']
    d = s['depth']
    txt = s['text'][:80]
    print(f"  {typ:10} d{d}  {txt}")
print(f"  -> outgoing stack: {stack}")
print()

# Para 2 (continuation)
text2 = (
    '\u2018She angrily addressed Janamejaya. \u201cMy son committed no wrong. '
    'He did not lick your sacri\ufb01cial ghee. He did not even look at it. Why did '
    'you then beat him? Since you beat my son who committed no wrong, evil will '
    'befall you when you least expect it.\u201d On hearing these words of Sarama, '
    'dog of the gods, Janamejaya was saddened and miserable.'
)

print("=== Para 2 (incoming stack=[\"'\"]) ===")
segs2, stack2 = segment_paragraph(text2, stack)
for s in segs2:
    typ = s['type']
    d = s['depth']
    txt = s['text'][:80]
    print(f"  {typ:10} d{d}  {txt}")
print(f"  -> outgoing stack: {stack2}")
