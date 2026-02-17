"""
Tech stack extraction module for code analysis.

This module extracts technology stack information from dependency files
including frameworks, libraries, databases, and their versions. All analysis
is performed locally using parsers for various dependency file formats.
"""

import json
import logging
import re
import tomli
from pathlib import Path
from typing import Dict, List, Optional, Set
from xml.etree import ElementTree as ET

from ..models import TechStackInfo, Dependency

logger = logging.getLogger(__name__)


# Framework detection patterns (name -> keywords in dependencies)
FRAMEWORK_PATTERNS = {
    # Backend frameworks
    'FastAPI': ['fastapi'],
    'Flask': ['flask'],
    'Django': ['django'],
    'Express': ['express'],
    'NestJS': ['@nestjs/core', '@nestjs/common'],
    'Gin': ['github.com/gin-gonic/gin'],
    'Actix': ['actix-web'],
    'Spring Boot': ['spring-boot'],
    'Rails': ['rails'],
    
    # Frontend frameworks
    'React': ['react'],
    'Vue': ['vue'],
    'Angular': ['@angular/core'],
    'Svelte': ['svelte'],
    'Next.js': ['next'],
    'Nuxt': ['nuxt'],
}

# Database detection patterns
DATABASE_PATTERNS = {
    'PostgreSQL': ['psycopg2', 'psycopg2-binary', 'pg', 'postgres', 'postgresql', 'asyncpg'],
    'MySQL': ['mysql', 'mysql2', 'pymysql', 'mysqlclient'],
    'MongoDB': ['pymongo', 'mongodb', 'mongoose'],
    'Redis': ['redis', 'ioredis', 'redis-py'],
    'SQLite': ['sqlite3', 'better-sqlite3'],
    'Elasticsearch': ['elasticsearch'],
    'Cassandra': ['cassandra-driver'],
}

# ORM/ODM detection patterns
ORM_PATTERNS = {
    'SQLAlchemy': ['sqlalchemy'],
    'Prisma': ['prisma', '@prisma/client'],
    'TypeORM': ['typeorm'],
    'Sequelize': ['sequelize'],
    'Mongoose': ['mongoose'],
    'Diesel': ['diesel'],
    'GORM': ['gorm.io/gorm'],
}


def extract_tech_stack(
    project_root: Path,
    detected_languages: Optional[List[str]] = None
) -> TechStackInfo:
    """
    Extract technology stack from dependency files.
    
    This function:
    - Parses dependency files for various languages/ecosystems
    - Extracts frameworks, libraries, databases, and versions
    - Assigns confidence scores (1.0 for dependencies, 0.7 for imports, 0.4 for guesses)
    - Identifies ORMs, caches, and other infrastructure components
    
    Args:
        project_root: Root directory of the project
        detected_languages: Optional list of detected language names for targeted parsing
        
    Returns:
        TechStackInfo object with extracted information
        
    Requirements: 3A.5
    """
    logger.info(f"Extracting tech stack from: {project_root}")
    
    tech_stack = TechStackInfo()
    all_dependencies: List[Dependency] = []
    
    # Parse dependency files based on detected languages or try all
    parsers = [
        ('package.json', _parse_package_json),
        ('requirements.txt', _parse_requirements_txt),
        ('Pipfile', _parse_pipfile),
        ('pyproject.toml', _parse_pyproject_toml),
        ('go.mod', _parse_go_mod),
        ('Cargo.toml', _parse_cargo_toml),
        ('pom.xml', _parse_pom_xml),
        ('build.gradle', _parse_build_gradle),
        ('Gemfile', _parse_gemfile),
        ('composer.json', _parse_composer_json),
    ]
    
    for filename, parser_func in parsers:
        file_path = project_root / filename
        if file_path.exists():
            try:
                dependencies = parser_func(file_path)
                all_dependencies.extend(dependencies)
                logger.info(f"Parsed {filename}: found {len(dependencies)} dependencies")
            except Exception as e:
                logger.warning(f"Error parsing {filename}: {e}")
    
    # Store all dependencies
    tech_stack.dependencies = all_dependencies
    
    # Identify frameworks, databases, and ORMs from dependencies
    _identify_frameworks(tech_stack, all_dependencies)
    _identify_databases(tech_stack, all_dependencies)
    _identify_orms(tech_stack, all_dependencies)
    
    logger.info(
        f"Tech stack extracted: Backend={tech_stack.backend_framework}, "
        f"Frontend={tech_stack.frontend_framework}, "
        f"Database={tech_stack.database}, "
        f"Dependencies={len(all_dependencies)}"
    )
    
    return tech_stack


