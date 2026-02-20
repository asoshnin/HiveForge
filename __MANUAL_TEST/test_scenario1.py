#!/usr/bin/env python3
"""Manual test for Scenario 1: User with docs in _DEVELOPMENT/"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hiveforge.steering.shared.adapters import SharedInitWorkflow

def test_scenario1():
    """Test init_steering with custom source_docs_path"""
    
    print("=" * 80)
    print("SCENARIO 1: User with docs in _DEVELOPMENT/")
    print("=" * 80)
    
    project_root = Path(__file__).parent / "scenario1"
    
    print(f"\n1. Project root: {project_root}")
    print(f"2. Source docs path: _DEVELOPMENT")
    
    # Check source documents exist
    source_path = project_root / "_DEVELOPMENT"
    docs = list(source_path.glob("*.md"))
    print(f"\n3. Source documents found: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.name}")
    
    # Run init workflow
    print("\n4. Running init_steering with source_docs_path='_DEVELOPMENT'...")
    
    try:
        workflow = SharedInitWorkflow(
            project_root=str(project_root),
            source_docs_path="_DEVELOPMENT",
            autonomous=False,
            dry_run=False
        )
        
        result = workflow.execute()
        
        print("\n5. Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Source documents found: {result.get('source_documents_found', 'N/A')}")
        print(f"   Confidence level: {result.get('confidence_level', 'N/A')}")
        
        if result.get('warnings'):
            print(f"\n6. Warnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"   - {warning}")
        
        # Check generated files
        steering_dir = project_root / ".kiro" / "steering"
        if steering_dir.exists():
            generated_files = list(steering_dir.glob("*.md"))
            print(f"\n7. Generated steering files: {len(generated_files)}")
            for file in generated_files:
                print(f"   - {file.name}")
                
                # Check for confidence metadata
                content = file.read_text()
                if "confidence:" in content:
                    print(f"     ✓ Has confidence metadata")
                if "<!-- INFERRED" in content:
                    print(f"     ⚠ Has inferred sections")
        
        print("\n" + "=" * 80)
        print("SCENARIO 1: ✅ PASSED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("SCENARIO 1: ❌ FAILED")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_scenario1()
    sys.exit(0 if success else 1)
