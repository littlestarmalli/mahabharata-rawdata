"""Main run script for TXT extraction pipeline.
Orchestrates all extraction, cleanup, and formatting steps."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_to_volumes.txt_parser import step1_extract_volumes
from text_to_volumes.text_fixes import run_all_fixes


def main():
    """Run the complete TXT extraction pipeline."""
    print("""
============================================================
       MAHABHARATA TXT EXTRACTION PIPELINE
       Extracting from: input/Complete_text_mahabharat.txt
       Output: text_to_volumes/output/
============================================================
""")
    
    # Step 1: Extract volumes from TXT
    print("\n[STEP 1] Extracting volumes from TXT file...")
    step1_extract_volumes(input_dir='input', output_dir='text_to_volumes/output')
    
    # Step 2: Clean up and fix text
    print("\n[STEP 2] Running text cleanup and fixes...")
    run_all_fixes(base_dir='text_to_volumes/output')
    
    print("""
============================================================
                    PIPELINE COMPLETE

  Output files created:
    - text_to_volumes/output/volume_N_chapters.txt
    - text_to_volumes/output/volume_N_footnotes.txt
    - text_to_volumes/output/volume_N_toc.txt

  Next steps:
    1. Review extracted chapters for accuracy
    2. Enhance footnote extraction if needed
    3. Add section header mapping (optional)
============================================================
""")


if __name__ == '__main__':
    main()
