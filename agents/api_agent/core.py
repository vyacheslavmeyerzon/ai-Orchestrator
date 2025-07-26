"""
API Agent - Enhanced Version with Auth Support and Correct Parameter Handling
Ensures compatibility between services, tests, and framework components
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import logging
from collections import defaultdict
import re
from dataclasses import dataclass, field
from enum import Enum

from common.ai_connector import AIConnectorFactory
from common.config import get_config
from common.logger import get_agent_logger


class ClassType(Enum):
    """Types of classes in the framework"""
    MODEL = "model"
    SERVICE = "service"
    CLIENT = "client"
    TEST = "test"
    UTIL = "util"
    CONFIG = "config"
    BASE = "base"
    VALIDATOR = "validator"
    EXCEPTION = "exception"
    ANNOTATION = "annotation"
    LISTENER = "listener"
    INTERCEPTOR = "interceptor"


@dataclass
class MethodSignature:
    """Represents a method signature for consistency between services and tests"""
    name: str
    params: List[Tuple[str, str]]  # [(param_name, param_type)]
    return_type: str
    description: str = ""
    http_method: str = ""
    endpoint: str = ""
    requires_auth: bool = False  # NEW: Track if endpoint requires authentication
    path_params: List[str] = field(default_factory=list)  # NEW: Track which params are path params
    query_params: List[str] = field(default_factory=list)  # NEW: Track which params are query params


@dataclass
class JavaClass:
    """Represents a Java class with all its metadata"""
    name: str
    package: str
    type: ClassType
    file_path: str
    imports: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    methods: Dict[str, MethodSignature] = field(default_factory=dict)
    fields: Dict[str, str] = field(default_factory=dict)
    is_interface: bool = False
    is_abstract: bool = False
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)


class ClassRegistry:
    """Registry to track all classes in the project"""

    def __init__(self, base_package: str):
        self.base_package = base_package
        self.classes: Dict[str, JavaClass] = {}
        self.package_structure: Dict[str, List[str]] = defaultdict(list)
        self.service_methods: Dict[str, List[MethodSignature]] = {}  # Track service methods

    def register_class(self, java_class: JavaClass):
        """Register a class in the registry"""
        self.classes[java_class.name] = java_class
        self.package_structure[java_class.package].append(java_class.name)

    def register_service_methods(self, service_name: str, methods: List[MethodSignature]):
        """Register methods for a service to ensure consistency with tests"""
        self.service_methods[service_name] = methods

    def get_service_methods(self, service_name: str) -> List[MethodSignature]:
        """Get registered methods for a service"""
        return self.service_methods.get(service_name, [])

    def get_class(self, class_name: str) -> Optional[JavaClass]:
        """Get class by name"""
        return self.classes.get(class_name)

    def get_full_class_name(self, class_name: str) -> Optional[str]:
        """Get fully qualified class name"""
        java_class = self.get_class(class_name)
        if java_class:
            return f"{java_class.package}.{java_class.name}"
        return None

    def get_import_for_class(self, class_name: str) -> Optional[str]:
        """Get import statement for a class"""
        full_name = self.get_full_class_name(class_name)
        return f"import {full_name};" if full_name else None

    def resolve_imports_for_class(self, java_class: JavaClass) -> Set[str]:
        """Resolve all imports needed for a class based on its dependencies"""
        imports = set()

        for dep_class_name in java_class.dependencies:
            if dep_class_name in self.classes:
                dep_class = self.classes[dep_class_name]
                if dep_class.package != java_class.package:
                    imports.add(f"import {dep_class.package}.{dep_class.name};")

        imports.update(java_class.imports)
        return imports


class TemplateGenerator:
    """Generates code from templates for critical classes"""

    def __init__(self, base_package: str, registry: ClassRegistry):
        self.base_package = base_package
        self.registry = registry

    def generate_pom_xml(self, project_name: str) -> str:
        """Generate production-ready pom.xml with all dependencies"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{self.base_package}</groupId>
    <artifactId>{project_name}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    <name>{project_name} API Test Automation</name>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>

        <!-- Dependency Versions -->
        <restassured.version>5.3.2</restassured.version>
        <testng.version>7.8.0</testng.version>
        <jackson.version>2.15.3</jackson.version>
        <slf4j.version>2.0.9</slf4j.version>
        <logback.version>1.4.11</logback.version>
        <assertj.version>3.24.2</assertj.version>
        <allure.version>2.24.0</allure.version>
        <commons.lang3.version>3.13.0</commons.lang3.version>
        <jsonpath.version>2.8.0</jsonpath.version>
        <javafaker.version>1.0.2</javafaker.version>

        <!-- Plugin Versions -->
        <maven.compiler.version>3.11.0</maven.compiler.version>
        <maven.surefire.version>3.1.2</maven.surefire.version>
    </properties>

    <dependencies>
        <!-- RestAssured -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <version>${{restassured.version}}</version>
        </dependency>

        <!-- TestNG -->
        <dependency>
            <groupId>org.testng</groupId>
            <artifactId>testng</artifactId>
            <version>${{testng.version}}</version>
        </dependency>

        <!-- Jackson -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>${{jackson.version}}</version>
        </dependency>

        <!-- JsonPath -->
        <dependency>
            <groupId>com.jayway.jsonpath</groupId>
            <artifactId>json-path</artifactId>
            <version>${{jsonpath.version}}</version>
        </dependency>

        <!-- JavaFaker for test data -->
        <dependency>
            <groupId>com.github.javafaker</groupId>
            <artifactId>javafaker</artifactId>
            <version>${{javafaker.version}}</version>
        </dependency>

        <!-- Logging -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>${{slf4j.version}}</version>
        </dependency>
        <dependency>
            <groupId>ch.qos.logback</groupId>
            <artifactId>logback-classic</artifactId>
            <version>${{logback.version}}</version>
        </dependency>

        <!-- AssertJ -->
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <version>${{assertj.version}}</version>
        </dependency>

        <!-- Apache Commons -->
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>${{commons.lang3.version}}</version>
        </dependency>

        <!-- Allure -->
        <dependency>
            <groupId>io.qameta.allure</groupId>
            <artifactId>allure-testng</artifactId>
            <version>${{allure.version}}</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>${{maven.compiler.version}}</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>

            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{maven.surefire.version}}</version>
                <configuration>
                    <suiteXmlFiles>
                        <suiteXmlFile>src/test/resources/testng.xml</suiteXmlFile>
                    </suiteXmlFiles>
                    <systemPropertyVariables>
                        <env>${{env}}</env>
                    </systemPropertyVariables>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>"""

    def generate_api_request(self) -> Tuple[str, JavaClass]:
        """Generate ApiRequest model class with all needed methods"""
        package = f"{self.base_package}.models"
        class_name = "ApiRequest"

        java_class = JavaClass(
            name=class_name,
            package=package,
            type=ClassType.MODEL,
            file_path=f"src/main/java/{package.replace('.', '/')}/{class_name}.java",
            imports={
                "import java.util.HashMap;",
                "import java.util.Map;",
                "import com.fasterxml.jackson.annotation.JsonIgnoreProperties;",
                "import com.fasterxml.jackson.annotation.JsonInclude;"
            }
        )

        content = f"""package {package};

