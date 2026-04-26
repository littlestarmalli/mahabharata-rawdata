"""Debug trailing attribution extraction."""
import re

TRAILING_ATTR_RE = re.compile(
    r'^((?:(?:the|his|her)\s+)?[\w][\w\'-]*(?:\s+[\w][\w\'-]*)?)\s+'
    r'(said|told|replied|asked|spoke|answered|exclaimed|continued|resumed|retorted|addressed)'
    r'(?:\s+(?:(?:to|before)\s+)?(?:him|her|them|it|his\s+[\w]+|her\s+[\w]+|the\s+[\w]+))?'
    r'\s*[,:]\s*$',
    re.IGNORECASE
)

tests = [
    ' Thus addressed, the preceptor replied, ',
    ' On hearing this, the preceptor replied, ',
    " Hearing his preceptor's voice, Aruni rose from the breach in the dike, stood before his preceptor and said, ",
    ' The preceptor also blessed him. ',
    " As he was thus thinking, the man said, ",
    " Thus addressed, Janamejaya replied, ",
    " Thus addressed, he told the queen, ",
]

for text in tests:
    text_r = text.rstrip()
    ends_ok = text_r.endswith(',') or text_r.endswith(':')
    
    # Extract tail
    tail = text_r
    for sep in ['. ', '! ', '? ', '; ']:
        idx = text_r.rfind(sep)
        if idx >= 0 and len(text_r) - idx > 10:
            tail = text_r[idx + len(sep):]
            break
    
    if len(tail) > 100:
        trimmed = tail.rstrip(', ')
        cidx = trimmed.rfind(', ')
        if cidx > 0:
            tail = trimmed[cidx + 2:] + tail[len(trimmed):]
    
    tail_s = tail.strip()
    m = TRAILING_ATTR_RE.match(tail_s)
    
    orig = text.strip()[:70]
    if m:
        print(f"  OK  [{orig}]")
        print(f"      tail=[{tail_s}] => name=[{m.group(1).strip()}] verb=[{m.group(2)}]")
    else:
        print(f"  MISS [{orig}]")
        print(f"      tail=[{tail_s}] ends_ok={ends_ok}")
    print()
