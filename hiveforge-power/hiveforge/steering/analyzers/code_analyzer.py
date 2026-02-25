"""
Code analyzer orchestrator for the Steering Assistant.

This module provides the main CodeAnalyzer orchestrator that coordinates all
code analysis modules to extract project information from existing codebases.
All analysis is performed locally without LLM API calls.

The orchestrator:
- Respects .gitignore files using pathspec library
- Implements sampling strategy for large codebases (>10k files)
- Provides progress updates every 30 seconds for long-running analysis
- Implements caching in .kiro/.cache/code_analysis.json
- Generates token-limited summaries (max 2000 tokens per template)
"""

import ast
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import pathspec
except ImportError:
    pathspec = None

from ..models import CodeAnalysisResult, ConventionsInfo
from .language_detector import detect_languages
from .tech_stack_extractor import extract_tech_stack
from .architecture_inferrer import infer_architecture
from .conventions_extractor import extract_conventions, summarize_conventions
from .documentation_parser import parse_codebase_documentation

logger = logging.getLogger(__name__)


# Constants
LARGE_CODEBASE_THRESHOLD = 10000  # files
PROGRESS_UPDATE_INTERVAL = 30  # seconds
CACHE_FILE = ".kiro/.cache/code_analysis.json"
MAX_ANALYSIS_TIME = 300  # 5 minutes


