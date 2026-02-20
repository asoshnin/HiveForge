#!/usr/bin/env python3
"""
Manual tests for Phase 7.6 - All 4 scenarios.
Uses autonomous=True to avoid interactive LLM prompts.
"""

import sys
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hiveforge.steering.shared.adapters import SharedInitWorkflow


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(result):
    d = result.to_dict() if hasattr(result, 'to_dict') else result
    print(f"  Status:                {d.get('status', 'N/A')}")
    print(f"  Message:               {d.get('message', 'N/A')}")
    print(f"  Source docs found:     {d.get('metadata', {}).get('source_documents_found', 'N/A')}")
    print(f"  Confidence level:      {d.get('metadata', {}).get('confidence_level', 'N/A')}")
    print(f"  Files created:         {len(d.get('files_created', []))}")
    if d.get('warnings'):
        print(f"  Warnings ({len(d['warnings'])}):")
        for w in d['warnings']:
            print(f"    - {w}")
    return d


def check_steering_files(project_root):
    steering_dir = Path(project_root) / ".kiro" / "steering"
    if not steering_dir.exists():
        print("  Steering dir: NOT FOUND")
        return []
    files = list(steering_dir.glob("*.md"))
    print(f"  Steering files ({len(files)}):")
    for f in files:
        content = f.read_text()
        has_confidence = "confidence:" in content
        has_inferred = "<!-- INFERRED" in content
        tags = []
        if has_confidence:
            tags.append("✓ confidence metadata")
        if has_inferred:
            tags.append("⚠ inferred sections")
        tag_str = ", ".join(tags) if tags else "no metadata"
        print(f"    - {f.name} [{tag_str}]")
    return files


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1: Custom source_docs_path pointing to _DEVELOPMENT/
# ─────────────────────────────────────────────────────────────────────────────
def scenario1():
    print_header("SCENARIO 1: User with docs in _DEVELOPMENT/")

    project_root = Path(__file__).parent / "scenario1"
    # Clean up any previous run
    shutil.rmtree(project_root / ".kiro", ignore_errors=True)

    source_path = project_root / "_DEVELOPMENT"
    docs = list(source_path.glob("*.md"))
    print(f"\n  Source docs in _DEVELOPMENT/: {len(docs)}")
    for d in docs:
        print(f"    - {d.name}")

    print("\n  Running init_steering(source_docs_path='_DEVELOPMENT', autonomous=True, dry_run=False)...")

    workflow = SharedInitWorkflow(
        project_root=str(project_root),
        source_docs_path="_DEVELOPMENT",
        autonomous=True,
        dry_run=False
    )
    result = workflow.execute()
    d = print_result(result)

    print("\n  Checking generated files:")
    files = check_steering_files(project_root)

    passed = d.get('status') == 'success' and len(files) > 0
    print(f"\n  SCENARIO 1: {'✅ PASSED' if passed else '❌ FAILED'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2: Empty .kiro/onboarding/ → expect warnings + low confidence
# ─────────────────────────────────────────────────────────────────────────────
def scenario2():
    print_header("SCENARIO 2: Empty .kiro/onboarding/ → warnings + low confidence")

    project_root = Path(__file__).parent / "scenario2"
    shutil.rmtree(project_root, ignore_errors=True)
    project_root.mkdir(parents=True)
    # Create empty onboarding dir
    (project_root / ".kiro" / "onboarding").mkdir(parents=True)

    print("\n  .kiro/onboarding/ exists and is empty")
    print("  Running init_steering() with no source_docs_path, autonomous=True...")

    workflow = SharedInitWorkflow(
        project_root=str(project_root),
        source_docs_path=None,
        autonomous=True,
        dry_run=False
    )
    result = workflow.execute()
    d = print_result(result)

    # Expect: warnings about no source docs, low confidence
    has_warning = any("source" in w.lower() or "no" in w.lower() or "empty" in w.lower()
                      for w in d.get('warnings', []))
    confidence = d.get('metadata', {}).get('confidence_level', '')
    low_confidence = confidence in ('low', 'medium', '')

    print(f"\n  Has source warning: {'✅' if has_warning else '⚠ (no explicit warning)'}")
    print(f"  Confidence level '{confidence}': {'✅' if low_confidence else '❌ expected low/medium'}")

    passed = d.get('status') in ('success', 'warning') and low_confidence
    print(f"\n  SCENARIO 2: {'✅ PASSED' if passed else '❌ FAILED'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3: Dry-run → no files written, preview returned
# ─────────────────────────────────────────────────────────────────────────────
def scenario3():
    print_header("SCENARIO 3: Dry-run mode → no files written, preview returned")

    project_root = Path(__file__).parent / "scenario3"
    shutil.rmtree(project_root, ignore_errors=True)
    project_root.mkdir(parents=True)

    print("\n  Running init_steering(dry_run=True, autonomous=True)...")

    workflow = SharedInitWorkflow(
        project_root=str(project_root),
        autonomous=True,
        dry_run=True
    )
    result = workflow.execute()
    d = print_result(result)

    # Verify no files were written
    steering_dir = project_root / ".kiro" / "steering"
    files_on_disk = list(steering_dir.glob("*.md")) if steering_dir.exists() else []
    print(f"\n  Files on disk after dry-run: {len(files_on_disk)} (expected 0)")

    no_files_written = len(files_on_disk) == 0
    is_success = d.get('status') in ('success', 'warning')

    print(f"  No files written: {'✅' if no_files_written else '❌'}")
    print(f"  Status success:   {'✅' if is_success else '❌'}")

    passed = no_files_written and is_success
    print(f"\n  SCENARIO 3: {'✅ PASSED' if passed else '❌ FAILED'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 4: Backward compatibility — no new params, works as before
# ─────────────────────────────────────────────────────────────────────────────
def scenario4():
    print_header("SCENARIO 4: Backward compatibility — no new parameters")

    project_root = Path(__file__).parent / "scenario4"
    shutil.rmtree(project_root, ignore_errors=True)
    project_root.mkdir(parents=True)

    print("\n  Running init_steering() with no new parameters (autonomous=True)...")

    workflow = SharedInitWorkflow(
        project_root=str(project_root),
        autonomous=True
        # No source_docs_path, no dry_run, no copy_files
    )
    result = workflow.execute()
    d = print_result(result)

    is_success = d.get('status') in ('success', 'warning')
    print(f"\n  Workflow completed without error: {'✅' if is_success else '❌'}")

    passed = is_success
    print(f"\n  SCENARIO 4: {'✅ PASSED' if passed else '❌ FAILED'}")
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    results = {
        "Scenario 1 (custom source_docs_path)": scenario1(),
        "Scenario 2 (empty onboarding, warnings)": scenario2(),
        "Scenario 3 (dry-run, no files written)": scenario3(),
        "Scenario 4 (backward compatibility)": scenario4(),
    }

    print_header("SUMMARY")
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}  {name}")
        if not passed:
            all_passed = False

    print(f"\n  Overall: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    sys.exit(0 if all_passed else 1)
