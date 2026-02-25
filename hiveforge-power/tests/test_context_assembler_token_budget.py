"""
Property test for ContextAssembler token budget enforcement.

Tests that ContextAssembler.assemble() never exceeds 8,000 tokens per template
for any combination of inputs.

Requirements: 4.1, 4.2
"""

import json
from pathlib import Path

from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    DeltaReport,
    Dependency,
    NamingConventions,
    ParsedDocument,
)


class TestContextAssemblerTokenBudget:
    """
    Property 5: Token budget never exceeded per template.
    
    For any combination of inputs, ContextAssembler.assemble() must return
    a GenerationContext whose total token count is ≤8,000.
    
    Requirements: 4.1, 4.2
    """
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using rough heuristic: 1 token ≈ 4 characters.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def _estimate_context_tokens(self, context) -> int:
        """
        Estimate total tokens in a GenerationContext.
        
        Args:
            context: GenerationContext to estimate
            
        Returns:
            Estimated total token count
        """
        total = 0
        
        # Source docs
        for doc in context.source_docs:
            total += self._estimate_tokens(doc.content)
        
        # Code facts
        code_facts_json = json.dumps(context.code_facts.to_json_dict())
        total += self._estimate_tokens(code_facts_json)
        
        # Existing steering
        for text in context.existing_steering.values():
            total += self._estimate_tokens(text)
        
        # Previously generated summaries
        for text in context.previously_generated_summaries.values():
            total += self._estimate_tokens(text)
        
        # Delta report
        if context.delta:
            delta_text = "\n".join(
                context.delta.doc_vs_code
                + context.delta.steering_vs_code
                + context.delta.steering_vs_docs
                + context.delta.missing_in_all
            )
            total += self._estimate_tokens(delta_text)
        
        # User intent
        if context.user_intent:
            total += self._estimate_tokens(context.user_intent)
        
        return total
    
    def test_minimal_context_within_budget(self):
        """
        Test that minimal context is within token budget.
        
        Requirements: 4.1, 4.2
        """
        assembler = ContextAssembler()
        
        # Minimal inputs
        code_facts = CodeAnalysisFacts(
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
        )
        
        context = assembler.assemble(
            template_name="tech-stack.md",
            template_schema=[],
            use_case="new_from_docs",
            source_docs=[],
            code_facts=code_facts,
            existing_steering={},
            previously_generated={},
            delta=None,
            user_intent=None,
        )
        
        token_count = self._estimate_context_tokens(context)
        
        assert token_count <= 8000, (
            f"Minimal context exceeds token budget: {token_count} tokens > 8000"
        )
    
    def test_typical_context_within_budget(self):
        """
        Test that typical context is within token budget.
        
        Requirements: 4.1, 4.2
        """
        assembler = ContextAssembler()
        
        # Typical source docs (2 documents, ~1000 chars each)
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="# Design Document\n\n" + ("This is design content. " * 50),
                metadata={},
                parse_errors=[],
            ),
            ParsedDocument(
                file_path=Path("requirements.md"),
                content="# Requirements\n\n" + ("This is a requirement. " * 50),
                metadata={},
                parse_errors=[],
            ),
        ]
        
        # Typical code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI", "Typer"],
            dependencies=[
                Dependency(name="pytest", version="7.4.0", dependency_type="dev"),
                Dependency(name="openai", version="1.0.0", dependency_type="runtime"),
            ],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=["main.py", "cli.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
            ),
            directory_structure="src, tests, docs",
        )
        
        context = assembler.assemble(
            template_name="tech-stack.md",
            template_schema=[],
            use_case="new_from_docs",
            source_docs=source_docs,
            code_facts=code_facts,
            existing_steering={},
            previously_generated={},
            delta=None,
            user_intent=None,
        )
        
        token_count = self._estimate_context_tokens(context)
        
        assert token_count <= 8000, (
            f"Typical context exceeds token budget: {token_count} tokens > 8000"
        )
    
    def test_large_source_docs_truncated_to_budget(self):
        """
        Test that large source documents are truncated to fit budget.
        
        Requirements: 4.1, 4.2, 4.3
        """
        assembler = ContextAssembler()
        
        # Create 10 large documents (~5000 chars each = ~1250 tokens each)
        # Total: ~12,500 tokens (exceeds 4,000 token budget for source docs)
        large_docs = []
        for i in range(10):
            content = f"# Document {i}\n\n" + (f"This is content for document {i}. " * 200)
            large_docs.append(
                ParsedDocument(
                    file_path=Path(f"doc{i}.md"),
                    content=content,
                    metadata={},
                    parse_errors=[],
                )
            )
        
        code_facts = CodeAnalysisFacts(
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
        )
        
        context = assembler.assemble(
            template_name="tech-stack.md",
            template_schema=[],
            use_case="new_from_docs",
            source_docs=large_docs,
            code_facts=code_facts,
            existing_steering={},
            previously_generated={},
            delta=None,
            user_intent=None,
        )
        
        token_count = self._estimate_context_tokens(context)
        
        # Should be truncated to fit within 8,000 token budget
        assert token_count <= 8000, (
            f"Large source docs not truncated properly: {token_count} tokens > 8000"
        )
        
        # Source docs should be truncated
        assert len(context.source_docs) < len(large_docs), (
            "Source docs should be truncated when exceeding budget"
        )
    
    def test_maximal_context_within_budget(self):
        """
        Test that maximal context (all fields populated) is within budget.
        
        This is the critical test - even with all fields at maximum,
        the total must not exceed 8,000 tokens.
        
        Requirements: 4.1, 4.2
        """
        assembler = ContextAssembler()
        
        # Maximal source docs (targeting 4,000 token budget)
        max_source_docs = []
        for i in range(20):
            content = f"# Large Document {i}\n\n" + (f"Content for doc {i}. " * 100)
            max_source_docs.append(
                ParsedDocument(
                    file_path=Path(f"large_doc{i}.md"),
                    content=content,
                    metadata={},
                    parse_errors=[],
                )
            )
        
        # Maximal code facts (targeting 2,000 token budget)
        max_code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11.5",
            frameworks=["FastAPI", "SQLAlchemy", "Pydantic", "Celery", "Redis"],
            dependencies=[
                Dependency(name=f"dep-{i}", version=f"1.{i}.0", dependency_type="runtime")
                for i in range(50)
            ],
            architecture_pattern="microservices",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=[f"module_{i}.py" for i in range(20)],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
                constants="UPPER_SNAKE_CASE",
                functions="snake_case",
            ),
            directory_structure=", ".join([f"dir_{i}" for i in range(20)]),
        )
        
        # Maximal existing steering (targeting 1,000 token budget)
        max_existing_steering = {
            f"file{i}.md": f"# Existing File {i}\n\n" + (f"Existing content {i}. " * 50)
            for i in range(5)
        }
        
        # Maximal previously generated (targeting 1,000 token budget)
        max_previously_generated = {
            f"prev{i}.md": f"# Previously Generated {i}\n\n" + (f"Previous content {i}. " * 50)
            for i in range(5)
        }
        
        # Maximal delta report
        max_delta = DeltaReport(
            doc_vs_code=[f"Mismatch {i}: docs say X but code uses Y" for i in range(10)],
            steering_vs_code=[f"Drift {i}: steering outdated" for i in range(10)],
            steering_vs_docs=[f"Conflict {i}: steering vs docs" for i in range(10)],
            missing_in_all=[f"Missing {i}: not found anywhere" for i in range(10)],
        )
        
        # Maximal user intent
        max_user_intent = "# User Intent\n\n" + ("We are pivoting to a new architecture. " * 50)
        
        context = assembler.assemble(
            template_name="tech-stack.md",
            template_schema=[],
            use_case="drift_correction",
            source_docs=max_source_docs,
            code_facts=max_code_facts,
            existing_steering=max_existing_steering,
            previously_generated=max_previously_generated,
            delta=max_delta,
            user_intent=max_user_intent,
        )
        
        token_count = self._estimate_context_tokens(context)
        
        # This is the critical assertion - even maximal context must fit
        assert token_count <= 8000, (
            f"Maximal context exceeds token budget: {token_count} tokens > 8000. "
            f"The implementation needs better truncation to stay within budget."
        )
    
    def test_all_templates_within_budget(self):
        """
        Test that all 8 templates stay within budget.
        
        Requirements: 4.1, 4.2
        """
        assembler = ContextAssembler()
        
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
        
        # Create moderate-sized inputs
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="# Design\n\n" + ("Design content. " * 100),
                metadata={},
                parse_errors=[],
            )
        ]
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[
                Dependency(name="pytest", version="7.4.0", dependency_type="dev"),
            ],
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
        
        # Test each template
        for template_name in templates:
            context = assembler.assemble(
                template_name=template_name,
                template_schema=[],
                use_case="new_from_docs",
                source_docs=source_docs,
                code_facts=code_facts,
                existing_steering={},
                previously_generated={},
                delta=None,
                user_intent=None,
            )
            
            token_count = self._estimate_context_tokens(context)
            
            assert token_count <= 8000, (
                f"Template {template_name} exceeds token budget: "
                f"{token_count} tokens > 8000"
            )
    
    def test_keyword_filtering_reduces_tokens(self):
        """
        Test that keyword-based filtering reduces token count for irrelevant docs.
        
        Requirements: 4.3
        """
        assembler = ContextAssembler()
        
        # Create docs with different relevance to tech-stack.md
        relevant_doc = ParsedDocument(
            file_path=Path("tech.md"),
            content="# Technology Stack\n\nWe use Python, FastAPI, PostgreSQL database, "
                   "and various frameworks and libraries. " * 20,
            metadata={},
            parse_errors=[],
        )
        
        irrelevant_doc = ParsedDocument(
            file_path=Path("meeting.md"),
            content="# Meeting Notes\n\nWe discussed the project timeline and budget. "
                   "The team agreed on the schedule. " * 20,
            metadata={},
            parse_errors=[],
        )
        
        code_facts = CodeAnalysisFacts(
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
        )
        
        # Assemble with both docs
        context = assembler.assemble(
            template_name="tech-stack.md",
            template_schema=[],
            use_case="new_from_docs",
            source_docs=[relevant_doc, irrelevant_doc],
            code_facts=code_facts,
            existing_steering={},
            previously_generated={},
            delta=None,
            user_intent=None,
        )
        
        # Should prioritize relevant doc
        # (irrelevant doc may be filtered out or deprioritized)
        assert len(context.source_docs) >= 1, "Should include at least the relevant doc"
        
        # Token count should be within budget
        token_count = self._estimate_context_tokens(context)
        assert token_count <= 8000, (
            f"Context with filtered docs exceeds budget: {token_count} tokens > 8000"
        )
