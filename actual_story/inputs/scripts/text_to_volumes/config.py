"""
Configuration constants for the Mahabharata TXT extraction pipeline.
Specific to: input/Complete_text_mahabharat.txt
"""

# Input TXT filename (expected in input/ folder)
TXT_FILENAME = 'The Mahabharata Set of 10 Volumes.txt'

# Number of volumes in the text
NUM_VOLUMES = 10

# Volume markers - these strings appear in the text to mark volume boundaries
VOLUME_MARKERS = {
    1: "Volume 1",
    2: "Volume 2",
    3: "Volume 3",
    4: "Volume 4",
    5: "Volume 5",
    6: "Volume 6",
    7: "Volume 7",
    8: "Volume 8",
    9: "Volume 9",
    10: "Volume 10",
}

# Patterns that indicate TOC, front matter, or non-story content
TOC_PATTERNS = [
    r'^Contents$',
    r'^About the Translator$',
    r'^Dedication$',
    r'^Family Tree$',
    r'^Map of Bharatavarsha',
    r'^Introduction$',
    r'^SECTION [A-Z]+$',
    r'^[A-Z\s]+ PARVA$',
    r'^\d+ [a-z]+$',  # Page numbers
]

# Patterns for section headers
SECTION_HEADER_PATTERN = r'^Section (One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|\d+)\s+(.+?)$'

# Chapter number pattern (standalone numbers at start of paragraphs)
CHAPTER_NUMBER_PATTERN = r'^\d{1,4}$'

# Footnote reference pattern in text
FOOTNOTE_REF_PATTERN = r'\{(\d+)\}'

# Patterns that indicate footers or page artifacts
FOOTER_PATTERNS = [
    r'^\d+$',  # Standalone page numbers
    r'^Page \d+',
    r'^\s*$',  # Empty lines
]
