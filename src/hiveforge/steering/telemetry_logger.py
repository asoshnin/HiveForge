"""
Telemetry logging for the Steering Assistant v02.

This module provides the TelemetryLogger class for logging steering operations
to file-based storage in .kiro/.telemetry/.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class TelemetryLogger:
    """Logs telemetry data for steering operations."""
    
    def __init__(
        self,
        telemetry_dir: Path = Path(".kiro/.telemetry"),
        enabled: bool = True,
    ):
        """
        Initialize the TelemetryLogger.
        
        Args:
            telemetry_dir: Directory to store telemetry data
            enabled: Whether telemetry is enabled
        """
        self.telemetry_dir = telemetry_dir
        self.enabled = enabled
        self._session_id: Optional[str] = None
        self._session_start: Optional[datetime] = None
        self._session_data: Dict[str, Any] = {}
        
        if self.enabled:
            self.telemetry_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())[:8]
    
    def log_session(
        self,
        workflow_type: str,
        project_root: Path,
        files_count: int = 0,
    ) -> str:
        """
        Start a new telemetry session.
        
        Args:
            workflow_type: Type of workflow (AUTONOMOUS or FALLBACK)
            project_root: Path to project root
            files_count: Number of files to process
            
        Returns:
            Session ID
        """
        if not self.enabled:
            return ""
        
        self._session_id = self._generate_session_id()
        self._session_start = datetime.now()
        
        self._session_data = {
            "session_id": self._session_id,
            "timestamp": self._session_start.isoformat(),
            "workflow_type": workflow_type,
            "project_root": str(project_root),
            "files_count": files_count,
            "files_processed": 0,
            "files_failed": 0,
            "confidence_scores": [],
            "validation_results": [],
            "token_usage": {
                "per_file": [],
                "total": 0,
            },
            "errors": [],
            "user_interactions": [],
            "durations_ms": [],
        }
        
        return self._session_id
    
    def log_workflow_type(self, workflow_type: str) -> None:
        """
        Log the workflow type.
        
        Args:
            workflow_type: Type of workflow (AUTONOMOUS or FALLBACK)
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["workflow_type"] = workflow_type
    
    def log_confidence_scores(
        self,
        file_name: str,
        scores: List[Dict[str, Any]],
    ) -> None:
        """
        Log confidence scores for a file.
        
        Args:
            file_name: Name of the file
            scores: List of confidence score records
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["confidence_scores"].append({
            "file": file_name,
            "scores": scores,
        })
    
    def log_validation_results(
        self,
        file_name: str,
        results: Dict[str, Any],
    ) -> None:
        """
        Log validation results for a file.
        
        Args:
            file_name: Name of the file
            results: Validation results dictionary
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["validation_results"].append({
            "file": file_name,
            "results": results,
        })
    
    def log_token_usage(
        self,
        file_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """
        Log token usage for a file.
        
        Args:
            file_name: Name of the file
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        if not self.enabled or not self._session_id:
            return
        
        total = prompt_tokens + completion_tokens
        
        self._session_data["token_usage"]["per_file"].append({
            "file": file_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total,
        })
        
        self._session_data["token_usage"]["total"] += total
    
    def log_error(
        self,
        error_type: str,
        message: str,
        file_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an error.
        
        Args:
            error_type: Type of error
            message: Error message
            file_name: Optional file name
            context: Optional error context
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "file": file_name,
            "context": context or {},
        })
    
    def log_user_interaction(
        self,
        interaction_type: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Log a user interaction.
        
        Args:
            interaction_type: Type of interaction (conflict_resolution, question_answer, etc.)
            details: Interaction details
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["user_interactions"].append({
            "timestamp": datetime.now().isoformat(),
            "interaction_type": interaction_type,
            "details": details,
        })
    
    def log_duration(
        self,
        operation: str,
        duration_ms: float,
        file_name: Optional[str] = None,
    ) -> None:
        """
        Log operation duration.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            file_name: Optional file name
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["durations_ms"].append({
            "operation": operation,
            "duration_ms": duration_ms,
            "file": file_name,
        })
    
    def record_file_processed(
        self,
        file_name: str,
        success: bool = True,
    ) -> None:
        """
        Record that a file was processed.
        
        Args:
            file_name: Name of the file
            success: Whether processing was successful
        """
        if not self.enabled or not self._session_id:
            return
        
        self._session_data["files_processed"] += 1
        
        if not success:
            self._session_data["files_failed"] += 1
    
    def update_summary(self) -> Path:
        """
        Update the telemetry summary file.
        
        Returns:
            Path to the summary file
        """
        if not self.enabled or not self._session_id:
            return Path("")
        
        summary_path = self.telemetry_dir / "summary.json"
        
        # Load existing summary or create new
        if summary_path.exists():
            with open(summary_path, "r") as f:
                summary = json.load(f)
        else:
            summary = {
                "total_sessions": 0,
                "total_files_processed": 0,
                "total_files_failed": 0,
                "total_token_usage": 0,
                "autonomous_sessions": 0,
                "fallback_sessions": 0,
            }
        
        # Update summary with current session data
        session_data = self._session_data
        
        summary["total_sessions"] += 1
        summary["total_files_processed"] += session_data["files_processed"]
        summary["total_files_failed"] += session_data["files_failed"]
        summary["total_token_usage"] += session_data["token_usage"]["total"]
        
        if session_data["workflow_type"] == "AUTONOMOUS":
            summary["autonomous_sessions"] += 1
        else:
            summary["fallback_sessions"] += 1
        
        # Save summary
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        return summary_path
    
    def save_session(self) -> Path:
        """
        Save the current session data to a file.
        
        Returns:
            Path to the session file
        """
        if not self.enabled or not self._session_id:
            return Path("")
        
        # Ensure sessions directory exists
        sessions_dir = self.telemetry_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Save session data
        session_path = sessions_dir / f"{self._session_start.strftime('%Y%m%d_%H%M%S')}_{self._session_id}.json"
        
        with open(session_path, "w") as f:
            json.dump(self._session_data, f, indent=2)
        
        # Update summary
        self.update_summary()
        
        return session_path
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Session summary dictionary
        """
        if not self._session_data:
            return {}
        
        return {
            "session_id": self._session_id,
            "workflow_type": self._session_data["workflow_type"],
            "files_processed": self._session_data["files_processed"],
            "files_failed": self._session_data["files_failed"],
            "total_token_usage": self._session_data["token_usage"]["total"],
            "errors_count": len(self._session_data["errors"]),
            "user_interactions_count": len(self._session_data["user_interactions"]),
        }
    
    def disable(self) -> None:
        """Disable telemetry logging."""
        self.enabled = False
    
    def enable(self) -> None:
        """Enable telemetry logging."""
        self.enabled = True
