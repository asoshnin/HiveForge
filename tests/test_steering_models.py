"""
Tests for steering assistant data models.

This module tests the data models defined in src/hiveforge/steering/models.py
to ensure they can be instantiated correctly and have proper validation.
"""

import pytest
from pathlib import Path
from hiveforge.steering.models import (
    ParsedDocument,
    Template,
    TemplateSection,
    ValidationRule,
    WorkflowState,
    SteeringConfig,
    LanguageInfo,
    TechStackInfo,
    ArchitectureInfo,
    ConventionsInfo,
    CodeAnalysisResult,
    Dependency,
    GapAnalysisResult,
    Question,
    Conflict,
    Customization,
    ValidationReport,
    ValidationIssue,
    FileDiff,
    DiffHunk,
    DiffLine,
    CachedResponse,
)


class TestParsedDocument:
    """Tests for ParsedDocument model."""
    
    def test_create_parsed_document(self):
        """Should create a ParsedDocument with required fields."""
        doc = ParsedDocument(
            file_path=Path("test.md"),
            content="Test content"
        )
        assert doc.file_path == Path("test.md")
        assert doc.content == "Test content"
        assert doc.metadata == {}
        assert doc.parse_errors == []
    
    def test_parsed_document_with_metadata(self):
        """Should create a ParsedDocument with metadata."""
        doc = ParsedDocument(
            file_path=Path("test.md"),
            content="Test content",
            metadata={"author": "Test Author"},
            parse_errors=["Warning: missing header"]
        )
        assert doc.metadata == {"author": "Test Author"}
        assert doc.parse_errors == ["Warning: missing header"]


class TestTemplateModels:
    """Tests for Template-related models."""
    
    def test_create_validation_rule(self):
        """Should create a ValidationRule."""
        rule = ValidationRule(
            rule_type="required",
            parameters={"min_length": 10},
            error_message="Field is required"
        )
        assert rule.rule_type == "required"
        assert rule.parameters == {"min_length": 10}
    
    def test_create_template_section(self):
        """Should create a TemplateSection."""
        section = TemplateSection(
            name="Overview",
            required=True,
            placeholder_pattern=r"\{.*?\}",
            validation_rules=[],
            examples=["Example 1"]
        )
        assert section.name == "Overview"
        assert section.required is True
    
    def test_create_template(self):
        """Should create a Template with sections."""
        section = TemplateSection(
            name="Overview",
            required=True,
            placeholder_pattern=r"\{.*?\}"
        )
        template = Template(
            name="project-vision",
            file_name="project-vision.md",
            priority=1,
            sections=[section],
            frontmatter={"inclusion": "auto"}
        )
        assert template.name == "project-vision"
        assert template.priority == 1
        assert len(template.sections) == 1


