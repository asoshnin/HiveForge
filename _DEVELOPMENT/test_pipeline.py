#!/usr/bin/env python3
"""
Quick test script to verify the HiveForge pipeline works correctly.
This bypasses CLI and directly tests the workflow.
"""

import sys
from pathlib import Path

# Add hiveforge-power to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hiveforge-power"))

from hiveforge.steering.workflows.init_workflow import InitWorkflow
from hiveforge.steering.models import SteeringConfig

def test_pipeline():
    """Test the init workflow pipeline."""
    print("="*70)
    print("TESTING HIVEFORGE PIPELINE")
    print("="*70)
    
    # Setup
    project_root = Path(__file__).parent.parent
    
    config = SteeringConfig(
        research_enabled=False,
        skip_validation=True,  # Skip validation for speed
        interactive=False,  # Non-interactive mode
        strict_mode=False,
        backup_enabled=True,
        backup_dir=project_root / ".kiro" / "backups",
        analyze_code=False,  # Disable code analysis (too slow)
    )
    
    print(f"\n📁 Project root: {project_root}")
    print(f"📊 Config: analyze_code={config.analyze_code}, interactive={config.interactive}")
    
    # Create workflow
    workflow = InitWorkflow(config, project_root=project_root)
    
    print(f"\n🎯 Staging dir: {workflow.state.staging_dir}")
    print(f"🎯 Steering dir: {workflow.state.steering_dir}")
    
    # Execute
    print("\n🚀 Executing workflow...")
    try:
        result = workflow.execute()
        
        if result:
            print("\n✅ Workflow completed successfully!")
            
            # Check generated files
            steering_dir = workflow.state.steering_dir
            if steering_dir.exists():
                files = list(steering_dir.glob("*.md"))
                print(f"\n📄 Generated {len(files)} files:")
                for f in files:
                    print(f"   • {f.name}")
                    
                # Check tech-stack.md for placeholders
                tech_stack = steering_dir / "tech-stack.md"
                if tech_stack.exists():
                    content = tech_stack.read_text()
                    
                    # Check for unreplaced placeholders
                    bad_patterns = [
                        "{Python|Node.js|",
                        "{FastAPI|Express|",
                        "{PostgreSQL|MongoDB|",
                    ]
                    
                    found_bad = []
                    for pattern in bad_patterns:
                        if pattern in content:
                            found_bad.append(pattern)
                    
                    if found_bad:
                        print(f"\n❌ FOUND UNREPLACED PLACEHOLDERS in tech-stack.md:")
                        for p in found_bad:
                            print(f"   • {p}")
                        return False
                    else:
                        print(f"\n✅ No unreplaced placeholders found in tech-stack.md")
                        
                        # Show a sample
                        lines = content.split('\n')
                        print("\n📝 Sample from tech-stack.md (first 30 lines):")
                        for line in lines[:30]:
                            print(f"   {line}")
                        
                        return True
            else:
                print(f"\n❌ Steering directory not found: {steering_dir}")
                return False
        else:
            print("\n❌ Workflow failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
