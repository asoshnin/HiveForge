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

Requirements: 7.1-7.8, 12.1-12.5
"""

import logging
from typing import Dict, Any, List, Optional

from ..knowledge_base import KnowledgeBase
from ..models import GapAnalysisResult, Question
from ..response_cache import ResponseCache

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
    
    Attributes:
        knowledge_base: KnowledgeBase with parsed documents and code analysis
        gap_analysis: GapAnalysisResult identifying missing information
        research_enabled: Whether web research is enabled
        interactive: Whether to ask user questions (vs non-interactive mode)
        response_cache: Optional cache for LLM responses
        
    Requirements: 7.1-7.8, 12.1-12.5
    """
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        gap_analysis: GapAnalysisResult,
        research_enabled: bool = False,
        interactive: bool = True,
        response_cache: Optional[ResponseCache] = None
    ):
        """
        Initialize the steering assistant.
        
        Args:
            knowledge_base: KnowledgeBase with parsed content
            gap_analysis: GapAnalysisResult with identified gaps
            research_enabled: Whether to enable web research (default: False)
            interactive: Whether to ask user questions (default: True)
            response_cache: Optional ResponseCache for caching LLM responses
            
        Requirements: 7.6, 7.8, 12.4
        """
        self.knowledge_base = knowledge_base
        self.gap_analysis = gap_analysis
        self.research_enabled = research_enabled
        self.interactive = interactive
        self.response_cache = response_cache or ResponseCache()
        
        # Track gathered information
        self.gathered_info: Dict[str, Any] = {}
        
        # Track research results
        self.research_results: List[ResearchResult] = []
    
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
