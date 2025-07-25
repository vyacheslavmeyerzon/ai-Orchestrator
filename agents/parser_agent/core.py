"""
Parser Agent - Specialized agent for parsing API specifications and generating comprehensive tests
"""

import os
import json
import yaml
import asyncio
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
import re

from common.ai_connector import AIConnectorFactory
from common.config import get_config
from common.logger import get_agent_logger


class ParserAgent:
    """Agent responsible for parsing API specifications and generating test data"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("parser_agent")
        self.ai_connector = AIConnectorFactory.create_connector()

        self.logger.info("Parser Agent initialized")

    async def parse_api_specification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse API specification file and extract test information"""

        spec_file_path = params.get('spec_file_path')
        project_name = params['project_name']
        language = params['language']

        self.logger.info(f"Parsing API specification: {spec_file_path}")

        if not spec_file_path or not os.path.exists(spec_file_path):
            raise ValueError(f"API specification file not found: {spec_file_path}")

        try:
            # Read specification file
            spec_content = self._read_specification_file(spec_file_path)

            # Determine specification type
            spec_type = self._detect_specification_type(spec_file_path, spec_content)

            # Parse based on type
            if spec_type == "openapi":
                parsed_data = await self._parse_openapi_spec(spec_content)
            elif spec_type == "postman":
                parsed_data = await self._parse_postman_collection(spec_content)
            elif spec_type == "yaml":
                parsed_data = await self._parse_yaml_spec(spec_content)
            else:
                raise ValueError(f"Unsupported specification type: {spec_type}")

            # Enhanced parsing with AI analysis
            enhanced_data = await self._enhance_with_ai_analysis(parsed_data, language)

            self.logger.info(
                f"Successfully parsed {spec_type} specification with {len(enhanced_data.get('endpoints', []))} endpoints")

            return {
                "operation": "parse_api_specification",
                "status": "completed",
                "spec_type": spec_type,
                "spec_file": spec_file_path,
                "parsed_data": enhanced_data,
                "endpoints_count": len(enhanced_data.get('endpoints', [])),
                "message": f"Parsed {spec_type} specification with {len(enhanced_data.get('endpoints', []))} endpoints"
            }

        except Exception as e:
            self.logger.error(f"Failed to parse API specification: {str(e)}")
            raise

    def _read_specification_file(self, file_path: str) -> Union[Dict, str]:
        """Read and parse specification file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    return json.load(f)
                elif file_path.endswith(('.yml', '.yaml')):
                    return yaml.safe_load(f)
                else:
                    return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read specification file: {str(e)}")

    def _detect_specification_type(self, file_path: str, content: Union[Dict, str]) -> str:
        """Detect the type of API specification"""

        # Check file extension first
        if file_path.endswith('.json'):
            if isinstance(content, dict):
                # Check for Postman collection indicators
                if 'info' in content and 'item' in content:
                    return "postman"
                # Check for OpenAPI indicators
                elif 'openapi' in content or 'swagger' in content:
                    return "openapi"

        elif file_path.endswith(('.yml', '.yaml')):
            if isinstance(content, dict):
                if 'openapi' in content or 'swagger' in content:
                    return "openapi"
                else:
                    return "yaml"

        # Default to OpenAPI if uncertain
        return "openapi"

    async def _parse_openapi_spec(self, spec_content: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAPI/Swagger specification"""

        parsed_data = {
            "title": spec_content.get('info', {}).get('title', 'API Tests'),
            "version": spec_content.get('info', {}).get('version', '1.0.0'),
            "description": spec_content.get('info', {}).get('description', ''),
            "base_url": self._extract_base_url(spec_content),
            "servers": spec_content.get('servers', []),
            "authentication": self._extract_auth_info(spec_content),
            "endpoints": [],
            "models": self._extract_data_models(spec_content),
            "security_schemes": spec_content.get('components', {}).get('securitySchemes', {})
        }

        # Parse endpoints
        paths = spec_content.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint_info = self._parse_endpoint_details(path, method.upper(), details)
                    parsed_data['endpoints'].append(endpoint_info)

        return parsed_data

    async def _parse_postman_collection(self, collection: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Postman collection"""

        parsed_data = {
            "title": collection.get('info', {}).get('name', 'API Tests'),
            "version": collection.get('info', {}).get('version', '1.0.0'),
            "description": collection.get('info', {}).get('description', ''),
            "base_url": self._extract_postman_base_url(collection),
            "authentication": self._extract_postman_auth(collection),
            "endpoints": [],
            "variables": collection.get('variable', []),
            "environments": []
        }

        # Parse requests from collection items
        items = collection.get('item', [])
        self._parse_postman_items(items, parsed_data['endpoints'])

        return parsed_data

    async def _parse_yaml_spec(self, yaml_content: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generic YAML API specification"""

        # Try to treat as OpenAPI first
        if 'openapi' in yaml_content or 'swagger' in yaml_content:
            return await self._parse_openapi_spec(yaml_content)

        # Generic YAML parsing
        parsed_data = {
            "title": yaml_content.get('title', 'API Tests'),
            "version": yaml_content.get('version', '1.0.0'),
            "description": yaml_content.get('description', ''),
            "base_url": yaml_content.get('base_url', '${api.base.url}'),
            "endpoints": [],
            "configuration": yaml_content
        }

        # Try to extract endpoints if they exist
        if 'endpoints' in yaml_content:
            for endpoint_data in yaml_content['endpoints']:
                parsed_data['endpoints'].append(self._parse_generic_endpoint(endpoint_data))

        return parsed_data

    def _extract_base_url(self, spec: Dict[str, Any]) -> str:
        """Extract base URL from OpenAPI spec"""
        servers = spec.get('servers', [])
        if servers:
            return servers[0].get('url', '${api.base.url}')

        # Fallback to host + basePath for Swagger 2.0
        host = spec.get('host', '')
        base_path = spec.get('basePath', '')
        schemes = spec.get('schemes', ['https'])

        if host:
            return f"{schemes[0]}://{host}{base_path}"

        return '${api.base.url}'

    def _extract_postman_base_url(self, collection: Dict[str, Any]) -> str:
        """Extract base URL from Postman collection"""
        # Look for base URL in variables
        variables = collection.get('variable', [])
        for var in variables:
            if var.get('key') in ['baseUrl', 'base_url', 'host']:
                return var.get('value', '${api.base.url}')

        return '${api.base.url}'

    def _extract_auth_info(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract authentication information"""
        auth_info = {
            "type": "none",
            "schemes": [],
            "security_requirements": spec.get('security', [])
        }

        security_schemes = spec.get('components', {}).get('securitySchemes', {})
        if security_schemes:
            auth_info["schemes"] = list(security_schemes.keys())
            # Determine primary auth type
            first_scheme = next(iter(security_schemes.values()), {})
            auth_info["type"] = first_scheme.get('type', 'none')

        return auth_info

    def _extract_postman_auth(self, collection: Dict[str, Any]) -> Dict[str, Any]:
        """Extract authentication from Postman collection"""
        auth = collection.get('auth', {})
        return {
            "type": auth.get('type', 'none'),
            "config": auth
        }

    def _extract_data_models(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data models/schemas from OpenAPI spec"""
        components = spec.get('components', {})
        schemas = components.get('schemas', {})

        models = {}
        for model_name, model_schema in schemas.items():
            models[model_name] = {
                "type": model_schema.get('type', 'object'),
                "properties": model_schema.get('properties', {}),
                "required": model_schema.get('required', []),
                "example": model_schema.get('example', {})
            }

        return models

    def _parse_endpoint_details(self, path: str, method: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual endpoint details"""

        endpoint = {
            "path": path,
            "method": method,
            "operation_id": details.get('operationId',
                                        f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}"),
            "summary": details.get('summary', ''),
            "description": details.get('description', ''),
            "tags": details.get('tags', []),
            "parameters": self._parse_parameters(details.get('parameters', [])),
            "request_body": self._parse_request_body(details.get('requestBody', {})),
            "responses": self._parse_responses(details.get('responses', {})),
            "security": details.get('security', []),
            "test_scenarios": self._generate_test_scenarios(path, method, details)
        }

        return endpoint

    def _parse_postman_items(self, items: List[Dict], endpoints: List[Dict]):
        """Recursively parse Postman collection items"""
        for item in items:
            if 'item' in item:  # Folder
                self._parse_postman_items(item['item'], endpoints)
            elif 'request' in item:  # Request
                endpoint = self._parse_postman_request(item)
                endpoints.append(endpoint)

    def _parse_postman_request(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual Postman request"""
        request = item.get('request', {})
        url = request.get('url', {})

        # Handle different URL formats
        if isinstance(url, str):
            path = url
        else:
            raw_url = url.get('raw', '')
            path = url.get('path', [])
            if isinstance(path, list):
                path = '/' + '/'.join(path)
            elif not path and raw_url:
                # Extract path from raw URL
                path = raw_url.split('/')[-1] if '/' in raw_url else raw_url

        endpoint = {
            "path": path,
            "method": request.get('method', 'GET'),
            "operation_id": item.get('name', '').replace(' ', '_').lower(),
            "summary": item.get('name', ''),
            "description": item.get('description', ''),
            "parameters": self._parse_postman_params(url.get('query', [])),
            "request_body": self._parse_postman_body(request.get('body', {})),
            "headers": request.get('header', []),
            "test_scenarios": []
        }

        return endpoint

    def _parse_parameters(self, parameters: List[Dict]) -> List[Dict]:
        """Parse OpenAPI parameters"""
        parsed_params = []
        for param in parameters:
            parsed_params.append({
                "name": param.get('name', ''),
                "in": param.get('in', 'query'),
                "required": param.get('required', False),
                "type": param.get('schema', {}).get('type', 'string'),
                "description": param.get('description', ''),
                "example": param.get('example', '')
            })
        return parsed_params

    def _parse_request_body(self, request_body: Dict) -> Dict[str, Any]:
        """Parse request body schema"""
        if not request_body:
            return {}

        content = request_body.get('content', {})
        json_content = content.get('application/json', {})

        return {
            "required": request_body.get('required', False),
            "content_type": "application/json",
            "schema": json_content.get('schema', {}),
            "example": json_content.get('example', {})
        }

    def _parse_responses(self, responses: Dict) -> Dict[str, Any]:
        """Parse response schemas"""
        parsed_responses = {}
        for status_code, response_info in responses.items():
            content = response_info.get('content', {})
            json_content = content.get('application/json', {})

            parsed_responses[status_code] = {
                "description": response_info.get('description', ''),
                "schema": json_content.get('schema', {}),
                "example": json_content.get('example', {})
            }

        return parsed_responses

    def _parse_postman_params(self, query_params: List[Dict]) -> List[Dict]:
        """Parse Postman query parameters"""
        if not query_params:
            return []

        params = []
        for param in query_params:
            params.append({
                "name": param.get('key', ''),
                "in": "query",
                "required": not param.get('disabled', False),
                "type": "string",
                "description": param.get('description', ''),
                "example": param.get('value', '')
            })
        return params

    def _parse_postman_body(self, body: Dict) -> Dict[str, Any]:
        """Parse Postman request body"""
        if not body:
            return {}

        mode = body.get('mode', 'raw')

        if mode == 'raw':
            raw_content = body.get('raw', '')
            try:
                # Try to parse as JSON
                json_data = json.loads(raw_content)
                return {
                    "required": True,
                    "content_type": "application/json",
                    "example": json_data
                }
            except:
                return {
                    "required": True,
                    "content_type": "text/plain",
                    "example": raw_content
                }

        return {}

    def _parse_generic_endpoint(self, endpoint_data: Dict) -> Dict[str, Any]:
        """Parse generic endpoint from YAML"""
        return {
            "path": endpoint_data.get('path', '/'),
            "method": endpoint_data.get('method', 'GET'),
            "operation_id": endpoint_data.get('name', '').replace(' ', '_').lower(),
            "summary": endpoint_data.get('summary', ''),
            "description": endpoint_data.get('description', ''),
            "parameters": endpoint_data.get('parameters', []),
            "test_scenarios": []
        }

    def _generate_test_scenarios(self, path: str, method: str, details: Dict) -> List[Dict]:
        """Generate test scenarios for endpoint"""
        scenarios = []

        # Basic positive scenario
        scenarios.append({
            "name": f"test_{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}_success",
            "type": "positive",
            "description": f"Successful {method} request to {path}",
            "expected_status": self._get_success_status_code(method, details)
        })

        # Negative scenarios based on parameters
        if details.get('parameters'):
            scenarios.append({
                "name": f"test_{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}_invalid_params",
                "type": "negative",
                "description": f"Invalid parameters for {method} {path}",
                "expected_status": 400
            })

        # Authentication scenarios
        if details.get('security'):
            scenarios.append({
                "name": f"test_{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}_unauthorized",
                "type": "negative",
                "description": f"Unauthorized access to {method} {path}",
                "expected_status": 401
            })

        return scenarios

    def _get_success_status_code(self, method: str, details: Dict) -> int:
        """Determine expected success status code"""
        responses = details.get('responses', {})

        # Check for explicit success responses
        for code in ['200', '201', '202', '204']:
            if code in responses:
                return int(code)

        # Default based on method
        if method == 'POST':
            return 201
        elif method == 'DELETE':
            return 204
        else:
            return 200

    def _detect_hardcoded_secrets(self, content: Any, path: str = "") -> List[Dict[str, str]]:
        """Detect and catalog hardcoded secrets in API specification"""
        secrets = []

        # Patterns for detecting secrets
        secret_patterns = {
            'api_key': r'[a-zA-Z0-9]{20,}',  # Long alphanumeric strings
            'jwt_token': r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',  # JWT tokens
            'bearer_token': r'Bearer\s+[a-zA-Z0-9_-]+',  # Bearer tokens
            'basic_auth': r'Basic\s+[a-zA-Z0-9+/=]+',  # Basic auth
            'password': r'password.*["\'][^"\']{6,}["\']'  # Passwords in examples
        }

        def scan_object(obj, current_path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key

                    # Check for auth-related keys with suspicious values
                    if any(auth_key in key.lower() for auth_key in ['auth', 'key', 'token', 'password', 'secret']):
                        if isinstance(value, str) and len(value) > 10:
                            # Check patterns
                            for secret_type, pattern in secret_patterns.items():
                                import re
                                if re.search(pattern, value, re.IGNORECASE):
                                    secrets.append({
                                        'type': secret_type,
                                        'key': key,
                                        'original': value,
                                        'path': new_path,
                                        'replacement': self._generate_replacement_var(key, secret_type)
                                    })
                                    break

                    scan_object(value, new_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    scan_object(item, f"{current_path}[{i}]")

        scan_object(content)
        return secrets

    def _generate_replacement_var(self, original_key: str, secret_type: str) -> str:
        """Generate appropriate replacement variable name"""
        key_upper = original_key.upper().replace('-', '_').replace(' ', '_')

        if secret_type == 'api_key':
            return f"${{{key_upper}_TO_CHANGE}}"
        elif secret_type == 'jwt_token':
            return "${JWT_TOKEN_TO_CHANGE}"
        elif secret_type == 'bearer_token':
            return "${BEARER_TOKEN_TO_CHANGE}"
        elif secret_type == 'basic_auth':
            return "${BASIC_AUTH_TO_CHANGE}"
        elif secret_type == 'password':
            return "${PASSWORD_TO_CHANGE}"
        else:
            return f"${{{key_upper}_SECRET_TO_CHANGE}}"

    def _replace_hardcoded_secrets(self, content: Any, secrets: List[Dict[str, str]]) -> Any:
        """Replace hardcoded secrets with parameterized variables"""
        if not secrets:
            return content

        def replace_in_object(obj):
            if isinstance(obj, dict):
                new_obj = {}
                for key, value in obj.items():
                    # Check if this value should be replaced
                    replacement = None
                    for secret in secrets:
                        if secret['original'] == value:
                            replacement = secret['replacement']
                            break

                    new_obj[key] = replacement if replacement else replace_in_object(value)
                return new_obj

            elif isinstance(obj, list):
                return [replace_in_object(item) for item in obj]
            else:
                return obj

        return replace_in_object(content)

    async def _enhance_with_ai_analysis(self, parsed_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Enhance parsed data with AI analysis and security scanning"""

        # First, detect hardcoded secrets
        security_warnings = self._detect_hardcoded_secrets(parsed_data)

        # Replace hardcoded secrets with parameterized variables
        if security_warnings:
            self.logger.warning(f"Detected {len(security_warnings)} hardcoded secrets, replacing with parameters")
            parsed_data = self._replace_hardcoded_secrets(parsed_data, security_warnings)
            parsed_data['security_warnings'] = security_warnings

        enhancement_prompt = f"""
        Analyze the parsed API specification and enhance it for comprehensive test generation:

        API Information:
        - Title: {parsed_data.get('title', 'Unknown')}
        - Endpoints: {len(parsed_data.get('endpoints', []))}
        - Language: {language}
        - Security Issues: {len(security_warnings)} hardcoded secrets detected and replaced

        For each endpoint, suggest:
        1. Additional test scenarios (edge cases, boundary values)
        2. Realistic test data generation strategies
        3. Data dependencies between endpoints
        4. Performance test considerations
        5. Security test scenarios

        Focus on creating parameterized tests and avoiding hardcoded values.
        Ensure all authentication and sensitive data uses environment variables.

        Respond with JSON:
        {{
            "test_data_strategies": {{"endpoint_path": "strategy_description"}},
            "test_dependencies": [
                {{"prerequisite": "endpoint1", "dependent": "endpoint2", "reason": "needs_id"}}
            ],
            "global_test_config": {{
                "base_url_param": "api.base.url",
                "auth_config": "parameterized authentication configuration",
                "environment_vars": ["API_KEY", "BASE_URL", "AUTH_TOKEN"],
                "security_recommendations": ["Use environment variables", "Rotate API keys regularly"]
            }},
            "enhanced_scenarios": {{
                "endpoint_path": [
                    {{"name": "scenario_name", "type": "positive|negative", "description": "what it tests"}}
                ]
            }}
        }}
        """

        try:
            enhancement = await self.ai_connector.generate_structured_response(
                enhancement_prompt,
                "You are an expert in API testing, security, and test automation best practices."
            )

            # Merge enhancements with parsed data
            parsed_data['ai_enhancements'] = enhancement
            parsed_data['test_strategies'] = enhancement.get('test_data_strategies', {})
            parsed_data['dependencies'] = enhancement.get('test_dependencies', [])
            parsed_data['global_config'] = enhancement.get('global_test_config', {})

            # Enhance individual endpoints with AI scenarios
            enhanced_scenarios = enhancement.get('enhanced_scenarios', {})
            for endpoint in parsed_data.get('endpoints', []):
                endpoint_key = endpoint['path']
                if endpoint_key in enhanced_scenarios:
                    endpoint['test_scenarios'].extend(enhanced_scenarios[endpoint_key])

            return parsed_data

        except Exception as e:
            self.logger.warning(f"AI enhancement failed, using basic parsing: {str(e)}")
            return parsed_data

    async def generate_environment_configs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate environment-specific configuration files with user-provided settings"""

        parsed_data = params.get('parsed_data', {})
        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])
        project_config = params.get('project_config', {})

        self.logger.info(f"Generating environment configurations for: {project_name}")

        # Extract configuration details
        base_url = project_config.get('base_url') or parsed_data.get('base_url', '${api.base.url}')
        auth_type = project_config.get('auth_type', 'none')
        environments = project_config.get('environments', ['dev', 'staging', 'prod'])
        environment_urls = project_config.get('environment_urls', {})
        security_warnings = parsed_data.get('security_warnings', [])

        config_prompt = f"""
        Generate environment-specific configuration files for API testing with user-provided settings:

        Project: {project_name}
        Language: {language}
        Base URL: {base_url}
        Authentication: {auth_type}
        Environments: {environments}
        Security Issues: {len(security_warnings)} secrets replaced with parameters

        Create configuration files for each environment with:
        - Parameterized base URLs (no hardcoding)
        - Environment-specific settings
        - Authentication configuration for {auth_type}
        - Timeout and retry settings
        - Logging configuration
        - Security variables from replaced secrets

        Environment URLs:
        {environment_urls}

        Include all security variables that were replaced:
        {[s['replacement'] for s in security_warnings]}

        Respond with JSON:
        {{
            "config_files": {{
                "environment_name.properties": "file content here"
            }},
            "env_template": ".env template content",
            "security_setup_guide": "Instructions for setting up replaced secrets"
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                config_prompt,
                "Create production-ready configuration files with proper parameterization and security."
            )

            created_files = []

            if language == "java":
                config_dir = output_path / "src/test/resources"
            else:
                config_dir = output_path / "config"

            config_dir.mkdir(parents=True, exist_ok=True)

            # Create environment-specific config files
            if "config_files" in response:
                for filename, content in response["config_files"].items():
                    config_file = config_dir / filename
                    config_file.write_text(content, encoding='utf-8')
                    created_files.append(str(config_file))

            # Create .env template
            if "env_template" in response:
                env_file = output_path / ".env.template"
                env_file.write_text(response["env_template"], encoding='utf-8')
                created_files.append(str(env_file))

            # Create security setup guide
            if "security_setup_guide" in response and security_warnings:
                security_file = output_path / "SECURITY_SETUP.md"
                security_content = response["security_setup_guide"]

                # Add detected secrets info
                security_content += "\n\n## Detected Hardcoded Secrets\n\n"
                security_content += "The following hardcoded secrets were detected and replaced:\n\n"

                for warning in security_warnings:
                    security_content += f"- **{warning['type']}** in `{warning['path']}`: "
                    security_content += f"`{warning['original'][:20]}...` → `{warning['replacement']}`\n"

                security_file.write_text(security_content, encoding='utf-8')
                created_files.append(str(security_file))

            return {
                "operation": "generate_environment_configs",
                "status": "completed",
                "created_files": created_files,
                "security_warnings": security_warnings,
                "message": f"Generated {len(created_files)} configuration files with security enhancements"
            }

        except Exception as e:
            self.logger.error(f"Failed to generate environment configurations: {str(e)}")
            raise

    async def generate_test_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic test data based on API models"""

        parsed_data = params.get('parsed_data', {})
        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])

        self.logger.info(f"Generating test data for: {project_name}")

        models = parsed_data.get('models', {})
        endpoints = parsed_data.get('endpoints', [])

        test_data_prompt = f"""
        Generate realistic test data for API testing based on the data models:

        Models: {list(models.keys()) if models else 'None defined'}
        Endpoints: {len(endpoints)}

        Create test data files with:
        - Valid data sets for positive tests
        - Invalid data sets for negative tests  
        - Boundary value test cases
        - Realistic data that follows business logic
        - Parameterized data sets (no hardcoded IDs)

        Use environment variables for sensitive data.

        Respond with JSON:
        {{
            "test_data_files": {{
                "filename.json": "file content here"
            }}
        }}
        """

        try:
            response = await self.ai_connector.generate_structured_response(
                test_data_prompt,
                "Generate realistic, production-ready test data with proper parameterization."
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
                "operation": "generate_test_data",
                "status": "completed",
                "created_files": created_files,
                "message": f"Generated {len(created_files)} test data files"
            }

        except Exception as e:
            self.logger.error(f"Failed to generate test data: {str(e)}")
            raise

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific parser agent operation"""

        self.logger.info(f"Executing operation: {operation}")

        operation_mapping = {
            "parse_api_specification": self.parse_api_specification,
            "generate_environment_configs": self.generate_environment_configs,
            "generate_test_data": self.generate_test_data,

            # Alternative operation names
            "parse_swagger": self.parse_api_specification,
            "parse_postman": self.parse_api_specification,
            "parse_yaml": self.parse_api_specification,
            "create_test_config": self.generate_environment_configs,
            "create_test_data": self.generate_test_data,
            "generate_test_configuration": self.generate_environment_configs
        }

        if operation in operation_mapping:
            return await operation_mapping[operation](params)
        else:
            # Default to API specification parsing
            self.logger.info(f"Unknown operation '{operation}', defaulting to parse_api_specification")
            return await self.parse_api_specification(params)