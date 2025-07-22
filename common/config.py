"""
Configuration management for AI Test Orchestrator
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AIConfig:
    """AI provider configuration"""
    default_provider: str = "anthropic"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_path: str = "./data/orchestrator.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class ProjectConfig:
    """Project-specific configuration"""
    default_language: str = "java"
    default_framework: str = "maven"
    templates_path: str = "./templates"
    output_path: str = r"C:\Users\user\test-projects"


@dataclass
class SystemConfig:
    """System-wide configuration"""
    log_level: str = "INFO"
    log_file: str = "./logs/orchestrator.log"
    max_concurrent_agents: int = 4
    command_timeout_seconds: int = 300


@dataclass
class OrchestratorConfig:
    """Main configuration container"""
    ai: AIConfig
    database: DatabaseConfig
    project: ProjectConfig
    system: SystemConfig

    @classmethod
    def load_from_env(cls) -> 'OrchestratorConfig':
        """Load configuration from environment variables"""

        # AI Configuration
        ai_config = AIConfig(
            default_provider=os.getenv("DEFAULT_AI_PROVIDER", "anthropic"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.7"))
        )

        # Database Configuration
        db_config = DatabaseConfig(
            db_path=os.getenv("DB_PATH", "./data/orchestrator.db"),
            backup_enabled=os.getenv("DB_BACKUP_ENABLED", "true").lower() == "true",
            backup_interval_hours=int(os.getenv("DB_BACKUP_INTERVAL", "24"))
        )

        # Project Configuration
        project_config = ProjectConfig(
            default_language=os.getenv("DEFAULT_LANGUAGE", "java"),
            default_framework=os.getenv("DEFAULT_FRAMEWORK", "maven"),
            templates_path=os.getenv("TEMPLATES_PATH", "./templates"),
            output_path=os.getenv("DEFAULT_OUTPUT_PATH", r"C:\Users\user\test-projects")
        )

        # System Configuration
        system_config = SystemConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "./logs/orchestrator.log"),
            max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "4")),
            command_timeout_seconds=int(os.getenv("COMMAND_TIMEOUT", "300"))
        )

        return cls(
            ai=ai_config,
            database=db_config,
            project=project_config,
            system=system_config
        )

    def save_to_file(self, file_path: str) -> None:
        """Save configuration to JSON file"""
        config_dict = asdict(self)

        # Remove sensitive data before saving
        if config_dict['ai']['anthropic_api_key']:
            config_dict['ai']['anthropic_api_key'] = "***"
        if config_dict['ai']['openai_api_key']:
            config_dict['ai']['openai_api_key'] = "***"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'OrchestratorConfig':
        """Load configuration from JSON file (without sensitive data)"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Load sensitive data from environment
        config_data['ai']['anthropic_api_key'] = os.getenv("ANTHROPIC_API_KEY")
        config_data['ai']['openai_api_key'] = os.getenv("OPENAI_API_KEY")

        return cls(
            ai=AIConfig(**config_data['ai']),
            database=DatabaseConfig(**config_data['database']),
            project=ProjectConfig(**config_data['project']),
            system=SystemConfig(**config_data['system'])
        )

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check AI API keys
        if self.ai.default_provider == "anthropic" and not self.ai.anthropic_api_key:
            errors.append("Anthropic API key is required when using Anthropic as default provider")

        if self.ai.default_provider == "openai" and not self.ai.openai_api_key:
            errors.append("OpenAI API key is required when using OpenAI as default provider")

        # Check paths
        db_dir = os.path.dirname(self.database.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory: {e}")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

        return True


# Global configuration instance
_config: Optional[OrchestratorConfig] = None


def get_config() -> OrchestratorConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = OrchestratorConfig.load_from_env()
        _config.validate()
    return _config


def reload_config() -> OrchestratorConfig:
    """Reload configuration from environment"""
    global _config
    _config = OrchestratorConfig.load_from_env()
    _config.validate()
    return _config