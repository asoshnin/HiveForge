"""
Customization detection for steering file updates.

This module provides functionality to identify user customizations in existing
steering files by comparing them with original templates using diff analysis
and heuristics.
"""

import difflib
import re
from typing import List

from .models import Customization


class CustomizationDetector:
    """
    Detects user customizations in steering files.
    
    Compares current steering file content with original templates to identify
    sections that have been manually customized by users. Uses heuristics including:
    - Content beyond template placeholders
    - Unique formatting patterns
    - Custom sections not in original template
    - Confidence scoring based on change characteristics
    """
    
    def __init__(self, original_template: str):
        """
        Initialize detector with the original template.
        
        Args:
            original_template: The original template content before any customization
        """
        self.original_template = original_template
        self.original_lines = original_template.splitlines()
    
    def detect_customizations(self, current_content: str) -> List[Customization]:
        """
        Find sections that differ from the original template.
        
        Analyzes the current content against the original template to identify
        customizations. Assigns confidence scores based on the nature of changes:
        - High confidence (0.8-1.0): Substantial content additions, custom sections
        - Medium confidence (0.5-0.7): Modified placeholders, formatting changes
        - Low confidence (0.3-0.4): Minor edits, whitespace changes
        
        Args:
            current_content: The current steering file content
            
        Returns:
            List of Customization objects with detected changes and confidence scores
        """
        current_lines = current_content.splitlines()
        customizations = []
        
        # Use SequenceMatcher to find differences
        matcher = difflib.SequenceMatcher(None, self.original_lines, current_lines)
        
        # Track current section for grouping related changes
        current_section = "Unknown"
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Update current section based on headers in equal blocks
                for line in current_lines[j1:j2]:
                    section_match = re.match(r'^#+\s+(.+)$', line)
                    if section_match:
                        current_section = section_match.group(1)
                continue
            
            # Extract the changed content
            original_chunk = '\n'.join(self.original_lines[i1:i2])
            customized_chunk = '\n'.join(current_lines[j1:j2])
            
            # Skip if both chunks are empty
            if not original_chunk and not customized_chunk:
                continue
            
            # Calculate confidence score based on change characteristics
            confidence = self._calculate_confidence(
                tag, original_chunk, customized_chunk, i1, i2, j1, j2
            )
            
            # Only include if confidence is above threshold
            if confidence >= 0.3:
                customization = Customization(
                    section=current_section,
                    original=original_chunk,
                    customized=customized_chunk,
                    confidence=confidence
                )
                customizations.append(customization)
        
        # Merge adjacent customizations in the same section
        customizations = self._merge_adjacent_customizations(customizations)
        
        return customizations
    
    def _calculate_confidence(
        self,
        tag: str,
        original: str,
        customized: str,
        i1: int,
        i2: int,
        j1: int,
        j2: int
    ) -> float:
        """
        Calculate confidence score for a detected customization.
        
        Uses multiple heuristics to determine how likely a change is a deliberate
        user customization versus an automated or minor change.
        
        Args:
            tag: Type of change ('replace', 'delete', 'insert')
            original: Original template content
            customized: Current customized content
            i1, i2: Start and end indices in original
            j1, j2: Start and end indices in current
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Factor 1: Type of change
        if tag == 'insert':
            # Insertions are likely customizations
            confidence += 0.2
        elif tag == 'delete':
            # Deletions might be intentional removal
            confidence += 0.1
        elif tag == 'replace':
            # Replacements need more analysis
            confidence += 0.0
        
        # Factor 2: Check if original contained placeholders
        placeholder_patterns = [
            r'\{[^}]+\}',  # {placeholder}
            r'\.\.\.',      # ...
            r'TODO',        # TODO markers
            r'FIXME',       # FIXME markers
        ]
        
        original_has_placeholder = any(
            re.search(pattern, original, re.IGNORECASE)
            for pattern in placeholder_patterns
        )
        
        customized_has_placeholder = any(
            re.search(pattern, customized, re.IGNORECASE)
            for pattern in placeholder_patterns
        )
        
        if original_has_placeholder and not customized_has_placeholder:
            # Placeholder was replaced with real content - high confidence
            confidence += 0.3
        elif not original_has_placeholder and not customized_has_placeholder:
            # Both have real content - medium confidence
            confidence += 0.1
        
        # Factor 3: Length of customization
        customized_length = len(customized.strip())
        if customized_length > 200:
            # Substantial content addition
            confidence += 0.2
        elif customized_length > 50:
            # Moderate content
            confidence += 0.1
        elif customized_length < 10:
            # Very short changes might be minor edits
            confidence -= 0.1
        
        # Factor 4: Check for custom sections (headers not in original)
        if re.match(r'^#+\s+', customized) and not re.match(r'^#+\s+', original):
            # New section header added - high confidence
            confidence += 0.3
        
        # Factor 5: Formatting changes (indentation, bullet points, etc.)
        original_stripped = original.strip()
        customized_stripped = customized.strip()
        
        if original_stripped == customized_stripped and original != customized:
            # Only whitespace/formatting changed - lower confidence
            confidence -= 0.2
        
        # Check if customized content is only whitespace
        if customized_stripped == "":
            if original_stripped == "":
                # Both empty or whitespace only - very low confidence
                confidence -= 0.4
            elif original_has_placeholder:
                # Placeholder replaced with whitespace - very low confidence
                confidence -= 0.4
            else:
                # Content was deleted - moderate confidence reduction
                confidence -= 0.1
        
        # Factor 6: Check for code blocks, tables, or structured content
        structured_patterns = [
            r'```',           # Code blocks
            r'\|.*\|',        # Tables
            r'^\s*[-*+]\s',   # Bullet lists
            r'^\s*\d+\.\s',   # Numbered lists
        ]
        
        has_structured_content = any(
            re.search(pattern, customized, re.MULTILINE)
            for pattern in structured_patterns
        )
        
        if has_structured_content and not any(
            re.search(pattern, original, re.MULTILINE)
            for pattern in structured_patterns
        ):
            # Added structured content - likely customization
            confidence += 0.15
        
        # Factor 7: Similarity ratio
        similarity = difflib.SequenceMatcher(None, original, customized).ratio()
        if similarity < 0.3:
            # Very different - likely significant customization
            confidence += 0.1
        elif similarity > 0.9:
            # Very similar - might be minor edit
            confidence -= 0.1
        
        # Clamp confidence to [0.0, 1.0]
        return max(0.0, min(1.0, confidence))
    
    def _merge_adjacent_customizations(
        self, customizations: List[Customization]
    ) -> List[Customization]:
        """
        Merge adjacent customizations in the same section.
        
        Combines consecutive customizations that belong to the same section
        to reduce fragmentation and provide a clearer view of changes.
        
        Args:
            customizations: List of detected customizations
            
        Returns:
            List of merged customizations
        """
        if not customizations:
            return []
        
        merged = []
        current = customizations[0]
        
        for next_custom in customizations[1:]:
            # Merge if same section and high confidence
            if (current.section == next_custom.section and
                current.confidence >= 0.5 and next_custom.confidence >= 0.5):
                # Combine the content
                current = Customization(
                    section=current.section,
                    original=current.original + '\n' + next_custom.original,
                    customized=current.customized + '\n' + next_custom.customized,
                    confidence=max(current.confidence, next_custom.confidence)
                )
            else:
                # Save current and start new
                merged.append(current)
                current = next_custom
        
        # Add the last one
        merged.append(current)
        
        return merged

    def _merge_adjacent_customizations(
        self, customizations: List[Customization]
    ) -> List[Customization]:
        """
        Merge adjacent customizations in the same section.

        Combines consecutive customizations that belong to the same section
        to reduce fragmentation and provide a clearer view of changes.

        Args:
            customizations: List of detected customizations

        Returns:
            List of merged customizations
        """
        if not customizations:
            return []

        merged = []
        current = customizations[0]

        for next_custom in customizations[1:]:
            # Merge if same section and high confidence
            if (current.section == next_custom.section and
                current.confidence >= 0.5 and next_custom.confidence >= 0.5):
                # Combine the content
                current = Customization(
                    section=current.section,
                    original=current.original + '\n' + next_custom.original,
                    customized=current.customized + '\n' + next_custom.customized,
                    confidence=max(current.confidence, next_custom.confidence)
                )
            else:
                # Save current and start new
                merged.append(current)
                current = next_custom

        # Add the last one
        merged.append(current)

        return merged

    def mark_protected(self, customizations: List[Customization]) -> List[Customization]:
        """
        Mark customized sections as protected.

        Args:
            customizations: List of detected customizations

        Returns:
            List of customizations with protected flag
        """
        for customization in customizations:
            customization.protected = True
        return customizations

    def calculate_customization_confidence(
        self,
        customization: Customization,
    ) -> float:
        """
        Calculate confidence score for a detected customization.

        Args:
            customization: The Customization object

        Returns:
            Confidence score between 0.0 and 1.0
        """
        return customization.confidence

    def highlight_customizations(
        self,
        content: str,
        customizations: List[Customization],
    ) -> str:
        """
        Add visual indicators for customizations in content.

        Args:
            content: Original content
            customizations: List of detected customizations

        Returns:
            Content with visual indicators for customizations
        """
        # Add markers for customizations
        result = content

        for customization in customizations:
            if customization.confidence >= 0.7:
                # High confidence - mark with strong indicator
                result = result.replace(
                    customization.customized,
                    f"[CUSTOMIZED: {customization.section}] {customization.customized} [END CUSTOMIZED]"
                )
            elif customization.confidence >= 0.5:
                # Medium confidence - mark with medium indicator
                result = result.replace(
                    customization.customized,
                    f"[POSSIBLE CUSTOMIZATION: {customization.section}] {customization.customized} [END]"
                )

        return result
