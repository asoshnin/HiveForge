"""
Context assembler for the LLM-Primary Steering Synthesis pipeline.

This module enforces strict per-template token budgets and produces
GenerationContext objects for each steering file template.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import json
import logging
from typing import Dict, List, Optional

from .models import (
    CodeAnalysisFacts,
    DebtAnalysisResult,
    DeltaReport,
    GenerationContext,
    ParsedDocument,
    UseCase,
)

logger = logging.getLogger(__name__)


class ContextAssembler:
    """
    Assembles token-budgeted context for LLM prompt generation.
    
    The ContextAssembler filters and truncates input data to fit within strict
    token budgets, ensuring predictable LLM API costs and performance.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
    
    # Token budget constants (Requirements 4.1, 4.2)
    TOKEN_BUDGET = 8_000
    BUDGET_SOURCE_DOCS = 4_000
    BUDGET_CODE_FACTS = 2_000
    BUDGET_EXISTING_STEERING = 1_000
    BUDGET_PREV_GENERATED = 1_000
    
    # Template-specific keywords for relevance filtering (Requirement 4.3)
    TEMPLATE_KEYWORDS = {
        "project-vision.md": [
            "vision", "goal", "objective", "mission", "purpose", "problem",
            "solution", "user", "customer", "stakeholder", "metric", "success",
            "timeline", "roadmap", "milestone",
        ],
        "tech-stack.md": [
            "technology", "stack", "framework", "library", "language", "runtime",
            "database", "infrastructure", "dependency", "version", "tool",
            "package", "module", "platform",
        ],
        "architecture.md": [
            "architecture", "component", "module", "service", "layer", "pattern",
            "design", "structure", "diagram", "flow", "integration", "interface",
            "api", "endpoint", "system", "subsystem",
        ],
        "conventions.md": [
            "convention", "style", "naming", "format", "standard", "guideline",
            "rule", "practice", "pattern", "code", "documentation", "comment",
            "lint", "formatter",
        ],
        "agents.md": [
            "agent", "role", "responsibility", "capability", "permission",
            "boundary", "enclave", "delegation", "orchestration", "swarm",
            "coordination", "communication",
        ],
        "workflows.md": [
            "workflow", "process", "procedure", "step", "phase", "stage",
            "pipeline", "automation", "ci", "cd", "deployment", "build",
            "test", "release",
        ],
        "security.md": [
            "security", "authentication", "authorization", "permission", "access",
            "encryption", "vulnerability", "threat", "risk", "compliance",
            "audit", "privacy", "credential", "secret",
        ],
        "testing.md": [
            "test", "testing", "unit", "integration", "e2e", "property",
            "coverage", "assertion", "mock", "fixture", "suite", "runner",
            "framework", "validation",
        ],
        "technical-debt.md": [
            "debt", "technical debt", "refactor", "smell", "violation", "dry",
            "duplicate", "complexity", "coupling", "cohesion", "legacy",
            "todo", "fixme", "hack", "workaround", "performance", "risk",
        ],
    }
    
    def __init__(self):
        """Initialize the ContextAssembler."""
        pass
    
    def assemble(
        self,
        template_name: str,
        template_schema: List[str],
        use_case: UseCase,
        source_docs: List[ParsedDocument],
        code_facts: CodeAnalysisFacts,
        existing_steering: Dict[str, str],
        previously_generated: Dict[str, str],
        delta: Optional[DeltaReport],
        user_intent: Optional[str],
        debt_facts: Optional[DebtAnalysisResult] = None,
    ) -> GenerationContext:
        """
        Assemble token-budgeted context for a single template.
        
        Args:
            template_name: Name of the template (e.g., "tech-stack.md")
            template_schema: List of section names in the template
            use_case: The determined workflow use case
            source_docs: All parsed source documents
            code_facts: Structured code analysis facts
            existing_steering: Existing steering file contents (filename -> content)
            previously_generated: Previously generated files in this run (filename -> content)
            delta: Optional delta report for drift correction
            user_intent: Optional user intent document content
        
        Returns:
            GenerationContext with filtered and truncated content
        
        Process:
        1. Filter source docs by keyword relevance to template (Requirement 4.3)
        2. Extract rolling summaries from previously generated files (Requirement 4.4)
        3. Truncate sections if budget exceeded (Requirement 4.5):
           - Priority: previously_generated → existing_steering → code_facts
        4. Return GenerationContext struct (Requirement 4.6)
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
        """
        logger.info(f"Assembling context for template: {template_name}")
        
        # Filter source docs by relevance (Requirement 4.3)
        filtered_docs = self._filter_source_docs_by_relevance(
            template_name, source_docs
        )
        
        # Truncate source docs to budget
        truncated_docs = self._truncate_source_docs(
            filtered_docs, self.BUDGET_SOURCE_DOCS
        )
        
        # Extract rolling summaries from previously generated files (Requirement 4.4)
        summaries = self._extract_rolling_summaries(previously_generated)
        
        # For technical-debt.md: ensure cross-reference steering files are included
        # (Requirements 9.1, 9.2, 9.3, 9.4)
        if template_name == "technical-debt.md":
            cross_ref_keys = {"conventions.md", "qa-standards.md", "architecture.md"}
            # Merge cross-ref files into existing_steering view (don't mutate original)
            enriched_steering: Dict[str, str] = {}
            for key in cross_ref_keys:
                if key in existing_steering:
                    enriched_steering[key] = existing_steering[key]
                elif key in previously_generated:
                    enriched_steering[key] = previously_generated[key]
            # Add remaining existing steering (may be truncated below)
            for k, v in existing_steering.items():
                enriched_steering.setdefault(k, v)
        else:
            enriched_steering = existing_steering

        # Truncate sections if budget exceeded (Requirement 4.5)
        truncated_summaries = self._truncate_text_dict(
            summaries, self.BUDGET_PREV_GENERATED
        )
        truncated_existing = self._truncate_text_dict(
            enriched_steering, self.BUDGET_EXISTING_STEERING
        )
        
        # Code facts are already constrained to ≤2,000 tokens by design
        # (enforced in CodeAnalysisFacts.to_json_dict())
        
        # Log token usage
        total_tokens = self._estimate_total_tokens(
            truncated_docs,
            code_facts,
            truncated_existing,
            truncated_summaries,
            delta,
            user_intent,
        )
        logger.info(
            f"Context assembled for {template_name}: "
            f"~{total_tokens} tokens (budget: {self.TOKEN_BUDGET})"
        )
        
        if total_tokens > self.TOKEN_BUDGET:
            logger.warning(
                f"Context exceeds budget by ~{total_tokens - self.TOKEN_BUDGET} tokens. "
                f"Further truncation may be needed."
            )
        
        # Return GenerationContext (Requirement 4.6)
        return GenerationContext(
            template_name=template_name,
            use_case=use_case,
            source_docs=truncated_docs,
            code_facts=code_facts,
            existing_steering=truncated_existing,
            previously_generated_summaries=truncated_summaries,
            delta=delta,
            user_intent=user_intent,
            debt_facts=debt_facts,
        )
    
    def _filter_source_docs_by_relevance(
        self,
        template_name: str,
        source_docs: List[ParsedDocument],
    ) -> List[ParsedDocument]:
        """
        Filter source documents by keyword relevance to template.
        
        Args:
            template_name: Name of the template
            source_docs: All source documents
        
        Returns:
            Filtered list of relevant documents
        
        Requirement: 4.3
        """
        keywords = self.TEMPLATE_KEYWORDS.get(template_name, [])
        
        if not keywords:
            # No keywords defined for this template, return all docs
            logger.debug(f"No keywords defined for {template_name}, using all docs")
            return source_docs
        
        # Score each document by keyword matches
        scored_docs = []
        for doc in source_docs:
            content_lower = doc.content.lower()
            score = sum(1 for keyword in keywords if keyword in content_lower)
            scored_docs.append((score, doc))
        
        # Sort by score (descending) and return documents with score > 0
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        relevant_docs = [doc for score, doc in scored_docs if score > 0]
        
        logger.debug(
            f"Filtered {len(source_docs)} docs to {len(relevant_docs)} relevant docs "
            f"for {template_name}"
        )
        
        return relevant_docs if relevant_docs else source_docs
    
    def _truncate_source_docs(
        self,
        docs: List[ParsedDocument],
        budget: int,
    ) -> List[ParsedDocument]:
        """
        Truncate source documents to fit within token budget.
        
        Args:
            docs: List of documents to truncate
            budget: Token budget
        
        Returns:
            Truncated list of documents
        """
        if not docs:
            return []
        
        # Estimate tokens for each document (rough: 1 token ≈ 4 characters)
        total_tokens = 0
        truncated_docs = []
        
        for doc in docs:
            doc_tokens = len(doc.content) // 4
            
            if total_tokens + doc_tokens <= budget:
                # Include full document
                truncated_docs.append(doc)
                total_tokens += doc_tokens
            elif total_tokens < budget:
                # Partial inclusion - truncate content
                remaining_tokens = budget - total_tokens
                remaining_chars = remaining_tokens * 4
                
                truncated_content = doc.content[:remaining_chars] + "\n\n[TRUNCATED]"
                truncated_doc = ParsedDocument(
                    file_path=doc.file_path,
                    content=truncated_content,
                    metadata=doc.metadata,
                    parse_errors=doc.parse_errors,
                )
                truncated_docs.append(truncated_doc)
                total_tokens = budget
                break
            else:
                # Budget exhausted
                break
        
        if len(truncated_docs) < len(docs):
            logger.debug(
                f"Truncated {len(docs)} docs to {len(truncated_docs)} "
                f"to fit {budget} token budget"
            )
        
        return truncated_docs
    
    def _extract_rolling_summaries(
        self,
        previously_generated: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Extract rolling summaries from previously generated files.
        
        For each previously generated file, extract a concise summary
        (first 500 characters or first section) to provide cross-file context.
        
        Args:
            previously_generated: Previously generated files (filename -> content)
        
        Returns:
            Dictionary of summaries (filename -> summary)
        
        Requirement: 4.4
        """
        summaries = {}
        
        for filename, content in previously_generated.items():
            # Extract first 500 characters as summary
            summary = content[:500]
            
            # Try to end at a sentence boundary
            if len(content) > 500:
                last_period = summary.rfind(".")
                last_newline = summary.rfind("\n")
                cutoff = max(last_period, last_newline)
                
                if cutoff > 200:  # Only use boundary if it's not too early
                    summary = summary[:cutoff + 1]
                
                summary += "\n\n[...]"
            
            summaries[filename] = summary
        
        return summaries
    
    def _truncate_text_dict(
        self,
        text_dict: Dict[str, str],
        budget: int,
    ) -> Dict[str, str]:
        """
        Truncate a dictionary of text content to fit within token budget.
        
        Args:
            text_dict: Dictionary of text content (key -> text)
            budget: Token budget
        
        Returns:
            Truncated dictionary
        
        Requirement: 4.5
        """
        if not text_dict:
            return {}
        
        # Estimate tokens for each entry
        total_tokens = 0
        truncated_dict = {}
        
        for key, text in text_dict.items():
            text_tokens = len(text) // 4
            
            if total_tokens + text_tokens <= budget:
                # Include full text
                truncated_dict[key] = text
                total_tokens += text_tokens
            elif total_tokens < budget:
                # Partial inclusion - truncate text
                remaining_tokens = budget - total_tokens
                remaining_chars = remaining_tokens * 4
                
                truncated_text = text[:remaining_chars] + "\n\n[TRUNCATED]"
                truncated_dict[key] = truncated_text
                total_tokens = budget
                break
            else:
                # Budget exhausted
                break
        
        if len(truncated_dict) < len(text_dict):
            logger.debug(
                f"Truncated {len(text_dict)} entries to {len(truncated_dict)} "
                f"to fit {budget} token budget"
            )
        
        return truncated_dict
    
    def _estimate_total_tokens(
        self,
        docs: List[ParsedDocument],
        code_facts: CodeAnalysisFacts,
        existing_steering: Dict[str, str],
        summaries: Dict[str, str],
        delta: Optional[DeltaReport],
        user_intent: Optional[str],
    ) -> int:
        """
        Estimate total token count for all context components.
        
        Args:
            docs: Source documents
            code_facts: Code analysis facts
            existing_steering: Existing steering content
            summaries: Previously generated summaries
            delta: Optional delta report
            user_intent: Optional user intent
        
        Returns:
            Estimated total token count
        """
        total = 0
        
        # Source docs
        for doc in docs:
            total += len(doc.content) // 4
        
        # Code facts (serialize to JSON and estimate)
        code_facts_json = json.dumps(code_facts.to_json_dict())
        total += len(code_facts_json) // 4
        
        # Existing steering
        for text in existing_steering.values():
            total += len(text) // 4
        
        # Summaries
        for text in summaries.values():
            total += len(text) // 4
        
        # Delta report (if present)
        if delta:
            delta_text = "\n".join(
                delta.doc_vs_code
                + delta.steering_vs_code
                + delta.steering_vs_docs
                + delta.missing_in_all
            )
            total += len(delta_text) // 4
        
        # User intent (if present)
        if user_intent:
            total += len(user_intent) // 4
        
        return total



def _rolling_summary(content: str, max_chars: int = 500) -> str:
    """
    Extract a rolling summary from generated content.
    
    Used to provide cross-file context for subsequently generated files.
    
    Args:
        content: Full content of a generated file
        max_chars: Maximum characters for the summary
    
    Returns:
        Summary string (first max_chars with sentence boundary)
    """
    if len(content) <= max_chars:
        return content
    
    # Extract first max_chars
    summary = content[:max_chars]
    
    # Try to end at a sentence boundary
    last_period = summary.rfind(".")
    last_newline = summary.rfind("\n")
    cutoff = max(last_period, last_newline)
    
    if cutoff > 200:  # Only use boundary if it's not too early
        summary = summary[:cutoff + 1]
    
    summary += "\n\n[...]"
    
    return summary
