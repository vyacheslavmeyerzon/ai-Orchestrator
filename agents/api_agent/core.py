"""
API Agent - Complete implementation with Page Object Pattern and dynamic imports
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from collections import defaultdict
import re

from common.ai_connector import AIConnectorFactory
from common.config import get_config
from common.logger import get_agent_logger


class APIAgent:
    """Agent responsible for API test creation and management with Page Object Pattern"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("api_agent")
        self.ai_connector = AIConnectorFactory.create_connector()

        self.logger.info("API Agent initialized with Page Object Pattern support")

    def _normalize_project_name(self, project_name: str) -> str:
        """Normalize project name for Java package naming"""
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', project_name.lower())
        # Remove consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        return normalized

    def _get_base_package(self, project_name: str) -> str:
        """Generate base package name from project name"""
        normalized_name = self._normalize_project_name(project_name)
        return f"com.{normalized_name}"

    async def create_project_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create project structure with Page Object Pattern and real tests"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])
        parsed_data = params.get('parsed_data')

        self.logger.info(f"Creating {language} project with Page Object Pattern: {project_name}")

        if parsed_data:
            self.logger.info(f"Using parsed API data with {len(parsed_data.get('endpoints', []))} endpoints")

        try:
            # Ensure output directory exists
            output_path.mkdir(parents=True, exist_ok=True)

            if language == "java":
                return await self._create_complete_java_project(project_name, output_path, params, parsed_data)
            elif language == "python":
                return await self._create_complete_python_project(project_name, output_path, params, parsed_data)
            else:
                raise ValueError(f"Unsupported language: {language}")

        except Exception as e:
            self.logger.error(f"Failed to create project structure: {str(e)}")
            raise

    async def _create_complete_java_project(self, project_name: str, output_path: Path,
                                            params: Dict[str, Any], parsed_data: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """Create complete Java project with Page Object Pattern"""

        base_package = self._get_base_package(project_name)
        package_path = base_package.replace('.', '/')

        self.logger.info(f"Creating Java project with base package: {base_package}")

        # Step 1: Create complete pom.xml with all dependencies
        pom_content = await self._generate_complete_pom_xml(project_name, parsed_data)

        # Step 2: Create base classes and utilities
        base_classes = await self._generate_java_base_classes(base_package, parsed_data)

        # Step 3: Generate API classes (Page Objects) in src/main/java
        api_classes = []
        model_classes = []

        if parsed_data and parsed_data.get('endpoints'):
            api_classes = await self._generate_java_api_classes(base_package, parsed_data)
            model_classes = await self._generate_java_model_classes(base_package, parsed_data)

        # Step 4: Generate test classes in src/test/java
        test_classes = []
        if parsed_data and parsed_data.get('endpoints'):
            test_classes = await self._generate_java_test_classes(base_package, parsed_data)

        # Step 5: Create configuration files
        config_files = await self._generate_java_config_files(parsed_data)

        # Combine all files
        all_files = {
            "pom.xml": pom_content,
            **base_classes,
            **api_classes,
            **model_classes,
            **test_classes,
            **config_files
        }

        # Write all files
        created_files = []
        created_dirs = set()

        for file_path, content in all_files.items():
            full_file = output_path / file_path
            full_file.parent.mkdir(parents=True, exist_ok=True)
            full_file.write_text(content, encoding='utf-8')
            created_files.append(str(full_file))
            created_dirs.add(str(full_file.parent))

        self.logger.info(
            f"Created complete Java project: {len(created_files)} files in {len(created_dirs)} directories")

        endpoints_count = len(parsed_data.get('endpoints', [])) if parsed_data else 0

        return {
            "operation": "create_project_structure",
            "status": "completed",
            "language": "java",
            "created_files": created_files,
            "created_directories": list(created_dirs),
            "base_package": base_package,
            "endpoints_processed": endpoints_count,
            "api_classes": len(api_classes),
            "test_classes": len(test_classes),
            "model_classes": len(model_classes),
            "message": f"Created complete Java project with Page Object Pattern: {endpoints_count} endpoints, {len(api_classes)} API classes, {len(test_classes)} test classes"
        }

    async def _generate_complete_pom_xml(self, project_name: str, parsed_data: Dict[str, Any] = None) -> str:
        """Generate complete pom.xml with all necessary dependencies"""

        pom_prompt = f"""
        Generate ONLY the raw pom.xml content for API test automation project:

        Project Name: {project_name}

        Requirements:
        - Maven 4.0.0 model
        - Java 11+ with proper compiler plugin
        - RestAssured latest stable version
        - TestNG latest stable version 
        - Jackson for JSON handling
        - SLF4J + Logback for logging
        - Maven Surefire Plugin for TestNG execution
        - Commons Lang3 utilities
        - Allure TestNG for reporting
        - All with proper versions and plugin configuration

        IMPORTANT: Return ONLY the raw XML content, no explanations, no markdown, no code blocks.
        Start directly with <?xml version="1.0" encoding="UTF-8"?>
        """

        try:
            response = await self.ai_connector.generate_response(
                pom_prompt,
                "Return ONLY raw pom.xml content without any markdown formatting or explanations."
            )

            # Clean response from any markdown
            cleaned_response = self._clean_markdown_from_response(response)
            return cleaned_response

        except Exception as e:
            self.logger.error(f"Failed to generate pom.xml: {str(e)}")
            return self._get_fallback_pom_xml(project_name)

    def _get_fallback_pom_xml(self, project_name: str) -> str:
        """Fallback pom.xml if AI generation fails"""
        normalized_name = self._normalize_project_name(project_name)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.{normalized_name}</groupId>
    <artifactId>{project_name}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <restassured.version>5.3.2</restassured.version>
        <testng.version>7.8.0</testng.version>
        <jackson.version>2.15.2</jackson.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <version>${{restassured.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.testng</groupId>
            <artifactId>testng</artifactId>
            <version>${{testng.version}}</version>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>${{jackson.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>2.0.7</version>
        </dependency>
        <dependency>
            <groupId>ch.qos.logback</groupId>
            <artifactId>logback-classic</artifactId>
            <version>1.4.11</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
                <configuration>
                    <suiteXmlFiles>
                        <suiteXmlFile>src/test/resources/testng.xml</suiteXmlFile>
                    </suiteXmlFiles>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>"""

    def _clean_markdown_from_response(self, response: str) -> str:
        """Clean markdown formatting from AI response"""
        import re

        # Remove markdown code blocks
        response = re.sub(r'```\w*\n', '', response)
        response = re.sub(r'```', '', response)

        # Remove explanatory text before and after code
        lines = response.split('\n')
        start_idx = 0
        end_idx = len(lines)

        # Find where actual code starts (usually <?xml or package)
        for i, line in enumerate(lines):
            if line.strip().startswith('<?xml') or line.strip().startswith('package '):
                start_idx = i
                break

        # Find where code ends (before explanatory text)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not line.startswith('This ') and not line.startswith('Note:') and not line.startswith('The '):
                if line.endswith('>') or line.endswith('}') or line.endswith(';'):
                    end_idx = i + 1
                    break

        # Extract clean code
        clean_lines = lines[start_idx:end_idx]
        return '\n'.join(clean_lines).strip()

    async def _generate_java_base_classes(self, base_package: str, parsed_data: Dict[str, Any] = None) -> Dict[
        str, str]:
        """Generate base classes with complete imports"""

        base_classes = {}
        package_path = base_package.replace('.', '/')

        # Generate BaseTest class
        base_test_prompt = f"""
        Generate ONLY the raw Java class content for BaseTest:

        Package: {base_package}.base

        Requirements:
        - All necessary imports (TestNG, RestAssured, logging, configuration)
        - Setup and teardown methods with @BeforeClass, @AfterClass
        - Configuration management (load from properties files)
        - RestAssured base configuration with parameterized base URL
        - Authentication setup for API key authentication
        - Common assertion methods
        - Request/response logging setup
        - Use ConfigManager for getting base URL from properties
        - NO hardcoded URLs or API keys

        Authentication: {parsed_data.get('authentication', {}).get('type', 'none') if parsed_data else 'none'}

        IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
        Start directly with package declaration.
        """

        try:
            base_test_response = await self.ai_connector.generate_response(
                base_test_prompt,
                "Return ONLY raw Java code without markdown formatting or explanations."
            )
            base_classes[f"src/test/java/{package_path}/base/BaseTest.java"] = self._clean_markdown_from_response(
                base_test_response)
        except Exception as e:
            self.logger.error(f"Failed to generate BaseTest: {str(e)}")

        # Generate ConfigManager class
        config_manager_prompt = f"""
        Generate ONLY the raw Java class content for ConfigManager:

        Package: {base_package}.utils

        Requirements:
        - All necessary imports (Properties, FileInputStream, logging)
        - Singleton pattern implementation
        - Load configuration from properties files (dev-config.properties, staging-config.properties, prod-config.properties)
        - Environment-specific configuration loading
        - Methods: getBaseUrl(), getApiKey(), getTimeout(), getRetryCount()
        - System property for environment selection (default: dev)
        - Proper exception handling
        - NO hardcoded values

        IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
        Start directly with package declaration.
        """

        try:
            config_manager_response = await self.ai_connector.generate_response(
                config_manager_prompt,
                "Return ONLY raw Java code without markdown formatting or explanations."
            )
            base_classes[f"src/main/java/{package_path}/utils/ConfigManager.java"] = self._clean_markdown_from_response(
                config_manager_response)
        except Exception as e:
            self.logger.error(f"Failed to generate ConfigManager: {str(e)}")

        # Generate ApiClient class
        api_client_prompt = f"""
        Generate ONLY the raw Java class content for ApiClient:

        Package: {base_package}.utils

        Requirements:
        - All necessary imports (RestAssured, Response, RequestSpecification, etc.)
        - Constructor that accepts ConfigManager
        - Wrapper methods for GET, POST, PUT, DELETE
        - Use ConfigManager.getBaseUrl() for base URL
        - Authentication handling using ConfigManager.getApiKey()
        - Request/response logging
        - Timeout configuration from ConfigManager
        - Common headers setup
        - Error handling with proper exceptions
        - NO hardcoded URLs or credentials

        IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
        Start directly with package declaration.
        """

        try:
            api_client_response = await self.ai_connector.generate_response(
                api_client_prompt,
                "Return ONLY raw Java code without markdown formatting or explanations."
            )
            base_classes[f"src/main/java/{package_path}/utils/ApiClient.java"] = self._clean_markdown_from_response(
                api_client_response)
        except Exception as e:
            self.logger.error(f"Failed to generate ApiClient: {str(e)}")

        return base_classes

    async def _generate_java_api_classes(self, base_package: str, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate API classes (Page Objects) with complete imports"""

        api_classes = {}
        package_path = base_package.replace('.', '/')
        endpoints = parsed_data.get('endpoints', [])

        # Group endpoints by category
        endpoints_by_category = self._group_endpoints_by_category(endpoints)

        for category, category_endpoints in endpoints_by_category.items():
            class_name = f"{category.capitalize()}Api"

            api_class_prompt = f"""
            Generate ONLY the raw Java class content for {class_name}:

            Package: {base_package}.api
            Class Name: {class_name}

            Endpoints to implement:
            {json.dumps(category_endpoints, indent=2)}

            Requirements:
            - All necessary imports ({base_package}.utils.ApiClient, {base_package}.utils.ConfigManager, io.restassured.response.Response, etc.)
            - Constructor with ApiClient and ConfigManager injection
            - Method for each endpoint with proper parameters from the endpoint specification
            - Use configManager.getBaseUrl() for base URL (NO hardcoded URLs)
            - Use configManager.getApiKey() for authentication (NO hardcoded keys)
            - Return Response objects
            - Handle path parameters and query parameters properly
            - Proper error handling with try/catch
            - Javadoc comments for each method
            - NO hardcoded URLs, credentials, or magic values

            IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
            Start directly with package declaration.
            """

            try:
                response = await self.ai_connector.generate_response(
                    api_class_prompt,
                    "Return ONLY raw Java code without markdown formatting or explanations."
                )
                api_classes[f"src/main/java/{package_path}/api/{class_name}.java"] = self._clean_markdown_from_response(
                    response)
                self.logger.info(f"Generated API class: {class_name}")
            except Exception as e:
                self.logger.error(f"Failed to generate API class {class_name}: {str(e)}")

        return api_classes

    async def _generate_java_model_classes(self, base_package: str, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate model classes for request/response data"""

        model_classes = {}
        package_path = base_package.replace('.', '/')

        # Extract models from parsed data
        models = parsed_data.get('models', {})
        endpoints = parsed_data.get('endpoints', [])

        # Generate models from API specification
        if models:
            for model_name, model_schema in models.items():
                model_prompt = f"""
                Generate ONLY the raw Java model class content for {model_name}:

                Package: {base_package}.models
                Class Name: {model_name}

                Schema:
                {json.dumps(model_schema, indent=2)}

                Requirements:
                - All necessary imports (Jackson annotations, validation annotations, etc.)
                - Private fields with proper Java types based on schema
                - Default constructor
                - Parameterized constructor
                - Getter and setter methods
                - toString() method
                - equals() and hashCode() methods
                - Jackson annotations (@JsonProperty, @JsonIgnoreProperties, etc.)
                - Builder pattern methods if appropriate

                IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
                Start directly with package declaration.
                """

                try:
                    response = await self.ai_connector.generate_response(
                        model_prompt,
                        "Return ONLY raw Java code without markdown formatting or explanations."
                    )
                    model_classes[
                        f"src/main/java/{package_path}/models/{model_name}.java"] = self._clean_markdown_from_response(
                        response)
                except Exception as e:
                    self.logger.error(f"Failed to generate model {model_name}: {str(e)}")

        # Generate common models if no specific models found
        if not models and endpoints:
            common_models = ['ApiResponse', 'ErrorResponse']
            for model_name in common_models:
                model_prompt = f"""
                Generate ONLY the raw Java model class content for {model_name}:

                Package: {base_package}.models
                Class Name: {model_name}

                Requirements:
                - All necessary imports
                - Fields appropriate for {model_name} (message, status, data, etc.)
                - Complete implementation with getters/setters
                - Jackson annotations
                - toString(), equals(), hashCode() methods

                IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
                Start directly with package declaration.
                """

                try:
                    response = await self.ai_connector.generate_response(
                        model_prompt,
                        "Return ONLY raw Java code without markdown formatting or explanations."
                    )
                    model_classes[
                        f"src/main/java/{package_path}/models/{model_name}.java"] = self._clean_markdown_from_response(
                        response)
                except Exception as e:
                    self.logger.error(f"Failed to generate model {model_name}: {str(e)}")

        return model_classes

    async def _generate_java_test_classes(self, base_package: str, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate test classes with complete imports"""

        test_classes = {}
        package_path = base_package.replace('.', '/')
        endpoints = parsed_data.get('endpoints', [])

        # Group endpoints by category
        endpoints_by_category = self._group_endpoints_by_category(endpoints)

        for category, category_endpoints in endpoints_by_category.items():
            test_class_name = f"{category.capitalize()}ApiTest"
            api_class_name = f"{category.capitalize()}Api"

            test_class_prompt = f"""
            Generate ONLY the raw Java test class content for {test_class_name}:

            Package: {base_package}.tests
            Class Name: {test_class_name}

            Endpoints to test:
            {json.dumps(category_endpoints, indent=2)}

            Requirements:
            - All necessary imports ({base_package}.base.BaseTest, {base_package}.api.{api_class_name}, org.testng.annotations.*, etc.)
            - Extend BaseTest class
            - Inject {api_class_name} and ConfigManager in setup method
            - Test method for each endpoint from the specification
            - Positive and negative test scenarios for each endpoint
            - Use realistic test data (NO hardcoded IDs like "1" or "123")
            - Use configManager or test data providers for test values
            - Proper assertions for status codes and response validation based on endpoint specification
            - TestNG annotations (@Test, @BeforeClass, @DataProvider if needed)
            - Meaningful test method names that reflect the endpoint being tested
            - Use Page Object methods from {api_class_name}
            - NO hardcoded URLs, IDs, or magic values

            IMPORTANT: Return ONLY raw Java code, no explanations, no markdown blocks.
            Start directly with package declaration.
            """

            try:
                response = await self.ai_connector.generate_response(
                    test_class_prompt,
                    "Return ONLY raw Java code without markdown formatting or explanations."
                )
                test_classes[
                    f"src/test/java/{package_path}/tests/{test_class_name}.java"] = self._clean_markdown_from_response(
                    response)
                self.logger.info(f"Generated test class: {test_class_name}")
            except Exception as e:
                self.logger.error(f"Failed to generate test class {test_class_name}: {str(e)}")

        return test_classes

    async def _generate_java_config_files(self, parsed_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate configuration files"""

        config_files = {}

        # Generate TestNG XML
        testng_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE suite SYSTEM "http://testng.org/testng-1.0.dtd">
<suite name="API Test Suite" parallel="methods" thread-count="3">
    <test name="API Tests">
        <packages>
            <package name="*.tests"/>
        </packages>
    </test>
</suite>"""
        config_files["src/test/resources/testng.xml"] = testng_xml

        # Generate environment configuration files
        environments = ['dev', 'staging', 'prod']
        base_url = parsed_data.get('base_url', 'https://api.example.com') if parsed_data else 'https://api.example.com'

        for env in environments:
            env_url = base_url.replace('https://', f'https://{env}.' if env != 'prod' else 'https://')

            config_content = f"""# {env.upper()} Environment Configuration
api.base.url={env_url}
api.timeout=30000
api.retry.count=3
api.log.requests=true
api.log.responses=true

# Authentication
auth.type=none
auth.api.key=
auth.bearer.token=

# Test Data
test.data.path=src/test/resources/testdata
test.reports.path=target/reports
"""
            config_files[f"src/test/resources/{env}-config.properties"] = config_content

        # Generate logback configuration
        logback_xml = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="FILE" class="ch.qos.logback.core.FileAppender">
        <file>target/logs/api-tests.log</file>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="FILE"/>
    </root>
</configuration>"""
        config_files["src/test/resources/logback-test.xml"] = logback_xml

        return config_files

    def _group_endpoints_by_category(self, endpoints: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group endpoints by tags/category for better organization"""
        grouped = defaultdict(list)

        for endpoint in endpoints:
            # Try to get category from tags
            tags = endpoint.get('tags', [])
            if tags:
                category = tags[0].lower().replace(' ', '').replace('-', '')
            else:
                # Fallback: use first part of path
                path = endpoint.get('path', '/unknown')
                if path.startswith('/'):
                    path_parts = path.split('/')
                    category = path_parts[1] if len(path_parts) > 1 else 'api'
                else:
                    category = 'api'

            # Clean category name for Java class
            category = ''.join(c for c in category if c.isalnum()).lower()
            if not category:
                category = 'api'

            grouped[category].append(endpoint)

        return dict(grouped)

    async def _create_complete_python_project(self, project_name: str, output_path: Path,
                                              params: Dict[str, Any], parsed_data: Dict[str, Any] = None) -> Dict[
        str, Any]:
        """Create complete Python project with Page Object Pattern"""

        # For now, focus on Java implementation
        # Python implementation can be added later with similar structure
        return await self._create_basic_python_structure(project_name, output_path, params)

    async def _create_basic_python_structure(self, project_name: str, output_path: Path, params: Dict[str, Any]) -> \
    Dict[str, Any]:
        """Create basic Python structure (placeholder)"""

        structure_prompt = f"""
        Create a Python project structure for API test automation:

        Project: {project_name}
        Framework: pytest + requests + pydantic

        Respond with JSON containing file paths and contents:
        {{
            "files": {{
                "requirements.txt": "requests>=2.31.0\\npytest>=7.4.0\\npydantic>=2.0.0",
                "pytest.ini": "[tool:pytest]\\ntestpaths = tests\\npython_files = test_*.py\\npython_classes = Test*\\npython_functions = test_*",
                "tests/__init__.py": "",
                "README.md": "# {project_name}\\n\\nAPI Test Automation Project"
            }},
            "directories": ["tests", "config", "utils"]
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                structure_prompt,
                "Create basic Python project structure."
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
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            return {
                "operation": "create_project_structure",
                "status": "completed",
                "language": "python",
                "created_files": created_files,
                "created_directories": created_dirs,
                "message": f"Created basic Python project structure with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create Python structure: {str(e)}")
            raise

    # Keep existing methods for backward compatibility
    async def generate_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional tests (legacy method)"""
        return {
            "operation": "generate_tests",
            "status": "completed",
            "message": "Tests already generated in project structure"
        }

    async def create_documentation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create project documentation"""

        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])
        parsed_data = params.get('parsed_data')

        # Generate comprehensive README
        readme_content = f"""# {project_name}

API Test Automation Project using {language.title()} and {'Maven + TestNG + RestAssured' if language == 'java' else 'pytest + requests'}.

## Project Structure

```
{project_name}/
├── src/
│   ├── main/java/           # Page Objects and utilities
│   │   ├── api/            # API classes (Page Objects)
│   │   ├── models/         # Data models
│   │   └── utils/          # Utilities and helpers
│   └── test/java/          # Test classes
│       ├── base/           # Base test classes
│       └── tests/          # Actual test classes
├── src/test/resources/     # Configuration files
├── target/                 # Build output
└── pom.xml                # Maven configuration
```

## Setup Instructions

1. **Prerequisites:**
   - Java 11+
   - Maven 3.6+

2. **Install Dependencies:**
   ```bash
   mvn clean install
   ```

3. **Run Tests:**
   ```bash
   mvn test
   ```

4. **Configuration:**
   - Update `src/test/resources/dev-config.properties` with your API details
   - Set environment variables for sensitive data

## Generated Features

{'- Real API tests for ' + str(len(parsed_data.get('endpoints', []))) + ' endpoints' if parsed_data else '- Basic API test structure'}
- Page Object Pattern implementation
- Complete Maven configuration with all dependencies
- Environment-specific configuration
- Comprehensive logging setup
- TestNG test execution framework

## Usage

The project follows Page Object Pattern:
- API operations are in `src/main/java/*/api/` classes
- Test scenarios are in `src/test/java/*/tests/` classes
- Models are in `src/main/java/*/models/` classes

Example:
```java
// Using Page Object in test
PetApi petApi = new PetApi(apiClient);
Response response = petApi.getPetById(123);
Assert.assertEquals(response.statusCode(), 200);
```
"""

        readme_file = output_path / "README.md"
        readme_file.write_text(readme_content, encoding='utf-8')

        return {
            "operation": "create_documentation",
            "status": "completed",
            "created_files": [str(readme_file)],
            "message": "Created comprehensive project documentation"
        }

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific API agent operation"""

        self.logger.info(f"Executing operation: {operation}")

        operation_mapping = {
            "create_project_structure": self.create_project_structure,
            "generate_tests": self.generate_tests,
            "create_documentation": self.create_documentation,
        }

        if operation in operation_mapping:
            return await operation_mapping[operation](params)
        else:
            # Default to project structure creation
            self.logger.info(f"Unknown operation '{operation}', defaulting to create_project_structure")
            return await self.create_project_structure(params)

    # Placeholder methods for backward compatibility
    async def create_configuration_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"operation": "create_configuration_files", "status": "completed",
                "message": "Configs included in project structure"}

    async def create_utility_classes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"operation": "create_utility_classes", "status": "completed",
                "message": "Utilities included in project structure"}

    async def create_test_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"operation": "create_test_data", "status": "completed",
                "message": "Test data handling included in project structure"}