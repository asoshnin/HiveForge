"""
Confidence calibration for the Steering Assistant v02.1.

This module provides the ConfidenceCalibrator class for calibrating confidence
scores against actual correctness based on user feedback and multi-project data.

Validates: Requirements 22.1-22.7
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .confidence_scorer import ConfidenceScorer
from .models import ConfidenceLevel


# Calibration data storage path
CALIBRATION_DIR = Path(".kiro/.telemetry/calibration")
CALIBRATION_FILE = CALIBRATION_DIR / "confidence_calibration.json"


@dataclass
class CorrectionRecord:
    """Records a user correction with original confidence data."""
    project_hash: str
    section_type: str
    original_confidence: float
    original_content: str
    corrected_content: str
    was_correct: bool
    timestamp: str
    file_path: str


@dataclass
class CalibrationAnalysis:
    """Results of calibration analysis."""
    calibration_status: str
    total_samples: int
    high_accuracy: float
    medium_accuracy: float
    low_accuracy: float
    overall_accuracy: float
    miscalibration_detected: bool
    adjustment_recommendations: List[str]
    calibration_data: Dict[str, Any]


@dataclass
class CalibrationAdjustment:
    """Adjustments to confidence calculation algorithms."""
    evidence_weights: Dict[str, float] = field(default_factory=dict)
    threshold_adjustments: Dict[str, float] = field(default_factory=dict)
    penalty_factors: Dict[str, float] = field(default_factory=dict)
    boost_factors: Dict[str, float] = field(default_factory=dict)


class ConfidenceCalibrator:
    """
    Calibrates confidence scores against actual correctness.
    
    This class implements a feedback loop to validate confidence scores,
    record user corrections, analyze score accuracy, and adjust algorithms
    based on calibration data across multiple projects.
    """
    
    # Default evidence weights (from ConfidenceScorer)
    DEFAULT_EVIDENCE_WEIGHTS = {
        "ARTIFACT": 0.95,
        "CODE_ANALYSIS": 0.90,
        "INFERENCE": 0.70,
        "USER": 0.85,
    }
    
    # Default confidence thresholds
    DEFAULT_THRESHOLDS = {
        "HIGH": 0.9,
        "MEDIUM": 0.7,
        "LOW": 0.0,
    }
    
    def __init__(
        self,
        calibration_path: Optional[Path] = None,
        min_samples_for_calibration: int = 10,
    ):
        """
        Initialize the ConfidenceCalibrator.
        
        Args:
            calibration_path: Path to calibration data file
            min_samples_for_calibration: Minimum samples needed for calibration
        """
        self.calibration_path = calibration_path or CALIBRATION_FILE
        self.min_samples = min_samples_for_calibration
        self._corrections: List[CorrectionRecord] = []
        self._adjustments = CalibrationAdjustment()
        self._load_calibration_data()
    
    def _load_calibration_data(self) -> None:
        """Load existing calibration data from file."""
        if self.calibration_path.exists():
            try:
                with open(self.calibration_path, 'r') as f:
                    data = json.load(f)
                    self._corrections = [
                        CorrectionRecord(**record) for record in data.get("corrections", [])
                    ]
                    adjustments = data.get("adjustments", {})
                    self._adjustments = CalibrationAdjustment(
                        evidence_weights=adjustments.get("evidence_weights", {}),
                        threshold_adjustments=adjustments.get("threshold_adjustments", {}),
                        penalty_factors=adjustments.get("penalty_factors", {}),
                        boost_factors=adjustments.get("boost_factors", {}),
                    )
            except (json.JSONDecodeError, KeyError, TypeError):
                self._corrections = []
                self._adjustments = CalibrationAdjustment()
        else:
            self._corrections = []
            self._adjustments = CalibrationAdjustment()
    
    def _save_calibration_data(self) -> None:
        """Save calibration data to file."""
        CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
        
        data = {
            "corrections": [
                {
                    "project_hash": c.project_hash,
                    "section_type": c.section_type,
                    "original_confidence": c.original_confidence,
                    "original_content": c.original_content,
                    "corrected_content": c.corrected_content,
                    "was_correct": c.was_correct,
                    "timestamp": c.timestamp,
                    "file_path": c.file_path,
                }
                for c in self._corrections
            ],
            "adjustments": {
                "evidence_weights": self._adjustments.evidence_weights,
                "threshold_adjustments": self._adjustments.threshold_adjustments,
                "penalty_factors": self._adjustments.penalty_factors,
                "boost_factors": self._adjustments.boost_factors,
            },
            "last_updated": self._get_timestamp(),
        }
        
        with open(self.calibration_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def _compute_project_hash(self, project_path: str) -> str:
        """Compute a hash for the project to identify it anonymously."""
        return hashlib.sha256(project_path.encode()).hexdigest()[:12]
    
    def record_corrections(
        self,
        project_path: str,
        file_path: str,
        section_type: str,
        original_confidence: float,
        original_content: str,
        corrected_content: str,
        was_correct: bool,
    ) -> None:
        """
        Record a user correction with original confidence.
        
        This method records when a user reviews and corrects generated content,
        along with the original confidence score. This data is used to analyze
        and improve confidence accuracy over time.
        
        Args:
            project_path: Path to the project
            file_path: Path to the steering file
            section_type: Type of section (e.g., "tech_stack", "architecture")
            original_confidence: The confidence score assigned to the original content
            original_content: The original generated content
            corrected_content: The user's corrected content
            was_correct: Whether the original content was correct
        """
        project_hash = self._compute_project_hash(project_path)
        
        record = CorrectionRecord(
            project_hash=project_hash,
            section_type=section_type,
            original_confidence=original_confidence,
            original_content=original_content,
            corrected_content=corrected_content,
            was_correct=was_correct,
            timestamp=self._get_timestamp(),
            file_path=file_path,
        )
        
        self._corrections.append(record)
        self._save_calibration_data()
    
    def record_batch_corrections(
        self,
        project_path: str,
        corrections: List[Dict[str, Any]],
    ) -> int:
        """
        Record multiple corrections at once.
        
        Args:
            project_path: Path to the project
            corrections: List of correction dictionaries with keys:
                - file_path: Path to the steering file
                - section_type: Type of section
                - original_confidence: Confidence score
                - original_content: Original content
                - corrected_content: Corrected content
                - was_correct: Whether original was correct
                
        Returns:
            Number of corrections recorded
        """
        count = 0
        for correction in corrections:
            try:
                self.record_corrections(
                    project_path=project_path,
                    file_path=correction["file_path"],
                    section_type=correction["section_type"],
                    original_confidence=correction["original_confidence"],
                    original_content=correction["original_content"],
                    corrected_content=correction["corrected_content"],
                    was_correct=correction["was_correct"],
                )
                count += 1
            except (KeyError, TypeError):
                continue
        
        return count
    
    def analyze_calibration(self) -> CalibrationAnalysis:
        """
        Analyze confidence score accuracy against actual correctness.
        
        Compares predicted confidence scores with actual correctness rates
        to identify systematic miscalibration.
        
        Returns:
            CalibrationAnalysis with accuracy metrics and recommendations
        """
        if len(self._corrections) < self.min_samples:
            return CalibrationAnalysis(
                calibration_status="insufficient_data",
                total_samples=len(self._corrections),
                high_accuracy=0.0,
                medium_accuracy=0.0,
                low_accuracy=0.0,
                overall_accuracy=0.0,
                miscalibration_detected=False,
                adjustment_recommendations=[
                    f"Need at least {self.min_samples} samples for reliable calibration. "
                    f"Currently have {len(self._corrections)}."
                ],
                calibration_data={},
            )
        
        # Calculate accuracy per confidence level
        high_correct = 0
        high_total = 0
        medium_correct = 0
        medium_total = 0
        low_correct = 0
        low_total = 0
        total_correct = 0
        
        for record in self._corrections:
            level = self._get_confidence_level(record.original_confidence)
            
            if level == ConfidenceLevel.HIGH:
                high_total += 1
                if record.was_correct:
                    high_correct += 1
            elif level == ConfidenceLevel.MEDIUM:
                medium_total += 1
                if record.was_correct:
                    medium_correct += 1
            else:
                low_total += 1
                if record.was_correct:
                    low_correct += 1
            
            if record.was_correct:
                total_correct += 1
        
        high_accuracy = high_correct / high_total if high_total > 0 else 0.0
        medium_accuracy = medium_correct / medium_total if medium_total > 0 else 0.0
        low_accuracy = low_correct / low_total if low_total > 0 else 0.0
        overall_accuracy = total_correct / len(self._corrections) if self._corrections else 0.0
        
        # Detect miscalibration
        # Expected: HIGH ~90%+, MEDIUM ~70%+, LOW ~50%+
        miscalibration_detected = False
        recommendations = []
        
        if high_total > 0 and high_accuracy < 0.8:
            miscalibration_detected = True
            recommendations.append(
                f"HIGH confidence accuracy is {high_accuracy:.1%} (expected ~90%). "
                "Consider reducing evidence weights for ARTIFACT and CODE_ANALYSIS."
            )
        
        if medium_total > 0 and medium_accuracy < 0.6:
            miscalibration_detected = True
            recommendations.append(
                f"MEDIUM confidence accuracy is {medium_accuracy:.1%} (expected ~70%). "
                "Consider adjusting inference evidence strength."
            )
        
        if low_total > 0 and low_accuracy > 0.6:
            miscalibration_detected = True
            recommendations.append(
                f"LOW confidence accuracy is {low_accuracy:.1%} (expected ~50%). "
                "Content marked as LOW may be too often correct - consider raising thresholds."
            )
        
        # Check for overconfidence (HIGH predictions that are often wrong)
        if high_total > 0 and high_accuracy < 0.7:
            miscalibration_detected = True
            recommendations.append(
                "System is overconfident - HIGH confidence predictions are often incorrect. "
                "Apply penalty factor to evidence weights."
            )
        
        return CalibrationAnalysis(
            calibration_status="calibrated" if not miscalibration_detected else "miscalibrated",
            total_samples=len(self._corrections),
            high_accuracy=high_accuracy,
            medium_accuracy=medium_accuracy,
            low_accuracy=low_accuracy,
            overall_accuracy=overall_accuracy,
            miscalibration_detected=miscalibration_detected,
            adjustment_recommendations=recommendations,
            calibration_data={
                "high_samples": high_total,
                "medium_samples": medium_total,
                "low_samples": low_total,
                "project_count": len(set(c.project_hash for c in self._corrections)),
            },
        )
    
    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Get confidence level from score."""
        if score >= 0.9:
            return ConfidenceLevel.HIGH
        elif score >= 0.7:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def adjust_algorithms(self) -> CalibrationAdjustment:
        """
        Adjust confidence calculation algorithms based on calibration data.
        
        Analyzes the collected correction data and adjusts evidence weights,
        thresholds, and other parameters to improve calibration accuracy.
        
        Returns:
            CalibrationAdjustment with recommended changes
        """
        analysis = self.analyze_calibration()
        
        if analysis.calibration_status == "insufficient_data":
            return self._adjustments
        
        # Calculate adjustment factors based on accuracy
        adjustments = CalibrationAdjustment()
        
        # Adjust evidence weights based on actual accuracy
        if analysis.high_accuracy < 0.8:
            # HIGH confidence is overconfident - reduce weights
            adjustments.evidence_weights["ARTIFACT"] = max(0.8, self.DEFAULT_EVIDENCE_WEIGHTS["ARTIFACT"] - 0.1)
            adjustments.evidence_weights["CODE_ANALYSIS"] = max(0.75, self.DEFAULT_EVIDENCE_WEIGHTS["CODE_ANALYSIS"] - 0.1)
        
        if analysis.medium_accuracy < 0.6:
            # MEDIUM confidence is underconfident - increase inference weight
            adjustments.evidence_weights["INFERENCE"] = min(0.85, self.DEFAULT_EVIDENCE_WEIGHTS["INFERENCE"] + 0.1)
        
        if analysis.low_accuracy > 0.6:
            # LOW confidence is too pessimistic - raise threshold
            adjustments.threshold_adjustments["MEDIUM"] = min(0.8, self.DEFAULT_THRESHOLDS["MEDIUM"] + 0.05)
        
        # Store adjustments
        self._adjustments = adjustments
        self._save_calibration_data()
        
        return adjustments
    
    def get_adjusted_confidence(
        self,
        base_confidence: float,
        evidence_source: str,
    ) -> float:
        """
        Get confidence score with calibration adjustments applied.
        
        Args:
            base_confidence: The original confidence score
            evidence_source: The source of evidence (ARTIFACT, CODE_ANALYSIS, etc.)
            
        Returns:
            Adjusted confidence score
        """
        adjusted = base_confidence
        
        # Apply evidence weight adjustments
        if evidence_source in self._adjustments.evidence_weights:
            weight = self._adjustments.evidence_weights[evidence_source]
            # Scale confidence based on weight adjustment
            default_weight = self.DEFAULT_EVIDENCE_WEIGHTS.get(evidence_source, 0.5)
            if default_weight > 0:
                adjusted = adjusted * (weight / default_weight)
        
        # Apply threshold adjustments
        if self._adjustments.threshold_adjustments:
            medium_threshold = self._adjustments.threshold_adjustments.get(
                "MEDIUM", self.DEFAULT_THRESHOLDS["MEDIUM"]
            )
            if adjusted >= medium_threshold and adjusted < 0.9:
                # Content near threshold - check if it should be adjusted
                adjusted = min(1.0, adjusted + 0.05)
        
        # Ensure confidence is in valid range
        return max(0.0, min(1.0, adjusted))
    
    def calibrate_across_projects(
        self,
        project_paths: List[str],
    ) -> Dict[str, Any]:
        """
        Use multi-project data to improve confidence scoring.
        
        Aggregates calibration data from multiple projects to identify
        patterns and improve overall calibration accuracy.
        
        Args:
            project_paths: List of project paths to include in calibration
            
        Returns:
            Summary of multi-project calibration analysis
        """
        # Filter corrections to only include specified projects
        project_hashes = [self._compute_project_hash(p) for p in project_paths]
        
        project_corrections = [
            c for c in self._corrections if c.project_hash in project_hashes
        ]
        
        if len(project_corrections) < self.min_samples:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {self.min_samples} samples from specified projects. "
                          f"Have {len(project_corrections)}.",
                "projects_analyzed": len(project_corrections),
            }
        
        # Analyze per-project accuracy
        project_stats = {}
        for project_hash in project_hashes:
            project_data = [c for c in project_corrections if c.project_hash == project_hash]
            if project_data:
                correct_count = sum(1 for c in project_data if c.was_correct)
                project_stats[project_hash] = {
                    "samples": len(project_data),
                    "accuracy": correct_count / len(project_data),
                }
        
        # Calculate overall multi-project accuracy
        total_correct = sum(1 for c in project_corrections if c.was_correct)
        overall_accuracy = total_correct / len(project_corrections) if project_corrections else 0.0
        
        # Identify section types with low accuracy
        section_accuracy = {}
        for record in project_corrections:
            if record.section_type not in section_accuracy:
                section_accuracy[record.section_type] = {"correct": 0, "total": 0}
            section_accuracy[record.section_type]["total"] += 1
            if record.was_correct:
                section_accuracy[record.section_type]["correct"] += 1
        
        low_accuracy_sections = [
            section for section, stats in section_accuracy.items()
            if stats["correct"] / stats["total"] < 0.6 if stats["total"] > 0
        ]
        
        return {
            "status": "analyzed",
            "projects_analyzed": len(project_hashes),
            "total_samples": len(project_corrections),
            "overall_accuracy": overall_accuracy,
            "project_stats": project_stats,
            "low_accuracy_sections": low_accuracy_sections,
            "recommendations": self._generate_multi_project_recommendations(
                project_stats, low_accuracy_sections
            ),
        }
    
    def _generate_multi_project_recommendations(
        self,
        project_stats: Dict[str, Dict[str, float]],
        low_accuracy_sections: List[str],
    ) -> List[str]:
        """Generate recommendations based on multi-project analysis."""
        recommendations = []
        
        # Check for consistent low accuracy across projects
        if project_stats:
            accuracies = [s["accuracy"] for s in project_stats.values()]
            if sum(accuracies) / len(accuracies) < 0.7:
                recommendations.append(
                    "Overall accuracy is below 70% across projects. "
                    "Consider reviewing the confidence scoring algorithm."
                )
        
        # Section-specific recommendations
        if low_accuracy_sections:
            recommendations.append(
                f"The following section types have low accuracy: {', '.join(low_accuracy_sections)}. "
                "Consider adding more evidence sources or adjusting thresholds for these sections."
            )
        
        return recommendations
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """
        Get the current calibration status for display to users.
        
        Returns:
            Dictionary with calibration status information
        """
        analysis = self.analyze_calibration()
        unique_projects = len(set(c.project_hash for c in self._corrections))
        
        return {
            "calibration_status": analysis.calibration_status,
            "total_samples": analysis.total_samples,
            "unique_projects": unique_projects,
            "high_accuracy": f"{analysis.high_accuracy:.1%}" if analysis.high_accuracy > 0 else "N/A",
            "medium_accuracy": f"{analysis.medium_accuracy:.1%}" if analysis.medium_accuracy > 0 else "N/A",
            "low_accuracy": f"{analysis.low_accuracy:.1%}" if analysis.low_accuracy > 0 else "N/A",
            "overall_accuracy": f"{analysis.overall_accuracy:.1%}" if analysis.overall_accuracy > 0 else "N/A",
            "is_calibrated": analysis.calibration_status == "calibrated",
            "message": self._get_status_message(analysis, unique_projects),
        }
    
    def _get_status_message(
        self,
        analysis: CalibrationAnalysis,
        unique_projects: int,
    ) -> str:
        """Generate a user-friendly status message."""
        if analysis.total_samples == 0:
            return "No calibration data yet. Corrections will be recorded as you use the system."
        
        if analysis.calibration_status == "insufficient_data":
            return (
                f"Collecting calibration data: {analysis.total_samples} samples from "
                f"{unique_projects} projects. Need {self.min_samples} samples for calibration."
            )
        
        if analysis.miscalibration_detected:
            return (
                f"Calibration issues detected. Overall accuracy: {analysis.overall_accuracy:.1%}. "
                "Run with --calibrate-confidence to analyze and adjust algorithms."
            )
        
        return (
            f"Confidence scores calibrated on {unique_projects} projects "
            f"({analysis.total_samples} total samples). Overall accuracy: {analysis.overall_accuracy:.1%}."
        )
    
    def run_calibration_analysis(self) -> str:
        """
        Run full calibration analysis and return a report.
        
        This method is called when the --calibrate-confidence flag is used.
        
        Returns:
            Formatted calibration report
        """
        analysis = self.analyze_calibration()
        adjustments = self.adjust_algorithms()
        status = self.get_calibration_status()
        
        report_lines = [
            "=" * 60,
            "CONFIDENCE CALIBRATION REPORT",
            "=" * 60,
            "",
            f"Status: {status['calibration_status'].upper()}",
            f"Total Samples: {analysis.total_samples}",
            f"Unique Projects: {status['unique_projects']}",
            "",
            "Accuracy by Confidence Level:",
            f"  HIGH (≥0.9):   {status['high_accuracy']}",
            f"  MEDIUM (0.7-0.9): {status['medium_accuracy']}",
            f"  LOW (<0.7):    {status['low_accuracy']}",
            "",
            f"Overall Accuracy: {status['overall_accuracy']}",
            "",
        ]
        
        if analysis.miscalibration_detected:
            report_lines.append("Recommendations:")
            for i, rec in enumerate(analysis.adjustment_recommendations, 1):
                report_lines.append(f"  {i}. {rec}")
            report_lines.append("")
        
        if adjustments.evidence_weights:
            report_lines.append("Applied Adjustments:")
            for source, weight in adjustments.evidence_weights.items():
                report_lines.append(f"  {source} weight: {weight:.2f}")
            if adjustments.threshold_adjustments:
                for threshold, value in adjustments.threshold_adjustments.items():
                    report_lines.append(f"  {threshold} threshold: {value:.2f}")
            report_lines.append("")
        
        report_lines.append(status["message"])
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def get_corrections_count(self) -> int:
        """Get the number of recorded corrections."""
        return len(self._corrections)
    
    def clear_calibration_data(self) -> None:
        """Clear all calibration data."""
        self._corrections = []
        self._adjustments = CalibrationAdjustment()
        if self.calibration_path.exists():
            self.calibration_path.unlink()