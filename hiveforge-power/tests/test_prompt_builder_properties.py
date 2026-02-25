"""
Property tests for PromptBuilder.

Tests that prompts contain all required instruction strings and context fields.

Requirements: 1.4, 1.5, 10.1, 10.2, 10.3, 10.4
"""

from pathlib import Path

from hiveforge.steering.prompt_builder import PromptBuilder
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    DeltaReport,
    GenerationContext,
    NamingConventions,
    ParsedDocument,
)


class TestPromptBuilderInstructionStrings:
    """
    Property 4: Prompt contains all required instruction strings.
    
    For any template and context, the system prompt must contain all five
    required instruction strings.
    
    Requirements: 1.5, 10.1, 10.2, 10.3, 10.4
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.builder = PromptBuilder()
        
        # Create a minimal context for testing
        self.minimal_context = GenerationContext(
            template_name="tech-stack.md",
            use_case="new_from_docs",
            source_docs=[],
            code_facts=CodeAnalysisFacts(
                primary_language="Python 3.11",
                frameworks=[],
                dependencies=[],
                architecture_pattern="custom",
                has_tests=False,
                test_framework=None,
                api_type=None,
                database=None,
                entry_points=[],
                naming_conventions=NamingConventions(),
                directory_structure="",
            ),
            existing_steering={},
            previously_generated_summaries={},
            delta=None,
            user_intent=None,
        )
    
    def test_all_five_instruction_strings_present(self):
        """
        Test that all five required instruction strings are in system prompt.
        
        Requirements: 1.5, 10.1, 10.2, 10.3, 10.4
        """
        template_content = "# Tech Stack\n\n## Backend\n\n## Frontend\n"
        
        system_prompt, _ = self.builder.build(
            "tech-stack.md",
            template_content,
            self.minimal_context,
        )
        
        # Check for all five required instructions
        assert self.builder.INSTRUCTION_FILL_INDEPENDENTLY in system_prompt
        assert self.builder.INSTRUCTION_NA_FOR_ABSENT in system_prompt
        assert self.builder.INSTRUCTION_NOT_FOUND_FOR_EXPECTED in system_prompt
        assert self.builder.INSTRUCTION_NO_REPETITION in system_prompt
        assert self.builder.INSTRUCTION_MARKDOWN_ONLY in system_prompt
    
    def test_instruction_fill_independently_present(self):
        """
        Test that "fill every section independently" instruction is present.
        
        Requirement: 10.1
        """
        template_content = "# Architecture\n"
        
        system_prompt, _ = self.builder.build(
            "architecture.md",
            template_content,
            self.minimal_context,
        )
        
        assert "fill every section independently" in system_prompt.lower()
    
    def test_instruction_na_for_absent_present(self):
        """
        Test that "write N/A for absent info" instruction is present.
        
        Requirement: 10.2
        """
        template_content = "# Conventions\n"
        
        system_prompt, _ = self.builder.build(
            "conventions.md",
            template_content,
            self.minimal_context,
        )
        
        assert "n/a" in system_prompt.lower()
        assert "absent" in system_prompt.lower()
    
    def test_instruction_not_found_for_expected_present(self):
        """
        Test that "[NOT FOUND] for expected-but-absent" instruction is present.
        
        Requirement: 10.3
        """
        template_content = "# Testing\n"
        
        system_prompt, _ = self.builder.build(
            "testing.md",
            template_content,
            self.minimal_context,
        )
        
        assert "[not found]" in system_prompt.lower()
        assert "expected" in system_prompt.lower()
    
    def test_instruction_no_repetition_present(self):
        """
        Test that "no content repeated across sections" instruction is present.
        
        Requirement: 10.4
        """
        template_content = "# Security\n"
        
        system_prompt, _ = self.builder.build(
            "security.md",
            template_content,
            self.minimal_context,
        )
        
        assert "repeat" in system_prompt.lower() or "repetition" in system_prompt.lower()
    
    def test_instruction_markdown_only_present(self):
        """
        Test that "output only Markdown, no preamble" instruction is present.
        
        Requirement: 1.5
        """
        template_content = "# Workflows\n"
        
        system_prompt, _ = self.builder.build(
            "workflows.md",
            template_content,
            self.minimal_context,
        )
        
        assert "markdown" in system_prompt.lower()
        assert "preamble" in system_prompt.lower() or "only" in system_prompt.lower()
    
    def test_instructions_present_for_all_templates(self):
        """
        Test that instructions are present regardless of template name.
        
        Requirement: 1.5
        """
        templates = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        for template_name in templates:
            system_prompt, _ = self.builder.build(
                template_name,
                f"# {template_name}\n",
                self.minimal_context,
            )
            
            # All five instructions must be present
            assert self.builder.INSTRUCTION_FILL_INDEPENDENTLY in system_prompt
            assert self.builder.INSTRUCTION_NA_FOR_ABSENT in system_prompt
            assert self.builder.INSTRUCTION_NOT_FOUND_FOR_EXPECTED in system_prompt
            assert self.builder.INSTRUCTION_NO_REPETITION in system_prompt
            assert self.builder.INSTRUCTION_MARKDOWN_ONLY in system_prompt


class TestPromptBuilderContextFields:
    """
    Property 3: Prompt contains all required context fields.
    
    For any GenerationContext with all fields populated, PromptBuilder.build()
    output must contain each field's content.
    
    Requirement: 1.4
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.builder = PromptBuilder()
    
    def test_source_docs_included_in_prompt(self):
        """
        Test that source documents are included in user prompt.
        
        Requirement: 1.4
        """
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="This is a design document with unique content xyz123.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        context = GenerationContext(
            template_name="tech-stack.md",
            use_case="new_from_docs",
            source_docs=source_docs,
            code_facts=CodeAnalysisFacts(
                primary_language="Python 3.11",
                frameworks=[],
                dependencies=[],
                architecture_pattern="custom",
                has_tests=False,
                test_framework=None,
                api_type=None,
                database=None,
                entry_points=[],
                naming_conventions=NamingConventions(),
                directory_structure="",
            ),
            existing_steering={},
            previously_generated_summaries={},
            delta=None,
            user_intent=None,
        )
        
        _, user_prompt = self.builder.build(
            "tech-stack.md",
            "# Tech Stack\n",
            context,
        )
        
        # Source doc content should be in user prompt
        assert "unique content xyz123" in user_prompt
        assert "design.md" in user_prompt
    
    def test_code_facts_included_in_prompt(self):
        """
        Test that code facts are included in user prompt.
        
        Requirement: 1.4
        """
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=["main.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
            ),
            directory_structure="src, tests",
        )
        
        context = GenerationContext(
            template_name="tech-stack.md",
            use_case="reverse_engineer",
            source_docs=[],
            code_facts=code_facts,
            existing_steering={},
            previously_generated_summaries={},
            delta=None,
            user_intent=None,
        )
        
        _, user_prompt = self.builder.build(
            "tech-stack.md",
            "# Tech Stack\n",
            context,
        )
        
        # Code facts should be in user prompt
        assert "fastapi" in user_prompt.lower()
        assert "postgresql" in user_prompt.lower()
        assert "pytest" in user_prompt.lower()
    
    def test_existing_steering_included_in_prompt(self):
        """
        Test that existing steering content is included in user prompt.
        
        Requirement: 1.4
        """
        existing_steering = {
            "tech-stack.md": "Backend: Django framework with unique marker abc789"
        }
        
        context = GenerationContext(
            template_name="tech-stack.md",
            use_case="update",
            source_docs=[],
            code_facts=CodeAnalysisFacts(
                primary_language="Python 3.11",
                frameworks=[],
                dependencies=[],
                architecture_pattern="custom",
                has_tests=False,
                test_framework=None,
                api_type=None,
                database=None,
                entry_points=[],
                naming_conventions=NamingConventions(),
                directory_structure="",
            ),
            existing_steering=existing_steering,
            previously_generated_summaries={},
            delta=None,
            user_intent=None,
        )
        
        _, user_prompt = self.builder.build(
            "tech-stack.md",
            "# Tech Stack\n",
            context,
        )
        
        # Existing steering should be in user prompt
        assert "unique marker abc789" in user_prompt
    
    def test_delta_report_included_for_drift_correction(self):
        """
        Test that delta report is included for drift_correction use case.
        
        Requirement: 1.4
        """
        delta = DeltaReport(
            doc_vs_code=["Database mismatch: docs say PostgreSQL but code uses MySQL"],
            steering_vs_code=["Framework drift detected"],
            steering_vs_docs=["Conflict between steering and docs"],
            missing_in_all=["Testing strategy not defined"],
        )
        
        context = GenerationContext(
            template_name="tech-stack.md",
            use_case="drift_correction",
            source_docs=[],
            code_facts=CodeAnalysisFacts(
                primary_language="Python 3.11",
                frameworks=[],
                dependencies=[],
                architecture_pattern="custom",
                has_tests=False,
                test_framework=None,
                api_type=None,
                database=None,
                entry_points=[],
                naming_conventions=NamingConventions(),
                directory_structure="",
            ),
            existing_steering={},
            previously_generated_summaries={},
            delta=delta,
            user_intent=None,
        )
        
        _, user_prompt = self.builder.build(
            "tech-stack.md",
            "# Tech Stack\n",
            context,
        )
        
        # Delta report content should be in user prompt
        assert "database mismatch" in user_prompt.lower()
        assert "postgresql" in user_prompt.lower()
        assert "mysql" in user_prompt.lower()
    
    def test_user_intent_included_when_present(self):
        """
        Test that user intent is included when provided.
        
        Requirement: 1.4
        """
        user_intent = "We are pivoting to use microservices architecture with unique marker def456."
        
        context = GenerationContext(
            template_name="architecture.md",
            use_case="pivot",
            source_docs=[],
            code_facts=CodeAnalysisFacts(
                primary_language="Python 3.11",
                frameworks=[],
                dependencies=[],
                architecture_pattern="custom",
                has_tests=False,
                test_framework=None,
                api_type=None,
                database=None,
                entry_points=[],
                naming_conventions=NamingConventions(),
                directory_structure="",
            ),
            existing_steering={},
            previously_generated_summaries={},
            delta=None,
            user_intent=user_intent,
        )
        
        _, user_prompt = self.builder.build(
            "architecture.md",
            "# Architecture\n",
            context,
        )
        
        # User intent should be in user prompt
        assert "unique marker def456" in user_prompt
        assert "microservices" in user_prompt.lower()
    
    def test_previously_generated_summaries_included(self):
        """
        Test that previously generated file summaries are included.
        
        Requirement: 1.4
        """
        previously_generated = {
            "project-vision.md": "Vision summary with unique marker ghi789"
        }
        
        context = GenerationContext(
            template_name="tech-stack.md",
            use_case="new_from_docs",
            source_docs=[],
            code_facts=CodeAnalysisFacts(
                primary_language="Python 3.11",
                frameworks=[],
                dependencies=[],
                architecture_pattern="custom",
                has_tests=False,
                test_framework=None,
                api_type=None,
                database=None,
                entry_points=[],
                naming_conventions=NamingConventions(),
                directory_structure="",
            ),
            existing_steering={},
            previously_generated_summaries=previously_generated,
            delta=None,
            user_intent=None,
        )
        
        _, user_prompt = self.builder.build(
            "tech-stack.md",
            "# Tech Stack\n",
            context,
        )
        
        # Previously generated summaries should be in user prompt
        assert "unique marker ghi789" in user_prompt
    
    def test_all_context_fields_included_when_populated(self):
        """
        Test that all context fields are included when all are populated.
        
        Requirement: 1.4
        """
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="Design content marker1",
                metadata={},
                parse_errors=[],
            )
        ]
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        existing_steering = {
            "tech-stack.md": "Existing content marker2"
        }
        
        previously_generated = {
            "project-vision.md": "Vision summary marker3"
        }
        
        delta = DeltaReport(
            doc_vs_code=["Mismatch marker4"],
            steering_vs_code=[],
            steering_vs_docs=[],
            missing_in_all=[],
        )
        
        user_intent = "Intent content marker5"
        
        context = GenerationContext(
            template_name="tech-stack.md",
            use_case="drift_correction",
            source_docs=source_docs,
            code_facts=code_facts,
            existing_steering=existing_steering,
            previously_generated_summaries=previously_generated,
            delta=delta,
            user_intent=user_intent,
        )
        
        _, user_prompt = self.builder.build(
            "tech-stack.md",
            "# Tech Stack\n",
            context,
        )
        
        # All markers should be present
        assert "marker1" in user_prompt
        assert "marker2" in user_prompt
        assert "marker3" in user_prompt
        assert "marker4" in user_prompt
        assert "marker5" in user_prompt