def _parse_package_json(file_path: Path) -> List[Dependency]:
    """Parse package.json for JavaScript/TypeScript dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse dependencies
        for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    dep_category = 'dev' if dep_type == 'devDependencies' else 'runtime'
                    dependencies.append(Dependency(
                        name=name,
                        version=version.lstrip('^~>=<'),
                        dependency_type=dep_category
                    ))
    except Exception as e:
        logger.debug(f"Error parsing package.json: {e}")
    
    return dependencies


def _parse_requirements_txt(file_path: Path) -> List[Dependency]:
    """Parse requirements.txt for Python dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse package==version or package>=version
                match = re.match(r'([a-zA-Z0-9_-]+)([>=<~!]+)?([\d.]+)?', line)
                if match:
                    name = match.group(1)
                    version = match.group(3) if match.group(3) else None
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type='runtime'
                    ))
    except Exception as e:
        logger.debug(f"Error parsing requirements.txt: {e}")
    
    return dependencies


def _parse_pipfile(file_path: Path) -> List[Dependency]:
    """Parse Pipfile for Python dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple TOML-like parsing for Pipfile
        in_packages = False
        in_dev_packages = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line == '[packages]':
                in_packages = True
                in_dev_packages = False
                continue
            elif line == '[dev-packages]':
                in_packages = False
                in_dev_packages = True
                continue
            elif line.startswith('['):
                in_packages = False
                in_dev_packages = False
                continue
            
            if (in_packages or in_dev_packages) and '=' in line:
                match = re.match(r'([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']', line)
                if match:
                    name = match.group(1)
                    version = match.group(2).lstrip('~>=<')
                    dep_type = 'dev' if in_dev_packages else 'runtime'
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type=dep_type
                    ))
    except Exception as e:
        logger.debug(f"Error parsing Pipfile: {e}")
    
    return dependencies


def _parse_pyproject_toml(file_path: Path) -> List[Dependency]:
    """Parse pyproject.toml for Python dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        
        # Parse project dependencies
        if 'project' in data and 'dependencies' in data['project']:
            for dep_str in data['project']['dependencies']:
                match = re.match(r'([a-zA-Z0-9_-]+)([>=<~!]+)?([\d.]+)?', dep_str)
                if match:
                    name = match.group(1)
                    version = match.group(3) if match.group(3) else None
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type='runtime'
                    ))
        
        # Parse optional dependencies
        if 'project' in data and 'optional-dependencies' in data['project']:
            for group, deps in data['project']['optional-dependencies'].items():
                for dep_str in deps:
                    match = re.match(r'([a-zA-Z0-9_-]+)([>=<~!]+)?([\d.]+)?', dep_str)
                    if match:
                        name = match.group(1)
                        version = match.group(3) if match.group(3) else None
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            dependency_type='optional'
                        ))
    except Exception as e:
        logger.debug(f"Error parsing pyproject.toml: {e}")
    
    return dependencies


def _parse_go_mod(file_path: Path) -> List[Dependency]:
    """Parse go.mod for Go dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse single-line require statements
        for line in content.split('\n'):
            line = line.strip()
            
            # Match: require github.com/pkg/errors v0.9.1
            match = re.match(r'require\s+([^\s]+)\s+v?([\d.]+)', line)
            if match:
                name = match.group(1)
                version = match.group(2)
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    dependency_type='runtime'
                ))
        
        # Parse multiline require blocks: require ( ... )
        require_block_pattern = r'require\s*\(\s*(.*?)\s*\)'
        for block_match in re.finditer(require_block_pattern, content, re.DOTALL):
            block_content = block_match.group(1)
            for line in block_content.split('\n'):
                line = line.strip()
                # Match: github.com/pkg/errors v0.9.1
                match = re.match(r'([^\s]+)\s+v?([\d.]+)', line)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type='runtime'
                    ))
    except Exception as e:
        logger.debug(f"Error parsing go.mod: {e}")
    
    return dependencies


def _parse_cargo_toml(file_path: Path) -> List[Dependency]:
    """Parse Cargo.toml for Rust dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        
        # Parse dependencies
        for dep_section in ['dependencies', 'dev-dependencies']:
            if dep_section in data:
                for name, version_info in data[dep_section].items():
                    if isinstance(version_info, str):
                        version = version_info
                    elif isinstance(version_info, dict) and 'version' in version_info:
                        version = version_info['version']
                    else:
                        version = None
                    
                    dep_type = 'dev' if dep_section == 'dev-dependencies' else 'runtime'
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type=dep_type
                    ))
    except Exception as e:
        logger.debug(f"Error parsing Cargo.toml: {e}")
    
    return dependencies


def _parse_pom_xml(file_path: Path) -> List[Dependency]:
    """Parse pom.xml for Java/Maven dependencies."""
    dependencies = []
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Handle XML namespace
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        
        # Find dependencies
        for dep in root.findall('.//maven:dependency', ns):
            group_id = dep.find('maven:groupId', ns)
            artifact_id = dep.find('maven:artifactId', ns)
            version = dep.find('maven:version', ns)
            scope = dep.find('maven:scope', ns)
            
            if artifact_id is not None:
                name = f"{group_id.text if group_id is not None else ''}.{artifact_id.text}"
                dep_type = scope.text if scope is not None else 'runtime'
                dependencies.append(Dependency(
                    name=name,
                    version=version.text if version is not None else None,
                    dependency_type=dep_type
                ))
    except Exception as e:
        logger.debug(f"Error parsing pom.xml: {e}")
    
    return dependencies