class TestCodeAnalysisModels:
    """Tests for code analysis models."""
    
    def test_create_language_info(self):
        """Should create LanguageInfo."""
        lang = LanguageInfo(
            name="Python",
            version="3.11",
            file_count=50,
            line_count=5000,
            percentage=65.5
        )
        assert lang.name == "Python"
        assert lang.version == "3.11"
        assert lang.percentage == 65.5
    
    def test_create_dependency(self):
        """Should create Dependency."""
        dep = Dependency(
            name="fastapi",
            version="0.104.0",
            dependency_type="runtime"
        )
        assert dep.name == "fastapi"
        assert dep.version == "0.104.0"
    
    def test_create_tech_stack_info(self):
        """Should create TechStackInfo."""
        tech = TechStackInfo(
            backend_framework="FastAPI",
            frontend_framework="React",
            database="PostgreSQL",
            cache="Redis",
            dependencies=[
                Dependency(name="fastapi", version="0.104.0")
            ]
        )
        assert tech.backend_framework == "FastAPI"
        assert len(tech.dependencies) == 1
    
    def test_create_architecture_info(self):
        """Should create ArchitectureInfo."""
        arch = ArchitectureInfo(
            pattern="layered",
            directory_structure={"src/controllers": "API controllers"},
            key_components=["API Gateway", "Auth Service"]
        )
        assert arch.pattern == "layered"
        assert len(arch.key_components) == 2
    
    def test_create_conventions_info(self):
        """Should create ConventionsInfo."""
        conv = ConventionsInfo(
            naming_style={"variables": "snake_case", "classes": "PascalCase"},
            formatting={"indent": 4, "line_length": 100},
            documentation_style="Google",
            test_framework="pytest"
        )
        assert conv.naming_style["variables"] == "snake_case"
        assert conv.test_framework == "pytest"
    
    def test_create_code_analysis_result(self):
        """Should create CodeAnalysisResult."""
        result = CodeAnalysisResult(
            languages=[
                LanguageInfo(name="Python", percentage=70.0),
                LanguageInfo(name="JavaScript", percentage=30.0)
            ],
            tech_stack=TechStackInfo(backend_framework="FastAPI"),
            architecture=ArchitectureInfo(pattern="layered"),
            conventions=ConventionsInfo(naming_style={"variables": "snake_case"}),
            confidence_scores={"language": 0.95, "framework": 0.85}
        )
        assert len(result.languages) == 2
        assert result.confidence_scores["language"] == 0.95
    
    def test_code_analysis_to_summary(self):
        """Should convert CodeAnalysisResult to summary string."""
        result = CodeAnalysisResult(
            languages=[
                LanguageInfo(name="Python", version="3.11", percentage=70.0),
                LanguageInfo(name="JavaScript", percentage=30.0)
            ],
            tech_stack=TechStackInfo(
                backend_framework="FastAPI",
                database="PostgreSQL"
            ),
            architecture=ArchitectureInfo(
                pattern="layered",
                key_components=["API", "Service", "Repository"]
            ),
            conventions=ConventionsInfo(
                naming_style={"variables": "snake_case", "classes": "PascalCase"}
            )
        )
        
        summary = result.to_summary(max_tokens=2000)
        assert "Python" in summary
        assert "FastAPI" in summary
        assert "layered" in summary
        assert "snake_case" in summary
    
    def test_code_analysis_summary_truncation(self):
        """Should truncate summary if it exceeds max_tokens."""
        result = CodeAnalysisResult(
            languages=[LanguageInfo(name=f"Lang{i}", percentage=1.0) for i in range(100)]
        )
        
        summary = result.to_summary(max_tokens=10)  # Very small limit
        assert len(summary) <= 10 * 4 + 3  # 4 chars per token + "..."


class TestGapAnalysisModels:
    """Tests for gap analysis models."""
    
    def test_create_question(self):
        """Should create Question."""
        question = Question(
            template_name="project-vision",
            section_name="Problem Statement",
            question_text="What problem does this solve?",
            context="This helps define the project scope",
            priority=1
        )
        assert question.template_name == "project-vision"
        assert question.priority == 1
    
    def test_create_gap_analysis_result(self):
        """Should create GapAnalysisResult."""
        result = GapAnalysisResult(
            complete_sections={"project-vision": ["Overview"]},
            missing_sections={"tech-stack": ["Database"]},
            ambiguous_sections={"architecture": ["Scalability"]},
            questions=[
                Question(
                    template_name="tech-stack",
                    section_name="Database",
                    question_text="What database?",
                    context="Required for tech stack",
                    priority=1
                )
            ]
        )
        assert len(result.questions) == 1
        assert "tech-stack" in result.missing_sections


class TestConflictModels:
    """Tests for conflict resolution models."""
    
    def test_create_conflict(self):
        """Should create Conflict."""
        conflict = Conflict(
            section="Database",
            old_value="PostgreSQL",
            new_value="MongoDB",
            explanation="New requirements specify document storage"
        )
        assert conflict.old_value == "PostgreSQL"
        assert conflict.new_value == "MongoDB"
        assert "keep_old" in conflict.resolution_options
    
    def test_create_customization(self):
        """Should create Customization."""
        custom = Customization(
            section="Testing",
            original="Use pytest",
            customized="Use pytest with coverage plugin",
            confidence=0.85
        )
        assert custom.confidence == 0.85


