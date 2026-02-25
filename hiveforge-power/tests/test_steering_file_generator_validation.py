"""
Property tests for SteeringFileGenerator validation logic.

Tests hallucination detection and duplicate paragraph detection.

Requirements: 6.1, 6.2, 6.3, 10.5
"""

import pytest

from hiveforge.steering.steering_file_generator import SteeringFileGenerator
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    Dependency,
    NamingConventions,
)


class TestHallucinationDetection:
    """
    Property 7: Hallucination detection — database/framework contradictions caught.
    
    For any draft containing a database or framework name that contradicts
    CodeAnalysisFacts, _validate_draft() must return a non-empty error list.
    
    Requirements: 6.1, 6.2, 6.3
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock LLM provider that's available
        class MockLLMProvider:
            def is_available(self):
                return True
        
        self.generator = SteeringFileGenerator(MockLLMProvider())
    
    def test_database_contradiction_detected(self):
        """
        Test that database contradictions are detected.
        
        Requirement: 6.2
        """
        # Code uses PostgreSQL
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Django"],
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
        
        # Draft mentions MySQL (contradiction)
        draft = """
# Tech Stack

## Backend
- Framework: Django
- Database: MySQL

## Dependencies
- Django 4.2
"""
        
        errors = self.generator._validate_draft("tech-stack.md", draft, code_facts)
        
        # Should detect hallucination
        assert len(errors) > 0
        assert any("hallucination" in err.lower() for err in errors)
        assert any("mysql" in err.lower() for err in errors)
    
    def test_framework_contradiction_detected(self):
        """
        Test that framework contradictions are detected.
        
        Requirement: 6.3
        """
        # Code uses FastAPI
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        # Draft mentions Flask (contradiction)
        draft = """
# Tech Stack

## Backend
- Framework: Flask
- Language: Python 3.11

## API
- REST API using Flask
"""
        
        errors = self.generator._validate_draft("tech-stack.md", draft, code_facts)
        
        # Should detect hallucination
        assert len(errors) > 0
        assert any("hallucination" in err.lower() for err in errors)
        assert any("flask" in err.lower() for err in errors)
    
    def test_multiple_contradictions_detected(self):
        """
        Test that multiple contradictions are all detected.
        
        Requirements: 6.2, 6.3
        """
        # Code uses PostgreSQL and Django
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Django"],
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
        
        # Draft mentions MySQL and Flask (both wrong)
        draft = """
# Tech Stack

## Backend
- Framework: Flask
- Database: MySQL

## Architecture
- Layered architecture with Flask
"""
        
        errors = self.generator._validate_draft("tech-stack.md", draft, code_facts)
        
        # Should detect both hallucinations
        assert len(errors) >= 2
        assert any("mysql" in err.lower() for err in errors)
        assert any("flask" in err.lower() for err in errors)
    
    def test_correct_database_no_error(self):
        """
        Test that correct database mention produces no error.
        
        Requirement: 6.2
        """
        # Code uses PostgreSQL
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Django"],
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
        
        # Draft correctly mentions PostgreSQL
        draft = """
# Tech Stack

## Backend
- Framework: Django
- Database: PostgreSQL

## Dependencies
- Django 4.2
- psycopg2
"""
        
        errors = self.generator._validate_draft("tech-stack.md", draft, code_facts)
        
        # Should have no database-related errors
        assert not any("database" in err.lower() and "hallucination" in err.lower() for err in errors)
    
    def test_correct_framework_no_error(self):
        """
        Test that correct framework mention produces no error.
        
        Requirement: 6.3
        """
        # Code uses FastAPI
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        # Draft correctly mentions FastAPI
        draft = """
# Tech Stack

## Backend
- Framework: FastAPI
- Language: Python 3.11

## API
- REST API using FastAPI
"""
        
        errors = self.generator._validate_draft("tech-stack.md", draft, code_facts)
        
        # Should have no framework-related errors
        assert not any("framework" in err.lower() and "hallucination" in err.lower() for err in errors)
    
    def test_validation_only_for_tech_stack_and_architecture(self):
        """
        Test that validation only applies to tech-stack.md and architecture.md.
        
        Requirement: 6.1
        """
        # Code uses PostgreSQL
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Django"],
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
        
        # Draft mentions MySQL (but in conventions.md, not tech-stack.md)
        draft = """
