#!/usr/bin/env python3
"""
Sync documentation files to .kiro/onboarding/ folder.

This script copies key documentation files from their source locations
to the .kiro/onboarding/ folder for use by the steering assistant.

Usage:
    python scripts/sync_onboarding_docs.py
"""

import shutil
from pathlib import Path


def main():
    """Copy documentation files to .kiro/onboarding/."""
    # Project root
    root = Path(__file__).parent.parent
    onboarding = root / ".kiro" / "onboarding"
    
    # Ensure onboarding directory exists
    onboarding.mkdir(parents=True, exist_ok=True)
    
    # Files to sync: (source_path, dest_name)
    files_to_sync = [
        # Root-level files
        (root / "README.md", "README.md"),
        (root / "CHANGELOG.md", "CHANGELOG.md"),
        (root / "CONTRIBUTING.md", "CONTRIBUTING.md"),
        
        # docs/ folder
        (root / "docs" / "architecture.md", "architecture.md"),
        (root / "docs" / "development.md", "development.md"),
        (root / "docs" / "steering-assistant-guide.md", "steering-assistant-guide.md"),
        
        # hiveforge-power/docs/ folder
        (root / "hiveforge-power" / "docs" / "CONFIGURATION.md", "CONFIGURATION.md"),
        (root / "hiveforge-power" / "docs" / "LLM_CONFIGURATION.md", "LLM_CONFIGURATION.md"),
        (root / "hiveforge-power" / "docs" / "API_REFERENCE.md", "API_REFERENCE.md"),
        (root / "hiveforge-power" / "docs" / "TECHNICAL_DEBT_IMPLEMENTATION.md", "TECHNICAL_DEBT_IMPLEMENTATION.md"),
        (root / "hiveforge-power" / "docs" / "LLM_PRIMARY_SYNTHESIS_IMPLEMENTATION.md", "LLM_PRIMARY_SYNTHESIS_IMPLEMENTATION.md"),
        
        # Spec files (for reference)
        (root / ".kiro" / "specs" / "code-review-and-debt-tracking" / "requirements.md", "requirements.md"),
        (root / ".kiro" / "specs" / "code-review-and-debt-tracking" / "design.md", "design.md"),
    ]
    
    copied = []
    skipped = []
    
    for source, dest_name in files_to_sync:
        dest = onboarding / dest_name
        
        if not source.exists():
            skipped.append((source, "Source file not found"))
            continue
        
        try:
            shutil.copy2(source, dest)
            copied.append((source, dest))
            print(f"✓ Copied: {source.relative_to(root)} → {dest.relative_to(root)}")
        except Exception as e:
            skipped.append((source, str(e)))
            print(f"✗ Failed: {source.relative_to(root)} - {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Sync complete:")
    print(f"  Copied: {len(copied)} files")
    print(f"  Skipped: {len(skipped)} files")
    
    if skipped:
        print(f"\nSkipped files:")
        for source, reason in skipped:
            print(f"  - {source.relative_to(root)}: {reason}")


if __name__ == "__main__":
    main()
