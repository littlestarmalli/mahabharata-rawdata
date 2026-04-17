"""
Configuration constants for the Mahabharata PDF pipeline.
Specific to: "The Mahabharata Set of 10 Volumes.pdf" (3,723 pages)
"""

# Page index (0-based) where each volume starts in the PDF
VOLUME_START_PAGES = {
    1: 0, 2: 275, 3: 548, 4: 879, 5: 1185,
    6: 1496, 7: 1767, 8: 2253, 9: 2988, 10: 3356,
}

# Input PDF filename (expected in input/ folder)
PDF_FILENAME = 'The Mahabharata Set of 10 Volumes.pdf'

# Number of volumes
NUM_VOLUMES = 10