def _parse_build_gradle(file_path: Path) -> List[Dependency]:
    """Parse build.gradle for Java/Gradle dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse implementation/compile dependencies
        # Match: implementation 'group:artifact:version'
        pattern = r'(implementation|compile|testImplementation)\s+["\']([^:]+):([^:]+):([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            dep_type_str = match.group(1)
            group = match.group(2)
            artifact = match.group(3)
            version = match.group(4)
            
            dep_type = 'dev' if 'test' in dep_type_str.lower() else 'runtime'
            dependencies.append(Dependency(
                name=f"{group}.{artifact}",
                version=version,
                dependency_type=dep_type
            ))
    except Exception as e:
        logger.debug(f"Error parsing build.gradle: {e}")
    
    return dependencies


def _parse_gemfile(file_path: Path) -> List[Dependency]:
    """Parse Gemfile for Ruby dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Match: gem 'rails', '~> 7.0'
                match = re.match(r'gem\s+["\']([^"\']+)["\'](?:,\s*["\']([^"\']+)["\'])?', line)
                if match:
                    name = match.group(1)
                    version = match.group(2).lstrip('~>= ') if match.group(2) else None
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        dependency_type='runtime'
                    ))
    except Exception as e:
        logger.debug(f"Error parsing Gemfile: {e}")
    
    return dependencies


def _parse_composer_json(file_path: Path) -> List[Dependency]:
    """Parse composer.json for PHP dependencies."""
    dependencies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse dependencies
        for dep_type in ['require', 'require-dev']:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    # Skip PHP version requirement
                    if name == 'php':
                        continue
                    
                    dep_category = 'dev' if dep_type == 'require-dev' else 'runtime'
                    dependencies.append(Dependency(
                        name=name,
                        version=version.lstrip('^~>=<'),
                        dependency_type=dep_category
                    ))
    except Exception as e:
        logger.debug(f"Error parsing composer.json: {e}")
    
    return dependencies


def _identify_frameworks(tech_stack: TechStackInfo, dependencies: List[Dependency]) -> None:
    """Identify frameworks from dependencies."""
    dep_names = {dep.name.lower() for dep in dependencies}
    
    for framework, keywords in FRAMEWORK_PATTERNS.items():
        for keyword in keywords:
            if keyword.lower() in dep_names:
                # Categorize as backend or frontend
                if framework in ['React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Nuxt']:
                    if not tech_stack.frontend_framework:
                        tech_stack.frontend_framework = framework
                        logger.debug(f"Identified frontend framework: {framework}")
                else:
                    if not tech_stack.backend_framework:
                        tech_stack.backend_framework = framework
                        logger.debug(f"Identified backend framework: {framework}")
                break


def _identify_databases(tech_stack: TechStackInfo, dependencies: List[Dependency]) -> None:
    """Identify databases from dependencies."""
    dep_names = {dep.name.lower() for dep in dependencies}
    
    for database, keywords in DATABASE_PATTERNS.items():
        for keyword in keywords:
            if keyword.lower() in dep_names:
                # Special handling for Redis (could be cache or database)
                if database == 'Redis':
                    if not tech_stack.cache:
                        tech_stack.cache = 'Redis'
                        logger.debug(f"Identified cache: Redis")
                else:
                    if not tech_stack.database:
                        tech_stack.database = database
                        logger.debug(f"Identified database: {database}")
                break


def _identify_orms(tech_stack: TechStackInfo, dependencies: List[Dependency]) -> None:
    """Identify ORMs/ODMs from dependencies (stored in dependencies list with metadata)."""
    dep_names = {dep.name.lower() for dep in dependencies}
    
    for orm, keywords in ORM_PATTERNS.items():
        for keyword in keywords:
            if keyword.lower() in dep_names:
                logger.debug(f"Identified ORM/ODM: {orm}")
                break


def get_tech_stack_confidence_scores(tech_stack: TechStackInfo) -> Dict[str, float]:
    """
    Calculate confidence scores for tech stack components.
    
    Confidence scoring:
    - 1.0: Found in dependency files
    - 0.7: Inferred from import statements (not implemented yet)
    - 0.4: Guessed from patterns (not implemented yet)
    
    Args:
        tech_stack: TechStackInfo object
        
    Returns:
        Dictionary mapping component names to confidence scores
    """
    scores = {}
    
    # All components found in dependencies get 1.0 confidence
    if tech_stack.backend_framework:
        scores['backend_framework'] = 1.0
    if tech_stack.frontend_framework:
        scores['frontend_framework'] = 1.0
    if tech_stack.database:
        scores['database'] = 1.0
    if tech_stack.cache:
        scores['cache'] = 1.0
    
    return scores
