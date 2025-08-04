# agents/devops_agent/core.py
"""
DevOps Agent - version with comprehensive infrastructure support
Includes Docker, CI/CD, Kubernetes, Monitoring, and Security features
"""
import os
import json
import platform
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import re
import yaml

from common.ai_connector import AIConnectorFactory
from common.config import get_config
from common.logger import get_agent_logger


class DevOpsAgent:
    """Enhanced DevOps Agent with comprehensive infrastructure capabilities"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("devops_agent")
        self.ai_connector = AIConnectorFactory.create_connector()
        self.logger.info("Enhanced DevOps Agent initialized")

    def analyze_host_system(self) -> Dict[str, Any]:
        """Analyze host system for comprehensive DevOps setup"""

        self.logger.info("Analyzing host system for DevOps setup")

        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "docker_installed": False,
            "docker_version": None,
            "docker_compose_version": None,
            "kubernetes_installed": False,
            "kubectl_version": None,
            "helm_installed": False,
            "helm_version": None,
            "git_installed": False,
            "git_version": None,
            "java_installed": False,
            "java_version": None,
            "maven_installed": False,
            "maven_version": None,
            "recommended_base_images": [],
            "docker_platform": None,
            "volume_mount_style": None,
            "path_separator": "\\" if platform.system() == "Windows" else "/",
            "ci_cd_platforms": [],
            "monitoring_tools": [],
            "security_tools": [],
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

            # Check Docker Compose
            if shutil.which("docker-compose"):
                try:
                    result = subprocess.run(["docker-compose", "--version"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_info["docker_compose_version"] = result.stdout.strip()
                except:
                    pass

            # Check Kubernetes tools
            if shutil.which("kubectl"):
                system_info["kubernetes_installed"] = True
                try:
                    result = subprocess.run(["kubectl", "version", "--client", "--short"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_info["kubectl_version"] = result.stdout.strip()
                except:
                    pass

            # Check Helm
            if shutil.which("helm"):
                system_info["helm_installed"] = True
                try:
                    result = subprocess.run(["helm", "version", "--short"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_info["helm_version"] = result.stdout.strip()
                except:
                    pass

            # Check Git
            if shutil.which("git"):
                system_info["git_installed"] = True
                try:
                    result = subprocess.run(["git", "--version"],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        system_info["git_version"] = result.stdout.strip()
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

            # Detect CI/CD platforms
            self._detect_ci_cd_platforms(system_info)

            # Determine recommendations
            self._determine_docker_recommendations(system_info)
            self._determine_monitoring_recommendations(system_info)
            self._determine_security_recommendations(system_info)

            self.logger.info(f"Host system analysis completed: {system_info['os']} {system_info['architecture']}")
            return system_info

        except Exception as e:
            self.logger.error(f"Failed to analyze host system: {str(e)}")
            return system_info

    def _detect_ci_cd_platforms(self, system_info: Dict[str, Any]):
        """Detect available CI/CD platforms"""
        ci_cd_files = {
            ".github/workflows": "github_actions",
            ".gitlab-ci.yml": "gitlab_ci",
            "Jenkinsfile": "jenkins",
            ".circleci/config.yml": "circleci",
            "azure-pipelines.yml": "azure_devops",
            ".travis.yml": "travis_ci"
        }

        # Check environment variables and files
        if os.getenv("GITHUB_ACTIONS"):
            system_info["ci_cd_platforms"].append("github_actions")
        if os.getenv("GITLAB_CI"):
            system_info["ci_cd_platforms"].append("gitlab_ci")
        if os.getenv("JENKINS_HOME"):
            system_info["ci_cd_platforms"].append("jenkins")

    def _determine_docker_recommendations(self, system_info: Dict[str, Any]):
        """Determine Docker recommendations based on host system"""

        os_type = system_info["os"]
        arch = system_info["architecture"].lower()

        # Determine Docker platform
        if "arm" in arch or "aarch64" in arch:
            system_info["docker_platform"] = "linux/arm64"
            system_info["recommended_base_images"] = [
                "eclipse-temurin:17-jre",
                "maven:3.9-eclipse-temurin-17"
            ]
        else:
            system_info["docker_platform"] = "linux/amd64"
            system_info["recommended_base_images"] = [
                "eclipse-temurin:17-jre",
                "maven:3.9-eclipse-temurin-17"
            ]

        # OS-specific recommendations
        if os_type == "Windows":
            system_info["volume_mount_style"] = "windows"
            system_info["docker_notes"] = [
                "Use Docker Desktop for Windows",
                "Enable WSL 2 backend for better performance",
                "Use forward slashes in Dockerfile paths",
                "Consider using docker-compose.exe instead of docker-compose"
            ]
        elif os_type == "Darwin":
            system_info["volume_mount_style"] = "mac"
            system_info["docker_notes"] = [
                "Use Docker Desktop for Mac",
                "Consider file sharing performance",
                "Use :delegated for better volume performance"
            ]
        else:
            system_info["volume_mount_style"] = "linux"
            system_info["docker_notes"] = [
                "Native Docker support available",
                "Consider using podman as alternative"
            ]

    def _determine_monitoring_recommendations(self, system_info: Dict[str, Any]):
        """Determine monitoring tools recommendations"""
        system_info["monitoring_tools"] = [
            "prometheus",
            "grafana",
            "elasticsearch",
            "kibana",
            "jaeger"
        ]

    def _determine_security_recommendations(self, system_info: Dict[str, Any]):
        """Determine security tools recommendations"""
        system_info["security_tools"] = [
            "trivy",
            "sonarqube",
            "owasp-dependency-check",
            "hadolint"
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
            "has_tests": False,
            "has_integration_tests": False,
            "reporting_tools": [],
            "quality_tools": []
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
                analysis["dependencies"] = self._extract_maven_dependencies(pom_content)
                analysis["test_framework"] = self._detect_test_framework(pom_content)
                analysis["reporting_tools"] = self._detect_reporting_tools(pom_content)
                analysis["quality_tools"] = self._detect_quality_tools(pom_content)

            # Check for test directories
            test_dirs = ["src/test", "src/integration-test", "tests", "test"]
            for test_dir in test_dirs:
                test_path = project_path / test_dir
                if test_path.exists():
                    analysis["has_tests"] = True
                    if "integration" in test_dir:
                        analysis["has_integration_tests"] = True

            # Scan for ports and environment variables
            analysis["ports"] = self._scan_for_ports(project_path)
            analysis["environment_vars"] = self._scan_for_env_vars(project_path)

            self.logger.info(f"Project analysis completed: {analysis['language']} {analysis['build_tool']}")
            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze project: {str(e)}")
            return analysis

    def _extract_maven_dependencies(self, pom_content: str) -> List[str]:
        """Extract dependencies from pom.xml"""
        dependencies = []
        try:
            dep_pattern = r'<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?</dependency>'
            matches = re.findall(dep_pattern, pom_content, re.DOTALL)

            for group_id, artifact_id in matches:
                dependencies.append(f"{group_id.strip()}:{artifact_id.strip()}")

        except Exception as e:
            self.logger.warning(f"Failed to parse Maven dependencies: {str(e)}")

        return dependencies

    def _detect_test_framework(self, content: str) -> str:
        """Detect test framework from project content"""
        content_lower = content.lower()

        if "testng" in content_lower:
            return "testng"
        elif "junit" in content_lower:
            return "junit"

        return "unknown"

    def _detect_reporting_tools(self, content: str) -> List[str]:
        """Detect reporting tools from pom.xml"""
        tools = []
        content_lower = content.lower()

        if "allure" in content_lower:
            tools.append("allure")
        if "surefire-report" in content_lower:
            tools.append("surefire")
        if "extent" in content_lower:
            tools.append("extentreports")

        return tools

    def _detect_quality_tools(self, content: str) -> List[str]:
        """Detect code quality tools from pom.xml"""
        tools = []
        content_lower = content.lower()

        if "jacoco" in content_lower:
            tools.append("jacoco")
        if "sonarqube" in content_lower or "sonar" in content_lower:
            tools.append("sonarqube")
        if "spotbugs" in content_lower:
            tools.append("spotbugs")
        if "checkstyle" in content_lower:
            tools.append("checkstyle")

        return tools

    def _scan_for_ports(self, project_path: Path) -> List[int]:
        """Scan project files for port numbers"""
        ports = []
        try:
            port_patterns = [r'port[:\s=]+(\d+)', r':(\d{4,5})']

            for pattern in ["**/*.properties", "**/*.yml", "**/*.yaml", "**/*.json"]:
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

    def _scan_for_env_vars(self, project_path: Path) -> List[str]:
        """Scan project files for environment variables"""
        env_vars = []
        try:
            env_patterns = [
                r'\$\{([A-Z_][A-Z0-9_]*)\}',
                r'System\.getenv\("([A-Z_][A-Z0-9_]*)"\)',
                r'os\.environ\[[\'"]([\w_]+)[\'"]\]',
                r'process\.env\.([A-Z_][A-Z0-9_]*)'
            ]

            for pattern in ["**/*.java", "**/*.properties", "**/*.yml", "**/*.py", "**/*.js"]:
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
        """Create comprehensive Docker configuration with extended DevOps features"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating comprehensive Docker and DevOps setup for: {project_name}")

        try:
            # Analyze host system and project
            host_analysis = self.analyze_host_system()
            project_analysis = self.analyze_project_structure(output_path)

            # Create AI prompt for comprehensive setup
            docker_prompt = f"""
            Create comprehensive Docker and DevOps configuration for this system and project:

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
            - Reporting Tools: {project_analysis['reporting_tools']}
            - Dependencies: {project_analysis['dependencies'][:5]}
            - Environment Vars: {project_analysis['environment_vars']}

            Create comprehensive setup that includes:

            1. DOCKER FILES:
               - Dockerfile (multi-stage, security best practices)
               - docker-compose.yml (main services)
               - docker-compose.debug.yml (debug configuration)
               - docker-compose.allure.yml (reporting services)
               - docker-entrypoint.sh (smart entrypoint)
               - .dockerignore (optimized)

            2. CI/CD (GitHub Actions only for simplicity):
               - .github/workflows/test.yml (run tests on push/PR)
               - .github/workflows/docker-build.yml (build and cache images)

            3. SECURITY:
               - .hadolint.yml (Dockerfile linting)
               - security/docker-security-scan.sh (Trivy scanning)

            4. DOCUMENTATION:
               - DOCKER_QUICKSTART.md (how to run with Docker)
               - DEVOPS_GUIDE.md (complete DevOps guide)

            5. HELPER SCRIPTS for {host_analysis['os']}:
               - scripts/run-tests.{'.bat' if host_analysis['os'] == 'Windows' else '.sh'}
               - scripts/run-debug.{'.bat' if host_analysis['os'] == 'Windows' else '.sh'}
               - scripts/run-allure.{'.bat' if host_analysis['os'] == 'Windows' else '.sh'}
               - scripts/clean.{'.bat' if host_analysis['os'] == 'Windows' else '.sh'}

            Make everything production-ready and optimized for {host_analysis['os']}.

            Respond with a simple list format:
===FILE: Dockerfile===
[content here]
===END FILE===

===FILE: docker-compose.yml===
[content here]  
===END FILE===

And so on for all files.
            """

            response = await self.ai_connector.generate_structured_response(
                docker_prompt,
                f"Create comprehensive Docker and DevOps setup optimized for {host_analysis['os']} {host_analysis['architecture']} system"
            )

            created_files = []

            if "docker_files" in response:
                for file_path, content in response["docker_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)

                    # Make shell scripts executable
                    if file_path.endswith('.sh'):
                        full_file.write_text(content, encoding='utf-8')
                        full_file.chmod(0o755)
                    else:
                        full_file.write_text(content, encoding='utf-8')

                    created_files.append(str(full_file))

            # Create OS-specific helper scripts
            helper_scripts = await self._create_os_specific_scripts(output_path, host_analysis)
            created_files.extend(helper_scripts)

            # Create basic monitoring config
            monitoring_files = await self._create_basic_monitoring(output_path)
            created_files.extend(monitoring_files)

            # Create environment template
            env_template = self._create_env_template(project_analysis)
            env_file = output_path / ".env.template"
            env_file.write_text(env_template, encoding='utf-8')
            created_files.append(str(env_file))

            self.logger.info(f"Created comprehensive Docker and DevOps setup: {len(created_files)} files")

            return {
                "operation": "create_docker_setup",
                "status": "completed",
                "created_files": created_files,
                "features_included": [
                    "docker-multi-stage",
                    "docker-compose-variants",
                    "github-actions-ci",
                    "security-scanning",
                    "allure-reporting",
                    "debug-support",
                    "documentation",
                    "helper-scripts"
                ],
                "message": f"Created comprehensive Docker and DevOps setup for {host_analysis['os']} with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create Docker setup: {str(e)}")
            raise

    async def _create_os_specific_scripts(self, output_path: Path, host_analysis: Dict) -> List[str]:
        """Create OS-specific helper scripts"""
        created_files = []

        scripts_dir = output_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        if host_analysis['os'] == "Windows":
            # Windows batch scripts
            scripts = {
                "run-tests.bat": """@echo off
echo ========================================
echo Running all tests with Docker...
echo ========================================
docker-compose up test-runner
if %ERRORLEVEL% NEQ 0 (
    echo Tests failed with exit code: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
echo Tests completed successfully!
""",
                "run-debug.bat": """@echo off
echo ========================================
echo Starting debug mode...
echo ========================================
echo Debug port will be available at localhost:5005
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up test-runner
""",
                "run-allure.bat": """@echo off
echo ========================================
echo Starting Allure reporting...
echo ========================================
docker-compose -f docker-compose.yml -f docker-compose.allure.yml up -d allure
timeout /t 5
echo.
echo Allure report available at http://localhost:5252
echo Press Ctrl+C to stop Allure server
pause
""",
                "run-security-scan.bat": """@echo off
echo ========================================
echo Running security scan...
echo ========================================
if exist security\\docker-security-scan.sh (
    docker run --rm -v "%cd%":/src -w /src aquasec/trivy image --severity HIGH,CRITICAL java-test-automation:latest
) else (
    echo Security scan script not found
)
""",
                "clean.bat": """@echo off
echo ========================================
echo Cleaning up Docker resources...
echo ========================================
docker-compose down -v
docker system prune -f
echo Cleanup completed!
"""
            }
        else:
            # Unix shell scripts
            scripts = {
                "run-tests.sh": """#!/bin/bash
echo "========================================"
echo "Running all tests with Docker..."
echo "========================================"
docker-compose up test-runner
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Tests failed with exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi
echo "Tests completed successfully!"
""",
                "run-debug.sh": """#!/bin/bash
echo "========================================"
echo "Starting debug mode..."
echo "========================================"
echo "Debug port will be available at localhost:5005"
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up test-runner
""",
                "run-allure.sh": """#!/bin/bash
echo "========================================"
echo "Starting Allure reporting..."
echo "========================================"
docker-compose -f docker-compose.yml -f docker-compose.allure.yml up -d allure
sleep 5
echo ""
echo "Allure report available at http://localhost:5252"
echo "Press Ctrl+C to stop Allure server"
read -r -p "Press Enter to continue..."
""",
                "run-security-scan.sh": """#!/bin/bash
echo "========================================"
echo "Running security scan..."
echo "========================================"
if [ -f security/docker-security-scan.sh ]; then
    ./security/docker-security-scan.sh
else
    docker run --rm -v "$(pwd)":/src -w /src aquasec/trivy image --severity HIGH,CRITICAL java-test-automation:latest
fi
""",
                "clean.sh": """#!/bin/bash
echo "========================================"
echo "Cleaning up Docker resources..."
echo "========================================"
docker-compose down -v
docker system prune -f
echo "Cleanup completed!"
"""
            }

        # Create scripts
        for script_name, script_content in scripts.items():
            script_file = scripts_dir / script_name
            script_file.write_text(script_content, encoding='utf-8')
            if script_name.endswith('.sh'):
                script_file.chmod(0o755)
            created_files.append(str(script_file))

        # Create README for scripts
        scripts_readme = scripts_dir / "README.md"
        readme_content = f"""# Helper Scripts

These scripts simplify common Docker operations for {'Windows' if host_analysis['os'] == 'Windows' else 'Unix'} users.

## Available Scripts:

### run-tests{'bat' if host_analysis['os'] == 'Windows' else '.sh'}
Runs all tests using Docker Compose.

### run-debug{'bat' if host_analysis['os'] == 'Windows' else '.sh'}
Starts tests in debug mode with remote debugging on port 5005.

### run-allure{'bat' if host_analysis['os'] == 'Windows' else '.sh'}
Starts Allure reporting server on http://localhost:5252.

### run-security-scan{'bat' if host_analysis['os'] == 'Windows' else '.sh'}
Runs security vulnerability scan on Docker images.

### clean{'bat' if host_analysis['os'] == 'Windows' else '.sh'}
Cleans up all Docker resources (containers, volumes, images).

## Usage:

{'```cmd' if host_analysis['os'] == 'Windows' else '```bash'}
cd scripts
{'run-tests.bat' if host_analysis['os'] == 'Windows' else './run-tests.sh'}
```
"""
        scripts_readme.write_text(readme_content, encoding='utf-8')
        created_files.append(str(scripts_readme))

        return created_files

    async def _create_basic_monitoring(self, output_path: Path) -> List[str]:
        """Create basic monitoring configuration"""
        created_files = []

        # Create simple Prometheus config for test metrics
        monitoring_dir = output_path / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)

        prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'test-metrics'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'

  - job_name: 'docker'
    static_configs:
      - targets: ['localhost:9323']
