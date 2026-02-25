"""
Prompt builder for the LLM-Primary Steering Synthesis pipeline.

This module constructs structured LLM prompts from GenerationContext objects,
including all required instruction strings and context fields.

Requirements: 1.4, 1.5, 7.3, 7.5, 10.1, 10.2, 10.3, 10.4
"""

import json
import logging
from typing import Tuple

from .models import GenerationContext

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Constructs structured LLM prompts for steering file generation.
    
    The PromptBuilder creates system and user prompts that include all required
    instruction strings and context fields for high-quality LLM output.
    
    Requirements: 1.4, 1.5, 7.3, 7.5, 10.1, 10.2, 10.3, 10.4
    """
    
    # Required instruction strings (Requirements 1.5, 10.1, 10.2, 10.3, 10.4)
    INSTRUCTION_FILL_INDEPENDENTLY = (
        "Fill every section independently based on the provided context."
    )
    INSTRUCTION_NA_FOR_ABSENT = (
        "Write 'N/A' for any information that is genuinely absent from all sources."
    )
    INSTRUCTION_NOT_FOUND_FOR_EXPECTED = (
        "Write '[NOT FOUND]' for fields that are expected but absent "
        "(e.g., a database name when the architecture clearly uses a database)."
    )
    INSTRUCTION_NO_REPETITION = (
        "Do not repeat content across sections. Each section should contain unique information."
    )
    INSTRUCTION_MARKDOWN_ONLY = (
        "Output only the final Markdown content with no preamble, explanation, or meta-commentary."
    )
    
    def __init__(self):
        """Initialize the PromptBuilder."""
        pass
    
    def build(
        self,
        template_name: str,
        template_content: str,
        context: GenerationContext,
    ) -> Tuple[str, str]:
        """
        Build structured LLM prompt from GenerationContext.
        
        Args:
            template_name: Name of the template (e.g., "tech-stack.md")
            template_content: Full template content with section markers
            context: GenerationContext with all input data
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        
        System prompt includes all five required instruction strings (Requirements 1.5, 10.1-10.4):
        - Fill every section independently
        - Write N/A for absent information
        - Write [NOT FOUND] for expected-but-absent fields
        - No content repeated across sections
        - Output only final Markdown, no preamble
        
        User prompt includes all required context fields (Requirement 1.4):
        - Template section schema
        - Source document content (filtered)
        - Code facts (JSON)
        - Existing steering content (truncated)
        - DeltaReport (if drift_correction or update use case)
        - User intent (if provided)
        - Previously generated file summaries
        
        Requirements: 1.4, 1.5, 7.3, 7.5, 10.1, 10.2, 10.3, 10.4
        """
        logger.info(f"Building prompt for template: {template_name}")
        
        # Build system prompt with all required instructions
        system_prompt = self._build_system_prompt(template_name, context.use_case)
        
        # Build user prompt with all context fields
        user_prompt = self._build_user_prompt(
            template_name, template_content, context
        )
        
        return system_prompt, user_prompt
    
    def build_simplified(
        self,
        template_name: str,
        template_content: str,
        context: GenerationContext,
    ) -> Tuple[str, str]:
        """
        Build simplified prompt for retry on empty/malformed response.
        
        The simplified prompt is more direct and concise, used when the initial
        generation attempt produces empty or malformed output.
        
        Args:
            template_name: Name of the template
            template_content: Full template content
            context: GenerationContext with all input data
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        
        Requirement: 6.5 (retry mechanism)
        """
        logger.info(f"Building simplified prompt for template: {template_name}")
        
        # Simplified system prompt
        system_prompt = f"""You are a technical documentation generator.

Generate a complete {template_name} steering file in Markdown format.

CRITICAL RULES:
1. Output ONLY the Markdown content - no preamble, no explanation
2. Fill ALL sections with relevant content
3. Use 'N/A' if information is genuinely absent
4. Do NOT leave any section empty
5. Do NOT repeat content across sections

