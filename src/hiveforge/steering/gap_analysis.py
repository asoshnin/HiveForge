"""
Gap Analysis Engine for Steering Assistant.

This module provides the GapAnalysisEngine class that identifies missing
information by comparing knowledge base content against template requirements.
"""

import re
from typing import Dict, List
from .knowledge_base import KnowledgeBase
from .models import Template, GapAnalysisResult, Question
from .templates import get_all_templates


class GapAnalysisEngine:
    """
    Identifies missing information by comparing knowledge base against templates.
    
    The GapAnalysisEngine analyzes the knowledge base content and determines
    which template sections are complete, missing, or ambiguous. It generates
    prioritized questions grouped by steering file to efficiently gather
    missing information.
    """
    
    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        templates: Dict[str, Template] = None
    ):
        """
        Initialize the gap analysis engine.
        
        Args:
            knowledge_base: KnowledgeBase containing parsed documents and code analysis
            templates: Optional dictionary of templates (defaults to all templates)
        """
        self.knowledge_base = knowledge_base
        self.templates = templates or get_all_templates()
    
    def analyze(self) -> GapAnalysisResult:
        """
        Perform gap analysis across all templates.
        
        Compares knowledge base content against template requirements and
        classifies each section as complete, missing, or ambiguous.
        
        Returns:
            GapAnalysisResult with classified sections and prioritized questions
        """
        result = GapAnalysisResult()
        
        # Sort templates by priority (project-vision and tech-stack first)
        sorted_templates = sorted(
            self.templates.items(),
            key=lambda x: x[1].priority
        )
        
        # Analyze each template
        for template_name, template in sorted_templates:
            self._analyze_template(template_name, template, result)
        
        # Sort questions by priority (based on template priority and section importance)
        result.questions.sort(key=lambda q: q.priority)
        
        return result
    
    def _analyze_template(
        self,
        template_name: str,
        template: Template,
        result: GapAnalysisResult
    ) -> None:
        """
        Analyze a single template and update the result.
        
        Args:
            template_name: Name of the template being analyzed
            template: Template definition
            result: GapAnalysisResult to update with findings
        """
        # Get relevant content for this template
        relevant_content = self.knowledge_base.get_relevant_content(
            template_name,
            max_tokens=4000
        )
        
        # Analyze each section
        for section in template.sections:
            classification = self._classify_section(
                template_name,
                section.name,
                section.placeholder_pattern,
                section.required,
                relevant_content
            )
            
            # Update result based on classification
            if classification == "complete":
                if template_name not in result.complete_sections:
                    result.complete_sections[template_name] = []
                result.complete_sections[template_name].append(section.name)
            
            elif classification == "missing":
                if template_name not in result.missing_sections:
                    result.missing_sections[template_name] = []
                result.missing_sections[template_name].append(section.name)
                
                # Generate question for missing section
                if section.required or self._is_important_section(section.name):
                    question = self._generate_question(
                        template_name,
                        template.priority,
                        section.name,
                        relevant_content
                    )
                    result.questions.append(question)
            
            elif classification == "ambiguous":
                if template_name not in result.ambiguous_sections:
                    result.ambiguous_sections[template_name] = []
                result.ambiguous_sections[template_name].append(section.name)
                
                # Generate clarification question for ambiguous section
                question = self._generate_clarification_question(
                    template_name,
                    template.priority,
                    section.name,
                    relevant_content
                )
                result.questions.append(question)
    
    def _classify_section(
        self,
        template_name: str,
        section_name: str,
        placeholder_pattern: str,
        required: bool,
        content: str
    ) -> str:
        """
        Classify a template section as complete, missing, or ambiguous.
        
        Args:
            template_name: Name of the template
            section_name: Name of the section
            placeholder_pattern: Regex pattern for placeholders
            required: Whether the section is required
            content: Relevant content from knowledge base
            
        Returns:
            Classification: "complete", "missing", or "ambiguous"
        """
        # Check if we have code analysis data for tech-related templates
        if template_name == "tech-stack":
            tech_stack = self.knowledge_base.get_tech_stack()
            if tech_stack:
                if section_name == "Backend" and tech_stack.backend_framework:
                    return "complete"
                elif section_name == "Frontend" and tech_stack.frontend_framework:
                    return "complete"
                elif section_name == "Database" and tech_stack.database:
                    return "complete"
                elif section_name == "Cache" and tech_stack.cache:
                    return "complete"
        
        elif template_name == "architecture":
            architecture = self.knowledge_base.get_architecture()
            if architecture:
                if section_name == "Component Responsibilities" and architecture.key_components:
                    return "complete"
        
        elif template_name == "conventions":
            conventions = self.knowledge_base.get_conventions()
            if conventions:
                if section_name == "Naming Conventions" and conventions.naming_style:
                    return "complete"
                elif section_name == "Code Style" and conventions.formatting:
                    return "complete"
        
        # Check if section exists in extracted content
        section_content = self.knowledge_base.extract_section(section_name)
        if section_content:
            # Check if it has substantial content (not just placeholders)
            if self._has_substantial_content(section_content, placeholder_pattern):
                return "complete"
            else:
                return "ambiguous"
        
        # Search for keywords related to the section
        keywords = self._get_section_keywords(template_name, section_name)
        if keywords:
            matches = sum(1 for keyword in keywords if keyword.lower() in content.lower())
            
            # If we found multiple keyword matches, content might be present but unclear
            if matches >= len(keywords) * 0.5:  # At least 50% of keywords found
                return "ambiguous"
        
        # No information found
        return "missing"
    
    def _has_substantial_content(self, content: str, placeholder_pattern: str) -> bool:
        """
        Check if content has substantial information (not just placeholders).
        
        Args:
            content: Section content to check
            placeholder_pattern: Regex pattern for placeholders
            
        Returns:
            True if content is substantial, False otherwise
        """
        # Remove markdown headers and whitespace
        text = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        text = text.strip()
        
        # Check if content is too short
        if len(text) < 20:
            return False
        
        # Check for placeholder patterns
        if placeholder_pattern:
            placeholders = re.findall(placeholder_pattern, text)
            # If more than 30% of content is placeholders, not substantial
            if placeholders and len(''.join(placeholders)) > len(text) * 0.3:
                return False
        
        # Check for common placeholder indicators
        placeholder_indicators = ['{', '}', '...', 'TODO', 'TBD', 'FIXME']
        indicator_count = sum(1 for indicator in placeholder_indicators if indicator in text)
        if indicator_count > 2:
            return False
        
        return True
    
    def _get_section_keywords(self, template_name: str, section_name: str) -> List[str]:
        """
        Get relevant keywords for a template section.
        
        Args:
            template_name: Name of the template
            section_name: Name of the section
            
        Returns:
            List of keywords to search for
        """
        # Define keywords for common sections
        keyword_map = {
            ("project-vision", "Elevator Pitch"): ["description", "purpose", "what", "who"],
            ("project-vision", "Problem Statement"): ["problem", "pain", "challenge", "issue"],
            ("project-vision", "Solution Overview"): ["solution", "approach", "how", "solve"],
            ("project-vision", "Target Users"): ["user", "customer", "audience", "persona"],
            ("project-vision", "Success Metrics"): ["metric", "kpi", "measure", "goal", "target"],
            ("tech-stack", "Backend"): ["backend", "server", "api", "language", "framework"],
            ("tech-stack", "Frontend"): ["frontend", "client", "ui", "react", "vue", "angular"],
            ("tech-stack", "Database"): ["database", "db", "postgres", "mongo", "mysql", "sql"],
            ("tech-stack", "Cache"): ["cache", "redis", "memcached"],
            ("architecture", "Component Responsibilities"): ["component", "service", "module", "layer"],
            ("architecture", "Data Flow"): ["flow", "data", "process", "pipeline"],
            ("conventions", "Naming Conventions"): ["naming", "camelCase", "snake_case", "PascalCase"],
            ("conventions", "Code Style"): ["style", "format", "indent", "line length"],
        }
        
        return keyword_map.get((template_name, section_name), [])
    
    def _is_important_section(self, section_name: str) -> bool:
        """
        Determine if a section is important enough to ask about even if not required.
        
        Args:
            section_name: Name of the section
            
        Returns:
            True if section is important, False otherwise
        """
        # These sections are important even if marked as optional
        important_sections = [
            "Rationale",
            "Component Responsibilities",
            "Error Handling",
            "Migration Strategy",
            "Testing Strategy",
            "Coverage Requirements",
        ]
        return section_name in important_sections
    
    def _generate_question(
        self,
        template_name: str,
        template_priority: int,
        section_name: str,
        context: str
    ) -> Question:
        """
        Generate a question for a missing section.
        
        Args:
            template_name: Name of the template
            template_priority: Priority of the template
            section_name: Name of the missing section
            context: Relevant context from knowledge base
            
        Returns:
            Question object with appropriate text and context
        """
        # Generate question text based on section
        question_text = self._get_question_text(template_name, section_name)
        
        # Extract relevant context (limit to 200 chars)
        context_snippet = context[:200] + "..." if len(context) > 200 else context
        
        return Question(
            template_name=template_name,
            section_name=section_name,
            question_text=question_text,
            context=f"For {template_name}.md - {section_name}: {context_snippet}",
            priority=template_priority
        )
    
    def _generate_clarification_question(
        self,
        template_name: str,
        template_priority: int,
        section_name: str,
        context: str
    ) -> Question:
        """
        Generate a clarification question for an ambiguous section.
        
        Args:
            template_name: Name of the template
            template_priority: Priority of the template
            section_name: Name of the ambiguous section
            context: Relevant context from knowledge base
            
        Returns:
            Question object requesting clarification
        """
        question_text = f"Can you clarify or provide more details about {section_name}?"
        
        # Extract relevant context
        context_snippet = context[:200] + "..." if len(context) > 200 else context
        
        return Question(
            template_name=template_name,
            section_name=section_name,
            question_text=question_text,
            context=f"For {template_name}.md - {section_name}: Found some information but need clarification. {context_snippet}",
            priority=template_priority + 10  # Lower priority than missing sections
        )
    
    def _get_question_text(self, template_name: str, section_name: str) -> str:
        """
        Get appropriate question text for a template section.
        
        Args:
            template_name: Name of the template
            section_name: Name of the section
            
        Returns:
            Question text string
        """
        # Define specific questions for common sections
        question_map = {
            ("project-vision", "Elevator Pitch"): "What is the one-sentence description of your project and who is it for?",
            ("project-vision", "Problem Statement"): "What specific problem does this project solve?",
            ("project-vision", "Solution Overview"): "How does your solution address the problem?",
            ("project-vision", "Target Users"): "Who are the primary and secondary users of this project?",
            ("project-vision", "Success Metrics"): "What metrics will you use to measure success?",
            ("tech-stack", "Backend"): "What backend language and framework are you using?",
            ("tech-stack", "Frontend"): "What frontend framework and language are you using?",
            ("tech-stack", "Database"): "What database system are you using?",
            ("tech-stack", "Cache"): "What caching solution are you using (if any)?",
            ("tech-stack", "Rationale"): "Why did you choose this technology stack? What trade-offs did you consider?",
            ("architecture", "Component Responsibilities"): "What are the main components of your system and their responsibilities?",
            ("architecture", "Data Flow"): "How does data flow through your system?",
            ("conventions", "Naming Conventions"): "What naming conventions do you follow (e.g., camelCase, snake_case)?",
            ("conventions", "Code Style"): "What are your code formatting standards (indentation, line length, etc.)?",
            ("api-standards", "Error Handling"): "What are your API error handling patterns and standards?",
            ("db-standards", "Migration Strategy"): "What is your database migration strategy?",
            ("qa-standards", "Coverage Requirements"): "What are your test coverage requirements?",
            ("ui-standards", "Component Patterns"): "What UI component patterns and guidelines do you follow?",
        }
        
        # Return specific question or generic one
        return question_map.get(
            (template_name, section_name),
            f"What information should be included in the {section_name} section?"
        )
