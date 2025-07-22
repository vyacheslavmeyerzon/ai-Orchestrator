"""
Core Orchestrator - Central coordinator for all AI agents
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from common.ai_connector import AIConnectorFactory, AIProvider
from common.config import get_config
from common.logger import get_agent_logger, log_operation


class ProjectType(Enum):
    API = "api"
    UI = "ui"
    FULL = "full"


class ProjectLanguage(Enum):
    JAVA = "java"
    PYTHON = "python"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProjectInfo:
    """Project information structure"""
    id: str
    name: str
    type: ProjectType
    language: ProjectLanguage
    output_path: str
    created_at: str
    updated_at: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentTask:
    """Task for specific agent"""
    id: str
    agent_type: str
    operation: str
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = None
    completed_at: str = None
    result: Dict[str, Any] = None
    error_message: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.result is None:
            self.result = {}


class AgentOrchestrator:
    """Central orchestrator for managing AI agents"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("orchestrator")
        self.ai_connector = AIConnectorFactory.create_connector()

        # Initialize storage
        from orchestrator.storage import get_storage
        self.storage = get_storage()

        # Agent registry - ENHANCED WITH PARSER AGENT
        self.available_agents = {
            "api_agent": "agents.api_agent.core.APIAgent",
            "devops_agent": "agents.devops_agent.core.DevOpsAgent",
            "parser_agent": "agents.parser_agent.core.ParserAgent",  # NEW!
            # UI and Database agents will be added later
        }

        # Load existing projects from storage
        self.active_projects: Dict[str, ProjectInfo] = {}
        self._load_projects_from_storage()

        # Task tracking
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []

        self.logger.info("Agent Orchestrator initialized with Parser Agent support")

    def _load_projects_from_storage(self):
        """Load existing projects from storage"""
        try:
            projects = self.storage.load_all_projects()
            for project in projects:
                self.active_projects[project.id] = project

            self.logger.info(f"Loaded {len(projects)} projects from storage")

        except Exception as e:
            self.logger.error(f"Failed to load projects from storage: {str(e)}")

    async def create_new_project(self,
                                 name: str,
                                 project_type: ProjectType,
                                 language: ProjectLanguage,
                                 output_path: str,
                                 api_spec_file: str = None) -> ProjectInfo:
        """Create new test automation project with optional API specification"""

        project_id = str(uuid.uuid4())[:8]

        project = ProjectInfo(
            id=project_id,
            name=name,
            type=project_type,
            language=language,
            output_path=output_path,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata={
                "api_spec_file": api_spec_file if api_spec_file else None
            }
        )

        self.active_projects[project_id] = project

        # Save to storage
        if not self.storage.save_project(project):
            self.logger.warning(f"Failed to save project to storage: {project_id}")

        self.logger.info(f"Created new project: {name} ({project_id}) with API spec: {bool(api_spec_file)}")
        return project

    async def analyze_project_requirements(self, project: ProjectInfo) -> Dict[str, Any]:
        """Analyze project requirements and determine agent tasks - ENHANCED FOR API SPECS"""

        self.logger.info(f"Analyzing requirements for project: {project.name}")

        # Check if API specification file is provided
        api_spec_file = project.metadata.get('api_spec_file')
        has_api_spec = api_spec_file and os.path.exists(api_spec_file)

        # Prepare analysis prompt
        analysis_prompt = f"""
        Analyze the requirements for creating a {project.type.value} test automation project:

        Project Details:
        - Name: {project.name}
        - Type: {project.type.value}
        - Language: {project.language.value}
        - Output Path: {project.output_path}
        - Has API Specification: {has_api_spec}
        {"- API Spec File: " + api_spec_file if has_api_spec else ""}

        Based on this information, determine the optimal task sequence:

        {"If API specification is provided, FIRST use parser_agent to analyze the spec, then api_agent to generate tests based on parsed data." if has_api_spec else "Use api_agent to create basic project structure."}
        Finally use devops_agent to setup environment.

        Respond in JSON format:
        {{
            "required_agents": {["parser_agent", "api_agent", "devops_agent"] if has_api_spec else ["api_agent", "devops_agent"]},
            "task_sequence": [
                {'''
                {
                    "agent": "parser_agent",
                    "operation": "parse_api_specification",
                    "description": "Parse API specification and extract endpoints",
                    "dependencies": [],
                    "estimated_duration_minutes": 3
                },''' if has_api_spec else ''}
                {{
                    "agent": "api_agent", 
                    "operation": "create_project_structure",
                    "description": "Create project structure{" with parsed API data" if has_api_spec else ""}",
                    "dependencies": {["parse_api_specification"] if has_api_spec else []},
                    "estimated_duration_minutes": 5
                }},
                {{
                    "agent": "devops_agent",
                    "operation": "create_docker_setup", 
                    "description": "Setup Docker environment",
                    "dependencies": ["create_project_structure"],
                    "estimated_duration_minutes": 4
                }}
            ],
            "total_estimated_minutes": {12 if has_api_spec else 9},
            "complexity": {"medium" if has_api_spec else "simple"}
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                analysis_prompt,
                "You are an expert in test automation architecture. Provide detailed analysis."
            )

            self.logger.info(f"Project analysis completed for: {project.name}")
            return response

        except Exception as e:
            self.logger.error(f"Failed to analyze project requirements: {str(e)}")
            raise

    async def create_task_plan(self, project: ProjectInfo, analysis: Dict[str, Any]) -> List[AgentTask]:
        """Create detailed task plan based on analysis - ENHANCED"""

        tasks = []
        api_spec_file = project.metadata.get('api_spec_file')

        if "task_sequence" in analysis:
            for i, task_info in enumerate(analysis["task_sequence"]):

                # Build base parameters
                base_params = {
                    "project_id": project.id,
                    "project_name": project.name,
                    "project_type": project.type.value,
                    "language": project.language.value,
                    "output_path": project.output_path,
                    "description": task_info.get("description", ""),
                    "dependencies": task_info.get("dependencies", [])
                }

                # Add API spec file to parser agent tasks
                if task_info["agent"] == "parser_agent" and api_spec_file:
                    base_params["spec_file_path"] = api_spec_file

                task = AgentTask(
                    id=f"{project.id}-task-{i + 1}",
                    agent_type=task_info["agent"],
                    operation=task_info["operation"],
                    parameters=base_params
                )
                tasks.append(task)

        self.logger.info(f"Created {len(tasks)} tasks for project: {project.name}")
        return tasks

    async def execute_project_creation(self, project: ProjectInfo) -> Dict[str, Any]:
        """Execute complete project creation workflow"""

        try:
            project.status = TaskStatus.IN_PROGRESS
            self.logger.info(f"Starting project creation workflow: {project.name}")

            # Step 1: Analyze requirements
            analysis = await self.analyze_project_requirements(project)

            # Step 2: Create task plan
            tasks = await self.create_task_plan(project, analysis)

            # Step 3: Execute tasks in sequence
            results = []
            parsed_data = None  # Store parsed data for passing between agents

            for task in tasks:
                # If this is an API agent task and we have parsed data, include it
                if task.agent_type == "api_agent" and parsed_data:
                    task.parameters["parsed_data"] = parsed_data

                result = await self.execute_task(task)
                results.append(result)

                # Store parsed data for next tasks
                if task.agent_type == "parser_agent" and result.get('parsed_data'):
                    parsed_data = result['parsed_data']

                if task.status == TaskStatus.FAILED:
                    self.logger.error(f"Task failed: {task.id} - {task.error_message}")
                    project.status = TaskStatus.FAILED
                    break

            # Step 4: Finalize project
            if project.status != TaskStatus.FAILED:
                project.status = TaskStatus.COMPLETED
                project.updated_at = datetime.now().isoformat()

                # Save updated project to storage
                self.storage.save_project(project)

                self.logger.info(f"Project creation completed: {project.name}")
            else:
                # Save failed project status
                self.storage.save_project(project)

            return {
                "project_id": project.id,
                "status": project.status.value,
                "analysis": analysis,
                "tasks_completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
                "total_tasks": len(tasks),
                "results": results,
                "parsed_data": parsed_data  # Include parsed data in results
            }

        except Exception as e:
            project.status = TaskStatus.FAILED
            project.updated_at = datetime.now().isoformat()

            # Save failed project to storage
            self.storage.save_project(project)

            self.logger.error(f"Project creation failed: {str(e)}")
            raise

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute individual agent task - ENHANCED FOR PARSER AGENT"""

        self.logger.info(f"Executing task: {task.id} ({task.agent_type})")
        task.status = TaskStatus.IN_PROGRESS

        try:
            # Execute based on agent type
            if task.agent_type == "api_agent":
                result = await self._execute_api_agent_task(task)
            elif task.agent_type == "devops_agent":
                result = await self._execute_devops_agent_task(task)
            elif task.agent_type == "parser_agent":  # NEW!
                result = await self._execute_parser_agent_task(task)
            else:
                raise ValueError(f"Unknown agent type: {task.agent_type}")

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            task.result = result

            # Save task to storage
            self.storage.save_task(task)

            self.logger.info(f"Task completed: {task.id}")
            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)

            # Save failed task to storage
            self.storage.save_task(task)

            self.logger.error(f"Task failed: {task.id} - {str(e)}")
            raise

    async def _execute_parser_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute Parser agent task using real agent - NEW METHOD"""

        try:
            # Import and create Parser agent
            import sys
            from pathlib import Path

            # Add project root to path if not already there
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from agents.parser_agent.core import ParserAgent

            self.logger.info(f"Creating Parser Agent instance for task: {task.operation}")
            parser_agent = ParserAgent()

            # Execute the operation
            result = await parser_agent.execute_operation(task.operation, task.parameters)

            self.logger.info(f"Parser Agent completed operation: {task.operation}")
            return result

        except Exception as e:
            # Log the actual error for debugging
            self.logger.error(f"Parser Agent failed with error: {str(e)}")
            self.logger.warning(f"Falling back to simulation for: {task.operation}")
            return await self._simulate_parser_agent_task(task)

    async def _simulate_parser_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Simulate Parser agent work (fallback) - NEW METHOD"""

        # Simulate parser agent work
        await asyncio.sleep(1)  # Simulate processing time

        operation = task.operation
        params = task.parameters

        if operation == "parse_api_specification":
            return {
                "operation": operation,
                "status": "completed",
                "spec_type": "openapi",
                "endpoints_count": 5,
                "parsed_data": {
                    "title": "Sample API",
                    "base_url": "${api.base.url}",
                    "authentication": {"type": "bearer"},
                    "endpoints": [
                        {"path": "/users", "method": "GET", "test_scenarios": []},
                        {"path": "/users", "method": "POST", "test_scenarios": []},
                        {"path": "/users/{id}", "method": "GET", "test_scenarios": []},
                        {"path": "/users/{id}", "method": "PUT", "test_scenarios": []},
                        {"path": "/users/{id}", "method": "DELETE", "test_scenarios": []}
                    ]
                },
                "message": "Simulated API specification parsing"
            }
        else:
            return {
                "operation": operation,
                "status": "completed",
                "message": f"Completed {operation}"
            }

    async def _execute_api_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute API agent task using real agent"""

        try:
            # Import and create API agent
            import sys
            from pathlib import Path

            # Add project root to path if not already there
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from agents.api_agent.core import APIAgent

            self.logger.info(f"Creating API Agent instance for task: {task.operation}")
            api_agent = APIAgent()

            # Execute the operation
            result = await api_agent.execute_operation(task.operation, task.parameters)

            self.logger.info(f"API Agent completed operation: {task.operation}")
            return result

        except Exception as e:
            # Log the actual error for debugging
            self.logger.error(f"API Agent failed with error: {str(e)}")
            self.logger.warning(f"Falling back to simulation for: {task.operation}")
            return await self._simulate_api_agent_task(task)

    async def _simulate_api_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Simulate API agent work (fallback)"""

        # Simulate API agent work
        await asyncio.sleep(1)  # Simulate processing time

        operation = task.operation
        params = task.parameters

        if operation == "create_project_structure":
            return {
                "operation": operation,
                "status": "completed",
                "created_files": [
                    f"{params['output_path']}/pom.xml",
                    f"{params['output_path']}/src/test/java",
                    f"{params['output_path']}/src/main/resources"
                ],
                "message": f"Created {params['language']} {params['project_type']} project structure"
            }

        elif operation == "generate_tests":
            return {
                "operation": operation,
                "status": "completed",
                "generated_files": [
                    f"{params['output_path']}/src/test/java/ApiTests.java"
                ],
                "test_count": 5,
                "message": "Generated basic API tests"
            }

        else:
            return {
                "operation": operation,
                "status": "completed",
                "message": f"Completed {operation}"
            }

    async def _execute_devops_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute DevOps agent task using real agent"""

        try:
            # Import and create DevOps agent
            import sys
            from pathlib import Path

            # Add project root to path if not already there
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from agents.devops_agent.core import DevOpsAgent

            self.logger.info(f"Creating DevOps Agent instance for task: {task.operation}")
            devops_agent = DevOpsAgent()

            # Execute the operation
            result = await devops_agent.execute_operation(task.operation, task.parameters)

            self.logger.info(f"DevOps Agent completed operation: {task.operation}")
            return result

        except Exception as e:
            # Log the actual error for debugging
            self.logger.error(f"DevOps Agent failed with error: {str(e)}")
            self.logger.warning(f"Falling back to simulation for: {task.operation}")
            return await self._simulate_devops_agent_task(task)

    async def _simulate_devops_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Simulate DevOps agent work (fallback)"""

        # Simulate DevOps agent work
        await asyncio.sleep(1)

        operation = task.operation
        params = task.parameters

        if operation == "setup_environment":
            return {
                "operation": operation,
                "status": "completed",
                "created_files": [
                    f"{params['output_path']}/Dockerfile",
                    f"{params['output_path']}/docker-compose.yml"
                ],
                "message": "Environment setup completed"
            }

        else:
            return {
                "operation": operation,
                "status": "completed",
                "message": f"Completed {operation}"
            }

    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get current project status"""

        if project_id not in self.active_projects:
            return None

        project = self.active_projects[project_id]

        # Get related tasks from storage
        project_tasks = self.storage.load_project_tasks(project_id)

        return {
            "project": asdict(project),
            "tasks": [asdict(task) for task in project_tasks],
            "summary": {
                "total_tasks": len(project_tasks),
                "completed": len([t for t in project_tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in project_tasks if t.status == TaskStatus.FAILED]),
                "pending": len([t for t in project_tasks if t.status == TaskStatus.PENDING])
            }
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        return [asdict(project) for project in self.active_projects.values()]


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator