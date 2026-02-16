"""
Knowledge Base for Steering Assistant.

This module provides the KnowledgeBase class that aggregates and indexes parsed
content for efficient retrieval. It combines information from parsed documents
(markdown, PDF, images) and optional code analysis results.
"""

from typing import List, Optional
from .models import (
    ParsedDocument,
    CodeAnalysisResult,
    TechStackInfo,
    ConventionsInfo,
    ArchitectureInfo,
)


class KnowledgeBase:
    """
    Aggregates and indexes parsed content for efficient retrieval.
    
    The KnowledgeBase combines information from parsed documents and optional
    code analysis results, providing methods to search and extract specific
    information types with token-aware limiting.
    """
    
    def __init__(
        self,
        documents: List[ParsedDocument],
        code_analysis: Optional[CodeAnalysisResult] = None
    ):
        """
        Initialize the knowledge base with parsed documents and optional code analysis.
        
        Args:
            documents: List of parsed documents from staging folder
            code_analysis: Optional code analysis results from codebase import
        """
        self.documents = documents
        self.code_analysis = code_analysis
        
        # Build a simple index of all content for searching
        self._content_index = self._build_content_index()
    
    def _build_content_index(self) -> str:
        """
        Build a searchable index of all content.
        
        Returns:
            Combined content from all documents
        """
        content_parts = []
        
        # Add document content
        for doc in self.documents:
            content_parts.append(f"# Document: {doc.file_path.name}\n{doc.content}")
        
        # Add code analysis summary if available
        if self.code_analysis:
            content_parts.append(f"\n# Code Analysis\n{self.code_analysis.to_summary()}")
        
        return "\n\n".join(content_parts)
    
    def search(self, query: str) -> List[str]:
        """
        Search for relevant content snippets matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of relevant content snippets
        """
        query_lower = query.lower()
        snippets = []
        
        # Search in documents
        for doc in self.documents:
            lines = doc.content.split('\n')
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    # Get context: 2 lines before and after
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = '\n'.join(lines[start:end])
                    snippets.append(f"From {doc.file_path.name}:\n{context}")
        
        return snippets
    
    def get_relevant_content(
        self,
        template_name: str,
        max_tokens: int = 4000
    ) -> str:
        """
        Get only relevant content for a specific template, token-limited.
        
        This method extracts content relevant to the specified template and
        limits it to the maximum token count to avoid exceeding LLM context limits.
        
        Args:
            template_name: Name of the template to get content for
            max_tokens: Maximum number of tokens to include (default: 4000)
            
        Returns:
            Token-limited relevant content string
        """
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        # Define template-specific keywords for relevance filtering
        template_keywords = {
            'project-vision': ['problem', 'solution', 'goal', 'user', 'metric', 'vision', 'mission'],
            'tech-stack': ['language', 'framework', 'library', 'database', 'technology', 'dependency'],
            'architecture': ['architecture', 'component', 'pattern', 'structure', 'design', 'system'],
            'conventions': ['convention', 'style', 'naming', 'format', 'standard', 'guideline'],
            'api-standards': ['api', 'endpoint', 'rest', 'graphql', 'http', 'request', 'response'],
            'db-standards': ['database', 'schema', 'migration', 'query', 'table', 'model'],
            'qa-standards': ['test', 'quality', 'coverage', 'qa', 'testing', 'validation'],
            'ui-standards': ['ui', 'component', 'design', 'interface', 'frontend', 'style'],
        }
        
        keywords = template_keywords.get(template_name, [])
        relevant_parts = []
        
        # Extract relevant sections from documents
        for doc in self.documents:
            lines = doc.content.split('\n')
            current_section = []
            
            for line in lines:
                line_lower = line.lower()
                # Check if line contains any relevant keywords
                if any(keyword in line_lower for keyword in keywords):
                    # Include this line and surrounding context
                    if current_section:
                        current_section.append(line)
                    else:
                        current_section = [line]
                elif current_section:
                    # Continue collecting lines after a match (for context)
                    current_section.append(line)
                    # Stop after 5 lines of context
                    if len(current_section) > 10:
                        relevant_parts.append('\n'.join(current_section))
                        current_section = []
            
            # Add any remaining section
            if current_section:
                relevant_parts.append('\n'.join(current_section))
        
        # Add code analysis if relevant to template
        if self.code_analysis:
            if template_name == 'tech-stack':
                relevant_parts.insert(0, self.code_analysis.to_summary(max_tokens=1000))
            elif template_name == 'architecture':
                arch_summary = f"Architecture Pattern: {self.code_analysis.architecture.pattern}"
                if self.code_analysis.architecture.key_components:
                    arch_summary += f"\nComponents: {', '.join(self.code_analysis.architecture.key_components)}"
                relevant_parts.insert(0, arch_summary)
            elif template_name == 'conventions':
                conv_parts = []
                if self.code_analysis.conventions.naming_style:
                    conv_parts.append(f"Naming: {self.code_analysis.conventions.naming_style}")
                if self.code_analysis.conventions.formatting:
                    conv_parts.append(f"Formatting: {self.code_analysis.conventions.formatting}")
                if self.code_analysis.conventions.documentation_style:
                    conv_parts.append(f"Documentation: {self.code_analysis.conventions.documentation_style}")
                if conv_parts:
                    relevant_parts.insert(0, '\n'.join(conv_parts))
        
        # Combine and truncate to max_chars
        combined = '\n\n'.join(relevant_parts)
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "\n... (truncated for token limit)"
        
        return combined
    
    def extract_section(self, section_name: str) -> Optional[str]:
        """
        Extract a specific section if identifiable in the documents.
        
        Args:
            section_name: Name of the section to extract
            
        Returns:
            Section content if found, None otherwise
        """
        section_lower = section_name.lower()
        
        for doc in self.documents:
            lines = doc.content.split('\n')
            in_section = False
            section_content = []
            
            for line in lines:
                # Check for markdown headers matching section name
                if line.startswith('#'):
                    header_text = line.lstrip('#').strip().lower()
                    if section_lower in header_text:
                        in_section = True
                        section_content = [line]
                    elif in_section and line.startswith('#'):
                        # Hit next section, stop collecting
                        break
                elif in_section:
                    section_content.append(line)
            
            if section_content:
                return '\n'.join(section_content)
        
        return None
    
    def get_tech_stack(self) -> Optional[TechStackInfo]:
        """
        Get technology stack information from code analysis.
        
        Returns:
            TechStackInfo if code analysis was performed, None otherwise
        """
        if self.code_analysis:
            return self.code_analysis.tech_stack
        return None
    
    def get_conventions(self) -> Optional[ConventionsInfo]:
        """
        Get coding conventions from code analysis.
        
        Returns:
            ConventionsInfo if code analysis was performed, None otherwise
        """
        if self.code_analysis:
            return self.code_analysis.conventions
        return None
    
    def get_architecture(self) -> Optional[ArchitectureInfo]:
        """
        Get architecture information from code analysis.
        
        Returns:
            ArchitectureInfo if code analysis was performed, None otherwise
        """
        if self.code_analysis:
            return self.code_analysis.architecture
        return None