# Coding Conventions

## Database Conventions
- Use MySQL naming conventions for tables
"""
        
        errors = self.generator._validate_draft("conventions.md", draft, code_facts)
        
        # Should NOT validate conventions.md for hallucinations
        assert len(errors) == 0


class TestDuplicateParagraphDetection:
    """
    Property 8: Duplicate paragraph detection.
    
    For any draft containing the same paragraph verbatim in more than one
    section, _check_duplicate_paragraphs() must return a non-empty error list.
    
    Requirement: 10.5
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        class MockLLMProvider:
            def is_available(self):
                return True
        
        self.generator = SteeringFileGenerator(MockLLMProvider())
    
    def test_duplicate_paragraph_detected(self):
        """
        Test that duplicate paragraphs are detected.
        
        Requirement: 10.5
        """
        # Note: Paragraphs must be separated by double newlines (\n\n)
        draft = """# Tech Stack

## Backend

This is a Python application using FastAPI framework for building REST APIs. FastAPI provides automatic API documentation and type validation.

## Frontend

N/A

## Database

This is a Python application using FastAPI framework for building REST APIs. FastAPI provides automatic API documentation and type validation.
"""
        
        errors = self.generator._check_duplicate_paragraphs(draft)
        
        # Should detect duplicate
        assert len(errors) > 0
        assert any("duplicate" in err.lower() for err in errors)
    
    def test_multiple_duplicates_detected(self):
        """
        Test that multiple duplicate paragraphs are all detected.
        
        Requirement: 10.5
        """
        # Note: Paragraphs must be separated by double newlines (\n\n)
        # Note: Paragraphs must be >80 chars to be checked
        draft = """# Architecture

## Overview

The system follows a layered architecture pattern with clear separation of concerns between presentation, business logic, and data access layers.

## Components

The API layer handles HTTP requests and responses, providing RESTful endpoints for client applications to interact with the system.

## Data Flow

The system follows a layered architecture pattern with clear separation of concerns between presentation, business logic, and data access layers.

## Scalability

The API layer handles HTTP requests and responses, providing RESTful endpoints for client applications to interact with the system.
"""
        
        errors = self.generator._check_duplicate_paragraphs(draft)
        
        # Should detect both duplicates
        assert len(errors) >= 2
    
    def test_short_paragraphs_ignored(self):
        """
        Test that short paragraphs (≤80 chars) are ignored.
        
        Requirement: 10.5
        """
        draft = """
# Tech Stack

## Backend
Python

## Frontend
N/A

## Database
Python
"""
        
        errors = self.generator._check_duplicate_paragraphs(draft)
        
        # Should not flag short duplicates
        assert len(errors) == 0
    
    def test_unique_paragraphs_no_error(self):
        """
        Test that unique paragraphs produce no errors.
        
        Requirement: 10.5
        """
        draft = """
# Tech Stack

## Backend
This is a Python application using FastAPI framework for building REST APIs. FastAPI provides automatic API documentation and type validation.

## Frontend
The frontend is built with React and TypeScript, providing a modern single-page application experience with strong type safety.

## Database
PostgreSQL is used as the primary database, chosen for its ACID compliance and robust support for complex queries and transactions.
"""
        
        errors = self.generator._check_duplicate_paragraphs(draft)
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_similar_but_not_identical_paragraphs_allowed(self):
        """
        Test that similar but not identical paragraphs are allowed.
        
        Requirement: 10.5
        """
        draft = """
# Tech Stack

## Backend
This is a Python application using FastAPI framework for building REST APIs.

## API Design
This is a Python application using FastAPI framework for building RESTful APIs.
"""
        
        errors = self.generator._check_duplicate_paragraphs(draft)
        
        # Should not flag similar but different paragraphs
        assert len(errors) == 0
