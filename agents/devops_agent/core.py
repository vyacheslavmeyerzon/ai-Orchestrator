"""
DevOps Agent - Fixed version with proper async handling and system analysis
"""

import os
import json
import platform
import subprocess
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from common.ai_connector import AIConnectorFactory
from common.config import get_config
from common.logger import get_agent_logger


class DevOpsAgent:
    """Agent responsible for DevOps infrastructure setup"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("devops_agent")
        self.ai_connector = AIConnectorFactory.create_connector()

        self.logger.info("DevOps Agent initialized")

    def analyze_host_system(self) -> Dict[str, Any]:
        """Analyze host system for Docker compatibility"""

        self.logger.info("Analyzing host system for Docker setup")

        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "docker_installed": False,
            "docker_version": None,
            "docker_desktop": False,
            "wsl_available": False,
            "hyperv_available": False,
            "java_installed": False,
            "java_version": None,
            "maven_installed": False,
            "maven_version": None,
            "recommended_base_images": [],
            "docker_platform": None,
            "volume_mount_style": None,
            "path_separator": "\\" if platform.system() == "Windows" else "/",
            "docker_notes": []
        }

        try:
            # Check Docker installation
            if shutil.which("docker"):
                system_info["docker_installed"] = True
                try:
                    result = subprocess.run(["docker", "--version"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_info["docker_version"] = result.stdout.strip()
                except:
                    pass

            # Check Java installation
            if shutil.which("java"):
                system_info["java_installed"] = True
                try:
                    result = subprocess.run(["java", "-version"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_output = result.stderr or result.stdout
                        system_info["java_version"] = version_output.split('\n')[0]
                except:
                    pass

            # Check Maven installation
            if shutil.which("mvn"):
                system_info["maven_installed"] = True
                try:
                    result = subprocess.run(["mvn", "--version"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_info["maven_version"] = result.stdout.split('\n')[0]
                except:
                    pass

            # Determine recommendations
            self.determine_docker_recommendations(system_info)

            self.logger.info(f"Host system analysis completed: {system_info['os']} {system_info['architecture']}")
            return system_info

        except Exception as e:
            self.logger.error(f"Failed to analyze host system: {str(e)}")
            return system_info

    def determine_docker_recommendations(self, system_info: Dict[str, Any]):
        """Determine Docker recommendations based on host system"""

        os_type = system_info["os"]
        arch = system_info["architecture"].lower()

        # Determine Docker platform
        if "arm" in arch or "aarch64" in arch:
            system_info["docker_platform"] = "linux/arm64"
            system_info["recommended_base_images"] = [
                "openjdk:11-jre-slim",
                "maven:3.8-openjdk-11-slim"
            ]
        else:
            system_info["docker_platform"] = "linux/amd64"
            system_info["recommended_base_images"] = [
                "openjdk:11-jre-slim",
                "maven:3.8-openjdk-11"
            ]

        # OS-specific recommendations
        if os_type == "Windows":
            system_info["volume_mount_style"] = "windows"
            system_info["docker_notes"] = [
                "Use Docker Desktop for Windows",
                "Enable WSL 2 backend for better performance",
                "Use forward slashes in Dockerfile paths"
            ]
        elif os_type == "Darwin":
            system_info["volume_mount_style"] = "mac"
            system_info["docker_notes"] = [
                "Use Docker Desktop for Mac",
                "Consider file sharing performance"
            ]
        else:
            system_info["volume_mount_style"] = "linux"
            system_info["docker_notes"] = [
                "Native Docker support available"
            ]

    def analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze existing project structure and dependencies"""

        self.logger.info(f"Analyzing project structure: {project_path}")

        analysis = {
            "project_type": "unknown",
            "language": "unknown",
            "build_tool": "unknown",
            "dependencies": [],
            "test_framework": "unknown",
            "test_commands": [],
            "ports": [],
            "environment_vars": [],
            "has_tests": False
        }

        try:
            # Check for Java Maven project
            pom_file = project_path / "pom.xml"
            if pom_file.exists():
                analysis["language"] = "java"
                analysis["build_tool"] = "maven"
                analysis["project_type"] = "maven"
                analysis["test_commands"] = ["mvn clean test", "mvn clean verify"]

                # Parse pom.xml for dependencies
                pom_content = pom_file.read_text(encoding='utf-8')
                analysis["dependencies"] = self.extract_maven_dependencies(pom_content)
                analysis["test_framework"] = self.detect_test_framework(pom_content)

            # Check for test directories
            test_dirs = ["src/test", "tests", "test"]
            for test_dir in test_dirs:
                if (project_path / test_dir).exists():
                    analysis["has_tests"] = True
                    break

            # Scan for ports and environment variables
            analysis["ports"] = self.scan_for_ports(project_path)
            analysis["environment_vars"] = self.scan_for_env_vars(project_path)

            self.logger.info(f"Project analysis completed: {analysis['language']} {analysis['build_tool']}")
            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze project: {str(e)}")
            return analysis

    def extract_maven_dependencies(self, pom_content: str) -> List[str]:
        """Extract dependencies from pom.xml"""
        dependencies = []
        try:
            import re
            dep_pattern = r'<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?</dependency>'
            matches = re.findall(dep_pattern, pom_content, re.DOTALL)

            for group_id, artifact_id in matches:
                dependencies.append(f"{group_id.strip()}:{artifact_id.strip()}")

        except Exception as e:
            self.logger.warning(f"Failed to parse Maven dependencies: {str(e)}")

        return dependencies

    def detect_test_framework(self, content: str) -> str:
        """Detect test framework from project content"""
        content_lower = content.lower()

        if "testng" in content_lower:
            return "testng"
        elif "junit" in content_lower:
            return "junit"

        return "unknown"

    def scan_for_ports(self, project_path: Path) -> List[int]:
        """Scan project files for port numbers"""
        ports = []
        try:
            import re
            port_patterns = [r'port[:\s=]+(\d+)', r':(\d{4,5})']

            for pattern in ["**/*.properties", "**/*.yml", "**/*.yaml"]:
                for file_path in project_path.glob(pattern):
                    if file_path.is_file():
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            for port_pattern in port_patterns:
                                matches = re.findall(port_pattern, content, re.IGNORECASE)
                                for match in matches:
                                    try:
                                        port = int(match)
                                        if 1000 <= port <= 65535:
                                            ports.append(port)
                                    except ValueError:
                                        pass
                        except:
                            pass

        except Exception as e:
            self.logger.warning(f"Failed to scan for ports: {str(e)}")

        return list(set(ports))

    def scan_for_env_vars(self, project_path: Path) -> List[str]:
        """Scan project files for environment variables"""
        env_vars = []
        try:
            import re
            env_patterns = [
                r'\$\{([A-Z_][A-Z0-9_]*)\}',
                r'System\.getenv\("([A-Z_][A-Z0-9_]*)"\)'
            ]

            for pattern in ["**/*.java", "**/*.properties", "**/*.yml"]:
                for file_path in project_path.glob(pattern):
                    if file_path.is_file():
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            for env_pattern in env_patterns:
                                matches = re.findall(env_pattern, content)
                                env_vars.extend(matches)
                        except:
                            pass

        except Exception as e:
            self.logger.warning(f"Failed to scan for environment variables: {str(e)}")

        return list(set(env_vars))

    async def create_docker_setup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Docker configuration files based on host system and project analysis"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating Docker setup for: {project_name}")

        try:
            # Analyze host system and project
            host_analysis = self.analyze_host_system()
            project_analysis = self.analyze_project_structure(output_path)

            # Create AI prompt based on analysis
            docker_prompt = f"""
            Create Docker configuration optimized for this system and project:

            HOST SYSTEM:
            - OS: {host_analysis['os']}
            - Architecture: {host_analysis['architecture']}
            - Docker: {host_analysis['docker_installed']}
            - Platform: {host_analysis.get('docker_platform', 'linux/amd64')}
            - Java: {host_analysis['java_installed']}
            - Maven: {host_analysis['maven_installed']}

            PROJECT:
            - Language: {project_analysis['language']}
            - Build Tool: {project_analysis['build_tool']}
            - Test Framework: {project_analysis['test_framework']}
            - Test Commands: {project_analysis['test_commands']}
            - Dependencies: {project_analysis['dependencies'][:5]}

            Create Docker files that work on {host_analysis['os']}:

            Respond with JSON:
            {{
                "docker_files": {{
                    "Dockerfile": "dockerfile content",
                    "docker-compose.yml": "compose file",
                    ".dockerignore": "ignore file",
                    "docker-entrypoint.sh": "entry script"
                }}
            }}
            """

            response = await self.ai_connector.generate_structured_response(
                docker_prompt,
                f"Create Docker setup for {host_analysis['os']} {host_analysis['architecture']} system"
            )

            created_files = []

            if "docker_files" in response:
                for file_path, content in response["docker_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            self.logger.info(f"Created Docker setup: {len(created_files)} files")

            return {
                "operation": "create_docker_setup",
                "status": "completed",
                "created_files": created_files,
                "message": f"Created Docker configuration for {host_analysis['os']} with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create Docker setup: {str(e)}")
            raise

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific DevOps agent operation"""

        self.logger.info(f"Executing operation: {operation}")

        # Map all operations to docker setup for now
        operation_mapping = {
            "create_docker_setup": self.create_docker_setup,
            "setup_environment": self.create_docker_setup,
            "configure_environment": self.create_docker_setup,
            "create_project_structure": self.create_docker_setup,
            "configure_pom": self.create_docker_setup,
            "configure_reporting": self.create_docker_setup,
            "configure_ci": self.create_docker_setup,
        }

        if operation in operation_mapping:
            return await operation_mapping[operation](params)
        else:
            # Default to docker setup
            self.logger.info(f"Unknown operation '{operation}', defaulting to create_docker_setup")
            return await self.create_docker_setup(params)