import java.util.HashMap;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * Model class for API requests with builder pattern
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiRequest {{
    private String method;
    private String endpoint;
    private Map<String, String> headers;
    private Map<String, String> queryParams;
    private Map<String, String> pathParams;
    private Map<String, String> formParams;
    private Object body;
    private String contentType;
    private String authType;
    private String authToken;

    private ApiRequest() {{
        this.headers = new HashMap<>();
        this.queryParams = new HashMap<>();
        this.pathParams = new HashMap<>();
        this.formParams = new HashMap<>();
        this.contentType = "application/json";
    }}

    public static Builder builder() {{
        return new Builder();
    }}

    // Getters
    public String getMethod() {{ return method; }}
    public String getEndpoint() {{ return endpoint; }}
    public Map<String, String> getHeaders() {{ return headers; }}
    public Map<String, String> getQueryParams() {{ return queryParams; }}
    public Map<String, String> getPathParams() {{ return pathParams; }}
    public Map<String, String> getFormParams() {{ return formParams; }}
    public Object getBody() {{ return body; }}
    public String getContentType() {{ return contentType; }}
    public String getAuthType() {{ return authType; }}
    public String getAuthToken() {{ return authToken; }}

    public static class Builder {{
        private final ApiRequest request;

        private Builder() {{
            request = new ApiRequest();
        }}

        public Builder method(String method) {{
            request.method = method;
            return this;
        }}

        public Builder get() {{
            return method("GET");
        }}

        public Builder post() {{
            return method("POST");
        }}

        public Builder put() {{
            return method("PUT");
        }}

        public Builder delete() {{
            return method("DELETE");
        }}

        public Builder patch() {{
            return method("PATCH");
        }}

        public Builder endpoint(String endpoint) {{
            request.endpoint = endpoint;
            return this;
        }}

        public Builder header(String key, String value) {{
            request.headers.put(key, value);
            return this;
        }}

        public Builder headers(Map<String, String> headers) {{
            request.headers.putAll(headers);
            return this;
        }}

        public Builder queryParam(String key, String value) {{
            if (value != null && !value.isEmpty()) {{
                request.queryParams.put(key, value);
            }}
            return this;
        }}

        public Builder queryParams(Map<String, String> params) {{
            params.forEach((k, v) -> queryParam(k, v));
            return this;
        }}

        public Builder pathParam(String key, String value) {{
            request.pathParams.put(key, value);
            return this;
        }}

        public Builder formParam(String key, String value) {{
            request.formParams.put(key, value);
            request.contentType = "application/x-www-form-urlencoded";
            return this;
        }}

        public Builder body(Object body) {{
            request.body = body;
            return this;
        }}

        public Builder contentType(String contentType) {{
            request.contentType = contentType;
            return this;
        }}

        public Builder auth(String type, String token) {{
            request.authType = type;
            request.authToken = token;
            return this;
        }}

        public ApiRequest build() {{
            if (request.endpoint == null) {{
                throw new IllegalStateException("Endpoint is required");
            }}
            if (request.method == null) {{
                request.method = "GET"; // Default to GET
            }}
            return request;
        }}
    }}
}}"""

        self.registry.register_class(java_class)
        return content, java_class

    def generate_rest_assured_client(self) -> Tuple[str, JavaClass]:
        """Generate RestAssuredClient class with correct method signatures"""
        package = f"{self.base_package}.client"
        class_name = "RestAssuredClient"

        java_class = JavaClass(
            name=class_name,
            package=package,
            type=ClassType.CLIENT,
            file_path=f"src/main/java/{package.replace('.', '/')}/{class_name}.java",
            dependencies={"ApiRequest", "ApiResponse", "ConfigManager"},
            imports={
                "import io.restassured.RestAssured;",
                "import io.restassured.response.Response;",
                "import io.restassured.specification.RequestSpecification;",
                "import org.slf4j.Logger;",
                "import org.slf4j.LoggerFactory;",
                "import java.util.Map;"
            }
        )

        imports = self.registry.resolve_imports_for_class(java_class)
        imports.update(java_class.imports)
        imports_str = '\n'.join(sorted(imports))

        content = f"""package {package};

{imports_str}

/**
 * RestAssured client for API interactions
 */
public class RestAssuredClient {{
    private static final Logger logger = LoggerFactory.getLogger(RestAssuredClient.class);
    private final ConfigManager config;

    public RestAssuredClient() {{
        this.config = ConfigManager.getInstance();
        setupRestAssured();
    }}

    private void setupRestAssured() {{
        RestAssured.baseURI = config.getBaseUrl();
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails();

        if (config.isLoggingEnabled()) {{
            RestAssured.filters(new io.restassured.filter.log.RequestLoggingFilter(),
                               new io.restassured.filter.log.ResponseLoggingFilter());
        }}
    }}

    // Generic execute method for any HTTP method
    public ApiResponse execute(ApiRequest apiRequest) {{
        String method = apiRequest.getMethod().toUpperCase();
        logger.info("Executing {{}} request to {{}}", method, apiRequest.getEndpoint());

        Response response;
        String endpoint = resolveEndpoint(apiRequest);
        RequestSpecification spec = buildRequest(apiRequest);

        switch (method) {{
            case "GET":
                response = spec.get(endpoint);
                break;
            case "POST":
                response = spec.post(endpoint);
                break;
            case "PUT":
                response = spec.put(endpoint);
                break;
            case "DELETE":
                response = spec.delete(endpoint);
                break;
            case "PATCH":
                response = spec.patch(endpoint);
                break;
            default:
                throw new IllegalArgumentException("Unsupported HTTP method: " + method);
        }}

        return new ApiResponse(response);
    }}

    // Build request with all parameters
    private RequestSpecification buildRequest(ApiRequest apiRequest) {{
        RequestSpecification spec = RestAssured.given()
            .contentType(apiRequest.getContentType())
            .accept("application/json");

        // Add headers
        if (!apiRequest.getHeaders().isEmpty()) {{
            spec.headers(apiRequest.getHeaders());
        }}

        // Add query parameters
        if (!apiRequest.getQueryParams().isEmpty()) {{
            spec.queryParams(apiRequest.getQueryParams());
        }}

        // Add path parameters
        if (!apiRequest.getPathParams().isEmpty()) {{
            spec.pathParams(apiRequest.getPathParams());
        }}

        // Add form parameters
        if (!apiRequest.getFormParams().isEmpty()) {{
            spec.formParams(apiRequest.getFormParams());
        }}

        // Add body
        if (apiRequest.getBody() != null) {{
            spec.body(apiRequest.getBody());
        }}

        // Add authentication
        if (apiRequest.getAuthType() != null && apiRequest.getAuthToken() != null) {{
            switch (apiRequest.getAuthType().toLowerCase()) {{
                case "bearer":
                    spec.header("Authorization", "Bearer " + apiRequest.getAuthToken());
                    break;
                case "api-key":
                    spec.header("X-API-Key", apiRequest.getAuthToken());
                    break;
                case "basic":
                    String[] credentials = apiRequest.getAuthToken().split(":");
                    if (credentials.length == 2) {{
                        spec.auth().preemptive().basic(credentials[0], credentials[1]);
                    }}
                    break;
            }}
        }}

        return spec;
    }}

