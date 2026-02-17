"""
Validation rules loader for the Steering Assistant v02.

This module provides the ValidationRulesLoader class for loading and parsing
validation_rules.yaml configuration.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationRulesLoader:
    """Loads and manages validation rules from YAML configuration."""
    
    DEFAULT_RULES_PATH = Path(__file__).parent.parent / "validation_rules.yaml"
    
    def __init__(self, rules_path: Optional[Path] = None):
        """
        Initialize the ValidationRulesLoader.
        
        Args:
            rules_path: Path to validation_rules.yaml. If None, uses default path.
        """
        self.rules_path = rules_path or self.DEFAULT_RULES_PATH
        self._rules: Optional[Dict[str, Any]] = None
        self._framework_classifications: Optional[Dict[str, List[str]]] = None
    
    def load_rules(self) -> Dict[str, Any]:
        """
        Load validation rules from YAML file.
        
        Returns:
            Parsed rules dictionary
            
        Raises:
            FileNotFoundError: If rules file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Validation rules file not found: {self.rules_path}")
        
        with open(self.rules_path, "r") as f:
            self._rules = yaml.safe_load(f)
        
        return self._rules
    
    def get_framework_classifications(self) -> Dict[str, List[str]]:
        """
        Get framework classifications from loaded rules.
        
        Returns:
            Dictionary mapping classification types to lists of frameworks
        """
        if self._rules is None:
            self.load_rules()
        
        if self._framework_classifications is None:
            self._framework_classifications = self._rules.get(
                "framework_classifications", {}
            )
        
        return self._framework_classifications
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get validation rules from loaded rules.
        
        Returns:
            List of rule dictionaries
        """
        if self._rules is None:
            self.load_rules()
        
        return self._rules.get("rules", [])
    
    def validate_rule_syntax(self, rule: Dict[str, Any]) -> List[str]:
        """
        Validate the syntax of a single rule.
        
        Args:
            rule: Rule dictionary to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        required_fields = ["id", "description", "severity", "check"]
        for field in required_fields:
            if field not in rule:
                errors.append(f"Rule missing required field: {field}")
        
        # Validate severity
        if "severity" in rule:
            valid_severities = ["CRITICAL", "MAJOR", "MINOR"]
            if rule["severity"] not in valid_severities:
                errors.append(
                    f"Invalid severity '{rule['severity']}'. "
                    f"Must be one of: {', '.join(valid_severities)}"
                )
        
        # Validate check field structure
        if "check" in rule:
            check = rule["check"]
            
            if not isinstance(check, dict):
                errors.append("'check' field must be a dictionary")
            else:
                # Check for file or files field
                if "file" not in check and "files" not in check:
                    errors.append("'check' must have either 'file' or 'files' field")
        
        return errors
    
    def validate_all_rules(self) -> List[str]:
        """
        Validate all rules in the configuration.
        
        Returns:
            List of validation errors (empty if all valid)
        """
        if self._rules is None:
            self.load_rules()
        
        all_errors = []
        rules = self.get_rules()
        
        for i, rule in enumerate(rules):
            errors = self.validate_rule_syntax(rule)
            if errors:
                all_errors.append(f"Rule {i + 1} ({rule.get('id', 'unnamed')}):")
                all_errors.extend(f"  {e}" for e in errors)
        
        return all_errors
