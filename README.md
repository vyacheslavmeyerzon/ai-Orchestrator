# 🤖 AI Test Orchestrator - MVP

Enterprise-grade test automation framework generator powered by AI agents that creates complete testing infrastructure and framework from API specifications.

## 🚀 What is this?

AI Test Orchestrator is a production-ready system that uses Claude AI to orchestrate multiple specialized agents for automated test framework generation. Simply provide an API specification (Swagger/OpenAPI/Postman), and the system will:

- Parse and analyze your API specification
- Detect and replace hardcoded secrets automatically  
- Generate complete Java test framework with RestAssured infrastructure
- Create Docker environments and CI/CD pipelines
- Setup project structure with all necessary configurations

**Current Version (v0.1.0)**: The system generates a complete test framework with infrastructure where you can quickly write and deploy your tests. It creates basic test cases that require manual implementation.

**Future Versions**: Full test generation from Postman collections and API specifications is planned for upcoming releases.

## ✨ Key Features

- **🔍 Smart API Parsing**: Supports Swagger 2.0/3.0, OpenAPI, Postman collections
- **🔒 Security First**: Automatic detection and parameterization of hardcoded secrets
- **☕ Java Framework Generation**: Complete RestAssured + TestNG framework with Maven
- **🐳 DevOps Ready**: Docker, Kubernetes, GitHub Actions, GitLab CI, Jenkins
- **🎨 Beautiful CLI**: Rich terminal UI with progress bars and colored output
- **🧠 AI-Powered**: Uses Claude AI for intelligent analysis and code generation
- **💾 Persistent Storage**: SQLite database for project and task management
- **🔄 Multi-Environment**: Support for dev, staging, prod configurations

## 📋 Requirements

- Python 3.9 or higher
- Anthropic API key (for Claude AI)
- Git
- 8GB RAM recommended

### Optional Requirements
- Docker Desktop (for containerization features)
- Java 11+ and Maven (for running generated tests)

## 🛠️ Installation

### 1. Clone the Repository

```bash
# All platforms
git clone https://github.com/vyacheslavmeyerzon/ai-Orchestrator.git
cd ai-Orchestrator
```

### 2. Set Up Python Environment

#### Windows (Command Prompt)
```cmd
# Check Python version
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Windows (PowerShell)
```powershell
# Check Python version
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

#### Linux/macOS
```bash
# Check Python version
python3 --version

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in project root:

#### Windows
```cmd
# Create .env file
copy .env.template .env
notepad .env
```

#### Linux/macOS
```bash
# Create .env file
cp .env.template .env
nano .env  # or vim .env
```

Add your configuration:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional - Default paths per OS
# Windows
DEFAULT_OUTPUT_PATH=C:\Users\%USERNAME%\test-projects

# Linux
DEFAULT_OUTPUT_PATH=/home/$USER/test-projects

# macOS
DEFAULT_OUTPUT_PATH=/Users/$USER/test-projects

# Common settings
LOG_LEVEL=INFO
DB_PATH=./data/orchestrator.db
DEFAULT_AI_PROVIDER=anthropic
```

## 🎯 Quick Start

### Check System Status

#### Windows (CMD)
```cmd
python cli\main.py status
```

#### Windows (PowerShell) / Linux / macOS
```bash
python cli/main.py status
```

### Test AI Connection

#### Windows (CMD)
```cmd
python cli\main.py test-ai
```

#### Windows (PowerShell) / Linux / macOS
```bash
python cli/main.py test-ai
```

### Create Your First Project

#### Interactive Mode (Recommended)

All platforms support interactive mode where the system will prompt you for all necessary information:

```bash
python cli/main.py project create
```

The system will ask you:
- Project name
- Project type (api/ui/full) - default: api
- Programming language (java/python) - default: java  
- API specification file (if you have one)
- Authentication settings
- Environment URLs

#### Quick Project Creation

##### Simple project without API specification:
```bash
python cli/main.py project create --name "my-first-project"
```

##### Project with API specification (One line - All platforms):
```bash
python cli/main.py project create --name "my-test-project" --api-spec-file swagger.yaml
```

##### Real Example with E-commerce API:
```bash
python cli/main.py project create --name "my-example-tests" --api-spec-file swagger3.yaml --base-url "your-endpoint.api.url.com"
```