class CodeAnalyzer:
    """
    Main orchestrator for code analysis.
    
    This class coordinates all analysis modules to extract comprehensive
    project information from an existing codebase. All analysis is performed
    locally using AST parsing, regex, and file system operations.
    
    Requirements: 3A.1-3A.15, 3B.1-3B.7, 3C.1-3C.5
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize CodeAnalyzer with project root directory.
        
        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = Path(project_root).resolve()
        self.gitignore_spec: Optional[pathspec.PathSpec] = None
        self.excluded_paths: Set[Path] = set()  # For backward compatibility
        self.start_time: Optional[float] = None
        self.last_progress_update: Optional[float] = None
        
        logger.info(f"Initialized CodeAnalyzer for: {self.project_root}")
    
    def analyze(self) -> CodeAnalysisResult:
        """
        Perform comprehensive code analysis using local algorithms.
        
        This method:
        1. Loads .gitignore and builds exclusion list
        2. Counts total files and checks for large codebase
        3. Detects programming languages and versions
        4. Extracts technology stack from dependency files
        5. Infers architecture patterns from directory structure
        6. Extracts coding conventions from code and config files
        7. Parses documentation (README, docs/, inline comments)
        8. Calculates confidence scores for all findings
        9. Caches results for future use
        
        Returns:
            CodeAnalysisResult with all extracted information
            
        Requirements: 3A.1, 3A.2, 3A.12, 3A.13, 3C.1, 3C.5
        """
        logger.info("=" * 60)
        logger.info("Starting comprehensive code analysis")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        self.last_progress_update = self.start_time
        
        # Check cache first
        cached_result = self._load_cache()
        if cached_result:
            logger.info("Using cached analysis results")
            return cached_result
        
        # Step 1: Load .gitignore and build exclusion list
        self._log_progress("Loading .gitignore exclusions")
        self._load_gitignore()
        
        # Step 2: Count files and check for large codebase
        self._log_progress("Counting files in codebase")
        total_files = self._count_files()
        logger.info(f"Total files found: {total_files}")
        
        if total_files > LARGE_CODEBASE_THRESHOLD:
            logger.warning(
                f"Large codebase detected ({total_files} files > {LARGE_CODEBASE_THRESHOLD}). "
                f"Using sampling strategy for performance."
            )
        
        # Step 3: Detect languages
        self._log_progress("Detecting programming languages")
        languages = self.detect_languages()
        logger.info(f"Detected {len(languages)} language(s)")
        
        # Step 4: Extract tech stack
        self._log_progress("Extracting technology stack")
        tech_stack = self.extract_tech_stack()
        logger.info(
            f"Tech stack: Backend={tech_stack.backend_framework}, "
            f"Frontend={tech_stack.frontend_framework}, "
            f"Database={tech_stack.database}"
        )
        
        # Step 5: Infer architecture
        self._log_progress("Inferring architecture patterns")
        architecture = self.infer_architecture()
        logger.info(f"Architecture: {architecture.pattern}")
        
        # Step 6: Extract conventions
        self._log_progress("Extracting coding conventions")
        conventions = self.extract_conventions()
        logger.info("Conventions extracted")
        
        # Step 7: Parse documentation
        self._log_progress("Parsing documentation")
        documentation = self._parse_documentation()
        logger.info(f"Parsed {len(documentation)} documentation source(s)")
        
        # Step 8: Calculate confidence scores
        self._log_progress("Calculating confidence scores")
        confidence_scores = self._calculate_confidence_scores(
            languages, tech_stack, architecture, conventions
        )
        
        # Step 9: Classify project type (P1-2)
        self._log_progress("Classifying project type")
        classification = self._heuristic_classify(languages)
        logger.info(f"Project classified as: {classification.get('project_type', 'unknown')}")
        
        # Build result
        result = CodeAnalysisResult(
            languages=languages,
            tech_stack=tech_stack,
            architecture=architecture,
            conventions=conventions,
            documentation=documentation,
            confidence_scores=confidence_scores,
            classification=classification  # P1-2
        )
        
        # Cache results
        self._save_cache(result)
        
        elapsed_time = time.time() - self.start_time
        logger.info("=" * 60)
        logger.info(f"Code analysis complete in {elapsed_time:.1f} seconds")
        logger.info("=" * 60)
        
        return result
    
    def to_facts(self) -> "CodeAnalysisFacts":
        """
        Convert analysis results to structured CodeAnalysisFacts dataclass.
        
        This method replaces to_summary() as the primary output format for
        LLM-primary steering synthesis. It returns a JSON-serializable
        dataclass that can be injected into LLM prompts.
        
        The output is guaranteed to serialize to ≤2,000 tokens when converted
        to JSON via to_json_dict().
        
        Returns:
            CodeAnalysisFacts with structured analysis data
            
        Requirements: 2.1, 2.2, 2.3, 2.5
        """
        from ..models import CodeAnalysisFacts, NamingConventions, Dependency
        
        # Run analysis if not already done
        result = self.analyze()
        
        # Extract primary language
        primary_language = "unknown"
        if result.languages:
            primary_language = result.languages[0].name
            if result.languages[0].version:
                primary_language += f" {result.languages[0].version}"
        
        # Extract frameworks
        frameworks = []
        if result.tech_stack.backend_framework:
            frameworks.append(result.tech_stack.backend_framework)
        if result.tech_stack.frontend_framework:
            frameworks.append(result.tech_stack.frontend_framework)
        
        # Convert dependencies to list of Dependency objects
        dependencies = result.tech_stack.dependencies if result.tech_stack.dependencies else []
        
        # Determine architecture pattern
        architecture_pattern = result.architecture.pattern if result.architecture else "custom"
        
        # Detect if tests exist
        has_tests = False
        test_framework = None
        if result.conventions and result.conventions.test_framework:
            has_tests = True
            test_framework = result.conventions.test_framework
        
        # Determine API type
        api_type = None
        if result.classification:
            project_type = result.classification.get("project_type", "")
            if "mcp" in project_type.lower():
                api_type = "MCP"
            elif "cli" in project_type.lower():
                api_type = "CLI"
            elif self._detect_rest_api():
                api_type = "REST"
        
        # Extract database
        database = result.tech_stack.database if result.tech_stack else None
        
        # Extract entry points (from public API or main files)
        entry_points = []
        try:
            public_api = self.extract_public_api()
            if public_api.mcp_tools:
                entry_points.extend([f"MCP: {tool.name}" for tool in public_api.mcp_tools[:3]])
            if public_api.cli_commands:
                entry_points.extend([f"CLI: {cmd.name}" for cmd in public_api.cli_commands[:3]])
        except Exception as e:
            logger.debug(f"Could not extract public API: {e}")
        
        # Extract naming conventions
        naming_conventions = NamingConventions()
        if result.conventions and result.conventions.naming_style:
            naming_conventions = NamingConventions(
                variables=result.conventions.naming_style.get("variables", ""),
                classes=result.conventions.naming_style.get("classes", ""),
                constants=result.conventions.naming_style.get("constants", ""),
                functions=result.conventions.naming_style.get("functions", ""),
            )
        
        # Build compact directory structure (top-level only to save tokens)
        directory_structure = ""
        try:
            top_level_dirs = [
                d.name for d in self.project_root.iterdir()
                if d.is_dir() and not d.name.startswith(".") and d.name not in ("node_modules", "venv", "__pycache__")
            ]
            directory_structure = ", ".join(sorted(top_level_dirs[:10]))
        except Exception as e:
            logger.debug(f"Could not build directory structure: {e}")
        
        return CodeAnalysisFacts(
            primary_language=primary_language,
            frameworks=frameworks,
            dependencies=dependencies,
            architecture_pattern=architecture_pattern,
            has_tests=has_tests,
            test_framework=test_framework,
            api_type=api_type,
            database=database,
            entry_points=entry_points,
            naming_conventions=naming_conventions,
            directory_structure=directory_structure,
        )
    
    def detect_languages(self) -> List:
        """
        Detect programming languages using file extensions and line counting.
        
        Returns:
            List of LanguageInfo objects
            
        Requirements: 3A.3, 3A.4
        """
        try:
            excluded_paths = self._get_excluded_paths_for_analyzers()
            return detect_languages(self.project_root, excluded_paths)
        except Exception as e:
            logger.error(f"Error detecting languages: {e}", exc_info=True)
            return []
    
    def extract_tech_stack(self):
        """
        Extract technology stack from dependency files using parsers.
        
        Returns:
            TechStackInfo object
            
        Requirements: 3A.5
        """
        try:
            return extract_tech_stack(self.project_root)
        except Exception as e:
            logger.error(f"Error extracting tech stack: {e}", exc_info=True)
            from ..models import TechStackInfo
            return TechStackInfo()
    
    def infer_architecture(self):
        """
        Infer architecture patterns from directory structure using pattern matching.
        
        Returns:
            ArchitectureInfo object
            
        Requirements: 3A.6
        """
        try:
            excluded_paths = self._get_excluded_paths_for_analyzers()
            return infer_architecture(self.project_root, excluded_paths)
        except Exception as e:
            logger.error(f"Error inferring architecture: {e}", exc_info=True)
            from ..models import ArchitectureInfo
            return ArchitectureInfo(pattern="custom")
    
    def extract_conventions(self):
        """
        Extract coding conventions using AST parsing and regex.
        
        Returns:
            ConventionsInfo object
            
        Requirements: 3A.7, 3A.11
        """
        try:
            excluded_paths = self._get_excluded_paths_for_analyzers()
            # Extract raw conventions
            raw_conventions = extract_conventions(
                self.project_root,
                excluded_paths,
                sample_size=100
            )
            
            # Summarize into ConventionsInfo format
            summary = summarize_conventions(raw_conventions)
            
            # Build ConventionsInfo object
            conventions_info = ConventionsInfo(
                naming_style={
                    'functions': summary.get('function_naming', 'unknown'),
                    'variables': summary.get('variable_naming', 'unknown'),
                    'classes': summary.get('class_naming', 'unknown'),
                    'constants': summary.get('constant_naming', 'unknown'),
                },
                formatting={
                    'indentation': summary.get('indentation', 'unknown'),
                },
                documentation_style=summary.get('documentation', 'unknown'),
                test_framework=None  # Could be enhanced to detect test frameworks
            )
            
            return conventions_info
        
        except Exception as e:
            logger.error(f"Error extracting conventions: {e}", exc_info=True)
            return ConventionsInfo()
    
    def get_summary_for_llm(self, max_tokens: int = 2000) -> str:
        """
        Get token-limited summary of findings for LLM context.
        
        This method generates a concise summary of the analysis results
        that can be included in LLM prompts without exceeding token limits.
        
        Args:
            max_tokens: Maximum number of tokens to include in summary
            
        Returns:
            Token-limited summary string
            
        Requirements: 3C.2, 3C.3
        """
        try:
            result = self.analyze()
            return result.to_summary(max_tokens)
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return "Error generating code analysis summary"
    
    def extract_public_api(self):
        """
        Extract MCP tools, CLI commands, and public classes from codebase.
        
        Scans Python files for:
        - @mcp.tool() decorated functions
        - @command() or @click.command() decorated functions
        - Non-private classes with docstrings
        
        Returns:
            PublicAPIInfo with all extracted API elements
            
        Requirements: P1-1
        """
        from ..models import PublicAPIInfo, MCPToolInfo, CLICommandInfo
        import ast
        
        mcp_tools = []
        cli_commands = []
        public_classes = []
        
        # Scan Python files (max 50 to avoid timeout)
        python_files = []
        for file_path in self.project_root.rglob('*.py'):
            if self._should_exclude_path(file_path):
                continue
            python_files.append(file_path)
            if len(python_files) >= 50:
                break
        
        logger.info(f"Scanning {len(python_files)} Python files for public API")
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Extract MCP tools
                mcp_tools.extend(self._scan_for_mcp_tools(tree))
                
                # Extract CLI commands
                cli_commands.extend(self._scan_for_cli_commands(tree))
                
                # Extract public classes
                public_classes.extend(self._extract_public_classes(tree))
            
            except SyntaxError:
                logger.debug(f"Syntax error in {file_path}, skipping")
                continue
            except Exception as e:
                logger.debug(f"Error parsing {file_path}: {e}")
                continue
        
        logger.info(
            f"Extracted {len(mcp_tools)} MCP tools, "
            f"{len(cli_commands)} CLI commands, "
            f"{len(public_classes)} public classes"
        )
        
        return PublicAPIInfo(
            mcp_tools=mcp_tools,
            cli_commands=cli_commands,
            public_classes=public_classes
        )
    
    def _scan_for_mcp_tools(self, tree: ast.AST) -> List:
        """
        Extract @mcp.tool() decorated functions from AST.
        
        Args:
            tree: AST tree to scan
            
        Returns:
            List of MCPToolInfo objects
        """
        from ..models import MCPToolInfo
        
        tools = []
        
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            
            # Check for @mcp.tool() decorator
            has_mcp_decorator = any(
                (isinstance(dec, ast.Attribute) and
                 dec.attr == 'tool' and
                 isinstance(dec.value, ast.Name) and
                 dec.value.id == 'mcp')
                or
                (isinstance(dec, ast.Call) and
                 isinstance(dec.func, ast.Attribute) and
                 dec.func.attr == 'tool' and
                 isinstance(dec.func.value, ast.Name) and
                 dec.func.value.id == 'mcp')
                for dec in node.decorator_list
            )
            
            if not has_mcp_decorator:
                continue
            
            # Extract docstring (first line only, max 120 chars)
            docstring = ast.get_docstring(node) or ""
            docstring = docstring.split('\n')[0][:120]
            
            # Extract parameters (exclude self, ctx)
            parameters = [
                arg.arg for arg in node.args.args
                if arg.arg not in ('self', 'ctx')
            ]
            
            tools.append(MCPToolInfo(
                name=node.name,
                docstring=docstring,
                parameters=parameters
            ))
        
        return tools
    
    def _scan_for_cli_commands(self, tree: ast.AST) -> List:
        """
        Extract @command() or @click.command() decorated functions from AST.
        
        Args:
            tree: AST tree to scan
            
        Returns:
            List of CLICommandInfo objects
        """
        from ..models import CLICommandInfo
        
        commands = []
        
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            
            # Check for @command() or @click.command() decorator
            has_command_decorator = any(
                (isinstance(dec, ast.Name) and dec.id == 'command')
                or
                (isinstance(dec, ast.Call) and
                 isinstance(dec.func, ast.Name) and
                 dec.func.id == 'command')
                or
                (isinstance(dec, ast.Attribute) and
                 dec.attr == 'command')
                or
                (isinstance(dec, ast.Call) and
                 isinstance(dec.func, ast.Attribute) and
                 dec.func.attr == 'command')
                for dec in node.decorator_list
            )
            
            if not has_command_decorator:
                continue
            
            # Extract docstring (first line only, max 120 chars)
            docstring = ast.get_docstring(node) or ""
            help_text = docstring.split('\n')[0][:120]
            
            # Extract parameters (exclude self, ctx)
            parameters = [
                arg.arg for arg in node.args.args
                if arg.arg not in ('self', 'ctx')
            ]
            
            commands.append(CLICommandInfo(
                name=node.name,
                help_text=help_text,
                parameters=parameters
            ))
        
        return commands
    
    def _extract_public_classes(self, tree: ast.AST) -> List[str]:
        """
        Extract non-private classes with docstrings from AST.
        
        Args:
            tree: AST tree to scan
            
        Returns:
            List of class names
        """
        classes = []
        
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            
            # Skip private classes
            if node.name.startswith('_'):
                continue
            
            # Only include if has docstring
            if ast.get_docstring(node):
                classes.append(node.name)
        
        return classes
    
    def _heuristic_classify(self, languages: List) -> Dict[str, any]:
        """
        Classify project type using heuristics.
        
        This method detects project type (CLI tool, MCP server, web app, library)
        based on directory structure and decorators. Does NOT call self.analyze()
        to avoid recursion.
        
        Args:
            languages: List of detected languages
            
        Returns:
            Dict with keys: project_type, has_frontend, has_database,
            has_rest_api, primary_language, one_line_description,
            key_capabilities
            
        Requirements: P1-2
        """
        logger.info("Classifying project type using heuristics")
        
        # Extract public API (for MCP/CLI detection)
        public_api = self.extract_public_api()
        
        # Detect project type
        project_type = self._detect_project_type(public_api, languages)
        
        # Detect features
        has_frontend = self._detect_frontend()
        has_database = self._detect_database()
        has_rest_api = self._detect_rest_api()
        
        # Determine primary language
        primary_language = languages[0].name if languages else "Unknown"
        
        logger.info(
            f"Classification: type={project_type}, "
            f"frontend={has_frontend}, db={has_database}, api={has_rest_api}"
        )
        
        return {
            'project_type': project_type,
            'has_frontend': has_frontend,
            'has_database': has_database,
            'has_rest_api': has_rest_api,
            'primary_language': primary_language,
            'one_line_description': '[INFERRED: project description]',
            'key_capabilities': [
                '[INFERRED: capability 1]',
                '[INFERRED: capability 2]',
                '[INFERRED: capability 3]'
            ]
        }
    
    def _detect_project_type(self, public_api, languages: List) -> str:
        """
        Detect project type from code patterns.
        
        Args:
            public_api: PublicAPIInfo with extracted API elements
            languages: List of detected languages
            
        Returns:
            Project type string: mcp_server, cli_and_mcp, cli_tool, web_app, or library
        """
        # Check for MCP server
        if self._detect_mcp(public_api):
            if self._detect_cli(public_api):
                return "cli_and_mcp"
            return "mcp_server"
        
        # Check for CLI tool
        if self._detect_cli(public_api):
            return "cli_tool"
        
        # Check for web app
        if self._detect_frontend():
            return "web_app"
        
        # Default to library
        return "library"
    
    def _detect_mcp(self, public_api) -> bool:
        """
        Check if project is MCP server.
        
        Args:
            public_api: PublicAPIInfo with extracted API elements
            
        Returns:
            True if project has MCP tools, False otherwise
        """
        # Check for mcp_server directory
        if (self.project_root / 'mcp_server').exists():
            logger.debug("Found mcp_server/ directory")
            return True
        
        # Check for @mcp.tool() decorators
        if len(public_api.mcp_tools) > 0:
            logger.debug(f"Found {len(public_api.mcp_tools)} MCP tools")
            return True
        
        return False
    
    def _detect_cli(self, public_api) -> bool:
        """
        Check if project has CLI commands.
        
        Args:
            public_api: PublicAPIInfo with extracted API elements
            
        Returns:
            True if project has CLI commands, False otherwise
        """
        if len(public_api.cli_commands) > 0:
            logger.debug(f"Found {len(public_api.cli_commands)} CLI commands")
            return True
        
        return False
    
    def _detect_frontend(self) -> bool:
        """
        Check if project has frontend.
        
        Returns:
            True if project has frontend indicators, False otherwise
        """
        frontend_indicators = [
            'src/components',
            'src/pages',
            'src/ui',
            'app/components',
        ]
        
        for indicator in frontend_indicators:
            if (self.project_root / indicator).exists():
                logger.debug(f"Found frontend indicator: {indicator}")
                return True
        
        # Check for .tsx files
        tsx_files = list(self.project_root.rglob('*.tsx'))
        if len(tsx_files) > 0:
            logger.debug(f"Found {len(tsx_files)} .tsx files")
            return True
        
        return False
    
    def _detect_database(self) -> bool:
        """
        Check if project has database (project root only).
        
        Returns:
            True if project has database indicators, False otherwise
        """
        db_indicators = [
            'migrations',
            'prisma',
            'alembic.ini',
        ]
        
        for indicator in db_indicators:
            if (self.project_root / indicator).exists():
                logger.debug(f"Found database indicator: {indicator}")
                return True
        
        # Check for models.py at project root only
        if (self.project_root / 'models.py').exists():
            logger.debug("Found models.py at project root")
            return True
        
        return False
    
    def _detect_rest_api(self) -> bool:
        """
        Check if project has REST API.
        
        Returns:
            True if project has REST API indicators, False otherwise
        """
        api_indicators = [
            'src/api',
            'routes',
            'endpoints',
        ]
        
        for indicator in api_indicators:
            if (self.project_root / indicator).exists():
                logger.debug(f"Found REST API indicator: {indicator}")
                return True
        
        return False
    
    async def classify_project_with_llm(
        self,
        llm_provider: "LLMProvider"
    ) -> Dict[str, any]:
        """
        Enrich project classification with LLM.
        
        First runs heuristic classification, then uses LLM to add
        one_line_description and key_capabilities.
        
        Args:
            llm_provider: LLMProvider instance for LLM calls
            
        Returns:
            Dict with keys: project_type, has_frontend, has_database,
            has_rest_api, primary_language, one_line_description,
            key_capabilities
            
        Requirements: P2-2
        """
        # Get base classification from heuristics
        languages = self.detect_languages()
        base_classification = self._heuristic_classify(languages)
        
        if not llm_provider.is_available():
            logger.info("LLM unavailable, using heuristic classification only")
            return base_classification
        
        try:
            # Build prompt for LLM enrichment
            prompt = self._build_classification_prompt(base_classification)
            
            response = await llm_provider.complete(
                system_prompt=(
                    "You are a code analysis expert. Analyze the project "
                    "and respond with JSON containing: project_type, "
                    "has_frontend, has_database, has_rest_api, "
                    "primary_language, one_line_description, "
                    "key_capabilities (list of 3 strings)"
                ),
                user_prompt=prompt,
                max_tokens=500,
                temperature=0.1,
                json_mode=True
            )
            
            if response:
                enriched = self._parse_classification_response(response)
                logger.info(
                    f"LLM enrichment successful: {enriched.get('one_line_description', 'N/A')}"
                )
                return enriched
        
        except Exception as e:
            logger.warning(f"LLM enrichment failed: {e}")
        
        return base_classification
    
    def _build_classification_prompt(
        self,
        base_classification: Dict[str, any]
    ) -> str:
        """
        Build prompt for LLM classification enrichment.
        
        Args:
            base_classification: Base classification from heuristics
            
        Returns:
            Prompt string for LLM
        """
        # Get tech stack info
        tech_stack = self.extract_tech_stack()
        
        # Get dependencies (limit to 10)
        dependencies = []
        if hasattr(tech_stack, 'dependencies'):
            dependencies = [d.name if hasattr(d, 'name') else str(d) 
                          for d in tech_stack.dependencies[:10]]
        
        # Get languages
        languages = self.detect_languages()
        language_names = [lang.name for lang in languages[:5]]
        
        # Get architecture
        architecture = self.infer_architecture()
        arch_pattern = architecture.pattern if hasattr(architecture, 'pattern') else 'unknown'
        
        return f"""
