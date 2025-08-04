# orchestrator/storage.py
"""
Storage system for AI Test Orchestrator - handles project and task persistence
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from contextlib import contextmanager

from common.config import get_config
from orchestrator.core import ProjectInfo, AgentTask, TaskStatus, ProjectType, ProjectLanguage


class OrchestratorStorage:
    """Storage manager for orchestrator data"""

    def __init__(self, db_path: str = None):
        self.config = get_config()
        self.db_path = db_path or self.config.database.db_path
        self.logger = logging.getLogger('orchestrator.storage')

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_database()

        self.logger.info(f"Storage initialized with database: {self.db_path}")

    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            # Projects table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    language TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    result TEXT,
                    error_message TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks (project_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)")

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def save_project(self, project: ProjectInfo) -> bool:
        """Save or update project in database"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO projects 
                    (id, name, type, language, output_path, status, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project.id,
                    project.name,
                    project.type.value,
                    project.language.value,
                    project.output_path,
                    project.status.value,
                    project.created_at,
                    project.updated_at,
                    json.dumps(project.metadata) if project.metadata else None
                ))
                conn.commit()

            self.logger.debug(f"Saved project: {project.id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save project {project.id}: {str(e)}")
            return False

    def load_project(self, project_id: str) -> Optional[ProjectInfo]:
        """Load project by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM projects WHERE id = ?",
                    (project_id,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                return ProjectInfo(
                    id=row['id'],
                    name=row['name'],
                    type=ProjectType(row['type']),
                    language=ProjectLanguage(row['language']),
                    output_path=row['output_path'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    status=TaskStatus(row['status']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )

        except Exception as e:
            self.logger.error(f"Failed to load project {project_id}: {str(e)}")
            return None

    def load_all_projects(self) -> List[ProjectInfo]:
        """Load all projects"""
        projects = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM projects ORDER BY created_at DESC"
                )

                for row in cursor.fetchall():
                    project = ProjectInfo(
                        id=row['id'],
                        name=row['name'],
                        type=ProjectType(row['type']),
                        language=ProjectLanguage(row['language']),
                        output_path=row['output_path'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        status=TaskStatus(row['status']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    projects.append(project)

            self.logger.debug(f"Loaded {len(projects)} projects")

        except Exception as e:
            self.logger.error(f"Failed to load projects: {str(e)}")

        return projects

    def save_task(self, task: AgentTask) -> bool:
        """Save or update task in database"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tasks
                    (id, project_id, agent_type, operation, parameters, status, 
                     created_at, completed_at, result, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.id,
                    task.parameters.get('project_id', ''),
                    task.agent_type,
                    task.operation,
                    json.dumps(task.parameters),
                    task.status.value,
                    task.created_at,
                    task.completed_at,
                    json.dumps(task.result) if task.result else None,
                    task.error_message
                ))
                conn.commit()

            self.logger.debug(f"Saved task: {task.id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save task {task.id}: {str(e)}")
            return False

    def load_project_tasks(self, project_id: str) -> List[AgentTask]:
        """Load all tasks for a project"""
        tasks = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at",
                    (project_id,)
                )

                for row in cursor.fetchall():
                    task = AgentTask(
                        id=row['id'],
                        agent_type=row['agent_type'],
                        operation=row['operation'],
                        parameters=json.loads(row['parameters']),
                        status=TaskStatus(row['status']),
                        created_at=row['created_at'],
                        completed_at=row['completed_at'],
                        result=json.loads(row['result']) if row['result'] else {},
                        error_message=row['error_message']
                    )
                    tasks.append(task)

            self.logger.debug(f"Loaded {len(tasks)} tasks for project {project_id}")

        except Exception as e:
            self.logger.error(f"Failed to load tasks for project {project_id}: {str(e)}")

        return tasks

    def delete_project(self, project_id: str) -> bool:
        """Delete project and all its tasks"""
        try:
            with self._get_connection() as conn:
                # Delete tasks first (foreign key constraint)
                conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))

                # Delete project
                conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

                conn.commit()

            self.logger.info(f"Deleted project: {project_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete project {project_id}: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'total_projects': 0,
            'projects_by_status': {},
            'projects_by_type': {},
            'projects_by_language': {},
            'total_tasks': 0,
            'tasks_by_status': {}
        }

        try:
            with self._get_connection() as conn:
                # Project statistics
                cursor = conn.execute("SELECT COUNT(*) as count FROM projects")
                stats['total_projects'] = cursor.fetchone()['count']

                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM projects 
                    GROUP BY status
                """)
                stats['projects_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

                cursor = conn.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM projects 
                    GROUP BY type
                """)
                stats['projects_by_type'] = {row['type']: row['count'] for row in cursor.fetchall()}

                cursor = conn.execute("""
                    SELECT language, COUNT(*) as count 
                    FROM projects 
                    GROUP BY language
                """)
                stats['projects_by_language'] = {row['language']: row['count'] for row in cursor.fetchall()}

                # Task statistics
                cursor = conn.execute("SELECT COUNT(*) as count FROM tasks")
                stats['total_tasks'] = cursor.fetchone()['count']

                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM tasks 
                    GROUP BY status
                """)
                stats['tasks_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")

        return stats

    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old completed/failed projects"""
        try:
            cutoff_date = datetime.now()
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            cutoff_str = cutoff_date.isoformat()

            with self._get_connection() as conn:
                # Get projects to delete
                cursor = conn.execute("""
                    SELECT id FROM projects 
                    WHERE status IN ('completed', 'failed') 
                    AND updated_at < ?
                """, (cutoff_str,))

                project_ids = [row['id'] for row in cursor.fetchall()]

                # Delete tasks for these projects
                for project_id in project_ids:
                    conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))

                # Delete projects
                conn.execute("""
                    DELETE FROM projects 
                    WHERE status IN ('completed', 'failed') 
                    AND updated_at < ?
                """, (cutoff_str,))

                conn.commit()

            self.logger.info(f"Cleaned up {len(project_ids)} old projects")
            return len(project_ids)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {str(e)}")
            return 0


# Global storage instance
_storage: Optional[OrchestratorStorage] = None


def get_storage() -> OrchestratorStorage:
    """Get global storage instance"""
    global _storage
    if _storage is None:
        _storage = OrchestratorStorage()
    return _storage