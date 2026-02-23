"""
Steering Assistant Agent for HiveForge.

This module implements the SteeringAssistant class that conducts token-efficient
conversations with users to gather missing information for steering file generation.

Key Features:
- Question batching (max 8 per batch)
- Token-efficient LLM prompting (max 4000 tokens knowledge base content)
- Response caching to avoid redundant API calls
- Optional web research functionality
- Interactive and non-interactive modes
- LLM-based steering file generation with fallback to [INFERRED] markers

Requirements: 7.1-7.8, 12.1-12.5, P0-2
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..knowledge_base import KnowledgeBase
from ..models import GapAnalysisResult, Question
from ..response_cache import ResponseCache
from ..llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class QuestionBatch:
    """
    Represents a batch of related questions.
    
    Questions are grouped by template or topic for efficient conversation flow.
    
    Attributes:
        questions: List of questions in this batch
        template_name: Name of the template these questions relate to
        batch_number: Sequential batch number
    """
    
    def __init__(
        self,
        questions: List[Question],
        template_name: str,
        batch_number: int
    ):
        """
        Initialize a question batch.
        
        Args:
            questions: List of questions in this batch
            template_name: Name of the template
            batch_number: Sequential batch number
        """
        self.questions = questions
        self.template_name = template_name
        self.batch_number = batch_number


class ResearchResult:
    """
    Result from web research for a topic.
    
    Attributes:
        topic: The topic that was researched
        findings: List of findings from research
        sources: List of source URLs
        approved: Whether user approved using these findings
    """
    
    def __init__(
        self,
        topic: str,
        findings: List[str],
        sources: List[str],
        approved: bool = False
    ):
        """
        Initialize research result.
        
        Args:
            topic: The topic that was researched
            findings: List of findings
            sources: List of source URLs
            approved: Whether user approved the findings
        """
        self.topic = topic
        self.findings = findings
        self.sources = sources
        self.approved = approved


class SteeringAssistant:
    """
    Conducts token-efficient conversations to gather missing information.
    
    The SteeringAssistant orchestrates the conversation flow with users,
    batching questions for efficiency, limiting token usage, and optionally
    performing web research to fill gaps in knowledge.
    
    Also provides LLM-based steering file generation with automatic fallback
    to [INFERRED] markers when LLM is unavailable.
    
    Attributes:
        knowledge_base: KnowledgeBase with parsed documents and code analysis
        gap_analysis: GapAnalysisResult identifying missing information
        research_enabled: Whether web research is enabled
        interactive: Whether to ask user questions (vs non-interactive mode)
        response_cache: Optional cache for LLM responses
        project_root: Path to project root directory
        llm_provider: LLMProvider for LLM calls
        generated_files: List of recently generated file contents (for context)
        
    Requirements: 7.1-7.8, 12.1-12.5, P0-2
    """
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        gap_analysis: GapAnalysisResult,
        research_enabled: bool = False,
        interactive: bool = True,
        response_cache: Optional[ResponseCache] = None,
        project_root: Optional[Path] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        """
        Initialize the steering assistant.
        
        Args:
            knowledge_base: KnowledgeBase with parsed content
            gap_analysis: GapAnalysisResult with identified gaps
            research_enabled: Whether to enable web research (default: False)
            interactive: Whether to ask user questions (default: True)
            response_cache: Optional ResponseCache for caching LLM responses
            project_root: Path to project root (for template loading)
            llm_provider: Optional LLMProvider for LLM calls
            
        Requirements: 7.6, 7.8, 12.4, P0-2
        """
        self.knowledge_base = knowledge_base
        self.gap_analysis = gap_analysis
        self.research_enabled = research_enabled
        self.interactive = interactive
        self.response_cache = response_cache or ResponseCache()
        self.project_root = project_root or Path.cwd()
        self.llm_provider = llm_provider
        
        # Track gathered information
        self.gathered_info: Dict[str, Any] = {}
        
        # Track research results
        self.research_results: List[ResearchResult] = []
        
        # Track generated files for context (last 3 files)
        self.generated_files: List[str] = []
    
    def conduct_conversation(
        self,
        max_questions_per_batch: int = 8
    ) -> Dict[str, Any]:
        """
        Run token-efficient conversation with question batching.
        
        This method orchestrates the entire conversation flow:
        1. Present extracted information for confirmation
        2. Batch questions (max 8 per batch)
        3. Ask batched questions with context
        4. Optionally perform web research for critical gaps
        5. Validate responses and gather information
        
        Args:
            max_questions_per_batch: Maximum questions per batch (default: 8)
            
        Returns:
            Dictionary of gathered information keyed by template and section
            
        Requirements: 7.1, 7.2, 7.3, 7.5, 7.6
        """
        logger.info("Starting conversation to gather missing information")
        
        # Step 1: Present extracted information for confirmation (Req 7.1)
        if self.interactive:
            self._present_extracted_info()
        
        # Step 2: Check if we're in non-interactive mode (Req 7.6)
        if not self.interactive:
            logger.info("Non-interactive mode: using only parsed artifacts")
            return self._gather_from_knowledge_base()
        
        # Step 3: Batch questions (Req 7.2)
        batches = self.batch_questions(
            self.gap_analysis.questions,
            max_per_batch=max_questions_per_batch
        )
        
        logger.info(f"Created {len(batches)} question batches")
        
        # Step 4: Process each batch
        for batch in batches:
            self._process_batch(batch)
        
        # Step 5: Optionally perform web research for remaining gaps (Req 12.1-12.5)
        if self.research_enabled:
            self._perform_research()
        
        logger.info("Conversation complete")
        return self.gathered_info
    
    def _present_extracted_info(self) -> None:
        """
        Present extracted information for user confirmation.
        
        Shows what information was successfully extracted from documents
        and code analysis before asking questions.
        
        Requirements: 7.1
        """
        logger.info("Presenting extracted information for confirmation")
        
        print("\n" + "="*70)
        print("EXTRACTED INFORMATION")
        print("="*70)
        
        # Show complete sections
        if self.gap_analysis.complete_sections:
            print("\n✓ Successfully extracted:")
            for template_name, sections in self.gap_analysis.complete_sections.items():
                print(f"  • {template_name}: {', '.join(sections)}")
        
        # Show ambiguous sections
        if self.gap_analysis.ambiguous_sections:
            print("\n⚠ Found but needs clarification:")
            for template_name, sections in self.gap_analysis.ambiguous_sections.items():
                print(f"  • {template_name}: {', '.join(sections)}")
        
        # Show missing sections
        if self.gap_analysis.missing_sections:
            print("\n✗ Missing information:")
            for template_name, sections in self.gap_analysis.missing_sections.items():
                print(f"  • {template_name}: {', '.join(sections)}")
        
        print("\n" + "="*70)
        print()
    
    def _gather_from_knowledge_base(self) -> Dict[str, Any]:
        """
        Gather information from knowledge base without user interaction.
        
        Used in non-interactive mode to extract as much information as
        possible from parsed artifacts and code analysis.
        
        Returns:
            Dictionary of gathered information
            
        Requirements: 7.6
        """
        gathered = {}
        
        # Extract information from complete sections
        for template_name, sections in self.gap_analysis.complete_sections.items():
            if template_name not in gathered:
                gathered[template_name] = {}
            
            for section in sections:
                # Get relevant content for this section
                content = self.knowledge_base.get_relevant_content(
                    template_name,
                    max_tokens=4000
                )
                
                # Extract section-specific content
                section_content = self.knowledge_base.extract_section(section)
                if section_content:
                    gathered[template_name][section] = section_content
                else:
                    gathered[template_name][section] = content[:500]  # Use first 500 chars
        
        return gathered
    
    def batch_questions(
        self,
        questions: List[Question],
        max_per_batch: int = 8
    ) -> List[QuestionBatch]:
        """
        Group related questions with size limits.
        
        Questions are batched by template name to maintain context and
        limited to max_per_batch to avoid overwhelming the user.
        
        Args:
            questions: List of questions to batch
            max_per_batch: Maximum questions per batch (default: 8)
            
        Returns:
            List of QuestionBatch objects
            
        Requirements: 7.2
        """
        # Group questions by template
        by_template: Dict[str, List[Question]] = {}
        for question in questions:
            if question.template_name not in by_template:
                by_template[question.template_name] = []
            by_template[question.template_name].append(question)
        
        # Create batches respecting max_per_batch limit
        batches = []
        batch_number = 1
        
        for template_name, template_questions in by_template.items():
            # Split into chunks of max_per_batch
            for i in range(0, len(template_questions), max_per_batch):
                batch_questions = template_questions[i:i + max_per_batch]
                batches.append(QuestionBatch(
                    questions=batch_questions,
                    template_name=template_name,
                    batch_number=batch_number
                ))
                batch_number += 1
        
        return batches
    
    def _process_batch(self, batch: QuestionBatch) -> None:
        """
        Process a single batch of questions.
        
        Presents questions with context, collects answers, validates responses,
        and stores gathered information.
        
        Args:
            batch: QuestionBatch to process
            
        Requirements: 7.3, 7.4, 7.7, 7.8
        """
        logger.info(
            f"Processing batch {batch.batch_number} for {batch.template_name} "
            f"({len(batch.questions)} questions)"
        )
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch.batch_number}: {batch.template_name.upper()}")
        print(f"{'='*70}\n")
        
        # Get relevant knowledge base content (token-limited) (Req 7.7)
        context = self.knowledge_base.get_relevant_content(
            batch.template_name,
            max_tokens=4000
        )
        
        # Process each question in the batch
        for i, question in enumerate(batch.questions, 1):
            self._ask_question(question, i, len(batch.questions), context)
    
    def _ask_question(
        self,
        question: Question,
        question_num: int,
        total_questions: int,
        context: str
    ) -> None:
        """
        Ask a single question and collect the answer.
        
        Args:
            question: Question to ask
            question_num: Current question number in batch
            total_questions: Total questions in batch
            context: Relevant context from knowledge base
            
        Requirements: 7.3, 7.4, 7.8
        """
        # Check cache first (Req 7.8)
        cached_response = self.response_cache.get(question.question_text)
        if cached_response:
            logger.info(f"Using cached response for: {question.question_text[:50]}...")
            self._store_answer(question, cached_response)
            return
        
        # Present question with context (Req 7.3)
        print(f"Q{question_num}/{total_questions}: {question.question_text}")
        if question.context:
            print(f"   Context: {question.context}")
        print()
        
        # Get user input
        answer = input("   Answer: ").strip()
        
        # Validate response format (Req 7.4)
        while not self._validate_response(answer, question):
            print("   ⚠ Please provide a more detailed answer.")
            answer = input("   Answer: ").strip()
        
        # Cache the response (Req 7.8)
        self.response_cache.set(
            question.question_text,
            answer,
            metadata={
                'template': question.template_name,
                'section': question.section_name
            }
        )
        
        # Store the answer
        self._store_answer(question, answer)
        print()
    
    def _validate_response(self, response: str, question: Question) -> bool:
        """
        Validate response format and content.
        
        Args:
            response: User's response
            question: Question that was asked
            
        Returns:
            True if response is valid, False otherwise
            
        Requirements: 7.4
        """
        # Basic validation: non-empty and minimum length
        if not response or len(response) < 3:
            return False
        
        # Check for placeholder-like responses (case-insensitive)
        response_lower = response.lower()
        placeholder_indicators = ['todo', 'tbd', 'n/a', '...', 'idk', "don't know"]
        if any(indicator in response_lower for indicator in placeholder_indicators):
            return False
        
        return True
    
    def _store_answer(self, question: Question, answer: str) -> None:
        """
        Store gathered answer in the appropriate structure.
        
        Args:
            question: Question that was answered
            answer: User's answer
        """
        template_name = question.template_name
        section_name = question.section_name
        
        if template_name not in self.gathered_info:
            self.gathered_info[template_name] = {}
        
        self.gathered_info[template_name][section_name] = answer
    
    def _perform_research(self) -> None:
        """
        Perform web research for critical missing information.
        
        Only called when research_enabled is True. Offers to search for
        relevant information and presents findings for user approval.
        
        Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
        """
        logger.info("Web research enabled, checking for critical gaps")
        
        # Identify critical missing information
        critical_gaps = self._identify_critical_gaps()
        
        if not critical_gaps:
            logger.info("No critical gaps requiring research")
            return
        
        print(f"\n{'='*70}")
        print("WEB RESEARCH")
        print(f"{'='*70}\n")
        print("The following critical information is missing:")
        for gap in critical_gaps:
            print(f"  • {gap['template']}: {gap['section']}")
        print()
        
        # Ask if user wants to perform research (Req 12.5)
        response = input("Would you like to search for this information online? (y/n): ").strip().lower()
        if response != 'y':
            logger.info("User declined web research")
            return
        
        # Perform research for each gap
        for gap in critical_gaps:
            result = self.research_topic(gap['topic'])
            if result and result.findings:
                self.research_results.append(result)
                
                # If approved, store in gathered_info
                if result.approved:
                    self._store_answer(
                        Question(
                            template_name=gap['template'],
                            section_name=gap['section'],
                            question_text="",
                            context="",
                            priority=0
                        ),
                        "\n".join(result.findings)
                    )
    
    def _identify_critical_gaps(self) -> List[Dict[str, str]]:
        """
        Identify critical gaps that could benefit from web research.
        
        Returns:
            List of dictionaries with template, section, and topic information
            
        Requirements: 12.1
        """
        critical_gaps = []
        
        # Focus on high-priority templates and specific sections
        critical_sections = {
            'tech-stack': ['Rationale', 'Key Dependencies'],
            'architecture': ['Scalability Considerations', 'Key Decisions'],
            'api-standards': ['Error Handling', 'Authentication'],
            'db-standards': ['Migration Strategy'],
        }
        
        for template_name, sections in critical_sections.items():
            if template_name in self.gap_analysis.missing_sections:
                missing = self.gap_analysis.missing_sections[template_name]
                for section in sections:
                    if section in missing:
                        critical_gaps.append({
                            'template': template_name,
                            'section': section,
                            'topic': f"{template_name} {section}"
                        })
        
        return critical_gaps
    
    def research_topic(self, topic: str) -> Optional[ResearchResult]:
        """
        Perform web research for a specific topic.
        
        Searches for relevant information and presents findings to user
        for approval before using them.
        
        Args:
            topic: Topic to research
            
        Returns:
            ResearchResult if research was successful, None otherwise
            
        Requirements: 12.2, 12.3
        """
        logger.info(f"Researching topic: {topic}")
        
        print(f"\n🔍 Researching: {topic}")
        print("   (This is a placeholder - actual web search would be implemented here)")
        
        # Placeholder for actual web search implementation
        # In real implementation, this would call a web search API
        findings = [
            f"Finding 1 about {topic}",
            f"Finding 2 about {topic}",
            f"Finding 3 about {topic}",
        ]
        sources = [
            "https://example.com/source1",
            "https://example.com/source2",
        ]
        
        # Present findings for approval (Req 12.3)
        print("\n   Research findings:")
        for i, finding in enumerate(findings, 1):
            print(f"   {i}. {finding}")
        print("\n   Sources:")
        for source in sources:
            print(f"   - {source}")
        print()
        
        # Get user approval
        response = input("   Use these findings? (y/n): ").strip().lower()
        approved = response == 'y'
        
        if approved:
            logger.info(f"User approved research findings for: {topic}")
        else:
            logger.info(f"User rejected research findings for: {topic}")
        
        return ResearchResult(
            topic=topic,
            findings=findings,
            sources=sources,
            approved=approved
        )

    # ========================================================================
    # LLM-Based File Generation Methods (P0-2)
    # ========================================================================
    
    async def generate_file(
        self,
        filename: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate steering file content using LLM synthesis.
        
        This method loads the template, strips frontmatter, sends to LLM
        with context, and returns populated markdown. Falls back to
        [INFERRED] markers if LLM is unavailable.
        
        Args:
            filename: Name of steering file (e.g., 'tech-stack.md')
            context: Knowledge base context including code analysis
        
        Returns:
            Populated markdown string (never empty)
        
        Raises:
            FileNotFoundError: If template not found
            
        Requirements: P0-2
        """
        try:
            # Step 1: Load raw template with frontmatter
            raw_template = self._get_raw_template(filename)
            
            # Step 2: Strip YAML frontmatter
            template_content = self._strip_frontmatter(raw_template)
            
            # Step 3: Check if LLM is available
            if self.llm_provider and self.llm_provider.is_available():
                # Step 4: Build LLM prompt
                system_prompt = self._get_system_prompt()
                user_prompt = self._build_llm_prompt(
                    filename,
                    template_content,
                    context
                )
                
                # Step 5: Call LLM
                response = await self.llm_provider.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=2000,
                    temperature=0.1,
                    json_mode=False
                )
                
                if response:
                    logger.info(
                        f"Generated {filename}: {len(response)} chars"
                    )
                    self._track_generated_file(response)
                    return response
            
            # Step 6: Fallback to [INFERRED] markers
            logger.warning(
                f"LLM unavailable for {filename}, using [INFERRED] markers"
            )
            fallback_content = self._apply_inferred_markers(template_content)
            return fallback_content
            
        except Exception as e:
            logger.error(
                f"Error generating {filename}: {type(e).__name__}: {e}"
            )
            # Return template with [INFERRED] markers as last resort
            try:
                raw_template = self._get_raw_template(filename)
                template_content = self._strip_frontmatter(raw_template)
                return self._apply_inferred_markers(template_content)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return f"[GENERATION FAILED — please fill manually]\n\nFile: {filename}"
    
    def _get_raw_template(self, template_name: str) -> str:
        """
        Load raw template content including frontmatter.
        
        Args:
            template_name: Template filename (e.g., 'tech-stack.md')
        
        Returns:
            Complete template file content as string
        
        Raises:
            FileNotFoundError: If template not found
            ValueError: If template_name is invalid
            
        Requirements: P0-2a
        """
        if not template_name:
            raise ValueError("template_name cannot be empty")
        
        template_path = self._resolve_template_path(template_name)
        
        if not template_path.exists():
            available = self._list_available_templates()
            raise FileNotFoundError(
                f"Template {template_name} not found at {template_path}. "
                f"Available: {', '.join(available)}"
            )
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise FileNotFoundError(
                f"Cannot read template {template_path}: {e}"
            )
    
    def _strip_frontmatter(self, content: str) -> str:
        """
        Remove YAML frontmatter from template.
        
        Frontmatter is between first and second '---' delimiters.
        
        Args:
            content: Template content with frontmatter
            
        Returns:
            Content without frontmatter
            
        Requirements: P0-2
        """
        lines = content.split('\n')
        
        if not lines or lines[0].strip() != '---':
            return content  # No frontmatter
        
        # Find closing ---
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                return '\n'.join(lines[i+1:])
        
        return content  # Malformed frontmatter, return as-is
    
    def _build_llm_prompt(
        self,
        filename: str,
        template_content: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive LLM prompt with context.
        
        Includes:
        - Template with placeholders
        - Code analysis summary
        - Last 3 generated files (for consistency)
        
        Args:
            filename: Name of file being generated
            template_content: Template content without frontmatter
            context: Project context dictionary
            
        Returns:
            Formatted prompt string
            
        Requirements: P0-2
        """
        recent_files = '\n\n'.join(self.generated_files[-3:])
        
        prompt = f"""# Task: Generate Steering File

## File: {filename}

## Template (replace all {{placeholders}} with real content):
{template_content}

## Project Context:
{self._format_context(context)}

## Previously Generated Files (for consistency):
{recent_files if recent_files else '(none yet)'}

## Instructions:
1. Replace ALL {{placeholder}} text with real, specific content
2. Use the project context to make accurate, detailed entries
3. Maintain consistency with previously generated files
4. Output ONLY the final Markdown (no explanations)
5. Never leave {{placeholder}} text in your output
"""
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format code analysis context for LLM.
        
        Args:
            context: Project context dictionary
            
        Returns:
            Formatted context string
            
        Requirements: P0-2
        """
        parts = []
        
        if 'languages' in context:
            parts.append(f"Languages: {', '.join(context['languages'])}")
        
        if 'dependencies' in context:
            deps = context['dependencies'][:10]  # Limit to 10
            parts.append(f"Key Dependencies: {', '.join(deps)}")
        
        if 'architecture' in context:
            parts.append(f"Architecture: {context['architecture']}")
        
        if 'mcp_tools' in context:
            tools = context['mcp_tools'][:5]  # Limit to 5
            parts.append(f"MCP Tools: {', '.join(tools)}")
        
        if 'project_type' in context:
            parts.append(f"Project Type: {context['project_type']}")
        
        return '\n'.join(parts)
    
    def _get_system_prompt(self) -> str:
        """
        System prompt for LLM.
        
        Returns:
            System prompt string
            
        Requirements: P0-2
        """
        return (
            "You are a technical documentation expert generating a KIRO "
            "steering file. Your task is to populate templates with "
            "accurate, project-specific content. Replace ALL {placeholder} "
            "text with real content. Output ONLY the final Markdown. "
            "Never leave {placeholder} text in your output."
        )
    
    def _apply_inferred_markers(self, template_content: str) -> str:
        """
        Replace placeholders with [INFERRED] markers.
        
        Pattern: {placeholder} → [INFERRED: placeholder]
        
        Args:
            template_content: Template content with placeholders
            
        Returns:
            Content with [INFERRED] markers
            
        Requirements: P0-2
        """
        def replace_placeholder(match):
            placeholder = match.group(1)
            return f"[INFERRED: {placeholder}]"
        
        return re.sub(r'\{([^}]+)\}', replace_placeholder, template_content)
    
    def _track_generated_file(self, content: str) -> None:
        """
        Track generated file for context in subsequent files.
        
        Keeps last 3 files for context to prevent token blowup.
        
        Args:
            content: Generated file content
            
        Requirements: P0-2
        """
        # Keep last 3 files for context (first 500 chars each)
        self.generated_files.append(content[:500])
        if len(self.generated_files) > 3:
            self.generated_files.pop(0)
    
    def _resolve_template_path(self, template_name: str) -> Path:
        """
        Resolve template path (handles variants).
        
        Tries project-type-specific variant first, then falls back
        to generic template.
        
        Args:
            template_name: Template filename
            
        Returns:
            Path to template file
            
        Requirements: P0-2
        """
        # Try to get project type from knowledge base
        project_type = None
        if hasattr(self.knowledge_base, 'code_analysis'):
            project_type = getattr(self.knowledge_base.code_analysis, 'project_type', None)
        
        # Try project-type-specific variant first
        if project_type:
            variant_path = (
                self.project_root / 'hiveforge' / 'templates' / 'steering' /
                f"{template_name.replace('.md', '')}.{project_type}.md"
            )
            if variant_path.exists():
                return variant_path
        
        # Fall back to generic template
        generic_path = (
            self.project_root / 'hiveforge' / 'templates' / 'steering' / template_name
        )
        return generic_path
    
    def _list_available_templates(self) -> List[str]:
        """
        List available template files.
        
        Returns:
            List of template filenames
            
        Requirements: P0-2
        """
        template_dir = self.project_root / 'hiveforge' / 'templates' / 'steering'
        if not template_dir.exists():
            return []
        
        return [f.name for f in template_dir.glob('*.md')]
