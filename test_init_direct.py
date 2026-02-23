"""Test init workflow directly without security wrapper"""
import sys
from pathlib import Path

# Add hiveforge-power to path
sys.path.insert(0, str(Path(__file__).parent / "hiveforge-power"))

from hiveforge.steering.shared.adapters import SharedInitWorkflow

try:
    print("Creating SharedInitWorkflow...")
    workflow = SharedInitWorkflow(
        project_root=".",
        source_docs_path="docs",
        auto_discover=True,
        autonomous=True,
        confidence_threshold=0.7,
        dry_run=False,
        copy_files=False
    )
    
    print("Executing workflow...")
    result = workflow.execute()
    
    print("\n=== RESULT ===")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print(f"Files created: {result.files_created}")
    print(f"Warnings: {result.warnings}")
    print(f"Errors: {result.errors}")
    print(f"Metadata: {result.metadata}")
    
except Exception as e:
    print(f"\n=== ERROR ===")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
    import traceback
    traceback.print_exc()