    // Resolve endpoint with path parameters
    private String resolveEndpoint(ApiRequest apiRequest) {{
        String endpoint = apiRequest.getEndpoint();

        // Replace path parameters in the endpoint
        for (Map.Entry<String, String> entry : apiRequest.getPathParams().entrySet()) {{
            endpoint = endpoint.replace("{{" + entry.getKey() + "}}", entry.getValue());
        }}

        return endpoint;
    }}
}}"""

        self.registry.register_class(java_class)
        return content, java_class

    def generate_response_validator(self) -> Tuple[str, JavaClass]:
        """Generate ResponseValidator with correct ApiResponse methods"""
        package = f"{self.base_package}.validators"
        class_name = "ResponseValidator"

        java_class = JavaClass(
            name=class_name,
            package=package,
            type=ClassType.VALIDATOR,
            file_path=f"src/main/java/{package.replace('.', '/')}/{class_name}.java",
            dependencies={"ApiResponse"},
            imports={
                "import com.jayway.jsonpath.JsonPath;",
                "import org.assertj.core.api.Assertions;",
                "import java.util.List;",
                "import java.util.Map;"
            }
        )

        imports = self.registry.resolve_imports_for_class(java_class)
        imports.update(java_class.imports)
        imports_str = '\n'.join(sorted(imports))

        content = f"""package {package};

{imports_str}

/**
 * Validator class for API responses
 */
public class ResponseValidator {{

    public static void validateStatusCode(ApiResponse response, int expectedStatusCode) {{
        Assertions.assertThat(response.getStatusCode())
                .as("Status code validation failed")
                .isEqualTo(expectedStatusCode);
    }}

    public static void validateStatusCodeRange(ApiResponse response, int minStatusCode, int maxStatusCode) {{
        Assertions.assertThat(response.getStatusCode())
                .as("Status code range validation failed")
                .isBetween(minStatusCode, maxStatusCode);
    }}

    public static void validateResponseTime(ApiResponse response, long maxResponseTimeMs) {{
        Assertions.assertThat(response.getResponseTime())
                .as("Response time validation failed")
                .isLessThanOrEqualTo(maxResponseTimeMs);
    }}

    public static void validateJsonPathExists(ApiResponse response, String jsonPath) {{
        try {{
            Object value = JsonPath.read(response.getBodyAsString(), jsonPath);
            Assertions.assertThat(value)
                    .as("JSON path '%s' should exist", jsonPath)
                    .isNotNull();
        }} catch (Exception e) {{
            Assertions.fail("JSON path '%s' does not exist in response", jsonPath);
        }}
    }}

    public static void validateJsonPathValue(ApiResponse response, String jsonPath, Object expectedValue) {{
        try {{
            Object actualValue = JsonPath.read(response.getBodyAsString(), jsonPath);
            Assertions.assertThat(actualValue)
                    .as("JSON path '%s' value validation failed", jsonPath)
                    .isEqualTo(expectedValue);
        }} catch (Exception e) {{
            Assertions.fail("Failed to validate JSON path '%s': %s", jsonPath, e.getMessage());
        }}
    }}

    public static void validateJsonPathArraySize(ApiResponse response, String jsonPath, int expectedSize) {{
        try {{
            List<Object> array = JsonPath.read(response.getBodyAsString(), jsonPath);
            Assertions.assertThat(array)
                    .as("JSON path '%s' array size validation failed", jsonPath)
                    .hasSize(expectedSize);
        }} catch (Exception e) {{
            Assertions.fail("Failed to validate JSON path '%s' array size: %s", jsonPath, e.getMessage());
        }}
    }}

    public static void validateContentType(ApiResponse response, String expectedContentType) {{
        String contentType = response.getHeader("Content-Type");
        if (contentType == null) {{
            contentType = response.getHeader("content-type");
        }}
        Assertions.assertThat(contentType)
                .as("Content-Type header validation failed")
                .contains(expectedContentType);
    }}

    public static void validateHeaderExists(ApiResponse response, String headerName) {{
        Map<String, String> headers = response.getAllHeaders();
        Assertions.assertThat(headers)
                .as("Header '%s' should exist", headerName)
                .containsKey(headerName);
    }}

    public static void validateHeaderValue(ApiResponse response, String headerName, String expectedValue) {{
        String actualValue = response.getHeader(headerName);
        Assertions.assertThat(actualValue)
                .as("Header '%s' value validation failed", headerName)
                .isEqualTo(expectedValue);
    }}

    public static void validateSuccessResponse(ApiResponse response) {{
        validateStatusCodeRange(response, 200, 299);
    }}

    public static void validateErrorResponse(ApiResponse response) {{
        validateStatusCodeRange(response, 400, 599);
    }}
}}"""

        self.registry.register_class(java_class)
        return content, java_class

    def generate_config_manager(self) -> Tuple[str, JavaClass]:
        """Generate ConfigManager class"""
        package = f"{self.base_package}.utils"
        class_name = "ConfigManager"

        java_class = JavaClass(
            name=class_name,
            package=package,
            type=ClassType.UTIL,
            file_path=f"src/main/java/{package.replace('.', '/')}/{class_name}.java",
            imports={
                "import java.io.IOException;",
                "import java.io.InputStream;",
                "import java.util.Properties;",
                "import org.slf4j.Logger;",
                "import org.slf4j.LoggerFactory;"
            }
        )

        content = f"""package {package};

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Configuration manager for loading and accessing properties
 */
public class ConfigManager {{
    private static final Logger logger = LoggerFactory.getLogger(ConfigManager.class);
    private static ConfigManager instance;
    private final Properties properties;

    private ConfigManager() {{
        properties = new Properties();
        loadProperties();
    }}

    public static ConfigManager getInstance() {{
        if (instance == null) {{
            synchronized (ConfigManager.class) {{
                if (instance == null) {{
                    instance = new ConfigManager();
                }}
            }}
        }}
        return instance;
    }}

    private void loadProperties() {{
        String env = System.getProperty("env", "dev");
        String fileName = String.format("config/%s.properties", env);

        try (InputStream input = getClass().getClassLoader().getResourceAsStream(fileName)) {{
            if (input == null) {{
                logger.error("Unable to find {{}}", fileName);
                return;
            }}
            properties.load(input);
            logger.info("Loaded configuration from {{}}", fileName);
        }} catch (IOException e) {{
            logger.error("Error loading configuration", e);
        }}
    }}

    public String getProperty(String key) {{
        return properties.getProperty(key);
    }}