#### Advanced Examples with All Parameters

##### Windows (CMD)
```cmd
python cli\main.py project create ^
  --name "my-api-tests" ^
  --api-spec-file swagger.yaml ^
  --base-url "https://api.example.com" ^
  --auth-type "bearer" ^
  --dev-url "https://dev.api.example.com" ^
  --staging-url "https://staging.api.example.com" ^
  --prod-url "https://api.example.com"
```

##### Windows (PowerShell)
```powershell
python cli/main.py project create `
  --name "my-api-tests" `
  --api-spec-file swagger.yaml `
  --base-url "https://api.example.com" `
  --auth-type "bearer" `
  --dev-url "https://dev.api.example.com" `
  --staging-url "https://staging.api.example.com" `
  --prod-url "https://api.example.com"
```

##### Linux/macOS
```bash
python cli/main.py project create \
  --name "my-api-tests" \
  --api-spec-file swagger.yaml \
  --base-url "https://api.example.com" \
  --auth-type "bearer" \
  --dev-url "https://dev.api.example.com" \
  --staging-url "https://staging.api.example.com" \
  --prod-url "https://api.example.com"
```

**Note**: When using `--api-spec-file`, the system will prompt you interactively for additional configuration like authentication type and environment URLs if not provided as parameters.

## 🏗️ Architecture

The system uses a multi-agent architecture coordinated by a central orchestrator:

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ Beautiful CLI (Rich)
┌──────▼──────────────────────────────────────┐
│          Agent Orchestrator                  │
│  • Claude AI-powered analysis                │
│  • Task planning & coordination              │
│  • SQLite persistence                        │
│  • Error handling & retry logic              │
└──────┬──────────────┬───────────┬───────────┘
       │              │           │
┌──────▼──────┐ ┌────▼────┐ ┌───▼──────┐
│ Parser Agent│ │API Agent │ │DevOps    │
│             │ │          │ │Agent     │
│ • Swagger   │ │ • Java   │ │ • Docker │
│ • Postman   │ │ • Maven  │ │ • K8s    │
│ • Security  │ │ • Tests  │ │ • CI/CD  │
└─────────────┘ └──────────┘ └──────────┘
```

## 📚 Detailed Usage

### All Available Commands

#### Project Management

##### Windows (CMD)
```cmd
# Create new project
python cli\main.py project create

# List all projects
python cli\main.py project list
```

##### Windows (PowerShell) / Linux / macOS
```bash
# Create new project
python cli/main.py project create

# List all projects
python cli/main.py project list
```

#### System Commands

##### Windows (CMD)
```cmd
# Check system status
python cli\main.py status

# Test AI connectivity
python cli\main.py test-ai

# View statistics
python cli\main.py stats

# Show version
python cli\main.py version
```

##### Windows (PowerShell) / Linux / macOS
```bash
# Check system status
python cli/main.py status

# Test AI connectivity
python cli/main.py test-ai

# View statistics
python cli/main.py stats

# Show version
python cli/main.py version
```

### Multi-Environment Project Setup

#### Windows (CMD)
```cmd
python cli\main.py project create ^
  --name "multi-env-api" ^
  --api-spec-file swagger.yaml ^
  --environments "dev,staging,prod" ^
  --dev-url "https://dev-api.example.com" ^
  --staging-url "https://staging-api.example.com" ^
  --prod-url "https://api.example.com"
```

#### Windows (PowerShell)
```powershell
python cli/main.py project create `
  --name "multi-env-api" `
  --api-spec-file swagger.yaml `
  --environments "dev,staging,prod" `
  --dev-url "https://dev-api.example.com" `
  --staging-url "https://staging-api.example.com" `
  --prod-url "https://api.example.com"
```

#### Linux/macOS
```bash
python cli/main.py project create \
  --name "multi-env-api" \
  --api-spec-file swagger.yaml \
  --environments "dev,staging,prod" \
  --dev-url "https://dev-api.example.com" \
  --staging-url "https://staging-api.example.com" \
  --prod-url "https://api.example.com"
```

### Working with Generated Projects

After project generation is complete, navigate to your generated project and execute tests:

