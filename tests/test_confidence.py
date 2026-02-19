"""
Tests for Confidence Calculator.

This module tests the confidence scoring system for steering file generation,
including file-level and overall confidence calculations.
"""

import pytest
from src.hiveforge.steering.confidence import ConfidenceCalculator, ConfidenceScore


class TestConfidenceScore:
    """Tests for ConfidenceScore dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        score = ConfidenceScore(
            overall=0.75,
            level="medium",
            sources={"documents": 0.5, "code_analysis": 0.2, "inferred": 0.05},
            inferred_sections=["Problem Statement", "Target Users"]
        )
        
        result = score.to_dict()
        
        assert result["overall"] == 0.75
        assert result["level"] == "medium"
        assert result["sources"]["documents"] == 0.5
        assert len(result["inferred_sections"]) == 2
        assert "Problem Statement" in result["inferred_sections"]


class TestConfidenceCalculator:
    """Tests for ConfidenceCalculator class."""
    
    def test_calculate_file_confidence_all_from_documents(self):
        """Test confidence when all sections come from source documents."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": ["Problem Statement", "Target Users", "Success Metrics"],
            "code_analysis": [],
            "inferred": []
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        # All from documents with weight 1.0 = 100% confidence
        assert score.overall == 1.0
        assert score.level == "high"
        assert score.sources["documents"] == 1.0
        assert score.sources["code_analysis"] == 0.0
        assert score.sources["inferred"] == 0.0
        assert len(score.inferred_sections) == 0
    
    def test_calculate_file_confidence_all_from_code(self):
        """Test confidence when all sections come from code analysis."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": [],
            "code_analysis": ["Backend", "Frontend", "Database"],
            "inferred": []
        }
        
        score = calculator.calculate_file_confidence(
            "tech-stack.md",
            sources,
            "# Tech Stack\n..."
        )
        
        # All from code with weight 0.8 = 80% confidence
        assert score.overall == 0.8
        assert score.level == "high"
        assert score.sources["documents"] == 0.0
        assert score.sources["code_analysis"] == 0.8
        assert score.sources["inferred"] == 0.0
        assert len(score.inferred_sections) == 0
    
    def test_calculate_file_confidence_all_inferred(self):
        """Test confidence when all sections are inferred (RED TEAM EDGE CASE)."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": [],
            "code_analysis": [],
            "inferred": ["Problem Statement", "Target Users", "Success Metrics"]
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        # All inferred with weight 0.3 = 30% confidence
        assert score.overall == 0.3
        assert score.level == "low"
        assert score.sources["documents"] == 0.0
        assert score.sources["code_analysis"] == 0.0
        assert score.sources["inferred"] == 0.3
        assert len(score.inferred_sections) == 3
        assert "Problem Statement" in score.inferred_sections
    
    def test_calculate_file_confidence_mixed_sources(self):
        """Test confidence with mixed sources."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": ["Problem Statement", "Target Users"],  # 2 sections
            "code_analysis": ["Tech Stack"],  # 1 section
            "inferred": ["Success Metrics"]  # 1 section
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        # Expected: (2/4 * 1.0) + (1/4 * 0.8) + (1/4 * 0.3) = 0.5 + 0.2 + 0.075 = 0.775
        assert abs(score.overall - 0.775) < 0.001
        assert score.level == "medium"
        assert abs(score.sources["documents"] - 0.5) < 0.001
        assert abs(score.sources["code_analysis"] - 0.2) < 0.001
        assert abs(score.sources["inferred"] - 0.075) < 0.001
        assert len(score.inferred_sections) == 1
        assert "Success Metrics" in score.inferred_sections
    
    def test_calculate_file_confidence_no_sections(self):
        """Test confidence when no sections are tracked (edge case)."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": [],
            "code_analysis": [],
            "inferred": []
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        assert score.overall == 0.0
        assert score.level == "low"
        assert score.sources == {}
        assert len(score.inferred_sections) == 0
    
    def test_calculate_file_confidence_missing_source_keys(self):
        """Test confidence when source dictionary is incomplete."""
        calculator = ConfidenceCalculator()
        
        # Only documents key present
        sources = {
            "documents": ["Problem Statement"]
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        # Should handle missing keys gracefully
        assert score.overall == 1.0
        assert score.level == "high"
        assert score.sources["documents"] == 1.0
        assert score.sources["code_analysis"] == 0.0
        assert score.sources["inferred"] == 0.0
    
    def test_calculate_file_confidence_high_threshold(self):
        """Test high confidence threshold (>= 0.8)."""
        calculator = ConfidenceCalculator()
        
        # 80% from documents, 20% from code = 0.8 + 0.16 = 0.96
        sources = {
            "documents": ["A", "B", "C", "D"],
            "code_analysis": ["E"],
            "inferred": []
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        assert score.overall >= 0.8
        assert score.level == "high"
    
    def test_calculate_file_confidence_medium_threshold(self):
        """Test medium confidence threshold (0.5 <= score < 0.8)."""
        calculator = ConfidenceCalculator()
        
        # 50% from documents, 50% from inferred = 0.5 + 0.15 = 0.65
        sources = {
            "documents": ["A", "B"],
            "code_analysis": [],
            "inferred": ["C", "D"]
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        assert 0.5 <= score.overall < 0.8
        assert score.level == "medium"
    
    def test_calculate_file_confidence_low_threshold(self):
        """Test low confidence threshold (< 0.5)."""
        calculator = ConfidenceCalculator()
        
        # 25% from documents, 75% from inferred = 0.25 + 0.225 = 0.475
        sources = {
            "documents": ["A"],
            "code_analysis": [],
            "inferred": ["B", "C", "D"]
        }
        
        score = calculator.calculate_file_confidence(
            "project-vision.md",
            sources,
            "# Project Vision\n..."
        )
        
        assert score.overall < 0.5
        assert score.level == "low"
    
    def test_calculate_overall_confidence_single_file(self):
        """Test overall confidence with a single file."""
        calculator = ConfidenceCalculator()
        
        file_scores = {
            "project-vision.md": ConfidenceScore(
                overall=0.8,
                level="high",
                sources={},
                inferred_sections=[]
            )
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        # Single file with weight 1.5: 0.8 * 1.5 / 1.5 = 0.8
        assert abs(overall.overall - 0.8) < 0.001
        assert overall.level == "high"
        assert len(overall.inferred_sections) == 0
    
    def test_calculate_overall_confidence_multiple_files(self):
        """Test overall confidence with multiple files."""
        calculator = ConfidenceCalculator()
        
        file_scores = {
            "project-vision.md": ConfidenceScore(0.8, "high", {}, []),
            "tech-stack.md": ConfidenceScore(0.6, "medium", {}, ["Backend"]),
            "conventions.md": ConfidenceScore(0.4, "low", {}, ["Naming"])
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        # Expected: (0.8*1.5 + 0.6*1.2 + 0.4*1.0) / (1.5+1.2+1.0)
        #         = (1.2 + 0.72 + 0.4) / 3.7 = 2.32 / 3.7 ≈ 0.627
        assert abs(overall.overall - 0.627) < 0.01
        assert overall.level == "medium"
        assert len(overall.inferred_sections) == 2
        assert "Backend" in overall.inferred_sections
        assert "Naming" in overall.inferred_sections
    
    def test_calculate_overall_confidence_mixed_levels(self):
        """Test overall confidence with mixed confidence levels (RED TEAM EDGE CASE)."""
        calculator = ConfidenceCalculator()
        
        file_scores = {
            "project-vision.md": ConfidenceScore(0.9, "high", {}, []),
            "tech-stack.md": ConfidenceScore(0.2, "low", {}, ["Backend", "Frontend"]),
            "conventions.md": ConfidenceScore(0.5, "medium", {}, ["Naming"])
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        # Expected: (0.9*1.5 + 0.2*1.2 + 0.5*1.0) / (1.5+1.2+1.0)
        #         = (1.35 + 0.24 + 0.5) / 3.7 = 2.09 / 3.7 ≈ 0.565
        assert abs(overall.overall - 0.565) < 0.01
        assert overall.level == "medium"
        assert len(overall.inferred_sections) == 3
    
    def test_calculate_overall_confidence_empty_file_scores(self):
        """Test overall confidence with no files (RED TEAM EDGE CASE)."""
        calculator = ConfidenceCalculator()
        
        file_scores = {}
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        assert overall.overall == 0.0
        assert overall.level == "low"
        assert overall.sources == {}
        assert len(overall.inferred_sections) == 0
    
    def test_calculate_overall_confidence_unknown_file(self):
        """Test overall confidence with file not in weight map."""
        calculator = ConfidenceCalculator()
        
        file_scores = {
            "custom-file.md": ConfidenceScore(0.7, "medium", {}, [])
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        # Unknown file gets default weight of 1.0
        assert overall.overall == 0.7
        assert overall.level == "medium"
    
    def test_calculate_overall_confidence_all_high(self):
        """Test overall confidence when all files are high confidence."""
        calculator = ConfidenceCalculator()
        
        file_scores = {
            "project-vision.md": ConfidenceScore(0.9, "high", {}, []),
            "tech-stack.md": ConfidenceScore(0.85, "high", {}, []),
            "conventions.md": ConfidenceScore(0.8, "high", {}, [])
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        assert overall.overall >= 0.8
        assert overall.level == "high"
    
    def test_calculate_overall_confidence_all_low(self):
        """Test overall confidence when all files are low confidence."""
        calculator = ConfidenceCalculator()
        
        file_scores = {
            "project-vision.md": ConfidenceScore(0.3, "low", {}, ["A", "B"]),
            "tech-stack.md": ConfidenceScore(0.2, "low", {}, ["C"]),
            "conventions.md": ConfidenceScore(0.4, "low", {}, ["D"])
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        assert overall.overall < 0.5
        assert overall.level == "low"
        assert len(overall.inferred_sections) == 4
    
    def test_weighting_algorithm_accuracy(self):
        """Test that weighting algorithm produces expected results."""
        calculator = ConfidenceCalculator()
        
        # Test case: 1 doc section, 1 code section, 1 inferred section
        sources = {
            "documents": ["A"],
            "code_analysis": ["B"],
            "inferred": ["C"]
        }
        
        score = calculator.calculate_file_confidence(
            "test.md",
            sources,
            "content"
        )
        
        # Expected: (1/3 * 1.0) + (1/3 * 0.8) + (1/3 * 0.3)
        #         = 0.333 + 0.267 + 0.1 = 0.7
        expected = (1.0 + 0.8 + 0.3) / 3
        assert abs(score.overall - expected) < 0.001
    
    def test_file_weights_are_applied(self):
        """Test that file importance weights are correctly applied."""
        calculator = ConfidenceCalculator()
        
        # Two files with same confidence but different importance
        file_scores = {
            "project-vision.md": ConfidenceScore(0.5, "medium", {}, []),  # weight 1.5
            "qa-standards.md": ConfidenceScore(0.5, "medium", {}, [])     # weight 0.8
        }
        
        overall = calculator.calculate_overall_confidence(file_scores)
        
        # Expected: (0.5*1.5 + 0.5*0.8) / (1.5+0.8) = (0.75 + 0.4) / 2.3 = 0.5
        assert abs(overall.overall - 0.5) < 0.001
    
    def test_confidence_weights_constants(self):
        """Test that confidence weight constants have expected values."""
        calculator = ConfidenceCalculator()
        
        assert calculator.WEIGHT_SOURCE_DOCUMENTS == 1.0
        assert calculator.WEIGHT_CODE_ANALYSIS == 0.8
        assert calculator.WEIGHT_LLM_INFERENCE == 0.3
    
    def test_file_weights_constants(self):
        """Test that file weight constants have expected values."""
        calculator = ConfidenceCalculator()
        
        assert calculator.FILE_WEIGHTS["project-vision.md"] == 1.5
        assert calculator.FILE_WEIGHTS["tech-stack.md"] == 1.2
        assert calculator.FILE_WEIGHTS["architecture.md"] == 1.2
        assert calculator.FILE_WEIGHTS["conventions.md"] == 1.0
        assert calculator.FILE_WEIGHTS["db-standards.md"] == 0.8
