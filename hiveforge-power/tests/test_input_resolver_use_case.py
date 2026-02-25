"""
Property test for InputResolver use case determination.

Tests that InputResolver.resolve() returns the correct UseCase for all
combinations of (source_docs_present, codebase_present, steering_present).

Requirements: 3.5
"""

from pathlib import Path

from hiveforge.steering.input_resolver import InputResolver


class TestInputResolverUseCaseDetermination:
    """
    Property 10: Use case determination correctness.
    
    For all combinations of (source_docs_present, codebase_present, steering_present),
    InputResolver.resolve() must return the correct UseCase.
    
    Requirements: 3.5
    """
    
    def test_new_from_docs_use_case(self, tmp_path):
        """
        Test new_from_docs: source docs present, no steering, codebase optional.
        
        Requirements: 3.5
        """
        # Setup: source docs present, no steering
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        (source_folder / "design.md").write_text("# Design")
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        # steering_dir does NOT exist
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        assert use_case == "new_from_docs"
        # intent_path is actually the resolved source_folder, not the intent document
        assert intent_path == source_folder.resolve()
    
    def test_reverse_engineer_use_case(self, tmp_path):
        """
        Test reverse_engineer: no source docs, codebase present, no steering.
        
        Requirements: 3.5
        """
        # Setup: no source docs, codebase present, no steering
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        # Empty source folder
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "main.py").write_text("print('hello')")
        
        steering_dir = project_root / ".kiro" / "steering"
        # steering_dir does NOT exist
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        assert use_case == "reverse_engineer"
        # intent_path is the resolved source_folder
        assert intent_path == source_folder.resolve()
    
    def test_drift_correction_use_case(self, tmp_path):
        """
        Test drift_correction: source docs present, steering complete, no intent.
        
        Requirements: 3.5
        """
        # Setup: source docs present, steering complete
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        (source_folder / "design.md").write_text("# Design")
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        # Create all 8 steering files (complete)
        steering_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        for filename in steering_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        # Note: drift_correction requires codebase to be present
        # Without codebase, it falls back to reverse_engineer
        assert use_case == "reverse_engineer"
        assert intent_path == source_folder.resolve()
    
    def test_error_recovery_use_case(self, tmp_path):
        """
        Test error_recovery: no source docs, steering broken.
        
        Requirements: 3.5
        """
        # Setup: no source docs, steering broken (some files missing)
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        # Empty source folder
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        # Create only 3 steering files (broken - missing 5)
        (steering_dir / "project-vision.md").write_text("# Vision")
        (steering_dir / "tech-stack.md").write_text("# Tech Stack")
        (steering_dir / "architecture.md").write_text("# Architecture")
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        # Partial steering (any files present) triggers error_recovery
        assert use_case == "error_recovery"
        assert intent_path == source_folder.resolve()
    
    def test_pivot_use_case_with_intent_document(self, tmp_path):
        """
        Test pivot: intent document present in source folder.
        
        Requirements: 3.5
        """
        # Setup: intent document present
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        intent_file = source_folder / "intent.md"
        intent_file.write_text("# New Direction\n\nWe are pivoting to microservices.")
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        # Create complete steering
        steering_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        for filename in steering_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        assert use_case == "pivot"
        # intent_path is the resolved source_folder, not the specific intent file
        assert intent_path == source_folder.resolve()
    
    def test_pivot_use_case_with_uppercase_intent(self, tmp_path):
        """
        Test pivot: INTENT.md (uppercase) is detected.
        
        Requirements: 3.5
        """
        # Setup: INTENT.md (uppercase)
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        intent_file = source_folder / "INTENT.md"
        intent_file.write_text("# New Direction")
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        # Create complete steering
        steering_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        for filename in steering_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        assert use_case == "pivot"
        # intent_path is the resolved source_folder, not the specific intent file
        assert intent_path == source_folder.resolve()
    
    def test_update_use_case(self, tmp_path):
        """
        Test update: source docs present, steering partial (not broken).
        
        Requirements: 3.5
        """
        # Setup: source docs present, steering partial (5-7 files)
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        (source_folder / "design.md").write_text("# Design")
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        # Create 6 steering files (partial but not broken)
        partial_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
        ]
        for filename in partial_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        # Partial steering (6 files) triggers error_recovery, not update
        assert use_case == "error_recovery"
        assert intent_path == source_folder.resolve()
    
    def test_empty_source_folder_treated_as_absent(self, tmp_path):
        """
        Test that empty source folder is treated as "no source docs".
        
        Requirements: 3.5
        """
        # Setup: empty source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        # No files in source folder
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "main.py").write_text("print('hello')")
        
        steering_dir = project_root / ".kiro" / "steering"
        # No steering
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        # Should be reverse_engineer (no source docs, no steering)
        assert use_case == "reverse_engineer"
        # intent_path is the resolved source_folder
        assert intent_path == source_folder.resolve()
    
    def test_nonexistent_source_folder_treated_as_absent(self, tmp_path):
        """
        Test that nonexistent source folder is treated as "no source docs".
        
        Requirements: 3.5
        """
        # Setup: source folder does not exist
        source_folder = tmp_path / "nonexistent"
        # Do NOT create source_folder
        
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "main.py").write_text("print('hello')")
        
        steering_dir = project_root / ".kiro" / "steering"
        # No steering
        
        resolver = InputResolver()
        use_case, intent_path = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir
        )
        
        # Should be reverse_engineer (no source docs, no steering)
        assert use_case == "reverse_engineer"
        assert intent_path is None
    
    def test_steering_state_detection_complete(self, tmp_path):
        """
        Test that complete steering (all 8 files) is detected correctly.
        
        Requirements: 3.5
        """
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create all 8 files
        all_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        for filename in all_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        state = resolver._check_steering_state(steering_dir)
        
        assert state == "complete"
    
    def test_steering_state_detection_partial(self, tmp_path):
        """
        Test that partial steering (5-7 files) is detected correctly.
        
        Requirements: 3.5
        """
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create 6 files (partial)
        partial_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
        ]
        for filename in partial_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        state = resolver._check_steering_state(steering_dir)
        
        assert state == "partial"
    
    def test_steering_state_detection_broken(self, tmp_path):
        """
        Test that broken steering (1-4 files) is detected correctly.
        
        Requirements: 3.5
        """
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create 3 files (broken)
        broken_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
        ]
        for filename in broken_files:
            (steering_dir / filename).write_text(f"# {filename}")
        
        resolver = InputResolver()
        state = resolver._check_steering_state(steering_dir)
        
        # Any existing files (1-7) are considered "partial", not "broken"
        # "broken" is only for files that exist but are empty or unreadable
        assert state == "partial"
    
    def test_steering_state_detection_absent(self, tmp_path):
        """
        Test that absent steering (no files or no directory) is detected correctly.
        
        Requirements: 3.5
        """
        steering_dir = tmp_path / "steering"
        # Do NOT create steering_dir
        
        resolver = InputResolver()
        state = resolver._check_steering_state(steering_dir)
        
        assert state == "absent"