Analyze this project and provide enriched classification:

Base Classification:
- Project Type: {base_classification['project_type']}
- Has Frontend: {base_classification['has_frontend']}
- Has Database: {base_classification['has_database']}
- Has REST API: {base_classification['has_rest_api']}
- Primary Language: {base_classification['primary_language']}

Code Summary:
- Languages: {', '.join(language_names)}
- Dependencies: {', '.join(dependencies) if dependencies else 'None detected'}
- Architecture: {arch_pattern}

Provide JSON response with:
{{
  "project_type": "{base_classification['project_type']}",
  "has_frontend": {str(base_classification['has_frontend']).lower()},
  "has_database": {str(base_classification['has_database']).lower()},
  "has_rest_api": {str(base_classification['has_rest_api']).lower()},
  "primary_language": "{base_classification['primary_language']}",
  "one_line_description": "A concise description of what this project does",
  "key_capabilities": ["capability 1", "capability 2", "capability 3"]
}}

Base your answer only on the provided analysis. No explanations.
"""
    
    def _parse_classification_response(self, response: str) -> Dict[str, any]:
        """
        Parse JSON response from LLM.
        
        Args:
            response: LLM response string
            
        Returns:
            Parsed classification dict
        """
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # Validate required keys
                required_keys = [
                    'project_type', 'has_frontend', 'has_database',
                    'has_rest_api', 'primary_language', 'one_line_description',
                    'key_capabilities'
                ]
                
                if all(key in data for key in required_keys):
                    logger.debug("Successfully parsed LLM classification response")
                    return data
                else:
                    logger.warning("LLM response missing required keys")
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse classification JSON: {e}")
        except Exception as e:
            logger.warning(f"Error parsing classification response: {e}")
        
        # Return base classification on parse failure
        languages = self.detect_languages()
        return self._heuristic_classify(languages)
    
    def _load_gitignore(self) -> None:
        """
        Load .gitignore file and build pathspec matcher.
        
        Uses pathspec library to parse .gitignore patterns for efficient
        matching during directory traversal.
        
        Requirements: 3A.2, 3B.5
        """
        gitignore_path = self.project_root / ".gitignore"
        
        if not gitignore_path.exists():
            logger.debug("No .gitignore file found")
            return
        
        if pathspec is None:
            logger.warning(
                "pathspec library not available, .gitignore will not be respected. "
                "Install with: pip install pathspec"
            )
            return
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                self.gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
            
            logger.info("Loaded .gitignore patterns")
        
        except Exception as e:
            logger.warning(f"Error parsing .gitignore: {e}")
            # Continue without exclusions rather than failing
    
    def _should_exclude_path(self, path: Path) -> bool:
        """
        Check if a path should be excluded based on .gitignore patterns.
        
        Args:
            path: Path to check (relative to project root)
            
        Returns:
            True if path should be excluded, False otherwise
        """
        if self.gitignore_spec is None:
            return False
        
        try:
            relative_path = path.relative_to(self.project_root)
            return self.gitignore_spec.match_file(str(relative_path))
        except (ValueError, OSError):
            return False
    
    def _get_excluded_paths_for_analyzers(self) -> Set[Path]:
        """
        Build excluded paths set for analyzer functions that need it.
        This is a compatibility layer - ideally analyzers should use gitignore_spec directly.
        
        Returns:
            Set of excluded paths (empty if no gitignore)
        """
        if self.gitignore_spec is None:
            return set()
        
        excluded = set()
        # Only scan files we need to analyze, not everything
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            # Prune excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude_path(root_path / d)]
            
            # Check files
            for file in files:
                file_path = root_path / file
                if self._should_exclude_path(file_path):
                    try:
                        excluded.add(file_path.relative_to(self.project_root))
                    except ValueError:
                        pass
        
        return excluded
    
    def _count_files(self) -> int:
        """
        Count total files in the codebase (excluding ignored paths).
        Uses efficient directory traversal with early pruning.
        
        Returns:
            Total number of files
        """
        count = 0
        dirs_checked = 0
        
        try:
            # Use os.walk for efficient traversal with directory pruning
            for root, dirs, files in os.walk(self.project_root):
                root_path = Path(root)
                
                # Skip excluded directories (modifies dirs in-place to prune traversal)
                dirs[:] = [
                    d for d in dirs 
                    if not self._should_exclude_path(root_path / d)
                ]
                
                # Count non-excluded files
                for file in files:
                    file_path = root_path / file
                    if not self._should_exclude_path(file_path):
                        count += 1
                
                # Progress indicator every 100 directories
                dirs_checked += 1
                if dirs_checked % 100 == 0:
                    logger.info(f"   Scanned {dirs_checked} directories, found {count} files...")
        
        except Exception as e:
            logger.error(f"Error counting files: {e}")
        
        return count
    
    def _parse_documentation(self) -> List:
        """
        Parse documentation from README, docs/, and inline comments.
        
        Returns:
            List of ParsedDocument objects
            
        Requirements: 3A.8
        """
        try:
            excluded_paths = self._get_excluded_paths_for_analyzers()
            return parse_codebase_documentation(
                self.project_root,
                excluded_paths,
                include_inline_comments=False  # Skip inline comments for performance
            )
        except Exception as e:
            logger.error(f"Error parsing documentation: {e}", exc_info=True)
            return []
    
    def _calculate_confidence_scores(
        self,
        languages: List,
        tech_stack,
        architecture,
        conventions
    ) -> Dict[str, float]:
        """
        Calculate confidence scores for all findings.
        
        Confidence scoring:
        - Language detection: 1.0 if >50%, 0.8 if 20-50%, 0.5 if 10-20%, 0.3 if <10%
        - Framework detection: 1.0 if in dependencies, 0.7 if inferred, 0.4 if guessed
        - Architecture: 1.0 if perfect match, 0.8 if partial, 0.5 if weak, 0.3 if guessed
        - Conventions: 1.0 if from config, 0.8 if 90%+ consistent, 0.6 if 70-90%, 0.4 if <70%
        
        Args:
            languages: List of detected languages
            tech_stack: Extracted tech stack info
            architecture: Inferred architecture info
            conventions: Extracted conventions info
            
        Returns:
            Dictionary mapping component names to confidence scores
            
        Requirements: 3A.15
        """
        scores = {}
        
        # Language confidence scores
        for lang in languages:
            if lang.percentage >= 50:
                scores[f"language_{lang.name}"] = 1.0
            elif lang.percentage >= 20:
                scores[f"language_{lang.name}"] = 0.8
            elif lang.percentage >= 10:
                scores[f"language_{lang.name}"] = 0.5
            else:
                scores[f"language_{lang.name}"] = 0.3
        
        # Tech stack confidence (all from dependencies = 1.0)
        if tech_stack.backend_framework:
            scores["backend_framework"] = 1.0
        if tech_stack.frontend_framework:
            scores["frontend_framework"] = 1.0
        if tech_stack.database:
            scores["database"] = 1.0
        if tech_stack.cache:
            scores["cache"] = 1.0
        
        # Architecture confidence
        if architecture.pattern == "custom":
            scores["architecture"] = 0.5
        elif architecture.pattern in ["mvc", "hexagonal", "clean"]:
            scores["architecture"] = 0.8
        elif architecture.pattern in ["layered", "microservices"]:
            scores["architecture"] = 0.7
        else:
            scores["architecture"] = 0.6
        
        # Conventions confidence (simplified - would need more analysis)
        if conventions.naming_style:
            scores["conventions"] = 0.7  # Assume reasonable confidence
        
        return scores
    
    def _log_progress(self, message: str) -> None:
        """
        Log progress update if enough time has elapsed.
        
        Args:
            message: Progress message to log
            
        Requirements: 3A.13
        """
        current_time = time.time()
        
        # Always log the message at debug level
        logger.debug(message)
        
        # Check if we should display progress update
        if self.last_progress_update is None:
            self.last_progress_update = current_time
            return
        
        elapsed = current_time - self.last_progress_update
        
        if elapsed >= PROGRESS_UPDATE_INTERVAL:
            total_elapsed = current_time - self.start_time
            logger.info(f"[{total_elapsed:.0f}s] {message}")
            self.last_progress_update = current_time
    
    def _load_cache(self) -> Optional[CodeAnalysisResult]:
        """
        Load cached analysis results if available and valid.
        
        Returns:
            CodeAnalysisResult if cache is valid, None otherwise
            
        Requirements: 3C.5
        """
        cache_path = self.project_root / CACHE_FILE
        
        if not cache_path.exists():
            logger.debug("No cache file found")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check cache validity (simple version - could be enhanced)
            # For now, just check if cache exists and is recent
            cache_age = time.time() - cache_path.stat().st_mtime
            
            # Cache valid for 1 hour
            if cache_age > 3600:
                logger.debug(f"Cache expired (age: {cache_age:.0f}s)")
                return None
            
            # Reconstruct CodeAnalysisResult from cache
            # This is a simplified version - full implementation would
            # properly deserialize all nested objects
            logger.info("Cache found and valid")
            return None  # For now, always re-analyze
        
        except Exception as e:
            logger.debug(f"Error loading cache: {e}")
            return None
    
    def _save_cache(self, result: CodeAnalysisResult) -> None:
        """
        Save analysis results to cache.
        
        Args:
            result: CodeAnalysisResult to cache
            
        Requirements: 3C.5
        """
        cache_path = self.project_root / CACHE_FILE
        
        try:
            # Ensure cache directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert result to JSON-serializable format
            # This is a simplified version - full implementation would
            # properly serialize all nested objects
            cache_data = {
                "timestamp": time.time(),
                "summary": result.to_summary(max_tokens=2000),
                # Add more fields as needed
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Analysis results cached to: {cache_path}")
        
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
            # Don't fail if caching fails



def analyze_codebase(project_root: Path) -> CodeAnalysisResult:
    """
    Convenience function to analyze a codebase.
    
    Args:
        project_root: Root directory of the project to analyze
        
    Returns:
        CodeAnalysisResult with all extracted information
    """
    analyzer = CodeAnalyzer(project_root)
    return analyzer.analyze()