Begin your response with the first Markdown heading."""
        
        # Simplified user prompt - focus on essential context only
        user_prompt_parts = [
            f"# Task: Generate {template_name}",
            "",
            "## Template Structure",
            "```markdown",
            template_content[:1000],  # First 1000 chars of template
            "```",
            "",
        ]
        
        # Include code facts (most essential context)
        if context.code_facts:
            code_facts_json = json.dumps(context.code_facts.to_json_dict(), indent=2)
            user_prompt_parts.extend([
                "## Codebase Facts",
                "```json",
                code_facts_json,
                "```",
                "",
            ])
        
        # Include source docs if present (truncated)
        if context.source_docs:
            user_prompt_parts.append("## Source Documents")
            for doc in context.source_docs[:2]:  # Max 2 docs
                user_prompt_parts.extend([
                    f"### {doc.file_path.name}",
                    doc.content[:500],  # First 500 chars
                    "",
                ])
        
        user_prompt_parts.append("Generate the complete steering file now:")
        
        user_prompt = "\n".join(user_prompt_parts)
        
        return system_prompt, user_prompt
    
    def _build_system_prompt(
        self,
        template_name: str,
        use_case: str,
    ) -> str:
        """
        Build system prompt with all required instruction strings.
        
        Args:
            template_name: Name of the template
            use_case: The workflow use case
        
        Returns:
            System prompt string
        
        Requirements: 1.5, 10.1, 10.2, 10.3, 10.4
        """
        prompt_parts = [
            "You are an expert technical documentation generator specializing in software project steering files.",
            "",
            f"Your task is to generate a complete {template_name} steering file based on the provided context.",
            "",
            "# Instructions",
            "",
            f"1. {self.INSTRUCTION_FILL_INDEPENDENTLY}",
            "",
            f"2. {self.INSTRUCTION_NA_FOR_ABSENT}",
            "",
            f"3. {self.INSTRUCTION_NOT_FOUND_FOR_EXPECTED}",
            "",
            f"4. {self.INSTRUCTION_NO_REPETITION}",
            "",
            f"5. {self.INSTRUCTION_MARKDOWN_ONLY}",
            "",
        ]
        
        # Add use-case-specific instructions
        if use_case in {"drift_correction", "update"}:
            prompt_parts.extend([
                "# Additional Context",
                "",
                "You are updating an existing steering file. A delta report is provided showing:",
                "- Divergences between design documents and codebase",
                "- Drifts between existing steering files and codebase",
                "- Conflicts between steering files and design documents",
                "",
                "When conflicts exist, prefer design documents as the source of truth unless user intent specifies otherwise.",
                "",
            ])
        
        if use_case == "pivot":
            prompt_parts.extend([
                "# User Intent",
                "",
                "A user intent document is provided that describes desired changes or new direction.",
                "Prioritize the user intent over existing documentation when they conflict.",
                "",
            ])
        
        return "\n".join(prompt_parts)
    
    def _build_user_prompt(
        self,
        template_name: str,
        template_content: str,
        context: GenerationContext,
    ) -> str:
        """
        Build user prompt with all required context fields.
        
        Args:
            template_name: Name of the template
            template_content: Full template content
            context: GenerationContext with all input data
        
        Returns:
            User prompt string
        
        Requirement: 1.4
        """
        prompt_parts = [
            f"# Generate: {template_name}",
            "",
            "## Template Structure",
            "",
            "Fill the following template with appropriate content:",
            "",
            "```markdown",
            template_content,
            "```",
            "",
        ]
        
        # Include source documents (Requirement 1.4)
        if context.source_docs:
            prompt_parts.extend([
                "## Source Documents",
                "",
                "The following source documents provide context for this project:",
                "",
            ])
            
            for doc in context.source_docs:
                prompt_parts.extend([
                    f"### Document: {doc.file_path.name}",
                    "",
                    doc.content,
                    "",
                    "---",
                    "",
                ])
        
        # Include code facts (Requirement 1.4)
        if context.code_facts:
            code_facts_json = json.dumps(context.code_facts.to_json_dict(), indent=2)
            prompt_parts.extend([
                "## Codebase Analysis",
                "",
                "The following structured facts were extracted from the codebase:",
                "",
                "```json",
                code_facts_json,
                "```",
                "",
            ])
        
        # Include existing steering content (Requirement 1.4)
        if context.existing_steering:
            prompt_parts.extend([
                "## Existing Steering Files",
                "",
                "The following steering files already exist:",
                "",
            ])
            
            for filename, content in context.existing_steering.items():
                prompt_parts.extend([
                    f"### {filename}",
                    "",
                    "```markdown",
                    content,
                    "```",
                    "",
                ])
        
        # Include delta report for drift correction (Requirements 7.3, 7.5)
        if context.delta and context.use_case in {"drift_correction", "update"}:
            prompt_parts.extend([
                "## Delta Report",
                "",
                "The following structural differences were detected:",
                "",
            ])
            
            if context.delta.doc_vs_code:
                prompt_parts.extend([
                    "### Design Documents vs. Codebase",
                    "",
                ])
                for item in context.delta.doc_vs_code:
                    prompt_parts.append(f"- {item}")
                prompt_parts.append("")
            
            if context.delta.steering_vs_code:
                prompt_parts.extend([
                    "### Steering Files vs. Codebase",
                    "",
                ])
                for item in context.delta.steering_vs_code:
                    prompt_parts.append(f"- {item}")
                prompt_parts.append("")
            
            if context.delta.steering_vs_docs:
                prompt_parts.extend([
                    "### Steering Files vs. Design Documents",
                    "",
                ])
                for item in context.delta.steering_vs_docs:
                    prompt_parts.append(f"- {item}")
                prompt_parts.append("")
            
            if context.delta.missing_in_all:
                prompt_parts.extend([
                    "### Missing Information",
                    "",
                ])
                for item in context.delta.missing_in_all:
                    prompt_parts.append(f"- {item}")
                prompt_parts.append("")
        
        # Include user intent (Requirement 1.4)
        if context.user_intent:
            prompt_parts.extend([
                "## User Intent",
                "",
                "The user has provided the following intent document:",
                "",
                context.user_intent,
                "",
            ])
        
        # Include previously generated summaries (Requirement 1.4)
        if context.previously_generated_summaries:
            prompt_parts.extend([
                "## Previously Generated Files (Summaries)",
                "",
                "The following files were generated earlier in this run:",
                "",
            ])
            
            for filename, summary in context.previously_generated_summaries.items():
                prompt_parts.extend([
                    f"### {filename}",
                    "",
                    summary,
                    "",
                ])
        
        # Include detected debt facts for technical-debt.md (Requirements 9.2, 9.3, 9.4)
        if context.debt_facts is not None:
            import json as _json
            prompt_parts.extend([
                "## Detected Debt Facts",
                "",
                "The following debt items were detected by static analysis:",
                "",
                "```json",
                _json.dumps(context.debt_facts.to_json_dict(), indent=2),
                "```",
                "",
            ])

        # Final instruction
        prompt_parts.extend([
            "---",
            "",
            f"Now generate the complete {template_name} file following the template structure and instructions above.",
            "",
            "Begin your response with the first Markdown heading:",
        ])
        
        return "\n".join(prompt_parts)