#### Windows
```cmd
cd C:\Users\%USERNAME%\test-projects\your-project-name

# Run tests with Maven
mvn clean test

# Or run specific test environment
mvn clean test -Denv=dev

# Run tests with Docker
scripts\run-tests.bat

# View Allure reports
scripts\run-allure.bat
```

#### Linux/macOS
```bash
cd ~/test-projects/your-project-name

# Run tests with Maven
mvn clean test

# Or run specific test environment
mvn clean test -Denv=dev

# Run tests with Docker
./scripts/run-tests.sh

# View Allure reports
./scripts/run-allure.sh
```

**Note**: 
- AI Test Orchestrator generates the complete test framework infrastructure
- Basic test cases are created but require manual implementation
- Test execution is done using standard tools (Maven, Docker) in the generated project
- Full automatic test generation from API specifications is planned for future releases

## 📁 Generated Project Structure

```
# Windows: C:\Users\{username}\test-projects\{project-name}\
# Linux: /home/{username}/test-projects/{project-name}/
# macOS: /Users/{username}/test-projects/{project-name}/

your-project/
├── src/
│   ├── main/java/com/yourproject/
│   │   ├── client/
│   │   │   └── RestAssuredClient.java
│   │   ├── models/
│   │   │   ├── ApiRequest.java
│   │   │   └── ApiResponse.java
│   │   ├── services/
│   │   │   └── [Generated service classes]
│   │   ├── utils/
│   │   │   ├── ConfigManager.java
│   │   │   └── TestDataManager.java
│   │   ├── validators/
│   │   │   └── ResponseValidator.java
│   │   └── exceptions/
│   │       └── ApiException.java
│   └── test/
│       ├── java/com/yourproject/
│       │   ├── base/
│       │   │   └── BaseTest.java
│       │   └── tests/
│       │       └── [Generated test classes]
│       └── resources/
│           ├── config/
│           │   ├── dev.properties
│           │   ├── staging.properties
│           │   └── prod.properties
│           ├── testdata/
│           ├── logback-test.xml
│           └── testng.xml
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.debug.yml
│   └── docker-compose.allure.yml
├── .github/workflows/
│   ├── test.yml
│   ├── nightly.yml
│   └── docker-build.yml
├── scripts/
│   ├── run-tests.bat (Windows)
│   ├── run-tests.sh (Linux/Mac)
│   ├── run-allure.bat (Windows)
│   ├── run-allure.sh (Linux/Mac)
│   ├── run-debug.bat (Windows)
│   ├── run-debug.sh (Linux/Mac)
│   ├── clean.bat (Windows)
│   └── clean.sh (Linux/Mac)
├── pom.xml
├── .env.template
├── SECURITY_SETUP.md (if secrets detected)
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create `.env` file with platform-specific paths:

#### Windows Example
```ini
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Project output path
DEFAULT_OUTPUT_PATH=C:\Users\%USERNAME%\test-projects

# Optional
LOG_LEVEL=INFO
DB_PATH=.\data\orchestrator.db
DEFAULT_AI_PROVIDER=anthropic
```

#### Linux Example
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Project output path
DEFAULT_OUTPUT_PATH=/home/$USER/test-projects

# Optional
LOG_LEVEL=INFO
DB_PATH=./data/orchestrator.db
DEFAULT_AI_PROVIDER=anthropic
```

#### macOS Example
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Project output path
DEFAULT_OUTPUT_PATH=/Users/$USER/test-projects

# Optional
LOG_LEVEL=INFO
DB_PATH=./data/orchestrator.db
DEFAULT_AI_PROVIDER=anthropic
```

## 🔒 Security Features

### Automatic Secret Detection

When parsing API specifications, the system automatically detects:
- API keys (e.g., `sk-1234567890abcdef...`)
- JWT tokens (e.g., `eyJ0eXAiOiJKV1QiLCJhbGc...`)
- Bearer tokens (e.g., `Bearer abc123...`)
- Basic auth credentials
- Passwords in examples

Example security warning:
```
🔴 SECURITY WARNING: Hardcoded secrets detected and replaced!