class TestDiffModels:
    """Tests for diff models."""
    
    def test_create_diff_line(self):
        """Should create DiffLine."""
        line = DiffLine(type="addition", content="+ New line")
        assert line.type == "addition"
        assert line.content == "+ New line"
    
    def test_create_diff_hunk(self):
        """Should create DiffHunk."""
        hunk = DiffHunk(
            old_start=10,
            old_count=3,
            new_start=10,
            new_count=4,
            lines=[
                DiffLine(type="context", content="  Context"),
                DiffLine(type="addition", content="+ Added")
            ]
        )
        assert hunk.old_start == 10
        assert len(hunk.lines) == 2
    
    def test_create_file_diff(self):
        """Should create FileDiff."""
        diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Line 1", "Line 2"],
            new_lines=["Line 1", "Line 2 modified"],
            hunks=[
                DiffHunk(
                    old_start=2,
                    old_count=1,
                    new_start=2,
                    new_count=1,
                    lines=[DiffLine(type="deletion", content="- Line 2")]
                )
            ]
        )
        assert diff.file_name == "tech-stack.md"
        assert len(diff.hunks) == 1


class TestValidationModels:
    """Tests for validation models."""
    
    def test_create_validation_issue(self):
        """Should create ValidationIssue."""
        issue = ValidationIssue(
            severity="critical",
            file_name="conventions.md",
            line_number=45,
            issue_type="missing_section",
            message="Missing Testing section",
            suggestion="Add testing conventions"
        )
        assert issue.severity == "critical"
        assert issue.line_number == 45
    
    def test_create_validation_report(self):
        """Should create ValidationReport."""
        report = ValidationReport(
            critical_issues=[
                ValidationIssue(
                    severity="critical",
                    file_name="test.md",
                    message="Critical error"
                )
            ],
            warnings=[
                ValidationIssue(
                    severity="warning",
                    file_name="test.md",
                    message="Warning"
                )
            ],
            files_checked=8,
            overall_status="fail",
            llm_calls_made=2,
            tokens_used=500
        )
        assert len(report.critical_issues) == 1
        assert len(report.warnings) == 1
        assert report.overall_status == "fail"
        assert report.llm_calls_made == 2


class TestWorkflowModels:
    """Tests for workflow models."""
    
    def test_create_workflow_state(self):
        """Should create WorkflowState."""
        state = WorkflowState(
            workflow_type="init",
            staging_dir=Path(".kiro/onboarding"),
            steering_dir=Path(".kiro/steering"),
            parsed_documents=[
                ParsedDocument(
                    file_path=Path("test.md"),
                    content="Test"
                )
            ]
        )
        assert state.workflow_type == "init"
        assert len(state.parsed_documents) == 1
    
    def test_create_steering_config(self):
        """Should create SteeringConfig with defaults."""
        config = SteeringConfig()
        assert config.research_enabled is False
        assert config.skip_validation is False
        assert config.interactive is True
        assert config.backup_enabled is True
    
    def test_create_steering_config_custom(self):
        """Should create SteeringConfig with custom values."""
        config = SteeringConfig(
            research_enabled=True,
            skip_validation=True,
            interactive=False,
            strict_mode=True,
            analyze_code=True
        )
        assert config.research_enabled is True
        assert config.skip_validation is True
        assert config.interactive is False
        assert config.strict_mode is True
        assert config.analyze_code is True


class TestCacheModels:
    """Tests for cache models."""
    
    def test_create_cached_response(self):
        """Should create CachedResponse."""
        cached = CachedResponse(
            question_hash="abc123",
            response="Cached answer",
            timestamp=1234567890.0,
            metadata={"model": "gpt-4"}
        )
        assert cached.question_hash == "abc123"
        assert cached.response == "Cached answer"
        assert cached.metadata["model"] == "gpt-4"