"""

        prom_file = monitoring_dir / "prometheus-basic.yml"
        prom_file.write_text(prometheus_config, encoding='utf-8')
        created_files.append(str(prom_file))

        # Create basic Grafana dashboard JSON
        dashboard = {
            "dashboard": {
                "title": "Test Automation Metrics",
                "panels": [
                    {
                        "title": "Test Execution Time",
                        "type": "graph",
                        "targets": [{"expr": "test_duration_seconds"}]
                    },
                    {
                        "title": "Test Pass Rate",
                        "type": "stat",
                        "targets": [{"expr": "test_pass_rate"}]
                    }
                ]
            }
        }

        dashboard_file = monitoring_dir / "test-dashboard.json"
        dashboard_file.write_text(json.dumps(dashboard, indent=2), encoding='utf-8')
        created_files.append(str(dashboard_file))

        # Create README for monitoring
        monitoring_readme = monitoring_dir / "README.md"
        readme_content = """# Monitoring Configuration

This directory contains basic monitoring configuration for test metrics.

## Files:
- `prometheus-basic.yml` - Basic Prometheus configuration
- `test-dashboard.json` - Grafana dashboard for test metrics

## Usage:
To enable monitoring, use:
```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
"""
        monitoring_readme.write_text(readme_content, encoding='utf-8')
        created_files.append(str(monitoring_readme))

        return created_files

    def _create_env_template(self, project_analysis: Dict) -> str:
        """Create environment variables template"""
        env_vars = project_analysis.get('environment_vars', [])

        template = """# Environment Variables Template
# Copy this file to .env and fill in your values

# Test Environment
TEST_ENV=dev
LOG_LEVEL=INFO

# API Configuration
BASE_URL=http://localhost:8080
API_TIMEOUT=30000

# Authentication
API_KEY=your-api-key-here
BEARER_TOKEN=your-bearer-token-here
BASIC_AUTH_USER=username
BASIC_AUTH_PASS=password

# Test Configuration
PARALLEL_TESTS=5
RETRY_COUNT=3
RETRY_DELAY=1000

# Reporting
ALLURE_RESULTS_PATH=target/allure-results
REPORT_PATH=target/test-reports

"""

        # Add discovered environment variables
        if env_vars:
            template += "# Discovered Environment Variables\n"
            for var in sorted(set(env_vars)):
                template += f"{var}=your-value-here\n"

        template += """
# Docker Configuration
DOCKER_REGISTRY=docker.io
IMAGE_TAG=latest

# Security Scanning
TRIVY_SEVERITY=HIGH,CRITICAL
SONAR_TOKEN=your-sonar-token-here
"""

        return template

    async def create_ci_cd_pipelines(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create CI/CD pipeline configurations for multiple platforms"""

        project_name = params['project_name']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating CI/CD pipelines for: {project_name}")

        try:
            # Analyze project for CI/CD requirements
            project_analysis = self.analyze_project_structure(output_path)

            ci_cd_prompt = f"""
            Create CI/CD pipeline configurations for a Java test automation project:

            Project: {project_name}
            Build Tool: {project_analysis['build_tool']}
            Test Framework: {project_analysis['test_framework']}
            Has Docker: Yes (Docker setup already created)

            Create pipelines for:

            1. GitHub Actions (.github/workflows/):
               - test.yml: Run tests on push/PR
               - nightly.yml: Nightly full regression
               - release.yml: Release workflow

            2. GitLab CI (.gitlab-ci.yml):
               - Build, test, and report stages
               - Docker caching
               - Allure reports

            3. Jenkins (Jenkinsfile):
               - Declarative pipeline
               - Docker agent
               - Post actions for reports

            All pipelines should include:
            - Docker build and caching
            - Parallel test execution
            - Test result archiving
            - Allure report generation
            - Failure notifications
            - Security scanning

            Respond with JSON:
            {{
                "ci_cd_files": {{
                    ".github/workflows/test.yml": "content",
                    ".github/workflows/nightly.yml": "content",
                    ".github/workflows/release.yml": "content",
                    ".gitlab-ci.yml": "content",
                    "Jenkinsfile": "content"
                }}
            }}
            """

            response = await self.ai_connector.generate_structured_response(
                ci_cd_prompt,
                "Create production-ready CI/CD pipelines with best practices"
            )

            created_files = []

            if "ci_cd_files" in response:
                for file_path, content in response["ci_cd_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            return {
                "operation": "create_ci_cd_pipelines",
                "status": "completed",
                "created_files": created_files,
                "ci_cd_platforms": ["github_actions", "gitlab_ci", "jenkins"],
                "message": f"Created CI/CD pipelines for {len(created_files)} platforms"
            }

        except Exception as e:
            self.logger.error(f"Failed to create CI/CD pipelines: {str(e)}")
            raise

    async def create_kubernetes_manifests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kubernetes manifests for test execution"""

        project_name = params['project_name']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating Kubernetes manifests for: {project_name}")

        try:
            k8s_prompt = f"""
            Create Kubernetes manifests for running Java test automation:

            Project: {project_name}

            Create:

            1. k8s/namespace.yaml - Dedicated namespace
            2. k8s/configmap.yaml - Test configuration
            3. k8s/secret.yaml - Sensitive data template
            4. k8s/job.yaml - Test execution job
            5. k8s/cronjob.yaml - Scheduled test runs
            6. k8s/pvc.yaml - Persistent volume for results
            7. k8s/service.yaml - Service for Allure reports
            8. k8s/deployment-allure.yaml - Allure server deployment

            Also create:
            - k8s/kustomization.yaml - Kustomize configuration
            - helm/Chart.yaml - Helm chart definition
            - helm/values.yaml - Helm values

            Include:
            - Resource limits and requests
            - Health checks
            - Security contexts
            - Volume mounts
            - Environment variables

            Respond with JSON:
            {{
                "k8s_files": {{
                    "k8s/namespace.yaml": "content",
                    "k8s/configmap.yaml": "content",
                    "k8s/secret.yaml": "content",
                    "k8s/job.yaml": "content",
                    "k8s/cronjob.yaml": "content",
                    "k8s/pvc.yaml": "content",
                    "k8s/service.yaml": "content",
                    "k8s/deployment-allure.yaml": "content",
                    "k8s/kustomization.yaml": "content",
                    "helm/Chart.yaml": "content",
                    "helm/values.yaml": "content"
                }}
            }}
            """

            response = await self.ai_connector.generate_structured_response(
                k8s_prompt,
                "Create production-ready Kubernetes manifests for test automation"
            )

            created_files = []

            if "k8s_files" in response:
                for file_path, content in response["k8s_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            # Create kubectl helper scripts
            kubectl_scripts = {
                "k8s/deploy.sh": """#!/bin/bash
kubectl apply -k k8s/
echo "Test infrastructure deployed to Kubernetes"
""",
                "k8s/run-test.sh": """#!/bin/bash
kubectl create job test-run-$(date +%s) --from=cronjob/test-automation -n test-automation
echo "Test job started"
""",
                "k8s/get-results.sh": """#!/bin/bash
POD=$(kubectl get pods -n test-automation -l job-name --no-headers -o custom-columns=:metadata.name | head -1)
kubectl cp test-automation/$POD:/app/test-results ./k8s-test-results
echo "Results copied to ./k8s-test-results"
"""
            }

            for script_path, script_content in kubectl_scripts.items():
                script_file = output_path / script_path
                script_file.write_text(script_content, encoding='utf-8')
                script_file.chmod(0o755)
                created_files.append(str(script_file))

            return {
                "operation": "create_kubernetes_manifests",
                "status": "completed",
                "created_files": created_files,
                "k8s_features": ["jobs", "cronjobs", "persistent-storage", "allure-deployment", "helm-chart"],
                "message": f"Created Kubernetes manifests with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create Kubernetes manifests: {str(e)}")
            raise

    async def create_monitoring_stack(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring stack configuration"""

        project_name = params['project_name']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating monitoring stack for: {project_name}")

        try:
            monitoring_prompt = f"""
            Create monitoring stack configuration for test automation:

            Project: {project_name}

            Create monitoring setup with:

            1. monitoring/prometheus.yml - Prometheus configuration
            2. monitoring/prometheus-rules.yml - Alert rules
            3. monitoring/grafana-datasource.yml - Grafana datasources
            4. monitoring/grafana-dashboard.json - Test metrics dashboard
            5. monitoring/docker-compose.monitoring.yml - Full monitoring stack
            6. monitoring/test-exporter/pom.xml - Test metrics exporter
            7. monitoring/test-exporter/TestMetricsExporter.java - Metrics exporter code

            Include metrics for:
            - Test execution time
            - Test pass/fail rates
            - Test coverage
            - API response times
            - Error rates
            - Resource usage

            Respond with JSON:
            {{
                "monitoring_files": {{
                    "monitoring/prometheus.yml": "content",
                    "monitoring/prometheus-rules.yml": "content",
                    "monitoring/grafana-datasource.yml": "content",
                    "monitoring/grafana-dashboard.json": "content",
                    "monitoring/docker-compose.monitoring.yml": "content"
                }}
            }}
            """

            response = await self.ai_connector.generate_structured_response(
                monitoring_prompt,
                "Create comprehensive monitoring stack for test automation"
            )

            created_files = []

            if "monitoring_files" in response:
                for file_path, content in response["monitoring_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            return {
                "operation": "create_monitoring_stack",
                "status": "completed",
                "created_files": created_files,
                "monitoring_tools": ["prometheus", "grafana", "test-metrics-exporter"],
                "message": f"Created monitoring stack with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create monitoring stack: {str(e)}")
            raise

    async def create_security_scanning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create security scanning configuration"""

        project_name = params['project_name']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating security scanning setup for: {project_name}")

        try:
            security_prompt = f"""
            Create security scanning configuration for test automation:

            Project: {project_name}

            Create security setup with:

            1. security/trivy-scan.yml - Container vulnerability scanning
            2. security/sonarqube.properties - Code quality and security
            3. security/dependency-check-suppression.xml - OWASP dependency check
            4. security/docker-bench-security.sh - Docker security audit
            5. .hadolint.yml - Dockerfile linting rules
            6. security/security-scan.sh - Master security scan script

            Include:
            - Container image scanning
            - Dependency vulnerability checks
            - Code security analysis
            - Secret detection
            - License compliance

            Respond with JSON:
            {{
                "security_files": {{
                    "security/trivy-scan.yml": "content",
                    "security/sonarqube.properties": "content",
                    "security/dependency-check-suppression.xml": "content",
                    "security/docker-bench-security.sh": "content",
                    ".hadolint.yml": "content",
                    "security/security-scan.sh": "content"
                }}
            }}
            """

            response = await self.ai_connector.generate_structured_response(
                security_prompt,
                "Create comprehensive security scanning setup"
            )

            created_files = []

            if "security_files" in response:
                for file_path, content in response["security_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)

                    if file_path.endswith('.sh'):
                        full_file.write_text(content, encoding='utf-8')
                        full_file.chmod(0o755)
                    else:
                        full_file.write_text(content, encoding='utf-8')

                    created_files.append(str(full_file))

            return {
                "operation": "create_security_scanning",
                "status": "completed",
                "created_files": created_files,
                "security_tools": ["trivy", "sonarqube", "dependency-check", "hadolint"],
                "message": f"Created security scanning setup with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create security scanning: {str(e)}")
            raise

    async def create_documentation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive DevOps documentation"""

        project_name = params['project_name']
        output_path = Path(params['output_path'])
        host_analysis = self.analyze_host_system()

        self.logger.info(f"Creating DevOps documentation for: {project_name}")

        try:
            docs_prompt = f"""
            Create comprehensive DevOps documentation for test automation project:

            Project: {project_name}
            Host OS: {host_analysis['os']}

            Create documentation:

            1. docs/DOCKER_SETUP.md - Complete Docker guide
            2. docs/CI_CD_GUIDE.md - CI/CD pipeline documentation
            3. docs/KUBERNETES_DEPLOYMENT.md - K8s deployment guide
            4. docs/MONITORING_GUIDE.md - Monitoring stack guide
            5. docs/SECURITY_GUIDE.md - Security best practices
            6. docs/TROUBLESHOOTING.md - Common issues and solutions
            7. README_DEVOPS.md - Main DevOps overview

            Include:
            - Prerequisites
            - Step-by-step instructions
            - Configuration examples
            - Common commands
            - Troubleshooting tips
            - Best practices

            Make it specific for {host_analysis['os']} users.

            Respond with JSON:
            {{
                "docs_files": {{
                    "docs/DOCKER_SETUP.md": "content",
                    "docs/CI_CD_GUIDE.md": "content",
                    "docs/KUBERNETES_DEPLOYMENT.md": "content",
                    "docs/MONITORING_GUIDE.md": "content",
                    "docs/SECURITY_GUIDE.md": "content",
                    "docs/TROUBLESHOOTING.md": "content",
                    "README_DEVOPS.md": "content"
                }}
            }}
            """

            response = await self.ai_connector.generate_structured_response(
                docs_prompt,
                f"Create comprehensive DevOps documentation for {host_analysis['os']} users"
            )

            created_files = []

            if "docs_files" in response:
                for file_path, content in response["docs_files"].items():
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            return {
                "operation": "create_documentation",
                "status": "completed",
                "created_files": created_files,
                "message": f"Created DevOps documentation with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create documentation: {str(e)}")
            raise

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific DevOps agent operation"""

        self.logger.info(f"Executing operation: {operation}")

        operation_mapping = {
            # Docker operations
            "create_docker_setup": self.create_docker_setup,
            "setup_environment": self.create_docker_setup,
            "configure_environment": self.create_docker_setup,

            # CI/CD operations
            "create_ci_cd_pipelines": self.create_ci_cd_pipelines,
            "setup_ci_cd": self.create_ci_cd_pipelines,
            "configure_ci": self.create_ci_cd_pipelines,

            # Kubernetes operations
            "create_kubernetes_manifests": self.create_kubernetes_manifests,
            "setup_k8s": self.create_kubernetes_manifests,

            # Monitoring operations
            "create_monitoring_stack": self.create_monitoring_stack,
            "setup_monitoring": self.create_monitoring_stack,

            # Security operations
            "create_security_scanning": self.create_security_scanning,
            "setup_security": self.create_security_scanning,

            # Documentation
            "create_documentation": self.create_documentation,
            "create_devops_docs": self.create_documentation,

            # Legacy operations (redirect to docker setup)
            "create_project_structure": self.create_docker_setup,
            "configure_pom": self.create_docker_setup,
            "configure_reporting": self.create_docker_setup,
        }

        if operation in operation_mapping:
            return await operation_mapping[operation](params)
        else:
            # Default to docker setup
            self.logger.info(f"Unknown operation '{operation}', defaulting to create_docker_setup")
            return await self.create_docker_setup(params)

    async def create_complete_devops_stack(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create complete DevOps stack with all components"""

        self.logger.info("Creating complete DevOps stack")

        all_results = {
            "operations": [],
            "total_files": 0,
            "components": []
        }

        # Create all components
        components = [
            ("Docker Setup", self.create_docker_setup),
            ("CI/CD Pipelines", self.create_ci_cd_pipelines),
            ("Kubernetes Manifests", self.create_kubernetes_manifests),
            ("Monitoring Stack", self.create_monitoring_stack),
            ("Security Scanning", self.create_security_scanning),
            ("Documentation", self.create_documentation)
        ]

        for component_name, component_func in components:
            try:
                self.logger.info(f"Creating {component_name}...")
                result = await component_func(params)
                all_results["operations"].append(result)
                all_results["total_files"] += len(result.get("created_files", []))
                all_results["components"].append(component_name)
            except Exception as e:
                self.logger.error(f"Failed to create {component_name}: {str(e)}")

        return {
            "operation": "create_complete_devops_stack",
            "status": "completed",
            "results": all_results,
            "message": f"Created complete DevOps stack with {all_results['total_files']} files"
        }