Found hardcoded secrets:
   • api_key: "sk-1234567890abcdef..." → ${API_KEY_TO_CHANGE}
   • bearer_token: "Bearer eyJ0eXAiOiJKV1..." → ${BEARER_TOKEN_TO_CHANGE}

Action required:
   • Set environment variables before running tests
   • Update your .env file with real values
   • Never commit real secrets to version control
```

## 🐳 Docker Support

The DevOps Agent creates platform-specific Docker configurations:

### Windows-Specific Features
- Optimized Dockerfile for Windows containers
- Batch scripts for all Docker operations
- Proper path handling for Windows volumes
- Docker Desktop detection

### Linux/macOS Features
- Native Docker support
- Shell scripts with proper permissions
- Performance optimizations
- Volume mount configurations

### Running Tests in Docker

#### Windows
```cmd
# Build and run tests
scripts\run-tests.bat

# Run with Allure reporting
scripts\run-allure.bat

# Debug mode (port 5005)
scripts\run-debug.bat

# Cleanup
scripts\clean.bat
```

#### Linux/macOS
```bash
# Build and run tests
./scripts/run-tests.sh

# Run with Allure reporting
./scripts/run-allure.sh

# Debug mode (port 5005)
./scripts/run-debug.sh

# Cleanup
./scripts/clean.sh
```

## 🚀 CI/CD Integration

Generated CI/CD configurations include:

### GitHub Actions
- Automated test execution on push/PR
- Docker image building and caching
- Multi-environment testing
- Allure report publishing

### GitLab CI
- Pipeline with stages
- Docker-in-Docker support
- Artifact management
- Parallel test execution

### Jenkins
- Declarative pipeline
- Docker agent support
- Post-build actions
- Email notifications

## 📊 Current Status & Roadmap

### ✅ Completed (v0.1.0)
- [x] Agent Orchestrator with AI task planning
- [x] Parser Agent with security scanning
- [x] API Agent for Java/Maven projects
- [x] DevOps Agent with multi-platform support
- [x] Beautiful CLI with Rich UI
- [x] SQLite persistence layer
- [x] Multi-environment configuration
- [x] Cross-platform compatibility

### 🔄 In Development
- [ ] Advanced Reporting (Allure, ExtentReports integration)
- [ ] Real-time test execution monitoring
- [ ] Web dashboard for results visualization

### 📋 Planned Features
- [ ] **Python Support**: pytest framework generation (v0.2.0)
- [ ] **UI Testing**: Selenium/Playwright agent (v0.3.0)
- [ ] **Database Agent**: Test data management (v0.4.0)
- [ ] **Cloud Integration**: AWS/Azure deployment
- [ ] **Test Management**: Jira/TestRail integration

## 🚨 Troubleshooting

### Common Issues

#### Python Command Not Found
- **Windows**: Make sure Python is in PATH. Use `py` instead of `python`
- **Linux/macOS**: Use `python3` instead of `python`

#### Permission Denied (Linux/macOS)
```bash
chmod +x scripts/*.sh
```

#### PowerShell Execution Policy (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Anthropic API Key Issues
- Ensure the key starts with `sk-ant-`
- Check for extra spaces or quotes in .env file
- Verify the key is active in your Anthropic account

## 🤝 Contributing

We welcome contributions! Areas where help is needed:
- Python/pytest framework generation
- Additional API specification formats
- UI testing agent development
- Cloud platform integrations

Contributing guidelines are coming soon. For now, please open an issue to discuss your ideas.

## 📄 License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
MIT License - see [LICENSE](https://github.com/vyacheslavmeyerzon/ai-Orchestrator/blob/main/LICENSE)

## 🙏 Acknowledgments

- Built by [Slava Meyerzon](https://www.linkedin.com/in/smeyerzon/) with [Claude AI](https://www.anthropic.com/) by Anthropic
- Beautiful CLI powered by [Rich](https://github.com/Textualize/rich)
- Test frameworks: [RestAssured](https://rest-assured.io/), [TestNG](https://testng.org/)
- Container support: [Docker](https://www.docker.com/), [Kubernetes](https://kubernetes.io/)

## 📞 Support

- GitHub Issues: (Coming Soon)
- Documentation: (Coming soon)

---

Made with ❤️ by [Slava Meyerzon](https://www.linkedin.com/in/smeyerzon/)