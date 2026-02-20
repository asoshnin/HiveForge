"""
Property-based tests for TelemetryLogger.

Validates: Requirements 14.1-14.9
"""

import json
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st
from hiveforge.steering.telemetry_logger import TelemetryLogger


def test_session_creation():
    """Property: Session is created with unique ID"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        session_id = logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
            files_count=5,
        )
        
        assert session_id is not None
        assert len(session_id) == 8  # First 8 chars of UUID


def test_session_data_structure():
    """Property: Session data has correct structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
            files_count=3,
        )
        
        summary = logger.get_session_summary()
        
        assert summary["session_id"] is not None
        assert summary["workflow_type"] == "AUTONOMOUS"
        assert summary["files_processed"] == 0


@given(st.text(min_size=1), st.integers(min_value=0, max_value=1000))
def test_confidence_scores_logging(file_name, score_value):
    """Property: Confidence scores are logged correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        scores = [
            {"section": "header", "value": score_value / 1000, "level": "HIGH"},
            {"section": "body", "value": score_value / 1000, "level": "MEDIUM"},
        ]
        
        logger.log_confidence_scores(file_name, scores)
        
        # Check data was recorded
        assert len(logger._session_data["confidence_scores"]) == 1
        assert logger._session_data["confidence_scores"][0]["file"] == file_name


def test_validation_results_logging():
    """Property: Validation results are logged correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        results = {
            "structural": {"passed": True, "issues": []},
            "semantic": {"passed": False, "issues": ["version mismatch"]},
        }
        
        logger.log_validation_results("project-vision.md", results)
        
        assert len(logger._session_data["validation_results"]) == 1
        assert logger._session_data["validation_results"][0]["file"] == "project-vision.md"


@given(st.integers(min_value=0, max_value=10000), st.integers(min_value=0, max_value=10000))
def test_token_usage_logging(prompt_tokens, completion_tokens):
    """Property: Token usage is logged correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        logger.log_token_usage("test.md", prompt_tokens, completion_tokens)
        
        usage = logger._session_data["token_usage"]
        assert usage["total"] == prompt_tokens + completion_tokens


def test_error_logging():
    """Property: Errors are logged with context"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        logger.log_error(
            error_type="LLM_ERROR",
            message="Connection timeout",
            file_name="test.md",
            context={"retry_count": 1},
        )
        
        assert len(logger._session_data["errors"]) == 1
        assert logger._session_data["errors"][0]["error_type"] == "LLM_ERROR"


def test_user_interaction_logging():
    """Property: User interactions are logged"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        logger.log_user_interaction(
            interaction_type="conflict_resolution",
            details={"conflict_id": "c1", "resolution": "keep_new"},
        )
        
        assert len(logger._session_data["user_interactions"]) == 1


@given(st.text(min_size=1), st.floats(min_value=0, max_value=1000))
def test_duration_logging(operation, duration_ms):
    """Property: Durations are logged correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        logger.log_duration(operation, duration_ms, "test.md")
        
        durations = logger._session_data["durations_ms"]
        assert len(durations) == 1
        assert durations[0]["operation"] == operation


def test_file_processed_tracking():
    """Property: Files processed are tracked correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
            files_count=5,
        )
        
        # Record some files
        logger.record_file_processed("file1.md", success=True)
        logger.record_file_processed("file2.md", success=True)
        logger.record_file_processed("file3.md", success=False)
        
        summary = logger.get_session_summary()
        
        assert summary["files_processed"] == 3
        assert summary["files_failed"] == 1


def test_session_file_creation():
    """Property: Session file is created on save"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        session_id = logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        session_path = logger.save_session()
        
        assert session_path.exists()
        
        # Verify file content
        with open(session_path) as f:
            data = json.load(f)
        
        assert data["session_id"] == session_id
        assert data["workflow_type"] == "AUTONOMOUS"


def test_summary_file_creation():
    """Property: Summary file is created and updated"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        logger.record_file_processed("test.md", success=True)
        summary_path = logger.update_summary()
        
        assert summary_path.exists()
        
        with open(summary_path) as f:
            summary = json.load(f)
        
        assert summary["total_sessions"] == 1
        assert summary["total_files_processed"] == 1


def test_telemetry_disabled():
    """Property: Disabled logger doesn't create files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry", enabled=False)
        
        session_id = logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        
        assert session_id == ""
        
        # No files should be created
        assert not (Path(tmpdir) / ".telemetry").exists()


def test_multiple_sessions():
    """Property: Multiple sessions are tracked separately"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(Path(tmpdir) / ".telemetry")
        
        # First session
        logger.log_session(
            workflow_type="AUTONOMOUS",
            project_root=Path(tmpdir),
        )
        logger.record_file_processed("test1.md", success=True)
        logger.save_session()
        
        # Second session
        logger.log_session(
            workflow_type="FALLBACK",
            project_root=Path(tmpdir),
        )
        logger.record_file_processed("test2.md", success=True)
        logger.save_session()
        
        # Check summary
        summary_path = Path(tmpdir) / ".telemetry" / "summary.json"
        with open(summary_path) as f:
            summary = json.load(f)
        
        assert summary["total_sessions"] == 2
        assert summary["autonomous_sessions"] == 1
        assert summary["fallback_sessions"] == 1