    public String getProperty(String key, String defaultValue) {{
        return properties.getProperty(key, defaultValue);
    }}

    public int getIntProperty(String key, int defaultValue) {{
        String value = properties.getProperty(key);
        if (value != null) {{
            try {{
                return Integer.parseInt(value);
            }} catch (NumberFormatException e) {{
                logger.warn("Invalid integer value for key {{}}: {{}}", key, value);
            }}
        }}
        return defaultValue;
    }}

    public boolean getBooleanProperty(String key, boolean defaultValue) {{
        String value = properties.getProperty(key);
        return value != null ? Boolean.parseBoolean(value) : defaultValue;
    }}

    // Convenience methods
    public String getBaseUrl() {{
        return getProperty("api.base.url", "http://localhost:8080");
    }}

    public int getTimeout() {{
        return getIntProperty("api.timeout", 30000);
    }}

    public boolean isLoggingEnabled() {{
        return getBooleanProperty("logging.enabled", true);
    }}

    public String getApiKey() {{
        return getProperty("auth.api.key", "");
    }}

    public int getRetryCount() {{
        return getIntProperty("retry.max.attempts", 3);
    }}

    public int getRetryDelay() {{
        return getIntProperty("retry.delay.seconds", 1);
    }}
}}"""

        self.registry.register_class(java_class)
        return content, java_class

    def generate_api_response(self) -> Tuple[str, JavaClass]:
        """Generate ApiResponse model class"""
        package = f"{self.base_package}.models"
        class_name = "ApiResponse"

        java_class = JavaClass(
            name=class_name,
            package=package,
            type=ClassType.MODEL,
            file_path=f"src/main/java/{package.replace('.', '/')}/{class_name}.java",
            imports={
                "import io.restassured.response.Response;",
                "import java.util.Map;",
                "import java.util.List;",
                "import java.util.stream.Collectors;"
            }
        )

        content = f"""package {package};

import io.restassured.response.Response;
import java.util.Map;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Wrapper for RestAssured Response with convenience methods
 */
public class ApiResponse {{
    private final Response response;
    private final long responseTime;

    public ApiResponse(Response response) {{
        this.response = response;
        this.responseTime = response.getTime();
    }}

    // Status methods
    public int getStatusCode() {{
        return response.getStatusCode();
    }}

    public boolean isSuccessful() {{
        int code = getStatusCode();
        return code >= 200 && code < 300;
    }}

    // Body methods
    public String getBodyAsString() {{
        return response.getBody().asString();
    }}

    public <T> T getBodyAs(Class<T> cls) {{
        return response.getBody().as(cls);
    }}

    public <T> T extractPath(String path) {{
        return response.jsonPath().get(path);
    }}

    // Header methods
    public String getHeader(String name) {{
        return response.getHeader(name);
    }}

    public Map<String, String> getAllHeaders() {{
        return response.getHeaders().asList().stream()
            .collect(Collectors.toMap(
                header -> header.getName(),
                header -> header.getValue(),
                (v1, v2) -> v1
            ));
    }}

    // Response time
    public long getResponseTime() {{
        return responseTime;
    }}

    // Get raw response
    public Response getRawResponse() {{
        return response;
    }}

    // Validation helpers
    public ApiResponse assertStatusCode(int expectedCode) {{
        if (getStatusCode() != expectedCode) {{
            throw new AssertionError(String.format(
                "Expected status code %d but got %d. Response: %s",
                expectedCode, getStatusCode(), getBodyAsString()
            ));
        }}
        return this;
    }}

    public ApiResponse assertSuccessful() {{
        if (!isSuccessful()) {{
            throw new AssertionError(String.format(
                "Expected successful response but got %d. Response: %s",
                getStatusCode(), getBodyAsString()
            ));
        }}
        return this;
    }}
}}"""

        self.registry.register_class(java_class)
        return content, java_class

    def generate_base_test(self) -> Tuple[str, JavaClass]:
        """Generate BaseTest class"""
        package = f"{self.base_package}.base"
        class_name = "BaseTest"

        java_class = JavaClass(
            name=class_name,
            package=package,
            type=ClassType.BASE,
            file_path=f"src/test/java/{package.replace('.', '/')}/{class_name}.java",
            dependencies={"RestAssuredClient", "ConfigManager"},
            imports={
                "import org.testng.annotations.BeforeClass;",
                "import org.testng.annotations.AfterClass;",
                "import org.slf4j.Logger;",
                "import org.slf4j.LoggerFactory;"
            },
            is_abstract=True
        )

        imports = self.registry.resolve_imports_for_class(java_class)
        imports.update(java_class.imports)
        imports_str = '\n'.join(sorted(imports))

        content = f"""package {package};

{imports_str}

/**
 * Base test class for all tests
 */
public abstract class BaseTest {{
    protected static final Logger logger = LoggerFactory.getLogger(BaseTest.class);
    protected RestAssuredClient client;
    protected ConfigManager config;

    @BeforeClass
    public void setupBase() {{
        logger.info("Setting up test base");
        config = ConfigManager.getInstance();
        client = new RestAssuredClient();

        // Any additional setup
        performAdditionalSetup();
    }}

    @AfterClass
    public void tearDownBase() {{
        logger.info("Tearing down test base");
        performAdditionalTearDown();
    }}

    /**
     * Override this method in subclasses for additional setup
     */
    protected void performAdditionalSetup() {{
        // Default implementation does nothing
    }}

