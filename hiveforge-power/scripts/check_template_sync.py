#!/usr/bin/env python3
"""
Template Sync Verification Script

Verifies that base templates in src/hiveforge/templates/steering/ and
hiveforge-power/hiveforge/templates/steering/ are byte-for-byte identical.

Exit codes:
    0: Templates are in sync
    1: Templates differ or directories not found
"""

import sys
from pathlib import Path
import filecmp


def main():
    """Check template synchronization between src/ and hiveforge-power/"""
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src" / "hiveforge" / "templates" / "steering"
    hf_dir = project_root / "hiveforge-power" / "hiveforge" / "templates" / "steering"
    
    # Check directories exist
    if not src_dir.exists():
        print(f"ERROR: Source template directory not found: {src_dir}")
        return 1
    
    if not hf_dir.exists():
        print(f"ERROR: HiveForge template directory not found: {hf_dir}")
        return 1
    
    # Base template files (excluding variants)
    base_templates = [
        "api-standards.md",
        "architecture.md",
        "conventions.md",
        "db-standards.md",
        "project-vision.md",
        "qa-standards.md",
        "tech-stack.md",
        "ui-standards.md",
    ]
    
    # Track differences
    differences = []
    missing_files = []
    
    print("Checking template synchronization...")
    print(f"  Source: {src_dir}")
    print(f"  Target: {hf_dir}")
    print()
    
    for template in base_templates:
        src_file = src_dir / template
        hf_file = hf_dir / template
        
        # Check if files exist
        if not src_file.exists():
            missing_files.append(f"Missing in src/: {template}")
            continue
        
        if not hf_file.exists():
            missing_files.append(f"Missing in hiveforge-power/: {template}")
            continue
        
        # Compare files byte-for-byte
        if not filecmp.cmp(src_file, hf_file, shallow=False):
            differences.append(template)
            print(f"  ✗ DIFFER: {template}")
        else:
            print(f"  ✓ IDENTICAL: {template}")
    
    print()
    
    # Report results
    if missing_files:
        print("Missing files:")
        for msg in missing_files:
            print(f"  - {msg}")
        print()
    
    if differences:
        print(f"ERROR: {len(differences)} template(s) differ:")
        for template in differences:
            print(f"  - {template}")
        print()
        print("Templates must be byte-for-byte identical.")
        print("Canonical location: hiveforge-power/hiveforge/templates/steering/")
        print("Copy changes from canonical location to src/ to sync.")
        return 1
    
    if missing_files:
        return 1
    
    print(f"SUCCESS: All {len(base_templates)} base templates are in sync!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
