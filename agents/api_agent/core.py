"""
API Agent - Specialized agent for creating and managing API tests
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from common.ai_connector import AIConnectorFactory
from common.config import get_config
from common.logger import get_agent_logger


class APIAgent:
    """Agent responsible for API test creation and management"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("api_agent")
        self.ai_connector = AIConnectorFactory.create_connector()

        # Template paths
        self.templates_path = Path(self.config.project.templates_path)

        self.logger.info("API Agent initialized")

    async def create_project_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic project structure for API tests"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating {language} project structure: {project_name}")

        try:
            # Ensure output directory exists
            output_path.mkdir(parents=True, exist_ok=True)

            if language == "java":
                return await self._create_java_structure(project_name, output_path, params)
            elif language == "python":
                return await self._create_python_structure(project_name, output_path, params)
            else:
                raise ValueError(f"Unsupported language: {language}")

        except Exception as e:
            self.logger.error(f"Failed to create project structure: {str(e)}")
            raise

    async def _create_java_structure(self, project_name: str, output_path: Path, params: Dict[str, Any]) -> Dict[
        str, Any]:
        """Create Java Maven project structure"""

        # Generate project structure using AI
        structure_prompt = f"""
        Create a Maven project structure for API test automation with these requirements:

        Project: {project_name}
        Framework: Maven + TestNG + RestAssured
        Structure needed:
        - Standard Maven directory structure
        - pom.xml with dependencies for RestAssured, TestNG, Jackson
        - Base test classes and utilities
        - Configuration for different environments
        - README with setup instructions

        Respond with JSON containing file paths and contents:
        {{
            "files": {{
                "pom.xml": "content here",
                "src/main/java/.gitkeep": "",
                "src/test/java/BaseTest.java": "content here",
                "src/test/resources/config.properties": "content here",
                "README.md": "content here"
            }},
            "directories": ["src/main/java", "src/test/java", "src/test/resources"]
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                structure_prompt,
                "You are an expert Java test automation engineer. Create production-ready project structure."
            )

            created_files = []
            created_dirs = []

            # Create directories
            if "directories" in response:
                for dir_path in response["directories"]:
                    full_dir = output_path / dir_path
                    full_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(str(full_dir))

            # Create files
            if "files" in response:
                for file_path, content in response["files"].items():
                    full_file = output_path / file_path

                    # Ensure parent directory exists
                    full_file.parent.mkdir(parents=True, exist_ok=True)

                    # Write file content
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            self.logger.info(
                f"Created Java project structure: {len(created_files)} files, {len(created_dirs)} directories")

            return {
                "operation": "create_project_structure",
                "status": "completed",
                "language": "java",
                "created_files": created_files,
                "created_directories": created_dirs,
                "message": f"Created Java Maven project structure with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create Java structure: {str(e)}")
            raise

    async def _create_python_structure(self, project_name: str, output_path: Path, params: Dict[str, Any]) -> Dict[
        str, Any]:
        """Create Python pytest project structure"""

        structure_prompt = f"""
        Create a Python project structure for API test automation:

        Project: {project_name}
        Framework: pytest + requests + pydantic
        Structure needed:
        - Python package structure
        - requirements.txt with necessary dependencies
        - pytest.ini configuration
        - Base test classes and utilities
        - Configuration management
        - README with setup instructions

        Respond with JSON containing file paths and contents:
        {{
            "files": {{
                "requirements.txt": "content here",
                "pytest.ini": "content here", 
                "tests/__init__.py": "",
                "tests/conftest.py": "content here",
                "tests/base_test.py": "content here",
                "config/config.py": "content here",
                "README.md": "content here"
            }},
            "directories": ["tests", "config", "utils"]
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                structure_prompt,
                "You are an expert Python test automation engineer. Create production-ready project structure."
            )

            created_files = []
            created_dirs = []

            # Create directories
            if "directories" in response:
                for dir_path in response["directories"]:
                    full_dir = output_path / dir_path
                    full_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(str(full_dir))

            # Create files
            if "files" in response:
                for file_path, content in response["files"].items():
                    full_file = output_path / file_path

                    # Ensure parent directory exists
                    full_file.parent.mkdir(parents=True, exist_ok=True)

                    # Write file content
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            self.logger.info(
                f"Created Python project structure: {len(created_files)} files, {len(created_dirs)} directories")

            return {
                "operation": "create_project_structure",
                "status": "completed",
                "language": "python",
                "created_files": created_files,
                "created_directories": created_dirs,
                "message": f"Created Python pytest project structure with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create Python structure: {str(e)}")
            raise

    async def generate_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API tests based on specifications"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Generating API tests for: {project_name}")

        # For MVP, generate basic sample tests
        test_prompt = f"""
        Generate sample API tests for a {language} project:

        Project: {project_name}
        Language: {language}

        Create basic API test examples that demonstrate:
        1. GET request with validation
        2. POST request with JSON payload
        3. Error handling and status code validation
        4. Response time validation
        5. Data validation using JSON schema

        {'Use RestAssured and TestNG for Java' if language == 'java' else 'Use requests and pytest for Python'}

        Respond with JSON:
        {{
            "test_files": {{
                "filename": "file content here"
            }},
            "test_count": 5,
            "test_categories": ["smoke", "regression"]
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                test_prompt,
                "You are an expert API test automation engineer. Generate comprehensive, production-ready tests."
            )

            generated_files = []

            if "test_files" in response:
                for filename, content in response["test_files"].items():
                    # Determine the correct path based on language
                    if language == "java":
                        test_file = output_path / "src/test/java" / filename
                    else:  # python
                        test_file = output_path / "tests" / filename

                    # Write test file
                    test_file.parent.mkdir(parents=True, exist_ok=True)
                    test_file.write_text(content, encoding='utf-8')
                    generated_files.append(str(test_file))

            test_count = response.get("test_count", len(generated_files))

            self.logger.info(f"Generated {test_count} API tests in {len(generated_files)} files")

            return {
                "operation": "generate_tests",
                "status": "completed",
                "generated_files": generated_files,
                "test_count": test_count,
                "categories": response.get("test_categories", []),
                "message": f"Generated {test_count} API tests"
            }

        except Exception as e:
            self.logger.error(f"Failed to generate tests: {str(e)}")
            raise

    async def create_documentation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create project documentation"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating documentation for: {project_name}")

        doc_prompt = f"""
        Create comprehensive documentation for API test automation project:

        Project: {project_name}
        Language: {language}

        Create documentation that includes:
        1. Project overview and setup instructions
        2. How to run tests
        3. Configuration management
        4. Adding new tests
        5. CI/CD integration
        6. Troubleshooting guide

        Respond with JSON:
        {{
            "README.md": "main readme content",
            "docs/SETUP.md": "detailed setup guide", 
            "docs/API_TESTING_GUIDE.md": "testing best practices"
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                doc_prompt,
                "You are a technical writer specializing in test automation documentation."
            )

            created_docs = []

            for doc_path, content in response.items():
                doc_file = output_path / doc_path
                doc_file.parent.mkdir(parents=True, exist_ok=True)
                doc_file.write_text(content, encoding='utf-8')
                created_docs.append(str(doc_file))

            self.logger.info(f"Created {len(created_docs)} documentation files")

            return {
                "operation": "create_documentation",
                "status": "completed",
                "created_files": created_docs,
                "message": f"Created documentation: {len(created_docs)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create documentation: {str(e)}")
            raise

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific API agent operation"""

        self.logger.info(f"Executing operation: {operation}")

        # Universal operation mapping - covers all possible operations
        operation_mapping = {
            # Core operations
            "create_project_structure": self.create_project_structure,
            "generate_tests": self.generate_tests,
            "create_documentation": self.create_documentation,

            # Project setup operations
            "setup_test_framework": self.create_project_structure,
            "test_framework_setup": self.create_project_structure,
            "setup_framework_base": self.create_project_structure,
            "initialize_project_structure": self.create_project_structure,

            # Configuration operations
            "create_config": self.create_configuration_files,
            "create_configuration_files": self.create_configuration_files,
            "setup_configuration": self.create_configuration_files,
            "environment_config_setup": self.create_configuration_files,
            "configure_dependencies": self.create_configuration_files,

            # Utility operations
            "create_utilities": self.create_utility_classes,
            "create_utility_classes": self.create_utility_classes,
            "create_config_files": self.create_utility_classes,
            "create_utility_classes": self.create_utility_classes,

            # Test operations
            "api_client_setup": self.generate_tests,
            "sample_test_creation": self.generate_tests,
            "create_sample_test": self.generate_tests,
            "create_example_tests": self.generate_tests,

            # Test data operations
            "test_data_setup": self.create_test_data,
            "create_test_data": self.create_test_data,

            # Documentation operations
            "reporting_setup": self.create_documentation,
            "create_documentation": self.create_documentation
        }

        if operation in operation_mapping:
            return await operation_mapping[operation](params)
        else:
            # If operation is unknown, try to guess based on keywords
            operation_lower = operation.lower()

            if any(keyword in operation_lower for keyword in ['structure', 'framework', 'setup', 'initialize']):
                self.logger.info(f"Mapping unknown operation '{operation}' to create_project_structure")
                return await self.create_project_structure(params)
            elif any(keyword in operation_lower for keyword in ['config', 'configuration', 'environment']):
                self.logger.info(f"Mapping unknown operation '{operation}' to create_configuration_files")
                return await self.create_configuration_files(params)
            elif any(keyword in operation_lower for keyword in ['test', 'example', 'sample']):
                self.logger.info(f"Mapping unknown operation '{operation}' to generate_tests")
                return await self.generate_tests(params)
            elif any(keyword in operation_lower for keyword in ['util', 'helper', 'class']):
                self.logger.info(f"Mapping unknown operation '{operation}' to create_utility_classes")
                return await self.create_utility_classes(params)
            elif any(keyword in operation_lower for keyword in ['doc', 'readme', 'report']):
                self.logger.info(f"Mapping unknown operation '{operation}' to create_documentation")
                return await self.create_documentation(params)
            else:
                # Default to project structure if nothing else matches
                self.logger.warning(f"Unknown operation '{operation}', defaulting to create_project_structure")
                return await self.create_project_structure(params)

    async def create_configuration_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create configuration files for the project"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating configuration files for: {project_name}")

        config_prompt = f"""
        Create configuration files for {language} API test project:

        Project: {project_name}
        Language: {language}

        Create configuration files for different environments (dev, staging, prod):
        - Properties/YAML files for environment-specific settings
        - Configuration for base URLs, timeouts, credentials
        - Logging configuration
        - Test data configuration

        Respond with JSON:
        {{
            "config_files": {{
                "filename": "file content here"
            }}
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                config_prompt,
                "You are an expert in test automation configuration management."
            )

            created_files = []

            if "config_files" in response:
                if language == "java":
                    config_dir = output_path / "src/test/resources"
                else:
                    config_dir = output_path / "config"

                config_dir.mkdir(parents=True, exist_ok=True)

                for filename, content in response["config_files"].items():
                    # Remove any path from filename - just use the filename
                    clean_filename = Path(filename).name
                    config_file = config_dir / clean_filename
                    config_file.write_text(content, encoding='utf-8')
                    created_files.append(str(config_file))

            return {
                "operation": "create_configuration_files",
                "status": "completed",
                "created_files": created_files,
                "message": f"Created {len(created_files)} configuration files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create configuration files: {str(e)}")
            raise

    async def create_utility_classes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create utility classes for the project"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating utility classes for: {project_name}")

        utility_prompt = f"""
        Create utility classes for {language} API test automation:

        Project: {project_name}
        Language: {language}

        Create utility classes for:
        - HTTP client wrapper
        - JSON/XML parsing utilities  
        - Test data generators
        - Assertion helpers
        - Report utilities
        - Common test helpers

        Respond with JSON:
        {{
            "utility_files": {{
                "filename": "file content here"
            }}
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                utility_prompt,
                "You are an expert in creating reusable test automation utilities."
            )

            created_files = []

            if "utility_files" in response:
                if language == "java":
                    util_dir = output_path / "src/test/java/utils"
                else:
                    util_dir = output_path / "utils"

                util_dir.mkdir(parents=True, exist_ok=True)

                for filename, content in response["utility_files"].items():
                    util_file = util_dir / filename
                    util_file.write_text(content, encoding='utf-8')
                    created_files.append(str(util_file))

            return {
                "operation": "create_utility_classes",
                "status": "completed",
                "created_files": created_files,
                "message": f"Created {len(created_files)} utility classes"
            }

        except Exception as e:
            self.logger.error(f"Failed to create utility classes: {str(e)}")
            raise

    async def create_test_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create test data files and generators"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Creating test data for: {project_name}")

        test_data_prompt = f"""
        Create test data management for {language} API tests:

        Project: {project_name}
        Language: {language}

        Create:
        - Sample JSON test data files
        - Test data builders/factories
        - Data providers for different test scenarios
        - Mock response data

        Respond with JSON:
        {{
            "test_data_files": {{
                "filename": "file content here"
            }}
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                test_data_prompt,
                "You are an expert in test data management and generation."
            )

            created_files = []

            if "test_data_files" in response:
                if language == "java":
                    data_dir = output_path / "src/test/resources/testdata"
                else:
                    data_dir = output_path / "testdata"

                data_dir.mkdir(parents=True, exist_ok=True)

                for filename, content in response["test_data_files"].items():
                    data_file = data_dir / filename
                    data_file.write_text(content, encoding='utf-8')
                    created_files.append(str(data_file))

            return {
                "operation": "create_test_data",
                "status": "completed",
                "created_files": created_files,
                "message": f"Created {len(created_files)} test data files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create test data: {str(e)}")
            raise