    /**
     * Override this method in subclasses for additional teardown
     */
    protected void performAdditionalTearDown() {{
        // Default implementation does nothing
    }}
}}"""

        self.registry.register_class(java_class)
        return content, java_class


class ServiceTestGenerator:
    """Generates services and tests with consistent method signatures"""

    def __init__(self, base_package: str, registry: ClassRegistry):
        self.base_package = base_package
        self.registry = registry

    def analyze_endpoints(self, endpoints: List[Dict[str, Any]]) -> Dict[str, List[MethodSignature]]:
        """Analyze endpoints and create method signatures for each service"""
        service_methods = defaultdict(list)

        for endpoint in endpoints:
            path = endpoint.get('path', '')
            method = endpoint.get('method', 'GET').upper()
            operation_id = endpoint.get('operationId', '')
            summary = endpoint.get('summary', '')
            parameters = endpoint.get('parameters', [])
            request_body = endpoint.get('requestBody', {})
            security = endpoint.get('security', [])  # NEW: Check security requirements

            # Determine if endpoint requires authentication
            requires_auth = bool(security)

            # Determine service name from tags or path
            tags = endpoint.get('tags', [])
            service_name = tags[0] if tags else path.split('/')[1] if '/' in path else 'api'
            service_name = f"{service_name.capitalize()}Service"

            # Create method name
            if operation_id:
                method_name = self._camel_case(operation_id)
            else:
                method_name = self._generate_method_name(method, path)

            # Check for duplicate method names in the same service
            existing_methods = [m.name for m in service_methods[service_name]]
            if method_name in existing_methods:
                # Make method name unique by adding path info
                path_suffix = self._extract_path_suffix(path)
                method_name = f"{method_name}{path_suffix}"

            # Parse parameters and track their types
            params = []
            path_params = []
            query_params = []
            param_names = set()  # Track parameter names to avoid duplicates

            for param in parameters:
                param_name = self._camel_case(param.get('name', ''))
                param_in = param.get('in', 'query')  # NEW: Check parameter location

                if param_name and param_name not in param_names:
                    param_type = self._get_java_type(param.get('type', param.get('schema', {}).get('type', 'string')))
                    params.append((param_name, param_type))
                    param_names.add(param_name)

                    # Track parameter location
                    if param_in == 'path':
                        path_params.append(param_name)
                    elif param_in == 'query':
                        query_params.append(param_name)

            # Add body parameter for POST/PUT/PATCH only if not already present
            if method in ['POST', 'PUT', 'PATCH'] and request_body and 'body' not in param_names:
                # Determine body type from request body schema
                body_type = 'String'  # Default to String for JSON body
                if 'content' in request_body:
                    for content_type, content_spec in request_body['content'].items():
                        if 'schema' in content_spec:
                            schema = content_spec['schema']
                            if schema.get('type') == 'array':
                                body_type = 'List<Object>'
                            elif '$ref' in schema:
                                # Reference to a model
                                body_type = 'String'  # We'll pass JSON string

                params.append(('body', body_type))

            # Create method signature
            method_sig = MethodSignature(
                name=method_name,
                params=params,
                return_type='ApiResponse',
                description=summary,
                http_method=method,
                endpoint=path,
                requires_auth=requires_auth,  # NEW: Store auth requirement
                path_params=path_params,  # NEW: Store path parameter names
                query_params=query_params  # NEW: Store query parameter names
            )

            service_methods[service_name].append(method_sig)

        return dict(service_methods)

    def generate_service(self, service_name: str, methods: List[MethodSignature]) -> str:
        """Generate service class with given methods"""
        package = f"{self.base_package}.services"

        # Register methods for this service
        self.registry.register_service_methods(service_name, methods)

        # Determine if we need List import
        needs_list = any('List' in str(param[1]) for method in methods for param in method.params)

        # Generate imports
        imports = [
            f"import {self.base_package}.client.RestAssuredClient;",
            f"import {self.base_package}.models.ApiRequest;",
            f"import {self.base_package}.models.ApiResponse;"
        ]

        if needs_list:
            imports.append("import java.util.List;")

        # Generate methods
        method_implementations = []

        for method in methods:
            # Generate base method
            base_method = self._generate_service_method(method, False)
            method_implementations.append(base_method)

            # Generate auth variant if endpoint requires authentication
            if method.requires_auth:
                auth_method = self._generate_service_method(method, True)
                method_implementations.append(auth_method)

        # Generate class
        content = f"""package {package};

{chr(10).join(imports)}

/**
 * Service class for {service_name.replace('Service', '')} API operations
 */
public class {service_name} {{

    private final RestAssuredClient client;

    public {service_name}(RestAssuredClient client) {{
        this.client = client;
    }}
    {chr(10).join(method_implementations)}
}}"""

        # Register class
        java_class = JavaClass(
            name=service_name,
            package=package,
            type=ClassType.SERVICE,
            file_path=f"src/main/java/{package.replace('.', '/')}/{service_name}.java",
            dependencies={"RestAssuredClient", "ApiRequest", "ApiResponse"}
        )
        self.registry.register_class(java_class)

        return content

    def _generate_service_method(self, method: MethodSignature, with_auth: bool) -> str:
        """Generate a service method implementation"""
        # Prepare method name and parameters
        method_name = method.name
        params = list(method.params)

        if with_auth:
            method_name = f"{method_name}WithAuth"
            params.append(('token', 'String'))

        params_str = ', '.join([f"{ptype} {pname}" for pname, ptype in params])

        # Build the endpoint with path parameters replaced
        endpoint = method.endpoint
        for path_param in method.path_params:
            endpoint = endpoint.replace(f"{{{path_param}}}", f"\" + {path_param} + \"")

        # Build request
        request_builder = ["        ApiRequest request = ApiRequest.builder()"]
        request_builder.append(f"            .{method.http_method.lower()}()")
        request_builder.append(f"            .endpoint(\"{endpoint}\")")

        # Add query parameters
        for param_name, param_type in method.params:
            if param_name in method.query_params:
                request_builder.append(f"            .queryParam(\"{param_name}\", String.valueOf({param_name}))")
            elif param_name == 'body':
                request_builder.append(f"            .body({param_name})")

        # Add authentication if this is the auth variant
        if with_auth:
            request_builder.append(f"            .auth(\"bearer\", token)")

        request_builder.append("            .build();")

        # Generate method documentation
        doc_lines = [f"    /**"]
        doc_lines.append(f"     * {method.description}")
        if with_auth:
            doc_lines.append(f"     * @param token Authentication token")
        doc_lines.append(f"     * @return ApiResponse")
        doc_lines.append(f"     */")

        method_impl = f"""
{chr(10).join(doc_lines)}
    public ApiResponse {method_name}({params_str}) {{
{chr(10).join(request_builder)}

        return client.execute(request);
    }}"""

        return method_impl

    def generate_test(self, service_name: str) -> str:
        """Generate test class for a service"""
        test_name = service_name.replace("Service", "ApiTest")
        package = f"{self.base_package}.tests"

        # Get methods for this service
        methods = self.registry.get_service_methods(service_name)

        # Collect all required imports by analyzing all test methods
        all_required_imports = set()

        # Pre-analyze all methods to collect imports
        for method in methods:
            for valid in [True, False]:
                _, imports = self._generate_test_data(method.params, valid)
                all_required_imports.update(imports)

        # Generate imports
        imports = [
            f"import {self.base_package}.base.BaseTest;",
            f"import {self.base_package}.services.{service_name};",
            f"import {self.base_package}.models.ApiResponse;",
            "import org.testng.annotations.BeforeClass;",
            "import org.testng.annotations.Test;",
            "import static org.assertj.core.api.Assertions.assertThat;"
        ]

        # Add collection imports in correct order
        if "java.util.List" in all_required_imports:
            imports.append("import java.util.List;")
        if "java.util.ArrayList" in all_required_imports:
            imports.append("import java.util.ArrayList;")
        if "java.util.Map" in all_required_imports:
            imports.append("import java.util.Map;")
        if "java.util.HashMap" in all_required_imports:
            imports.append("import java.util.HashMap;")

        # Generate test methods
        test_methods = []
        priority = 1
        test_name_counter = {}  # Track duplicate test names

        for method in methods:
            # Generate base test name
            base_test_name = method.name.capitalize()

            # Handle duplicate method names by adding suffix
            if base_test_name in test_name_counter:
                test_name_counter[base_test_name] += 1
                # Add parameter info to make it unique
                param_suffix = self._generate_param_suffix(method.params)
                base_test_name = f"{base_test_name}{param_suffix}"
            else:
                test_name_counter[base_test_name] = 1

            # Generate positive test
            test_name_positive = f"test{base_test_name}Success"
            test_positive = self._generate_test_method(
                method, service_name, test_name_positive, priority, True, False
            )
            test_methods.append(test_positive)
            priority += 1

            # Generate negative test
            test_name_negative = f"test{base_test_name}WithInvalidData"
            test_negative = self._generate_test_method(
                method, service_name, test_name_negative, priority, False, False
            )
            test_methods.append(test_negative)
            priority += 1

            # If method requires auth, generate auth tests
            if method.requires_auth:
                # Test with valid token
                test_name_auth = f"test{base_test_name}WithValidAuth"
                test_auth = self._generate_test_method(
                    method, service_name, test_name_auth, priority, True, True
                )
                test_methods.append(test_auth)
                priority += 1

                # Test without token (401 expected)
                test_name_unauth = f"test{base_test_name}WithoutAuth"
                test_unauth = self._generate_unauthorized_test(
                    method, service_name, test_name_unauth, priority
                )
                test_methods.append(test_unauth)
                priority += 1

        # Generate class
        content = f"""package {package};

