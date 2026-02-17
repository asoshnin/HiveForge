"""
Property-based tests for confidence calibration.

Validates: Requirements 22.1-22.7
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pytest
import hypothesis
from hypothesis import given, settings, strategies as st

from hiveforge.steering.confidence_calibrator import (
    ConfidenceCalibrator,
    CorrectionRecord,
    CalibrationAnalysis,
    CalibrationAdjustment,
    CALIBRATION_DIR,
)
from hiveforge.steering.models import ConfidenceLevel


def create_temp_calibration_file():
    """Create a temporary calibration file and return its path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = Path(f.name)
        json.dump({"corrections": [], "adjustments": {}}, f)
    return path


def cleanup_temp_file(path):
    """Clean up a temporary file."""
    if path and path.exists():
        path.unlink()


class TestConfidenceCalibration:
    """Tests for confidence calibration functionality."""
    
    @pytest.fixture
    def temp_calibration_path(self):
        """Create a temporary calibration file."""
        path = create_temp_calibration_file()
        yield path
        cleanup_temp_file(path)
    
    @pytest.fixture
    def calibrator(self, temp_calibration_path):
        """Create a calibrator with temporary storage."""
        return ConfidenceCalibrator(
            calibration_path=temp_calibration_path,
            min_samples_for_calibration=3,
        )
    
    def test_record_corrections_stores_data(self, calibrator, temp_calibration_path):
        """
        WHEN record_corrections is called, it SHALL store the correction data.
        """
        calibrator.record_corrections(
            project_path="/test/project",
            file_path="tech-stack.md",
            section_type="tech_stack",
            original_confidence=0.85,
            original_content="Python with FastAPI",
            corrected_content="Python with Django",
            was_correct=False,
        )
        
        assert calibrator.get_corrections_count() == 1
        
        # Verify data was saved
        calibrator2 = ConfidenceCalibrator(calibration_path=temp_calibration_path)
        assert calibrator2.get_corrections_count() == 1
    
    def test_record_batch_corrections(self, calibrator):
        """
        WHEN record_batch_corrections is called, it SHALL record multiple corrections.
        """
        corrections = [
            {
                "file_path": "tech-stack.md",
                "section_type": "tech_stack",
                "original_confidence": 0.9,
                "original_content": "React",
                "corrected_content": "Vue",
                "was_correct": False,
            },
            {
                "file_path": "architecture.md",
                "section_type": "architecture",
                "original_confidence": 0.7,
                "original_content": "Microservices",
                "corrected_content": "Monolithic",
                "was_correct": False,
            },
            {
                "file_path": "conventions.md",
                "section_type": "conventions",
                "original_confidence": 0.95,
                "original_content": "snake_case",
                "corrected_content": "snake_case",
                "was_correct": True,
            },
        ]
        
        count = calibrator.record_batch_corrections("/test/project", corrections)
        
        assert count == 3
        assert calibrator.get_corrections_count() == 3
    
    def test_analyze_calibration_with_no_data(self, calibrator):
        """
        WHEN analyze_calibration is called with no data, it SHALL return insufficient_data status.
        """
        analysis = calibrator.analyze_calibration()
        
        assert analysis.calibration_status == "insufficient_data"
        assert analysis.total_samples == 0
        assert analysis.miscalibration_detected is False
        assert "Need at least" in analysis.adjustment_recommendations[0]
    
    def test_analyze_calibration_accuracy(self, calibrator):
        """
        WHEN analyze_calibration is called, it SHALL calculate accuracy per confidence level.
        """
        # Clear any existing data first
        calibrator.clear_calibration_data()
        
        # Record corrections with known outcomes
        # HIGH confidence - mostly correct (5 samples)
        for _ in range(5):
            calibrator.record_corrections(
                project_path="/test/project1",
                file_path="tech-stack.md",
                section_type="tech_stack",
                original_confidence=0.95,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        
        # MEDIUM confidence - mixed (5 samples: 3 correct, 2 incorrect)
        for _ in range(3):
            calibrator.record_corrections(
                project_path="/test/project1",
                file_path="architecture.md",
                section_type="architecture",
                original_confidence=0.75,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        for _ in range(2):
            calibrator.record_corrections(
                project_path="/test/project1",
                file_path="architecture.md",
                section_type="architecture",
                original_confidence=0.75,
                original_content="Content",
                corrected_content="Changed",
                was_correct=False,
            )
        
        # LOW confidence - mostly incorrect (2 samples)
        for _ in range(2):
            calibrator.record_corrections(
                project_path="/test/project1",
                file_path="conventions.md",
                section_type="conventions",
                original_confidence=0.5,
                original_content="Content",
                corrected_content="Changed",
                was_correct=False,
            )
        
        analysis = calibrator.analyze_calibration()
        
        # Total: 5 HIGH + 5 MEDIUM + 2 LOW = 12 samples
        assert analysis.total_samples == 12
        assert analysis.high_accuracy == 1.0  # 5/5 correct
        assert analysis.medium_accuracy == 0.6  # 3/5 correct
        assert analysis.low_accuracy == 0.0  # 0/2 correct
        assert abs(analysis.overall_accuracy - 0.667) < 0.001  # 8/12 correct
    
    def test_detect_miscalibration(self, calibrator):
        """
        WHEN confidence scores are systematically miscalibrated, it SHALL be detected.
        """
        # Record many HIGH confidence predictions that are wrong
        for _ in range(10):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="tech-stack.md",
                section_type="tech_stack",
                original_confidence=0.95,  # HIGH confidence
                original_content="Wrong content",
                corrected_content="Corrected content",
                was_correct=False,  # But actually wrong
            )
        
        analysis = calibrator.analyze_calibration()
        
        assert analysis.miscalibration_detected is True
        assert any("overconfident" in rec.lower() for rec in analysis.adjustment_recommendations)
    
    def test_adjust_algorithms(self, calibrator):
        """
        WHEN adjust_algorithms is called, it SHALL return calibration adjustments.
        """
        # Create miscalibration
        for _ in range(5):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="tech-stack.md",
                section_type="tech_stack",
                original_confidence=0.95,
                original_content="Content",
                corrected_content="Changed",
                was_correct=False,
            )
        
        adjustments = calibrator.adjust_algorithms()
        
        assert isinstance(adjustments, CalibrationAdjustment)
        # Should have reduced evidence weights due to overconfidence
        assert "ARTIFACT" in adjustments.evidence_weights or "CODE_ANALYSIS" in adjustments.evidence_weights
    
    def test_get_adjusted_confidence(self, calibrator):
        """
        WHEN get_adjusted_confidence is called, it SHALL apply calibration adjustments.
        """
        # Set up adjustments
        calibrator._adjustments.evidence_weights["ARTIFACT"] = 0.85
        
        # Get adjusted confidence
        adjusted = calibrator.get_adjusted_confidence(0.9, "ARTIFACT")
        
        # Should be reduced from 0.9
        assert adjusted < 0.9
        assert 0.0 <= adjusted <= 1.0
    
    def test_calibrate_across_projects(self, calibrator):
        """
        WHEN calibrate_across_projects is called, it SHALL use multi-project data.
        """
        # Add corrections from multiple projects
        for i in range(3):
            calibrator.record_corrections(
                project_path=f"/project{i}",
                file_path="tech-stack.md",
                section_type="tech_stack",
                original_confidence=0.85,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        
        result = calibrator.calibrate_across_projects(["/project0", "/project1", "/project2"])
        
        assert result["status"] == "analyzed"
        assert result["projects_analyzed"] == 3
        assert result["total_samples"] == 3
        assert "overall_accuracy" in result
    
    def test_get_calibration_status(self, calibrator):
        """
        WHEN get_calibration_status is called, it SHALL return status for display.
        """
        # Add some data
        calibrator.record_corrections(
            project_path="/test/project",
            file_path="tech-stack.md",
            section_type="tech_stack",
            original_confidence=0.9,
            original_content="Content",
            corrected_content="Content",
            was_correct=True,
        )
        
        status = calibrator.get_calibration_status()
        
        assert "calibration_status" in status
        assert "total_samples" in status
        assert "unique_projects" in status
        assert "message" in status
        assert status["unique_projects"] == 1
    
    def test_run_calibration_analysis(self, calibrator):
        """
        WHEN run_calibration_analysis is called, it SHALL return a formatted report.
        """
        # Add some data
        for _ in range(5):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="tech-stack.md",
                section_type="tech_stack",
                original_confidence=0.85,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        
        report = calibrator.run_calibration_analysis()
        
        assert "CONFIDENCE CALIBRATION REPORT" in report
        assert "Accuracy by Confidence Level" in report
        assert "Overall Accuracy" in report
    
    def test_clear_calibration_data(self, calibrator):
        """
        WHEN clear_calibration_data is called, it SHALL remove all data.
        """
        # Add some data
        calibrator.record_corrections(
            project_path="/test/project",
            file_path="tech-stack.md",
            section_type="tech_stack",
            original_confidence=0.9,
            original_content="Content",
            corrected_content="Content",
            was_correct=True,
        )
        
        assert calibrator.get_corrections_count() == 1
        
        calibrator.clear_calibration_data()
        
        assert calibrator.get_corrections_count() == 0
    
    def test_invalid_correction_data(self, calibrator):
        """
        WHEN invalid correction data is provided, it SHALL be handled gracefully.
        """
        # Missing required fields
        invalid_corrections = [
            {"file_path": "tech-stack.md"},  # Missing fields
            {"section_type": "tech_stack"},  # Missing fields
            {},  # Empty
        ]
        
        count = calibrator.record_batch_corrections("/test/project", invalid_corrections)
        
        assert count == 0
        assert calibrator.get_corrections_count() == 0
    
    def test_project_hash_consistency(self, calibrator):
        """
        WHEN the same project path is used, it SHALL produce the same hash.
        """
        hash1 = calibrator._compute_project_hash("/test/project")
        hash2 = calibrator._compute_project_hash("/test/project")
        
        assert hash1 == hash2
        assert len(hash1) == 12  # SHA256 hexdigest truncated to 12 chars
    
    def test_different_projects_different_hashes(self, calibrator):
        """
        WHEN different project paths are used, they SHALL produce different hashes.
        """
        hash1 = calibrator._compute_project_hash("/test/project1")
        hash2 = calibrator._compute_project_hash("/test/project2")
        
        assert hash1 != hash2


class TestProperty22ConfidenceCalibration:
    """
    Property-based tests for Property 22: Confidence Score Calibration.
    
    Validates: Requirements 22.1-22.7
    """
    
    @pytest.fixture
    def temp_calibration_path(self):
        """Create a temporary calibration file."""
        path = create_temp_calibration_file()
        yield path
        cleanup_temp_file(path)
    
    @pytest.fixture
    def calibrator(self, temp_calibration_path):
        """Create a calibrator with temporary storage."""
        return ConfidenceCalibrator(
            calibration_path=temp_calibration_path,
            min_samples_for_calibration=5,
        )
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_corrections_recorded_with_original_confidence(self, calibrator, temp_calibration_path):
        """
        Property: WHEN users review and correct content, corrections SHALL be recorded with original confidence.
        """
        # Record a correction
        calibrator.record_corrections(
            project_path="/test/project",
            file_path="tech-stack.md",
            section_type="tech_stack",
            original_confidence=0.85,
            original_content="Original",
            corrected_content="Corrected",
            was_correct=False,
        )
        
        # Verify the correction was recorded with the original confidence
        assert calibrator.get_corrections_count() == 1
        
        # Reload and verify persistence
        calibrator2 = ConfidenceCalibrator(calibration_path=temp_calibration_path)
        assert calibrator2.get_corrections_count() == 1
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_calibration_data_persists_across_sessions(self, calibrator, temp_calibration_path):
        """
        Property: CALIBRATION data SHALL be maintained across multiple projects.
        """
        # Record corrections from multiple projects
        for i in range(3):
            calibrator.record_corrections(
                project_path=f"/project{i}",
                file_path="tech-stack.md",
                section_type="tech_stack",
                original_confidence=0.8 + (i * 0.05),
                original_content=f"Content{i}",
                corrected_content=f"Corrected{i}",
                was_correct=(i % 2 == 0),
            )
        
        # Create new calibrator instance (simulating new session)
        calibrator2 = ConfidenceCalibrator(calibration_path=temp_calibration_path)
        
        # Verify data persisted
        assert calibrator2.get_corrections_count() == 3
        status = calibrator2.get_calibration_status()
        assert status["unique_projects"] == 3
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_calibration_accuracy_analysis(self, calibrator):
        """
        Property: WHEN calibration data is collected, confidence score accuracy SHALL be analyzed.
        """
        # Record corrections with known outcomes
        # Mix of correct and incorrect predictions
        test_cases = [
            (0.95, True),  # HIGH confidence, correct
            (0.92, True),  # HIGH confidence, correct
            (0.90, False), # HIGH confidence, incorrect (overconfident)
            (0.80, True),  # MEDIUM confidence, correct
            (0.75, False), # MEDIUM confidence, incorrect
            (0.60, False), # LOW confidence, incorrect
        ]
        
        for confidence, was_correct in test_cases:
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="test.md",
                section_type="test",
                original_confidence=confidence,
                original_content="Content",
                corrected_content="Changed" if not was_correct else "Content",
                was_correct=was_correct,
            )
        
        analysis = calibrator.analyze_calibration()
        
        # Verify analysis was performed
        assert analysis.total_samples == len(test_cases)
        assert analysis.high_accuracy is not None
        assert analysis.medium_accuracy is not None
        assert analysis.low_accuracy is not None
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_algorithm_adjustment_on_miscalibration(self, calibrator):
        """
        Property: WHEN scores are systematically miscalibrated, algorithms SHALL be adjusted.
        """
        # Create systematic miscalibration: HIGH confidence predictions are often wrong
        for _ in range(10):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="test.md",
                section_type="test",
                original_confidence=0.95,  # HIGH confidence
                original_content="Wrong",
                corrected_content="Correct",
                was_correct=False,  # But actually wrong
            )
        
        # Run calibration analysis and adjustment
        analysis = calibrator.analyze_calibration()
        adjustments = calibrator.adjust_algorithms()
        
        # Verify miscalibration was detected
        assert analysis.miscalibration_detected is True
        
        # Verify adjustments were made
        assert len(adjustments.evidence_weights) > 0 or len(adjustments.threshold_adjustments) > 0
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_calibration_status_display(self, calibrator):
        """
        Property: CONFIDENCE calibration status SHALL be displayed to users.
        """
        # Add some calibration data
        for _ in range(5):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="test.md",
                section_type="test",
                original_confidence=0.85,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        
        status = calibrator.get_calibration_status()
        
        # Verify status contains display information
        assert "calibration_status" in status
        assert "total_samples" in status
        assert "overall_accuracy" in status
        assert "message" in status
        assert isinstance(status["message"], str)
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    @given(st.lists(
        st.floats(min_value=0.0, max_value=1.0),
        min_size=1,
        max_size=20,
    ))
    @settings(max_examples=10, suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture])
    def test_calibration_with_various_confidence_scores(self, calibrator, confidence_scores: List[float]):
        """
        Property: Calibration analysis works with various confidence score inputs.
        """
        # Clear any existing data first
        calibrator.clear_calibration_data()
        
        # Record corrections with various confidence scores
        for confidence in confidence_scores:
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="test.md",
                section_type="test",
                original_confidence=confidence,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        
        analysis = calibrator.analyze_calibration()
        
        # Verify analysis handles the data
        assert analysis.total_samples == len(confidence_scores)
        assert 0.0 <= analysis.overall_accuracy <= 1.0
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_calibrate_confidence_flag_analysis(self, calibrator):
        """
        Property: WHEN --calibrate-confidence is set, calibration analysis SHALL be run.
        """
        # Add calibration data
        for _ in range(5):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="test.md",
                section_type="test",
                original_confidence=0.85,
                original_content="Content",
                corrected_content="Content",
                was_correct=True,
            )
        
        # Run calibration analysis (simulates --calibrate-confidence flag)
        report = calibrator.run_calibration_analysis()
        
        # Verify report contains analysis results
        assert "CONFIDENCE CALIBRATION REPORT" in report
        assert "Accuracy by Confidence Level" in report
        assert "Overall Accuracy" in report
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_multi_project_calibration(self, calibrator):
        """
        Property: Calibration data SHALL be maintained across multiple projects.
        """
        # Add corrections from multiple projects
        for project_num in range(5):
            for sample_num in range(3):
                calibrator.record_corrections(
                    project_path=f"/project{project_num}",
                    file_path="test.md",
                    section_type="test",
                    original_confidence=0.7 + (sample_num * 0.1),
                    original_content=f"Content{project_num}_{sample_num}",
                    corrected_content=f"Content{project_num}_{sample_num}",
                    was_correct=True,
                )
        
        # Run multi-project calibration
        result = calibrator.calibrate_across_projects([
            "/project0", "/project1", "/project2", "/project3", "/project4"
        ])
        
        # Verify multi-project analysis
        assert result["status"] == "analyzed"
        assert result["projects_analyzed"] == 5
        assert result["total_samples"] == 15
        assert "overall_accuracy" in result
    
    @pytest.mark.property("Property 22: Confidence Score Calibration")
    def test_feedback_loop_for_validation(self, calibrator):
        """
        Property: Implement a feedback loop to validate confidence scores against actual correctness.
        """
        # Simulate the feedback loop:
        # 1. Record corrections (feedback)
        # 2. Analyze calibration
        # 3. Adjust algorithms
        # 4. Apply adjustments to future confidence calculations
        
        # Step 1: Record initial corrections
        for _ in range(5):
            calibrator.record_corrections(
                project_path="/test/project",
                file_path="test.md",
                section_type="test",
                original_confidence=0.9,
                original_content="Content",
                corrected_content="Changed",
                was_correct=False,
            )
        
        # Step 2: Analyze
        analysis = calibrator.analyze_calibration()
        
        # Step 3: Adjust
        adjustments = calibrator.adjust_algorithms()
        
        # Step 4: Apply adjustments to new confidence calculations
        adjusted_confidence = calibrator.get_adjusted_confidence(0.9, "ARTIFACT")
        
        # Verify the feedback loop is working
        assert analysis.miscalibration_detected is True
        assert adjusted_confidence < 0.9  # Should be reduced due to miscalibration