{chr(10).join(imports)}

/**
 * Test class for {service_name}
 */
public class {test_name} extends BaseTest {{

    private {service_name} {self._camel_case(service_name)};
    private String validAuthToken = "test-auth-token-123"; // TODO: Get from auth service

    @BeforeClass
    public void setUp() {{
        super.setupBase();
        {self._camel_case(service_name)} = new {service_name}(client);
    }}
    {chr(10).join(test_methods)}
}}"""

        # Register class
        java_class = JavaClass(
            name=test_name,
            package=package,
            type=ClassType.TEST,
            file_path=f"src/test/java/{package.replace('.', '/')}/{test_name}.java",
            dependencies={"BaseTest", service_name, "ApiResponse"},
            extends="BaseTest"
        )
        self.registry.register_class(java_class)

        return content

    def _generate_test_method(self, method: MethodSignature, service_name: str,
                              test_name: str, priority: int, valid: bool, with_auth: bool) -> str:
        """Generate a test method"""
        # Generate test data
        test_data_code, _ = self._generate_test_data(method.params, valid)

        # Build method call parameters
        params = self._generate_test_params(method.params, valid)
        if with_auth and method.requires_auth:
            params.append('validAuthToken')
        params_str = ', '.join(params)

        # Determine expected status code
        if not valid:
            expected_status = "assertThat(response.getStatusCode()).isGreaterThanOrEqualTo(400);"
            success_check = "assertThat(response.isSuccessful()).isFalse();"
        else:
            expected_status = "assertThat(response.getStatusCode()).isIn(200, 201, 204);"
            success_check = "assertThat(response.isSuccessful()).isTrue();"

        # Determine which method to call
        method_to_call = method.name
        if with_auth and method.requires_auth:
            method_to_call = f"{method.name}WithAuth"

        return f"""
    @Test(priority = {priority})
    public void {test_name}() {{
        // Arrange
{test_data_code}

        // Act
        ApiResponse response = {self._camel_case(service_name)}.{method_to_call}({params_str});

        // Assert
        {expected_status}
        {success_check}
    }}"""

    def _generate_unauthorized_test(self, method: MethodSignature, service_name: str,
                                    test_name: str, priority: int) -> str:
        """Generate a test for unauthorized access"""
        # Generate valid test data
        test_data_code, _ = self._generate_test_data(method.params, True)

        # Build method call parameters (without auth token)
        params = self._generate_test_params(method.params, True)
        params_str = ', '.join(params)

        return f"""
    @Test(priority = {priority})
    public void {test_name}() {{
        // Arrange
{test_data_code}

        // Act - Call without authentication
        ApiResponse response = {self._camel_case(service_name)}.{method.name}({params_str});

        // Assert - Should return 401 Unauthorized
        assertThat(response.getStatusCode()).isEqualTo(401);
        assertThat(response.isSuccessful()).isFalse();
    }}"""

    def _extract_path_suffix(self, path: str) -> str:
        """Extract suffix from path to make method names unique"""
        # Remove leading/trailing slashes and parameters
        clean_path = re.sub(r'\{[^}]+\}', '', path).strip('/')
        parts = clean_path.split('/')

        # Use last meaningful part of path
        if len(parts) > 1:
            suffix = parts[-1].capitalize()
            if suffix:
                return f"By{suffix}"

        return ""

    def _camel_case(self, text: str) -> str:
        """Convert to camelCase"""
        if not text:
            return text
        parts = re.split(r'[-_\s]', text)
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

    def _generate_method_name(self, http_method: str, path: str) -> str:
        """Generate method name from HTTP method and path"""
        # Remove parameters from path
        clean_path = re.sub(r'\{[^}]+\}', '', path)
        parts = clean_path.strip('/').split('/')

        # Create method name
        if http_method == 'GET':
            if '{' in path:
                return f"get{parts[-1].capitalize()}ById"
            else:
                return f"getAll{parts[-1].capitalize()}"
        elif http_method == 'POST':
            return f"create{parts[-1].capitalize()}"
        elif http_method == 'PUT':
            return f"update{parts[-1].capitalize()}"
        elif http_method == 'DELETE':
            return f"delete{parts[-1].capitalize()}"
        else:
            return f"{http_method.lower()}{parts[-1].capitalize()}"

    def _get_java_type(self, swagger_type: str) -> str:
        """Convert Swagger type to Java type"""
        type_mapping = {
            'integer': 'Integer',
            'number': 'Double',
            'string': 'String',
            'boolean': 'Boolean',
            'array': 'List<Object>',
            'object': 'Object'
        }

        # Handle array types with items
        if swagger_type == 'array':
            return 'List<Object>'

        return type_mapping.get(swagger_type, 'String')

    def _generate_test_params(self, params: List[Tuple[str, str]], valid: bool) -> List[str]:
        """Generate parameter names for test method call"""
        param_names = []
        for param_name, param_type in params:
            if param_name == 'body':
                param_names.append('requestBody')
            else:
                param_names.append(param_name)
        return param_names

    def _generate_param_suffix(self, params: List[Tuple[str, str]]) -> str:
        """Generate suffix based on parameters to make method names unique"""
        if not params:
            return "NoParams"

        # Use parameter names to create suffix
        param_names = []
        for param_name, param_type in params:
            if param_name != 'body':  # Skip generic body parameter
                # Capitalize first letter of each parameter
                param_names.append(param_name.capitalize())

        if param_names:
            return "With" + "And".join(param_names[:2])  # Use first 2 params max
        else:
            return "WithBody"

    def _generate_test_data(self, params: List[Tuple[str, str]], valid: bool) -> Tuple[str, Set[str]]:
        """Generate test data setup code and return required imports"""
        data_lines = []
        required_imports = set()

        for param_name, param_type in params:
            if param_name == 'body':
                if 'List' in param_type:
                    # Generate List data
                    required_imports.add("java.util.List")
                    required_imports.add("java.util.ArrayList")
                    required_imports.add("java.util.Map")
                    required_imports.add("java.util.HashMap")

                    if valid:
                        data_lines.append('        List<Object> requestBody = new ArrayList<>();')
                        data_lines.append('        Map<String, Object> item = new HashMap<>();')
                        data_lines.append('        item.put("name", "Test Item");')
                        data_lines.append('        item.put("status", "active");')
                        data_lines.append('        requestBody.add(item);')
                    else:
                        data_lines.append('        List<Object> requestBody = new ArrayList<>(); // Empty list')
                elif 'Map' in param_type:
                    # Generate Map data
                    required_imports.add("java.util.Map")
                    required_imports.add("java.util.HashMap")

                    if valid:
                        data_lines.append('        Map<String, Object> requestBody = new HashMap<>();')
                        data_lines.append('        requestBody.put("name", "Test");')
                        data_lines.append('        requestBody.put("status", "active");')
                    else:
                        data_lines.append('        Map<String, Object> requestBody = new HashMap<>(); // Empty map')
                else:
                    # Default Object/String body
                    if valid:
                        data_lines.append(
                            '        String requestBody = "{\\"name\\": \\"Test\\", \\"status\\": \\"active\\"}";')
                    else:
                        data_lines.append('        String requestBody = "{}"; // Invalid empty body')
            elif param_type == 'String':
                if valid:
                    data_lines.append(f'        String {param_name} = "test-{param_name}";')
                else:
                    data_lines.append(f'        String {param_name} = ""; // Invalid empty string')
            elif param_type == 'Integer':
                if valid:
                    data_lines.append(f'        Integer {param_name} = 123;')
                else:
                    data_lines.append(f'        Integer {param_name} = -1; // Invalid negative number')
            elif param_type == 'Boolean':
                data_lines.append(f'        Boolean {param_name} = {str(valid).lower()};')
            elif 'List' in param_type:
                # Non-body list parameter
                required_imports.add("java.util.List")
                required_imports.add("java.util.ArrayList")

                element_type = param_type.replace('List<', '').replace('>', '')
                if valid:
                    data_lines.append(f'        List<{element_type}> {param_name} = new ArrayList<>();')
                    data_lines.append(f'        {param_name}.add("test-item");')
                else:
                    data_lines.append(f'        List<{element_type}> {param_name} = new ArrayList<>(); // Empty list')
            else:
                data_lines.append(f'        {param_type} {param_name} = null; // TODO: Set appropriate value')

        return '\n'.join(data_lines), required_imports


class APIAgent:
    """Enhanced API Agent with auth support and correct parameter handling"""

    def __init__(self):
        self.config = get_config()
        self.logger = get_agent_logger("api_agent")
        self.ai_connector = AIConnectorFactory.create_connector()
        self.logger.info("Enhanced API Agent initialized")

    def _normalize_project_name(self, project_name: str) -> str:
        """Normalize project name for Java package naming"""
        normalized = re.sub(r'[^a-zA-Z0-9]', '', project_name.lower())
        return normalized if normalized else "project"

    def _get_base_package(self, project_name: str) -> str:
        """Generate base package name from project name"""
        normalized_name = self._normalize_project_name(project_name)
        return f"com.{normalized_name}"

    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation - main entry point from orchestrator"""
        self.logger.info(f"Executing operation: {operation}")

        if operation in ["create_project_structure", "setup_test_framework"]:
            return await self.create_project_structure(params)
        elif operation == "generate_test_classes":
            # For compatibility - just create project structure
            return await self.create_project_structure(params)
        elif operation == "create_test_utilities":
            # For compatibility - just create project structure
            return await self.create_project_structure(params)
        else:
            return {
                "operation": operation,
                "status": "completed",
                "message": f"Operation {operation} completed"
            }

    async def create_project_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create professional RestAssured framework structure"""
        project_name = params['project_name']
        language = params['language']
        output_path = Path(params['output_path'])
        parsed_data = params.get('parsed_data')

        self.logger.info(f"Creating enhanced RestAssured framework: {project_name}")

        if language != "java":
            raise ValueError("This framework generator only supports Java projects")

        try:
            output_path.mkdir(parents=True, exist_ok=True)
            base_package = self._get_base_package(project_name)

            # Initialize registry and generators
            registry = ClassRegistry(base_package)
            template_generator = TemplateGenerator(base_package, registry)
            service_test_generator = ServiceTestGenerator(base_package, registry)

            # Generate all files
            all_files = {}

            # Generate pom.xml
            all_files["pom.xml"] = template_generator.generate_pom_xml(project_name)

            # Generate core framework classes from templates
            self.logger.info("Generating core framework classes")

            # Generate utils first (ConfigManager is needed by RestAssuredClient)
            content, _ = template_generator.generate_config_manager()
            all_files[f"src/main/java/{base_package.replace('.', '/')}/utils/ConfigManager.java"] = content

            # Generate models
            content, _ = template_generator.generate_api_request()
            all_files[f"src/main/java/{base_package.replace('.', '/')}/models/ApiRequest.java"] = content

            content, _ = template_generator.generate_api_response()
            all_files[f"src/main/java/{base_package.replace('.', '/')}/models/ApiResponse.java"] = content

            # Generate client (after ConfigManager is registered)
            content, _ = template_generator.generate_rest_assured_client()
            all_files[f"src/main/java/{base_package.replace('.', '/')}/client/RestAssuredClient.java"] = content

            # Generate validators
            content, _ = template_generator.generate_response_validator()
            all_files[f"src/main/java/{base_package.replace('.', '/')}/validators/ResponseValidator.java"] = content

            # Generate base test
            content, _ = template_generator.generate_base_test()
            all_files[f"src/test/java/{base_package.replace('.', '/')}/base/BaseTest.java"] = content

            # Generate additional classes
            all_files.update(self._generate_additional_classes(base_package, registry))

            # Generate configuration files
            all_files.update(self._generate_configuration_files(base_package, parsed_data))

            # Generate services and tests from parsed data
            if parsed_data and parsed_data.get('endpoints'):
                self.logger.info("Generating services and tests from API specification")

                # Analyze endpoints to create method signatures
                endpoints = parsed_data.get('endpoints', [])
                service_methods = service_test_generator.analyze_endpoints(endpoints)

                # Generate services and tests
                for service_name, methods in service_methods.items():
                    # Generate service
                    service_content = service_test_generator.generate_service(service_name, methods)
                    service_path = f"src/main/java/{base_package.replace('.', '/')}/services/{service_name}.java"
                    all_files[service_path] = service_content

                    # Generate test
                    test_content = service_test_generator.generate_test(service_name)
                    test_name = service_name.replace("Service", "ApiTest")
                    test_path = f"src/test/java/{base_package.replace('.', '/')}/tests/{test_name}.java"
                    all_files[test_path] = test_content

            # Write all files
            created_files = []
            for file_path, content in all_files.items():
                if content:
                    full_file = output_path / file_path
                    full_file.parent.mkdir(parents=True, exist_ok=True)
                    full_file.write_text(content, encoding='utf-8')
                    created_files.append(str(full_file))

            self.logger.info(f"Created framework with {len(created_files)} files")

            return {
                "operation": "create_project_structure",
                "status": "completed",
                "language": "java",
                "framework": "Enhanced RestAssured + TestNG",
                "created_files": created_files,
                "base_package": base_package,
                "message": f"Created enhanced Java RestAssured framework with {len(created_files)} files"
            }

        except Exception as e:
            self.logger.error(f"Failed to create framework: {str(e)}")
            raise

    def _generate_additional_classes(self, base_package: str, registry: ClassRegistry) -> Dict[str, str]:
        """Generate additional utility and support classes"""
        files = {}

        # Generate TestDataManager
        files[
            f"src/main/java/{base_package.replace('.', '/')}/utils/TestDataManager.java"] = self._generate_test_data_manager(
            base_package, registry)

        # Generate ApiException
        files[
            f"src/main/java/{base_package.replace('.', '/')}/exceptions/ApiException.java"] = self._generate_api_exception(
            base_package, registry)

        return files

    def _generate_test_data_manager(self, base_package: str, registry: ClassRegistry) -> str:
        """Generate TestDataManager class"""
        package = f"{base_package}.utils"

        content = f"""package {package};

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.type.TypeFactory;
import org.testng.annotations.DataProvider;

import java.io.IOException;
import java.io.InputStream;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Test data management utility
 */
public class TestDataManager {{

    private static final TestDataManager INSTANCE = new TestDataManager();
    private final ObjectMapper objectMapper;
    private final Map<String, JsonNode> testDataCache;
    private final Random random;

    private TestDataManager() {{
        this.objectMapper = new ObjectMapper();
        this.testDataCache = new ConcurrentHashMap<>();
        this.random = ThreadLocalRandom.current();
    }}

    public static TestDataManager getInstance() {{
        return INSTANCE;
    }}

    public <T> T loadTestData(String fileName, Class<T> clazz) throws IOException {{
        JsonNode jsonNode = getJsonNode(fileName);
        return objectMapper.treeToValue(jsonNode, clazz);
    }}

    public <T> List<T> loadTestDataList(String fileName, Class<T> clazz) throws IOException {{
        JsonNode jsonNode = getJsonNode(fileName);
        TypeFactory typeFactory = objectMapper.getTypeFactory();
        return objectMapper.readValue(jsonNode.toString(), 
            typeFactory.constructCollectionType(List.class, clazz));
    }}

    @SuppressWarnings("unchecked")
    public Map<String, Object> loadTestDataAsMap(String fileName) throws IOException {{
        JsonNode jsonNode = getJsonNode(fileName);
        return objectMapper.convertValue(jsonNode, Map.class);
    }}

    public JsonNode getJsonNode(String fileName) throws IOException {{
        return testDataCache.computeIfAbsent(fileName, this::loadJsonFromFile);
    }}

    private JsonNode loadJsonFromFile(String fileName) {{
        try (InputStream inputStream = getClass().getClassLoader()
                .getResourceAsStream("testdata/" + fileName)) {{
            if (inputStream == null) {{
                throw new RuntimeException("Test data file not found: " + fileName);
            }}
            return objectMapper.readTree(inputStream);
        }} catch (IOException e) {{
            throw new RuntimeException("Failed to load test data from: " + fileName, e);
        }}
    }}

    public String generateRandomString(int length) {{
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {{
            sb.append(characters.charAt(random.nextInt(characters.length())));
        }}
        return sb.toString();
    }}

    public String generateRandomEmail() {{
        return generateRandomString(8) + "@" + generateRandomString(5) + ".com";
    }}

    public int generateRandomNumber(int min, int max) {{
        return random.nextInt(max - min + 1) + min;
    }}

    @DataProvider(name = "validTestData")
    public Object[][] getValidTestDataProvider() {{
        Object[][] data = new Object[5][];
        for (int i = 0; i < 5; i++) {{
            Map<String, Object> testData = new HashMap<>();
            testData.put("name", "Test" + i);
            testData.put("value", i);
            data[i] = new Object[]{{testData}};
        }}
        return data;
    }}
}}"""

        # Register class
        java_class = JavaClass(
            name="TestDataManager",
            package=package,
            type=ClassType.UTIL,
            file_path=f"src/main/java/{package.replace('.', '/')}/TestDataManager.java"
        )
        registry.register_class(java_class)

        return content

    def _generate_api_exception(self, base_package: str, registry: ClassRegistry) -> str:
        """Generate ApiException class"""
        package = f"{base_package}.exceptions"

        content = f"""package {package};

/**
 * Custom exception for API-related errors
 */
public class ApiException extends RuntimeException {{

    public ApiException(String message) {{
        super(message);
    }}

    public ApiException(String message, Throwable cause) {{
        super(message, cause);
    }}

    public ApiException(Throwable cause) {{
        super(cause);
    }}
}}"""

        # Register class
        java_class = JavaClass(
            name="ApiException",
            package=package,
            type=ClassType.EXCEPTION,
            file_path=f"src/main/java/{package.replace('.', '/')}/ApiException.java"
        )
        registry.register_class(java_class)

        return content

    def _generate_configuration_files(self, base_package: str, parsed_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate configuration files"""
        files = {}

        # Environment properties
        base_url = parsed_data.get('base_url', 'http://localhost:8080') if parsed_data else 'http://localhost:8080'

        for env in ['dev', 'staging', 'prod']:
            env_url = base_url
            if env != 'prod' and not base_url.startswith('http://localhost'):
                env_url = base_url.replace('://', f'://{env}.')

            content = f"""# {env.upper()} Environment Configuration
api.base.url={env_url}
api.timeout=30000

# Authentication
auth.api.key=${{API_KEY}}
auth.bearer.token=${{BEARER_TOKEN}}

# Retry Configuration  
retry.max.attempts=3
retry.delay.seconds=1

# Logging
logging.enabled=true
"""
            files[f"src/test/resources/config/{env}.properties"] = content

        # TestNG XML
        files["src/test/resources/testng.xml"] = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE suite SYSTEM "http://testng.org/testng-1.0.dtd">
<suite name="API Test Suite" parallel="methods" thread-count="5">
    <listeners>
        <listener class-name="io.qameta.allure.testng.AllureTestNg"/>
    </listeners>

    <test name="API Tests">
        <packages>
            <package name="{base_package}.tests.*"/>
        </packages>
    </test>

    <test name="Smoke Tests">
        <groups>
            <run>
                <include name="smoke"/>
            </run>
        </groups>
        <packages>
            <package name="{base_package}.tests.*"/>
        </packages>
    </test>
</suite>"""

        # Logback configuration
        files["src/test/resources/logback-test.xml"] = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="FILE" class="ch.qos.logback.core.FileAppender">
        <file>target/test-logs/api-tests.log</file>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="FILE"/>
    </root>
</configuration>"""

        return files




