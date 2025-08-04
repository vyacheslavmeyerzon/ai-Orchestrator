# cli/main.py
"""
CLI interface for AI Test Orchestrator with Rich formatting
with base URL and security parameter support
"""

import click
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Rich imports for beautiful CLI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich import box
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config import get_config, reload_config
from common.logger import setup_logging, get_agent_logger
from common.ai_connector import AIConnectorFactory, AIProvider

# Initialize Rich console
console = Console()


def print_header():
    """Print beautiful header"""
    header_text = """
🤖 AI Test Orchestrator
Automated test generation and management system
"""
    console.print(Panel(
        Align.center(header_text),
        box=box.DOUBLE_EDGE,
        style="bold blue",
        title="[bold cyan]Welcome[/bold cyan]",
        subtitle="[italic]v0.1.0[/italic]"
    ))


def print_success(message: str):
    """Print success message"""
    console.print(f"✅ [bold green]{message}[/bold green]")


def print_error(message: str):
    """Print error message"""
    console.print(f"❌ [bold red]{message}[/bold red]")


def print_info(message: str):
    """Print info message"""
    console.print(f"ℹ️  [bold blue]{message}[/bold blue]")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"⚠️  [bold yellow]{message}[/bold yellow]")


def print_security_warning(warnings: list):
    """Print security warnings in red"""
    if not warnings:
        return

    console.print("\n")
    console.print("🔴 [bold red]SECURITY WARNING: Hardcoded secrets detected and replaced![/bold red]")
    console.print()

    warning_text = "🔒 [bold red]Found hardcoded secrets:[/bold red]\n"
    for warning in warnings:
        warning_text += f"   • {warning['type']}: \"{warning['original'][:20]}...\" → {warning['replacement']}\n"

    warning_text += "\n📝 [bold yellow]Action required:[/bold yellow]\n"
    warning_text += "   • Set environment variables before running tests\n"
    warning_text += "   • Update your .env file with real values\n"
    warning_text += "   • Never commit real secrets to version control\n"
    warning_text += "\n✅ [bold green]Project creation continues...[/bold green]"

    security_panel = Panel(
        warning_text,
        title="[bold red]⚠️ SECURITY ALERT ⚠️[/bold red]",
        box=box.HEAVY,
        border_style="red"
    )
    console.print(security_panel)


def create_status_table(config) -> Table:
    """Create beautiful status table"""
    table = Table(title="System Status", box=box.ROUNDED)

    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Details", style="italic")

    # AI Provider status
    ai_status = "🟢 Ready" if config.ai.anthropic_api_key else "🔴 Not configured"
    table.add_row("AI Provider", ai_status, config.ai.default_provider)

    # Database status
    db_exists = os.path.exists(os.path.dirname(config.database.db_path))
    db_status = "🟢 Ready" if db_exists else "🔴 Missing"
    table.add_row("Database", db_status, config.database.db_path)

    # Output directory
    out_exists = os.path.exists(config.project.output_path)
    out_status = "🟢 Ready" if out_exists else "🔴 Missing"
    table.add_row("Output Directory", out_status, config.project.output_path)

    return table


def create_projects_table(projects: list) -> Table:
    """Create beautiful projects table"""
    table = Table(title="Active Projects", box=box.ROUNDED)

    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold cyan")
    table.add_column("Type", style="green")
    table.add_column("Language", style="yellow")
    table.add_column("Status", style="bold")
    table.add_column("API Spec", style="dim")
    table.add_column("Created", style="dim")

    for project in projects:
        status_icons = {
            'pending': '⏳ Pending',
            'in_progress': '🔄 In Progress',
            'completed': '✅ Completed',
            'failed': '❌ Failed'
        }

        # Convert enum values to strings and clean them up
        project_type = str(project['type']).replace('ProjectType.', '').lower()
        project_language = str(project['language']).replace('ProjectLanguage.', '').lower()
        project_status = str(project['status']).replace('TaskStatus.', '').lower()

        status = status_icons.get(project_status, f"❓ {project_status}")
        created = project['created_at'][:19].replace('T', ' ')

        # Check if project has API spec
        api_spec = "📄 Yes" if project.get('metadata', {}).get('api_spec_file') else "❌ No"

        table.add_row(
            project['id'],
            project['name'],
            project_type,
            project_language,
            status,
            api_spec,
            created
        )

    return table


def validate_project_type(value: str) -> str:
    """Validate project type with future release message"""
    if value in ['ui', 'full']:
        print_error("This functionality will be available in future releases")
        sys.exit(1)
    elif value not in ['api']:
        print_error(f"Invalid project type: {value}. Only 'api' is currently supported.")
        sys.exit(1)
    return value


def validate_language(value: str) -> str:
    """Validate language with future release message"""
    if value == 'python':
        print_error("This functionality will be available in future releases")
        sys.exit(1)
    elif value not in ['java']:
        print_error(f"Invalid language: {value}. Only 'java' is currently supported.")
        sys.exit(1)
    return value


@click.group(invoke_without_command=True)
@click.option('--config-file', help='Configuration file path')
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config_file, log_level, verbose):
    """AI Test Orchestrator - Automated test generation and management system"""

    # Print header
    print_header()

    # Ensure context object exists
    ctx.ensure_object(dict)

    # Setup logging
    try:
        config = get_config()
        if verbose:
            log_level = 'DEBUG'

        logger = setup_logging(log_level, config.system.log_file)
        logger.info("AI Test Orchestrator started")

        ctx.obj['config'] = config
        ctx.obj['logger'] = logger

        # If no command specified, show help
        if ctx.invoked_subcommand is None:
            console.print("\n[bold]Available commands:[/bold]")
            console.print("• [cyan]status[/cyan] - Show system status")
            console.print("• [cyan]project[/cyan] - Project management")
            console.print("• [cyan]test-ai[/cyan] - Test AI connectivity")
            console.print("• [cyan]stats[/cyan] - Show statistics")
            console.print("• [cyan]--help[/cyan] - Show detailed help")
            console.print("\n[dim]Run 'orchestrator --help' for more information[/dim]")

    except Exception as e:
        print_error(f"Error initializing system: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration"""
    logger = ctx.obj['logger']
    config = ctx.obj['config']

    console.print("\n")

    # Show status table
    status_table = create_status_table(config)
    console.print(status_table)

    # Show API keys status
    console.print("\n")
    api_panel = Panel(
        f"🔑 Anthropic: {'✅ Configured' if config.ai.anthropic_api_key else '❌ Missing'}\n"
        f"🔑 OpenAI: {'✅ Configured' if config.ai.openai_api_key else '❌ Missing'}",
        title="[bold]API Keys Status[/bold]",
        box=box.ROUNDED
    )
    console.print(api_panel)

    logger.info("System status check completed")


@cli.command()
@click.option('--provider', type=click.Choice(['anthropic', 'openai']), help='AI provider to test')
@click.pass_context
def test_ai(ctx, provider):
    """Test AI connectivity with progress indicator"""
    logger = ctx.obj['logger']
    config = ctx.obj['config']

    async def test_connection():
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
        ) as progress:

            task = progress.add_task("Testing AI connection...", total=None)

            try:
                # Determine provider
                if provider:
                    ai_provider = AIProvider(provider)
                else:
                    ai_provider = AIProvider(config.ai.default_provider)

                progress.update(task, description=f"Connecting to {ai_provider.value}...")

                # Create connector
                connector = AIConnectorFactory.create_connector(ai_provider)

                # Test simple request
                test_prompt = "Respond with exactly: 'AI connection test successful'"
                response = await connector.generate_response(test_prompt)

                progress.update(task, description="Connection successful!")

                # Show success
                print_success(f"AI Connection Test Successful!")
                console.print(f"[dim]Provider:[/dim] [bold]{ai_provider.value}[/bold]")
                console.print(f"[dim]Response:[/dim] [italic]{response}[/italic]")

                logger.info(f"AI connection test successful with {ai_provider.value}")

            except Exception as e:
                print_error(f"AI Connection failed: {str(e)}")
                logger.error(f"AI connection test failed: {str(e)}")

    # Run async function
    asyncio.run(test_connection())


@cli.group()
@click.pass_context
def project(ctx):
    """Project management commands"""
    pass


@project.command()
@click.option('--name', help='Name of the new project')
@click.option('--type', 'project_type',
              type=click.Choice(['api']),  # Only 'api' is available now
              help='Type of project to create')
@click.option('--language',
              type=click.Choice(['java']),  # Only 'java' is available now
              help='Programming language')
@click.option('--output-dir', help='Full path where project should be created')
@click.option('--api-spec-file', 'api_spec_file',
              type=click.Path(exists=True, readable=True),
              help='Path to API specification file (Swagger/OpenAPI, Postman collection, YAML)')
@click.option('--base-url', 'base_url',
              help='Base URL for API (e.g., https://api.example.com)')
@click.option('--auth-type', 'auth_type',
              type=click.Choice(['none', 'api-key', 'bearer', 'basic', 'oauth2']),
              help='Authentication type')
@click.option('--api-key-header', 'api_key_header',
              help='API key header name (e.g., X-API-Key, Authorization)')
@click.option('--auth-server', 'auth_server',
              help='OAuth2 authorization server URL')
@click.option('--environments', 'environments',
              help='Comma-separated list of environments (e.g., dev,staging,prod)')
@click.option('--dev-url', 'dev_url',
              help='Development environment base URL')
@click.option('--staging-url', 'staging_url',
              help='Staging environment base URL')
@click.option('--prod-url', 'prod_url',
              help='Production environment base URL')
@click.pass_context
def create(ctx, name, project_type, language, output_dir, api_spec_file, base_url,
           auth_type, api_key_header, auth_server, environments, dev_url, staging_url, prod_url):
    """Create a new test automation project with comprehensive configuration"""

    # Interactive prompts if not provided
    if not name:
        name = Prompt.ask("🏷️  [bold]Project name[/bold]")

    if not project_type:
        # Custom prompt validation for project type
        while True:
            project_type = Prompt.ask(
                "🎯 [bold]Project type[/bold]",
                default='api'
            )
            if project_type in ['ui', 'full']:
                print_error("This functionality will be available in future releases")
                continue
            elif project_type == 'api':
                break
            else:
                print_error(f"Invalid choice: {project_type}. Please enter 'api'.")
                continue

    if not language:
        # Custom prompt validation for language
        while True:
            language = Prompt.ask(
                "💻 [bold]Programming language[/bold]",
                default='java'
            )
            if language == 'python':
                print_error("This functionality will be available in future releases")
                continue
            elif language == 'java':
                break
            else:
                print_error(f"Invalid choice: {language}. Please enter 'java'.")
                continue

    # Validate command line arguments if provided
    if project_type:
        project_type = validate_project_type(project_type)

    if language:
        language = validate_language(language)

    # Ask for API specification file if not provided and project type is API
    if not api_spec_file and project_type in ['api']:
        has_spec = Confirm.ask("📄 [bold]Do you have an API specification file (Swagger/Postman/YAML)?[/bold]")
        if has_spec:
            api_spec_file = Prompt.ask("📂 [bold]Path to API specification file[/bold]")
            # Validate file exists
            if api_spec_file and not os.path.exists(api_spec_file):
                print_error(f"API specification file not found: {api_spec_file}")
                return

    # Ask for base URL if not provided and we have API spec
    if api_spec_file and not base_url:
        console.print("\n[bold yellow]⚠️ Base URL Configuration[/bold yellow]")
        console.print("The system will try to extract base URL from your API specification.")
        console.print("You can override it or provide additional environment URLs.")

        override_url = Confirm.ask("🌐 [bold]Override base URL from specification?[/bold]")
        if override_url:
            base_url = Prompt.ask("🔗 [bold]Base URL (e.g., https://api.example.com)[/bold]")

    # Ask for authentication details if not provided
    if api_spec_file and not auth_type:
        console.print("\n[bold yellow]🔐 Authentication Configuration[/bold yellow]")
        console.print("The system will try to detect authentication from your specification.")

        override_auth = Confirm.ask("🔑 [bold]Override authentication settings?[/bold]")
        if override_auth:
            auth_type = Prompt.ask(
                "🛡️ [bold]Authentication type[/bold]",
                choices=['none', 'api-key', 'bearer', 'basic', 'oauth2'],
                default='none'
            )

            if auth_type == 'api-key':
                api_key_header = Prompt.ask("📋 [bold]API key header name[/bold]", default="X-API-Key")
            elif auth_type == 'oauth2':
                auth_server = Prompt.ask("🔐 [bold]OAuth2 server URL[/bold]")

    # Ask for environment URLs if not provided
    if api_spec_file and not any([dev_url, staging_url, prod_url]):
        setup_envs = Confirm.ask("🌍 [bold]Setup multiple environments (dev/staging/prod)?[/bold]")
        if setup_envs:
            dev_url = Prompt.ask("🧪 [bold]Development URL[/bold]", default="")
            staging_url = Prompt.ask("🎭 [bold]Staging URL[/bold]", default="")
            prod_url = Prompt.ask("🚀 [bold]Production URL[/bold]", default="")

    async def create_project():
        logger = ctx.obj['logger']
        config = ctx.obj['config']

        if not output_dir:
            output_dir_path = f"{config.project.output_path}\\{name}"
        else:
            output_dir_path = f"{output_dir}\\{name}"

        # Validate that project is not being created inside orchestrator
        orchestrator_path = str(Path(__file__).parent.parent.resolve())
        project_path = str(Path(output_dir_path).resolve())

        if project_path.startswith(orchestrator_path):
            print_error("Cannot create projects inside AI Test Orchestrator directory")
            console.print(f"[dim]Orchestrator path:[/dim] {orchestrator_path}")
            console.print(f"[dim]Suggested path:[/dim] C:\\Users\\user\\test-projects\\{name}")
            return

        # Prepare project configuration
        project_config = {
            "base_url": base_url,
            "auth_type": auth_type,
            "api_key_header": api_key_header,
            "auth_server": auth_server,
            "environments": environments.split(',') if environments else ['dev', 'staging', 'prod'],
            "environment_urls": {
                "dev": dev_url,
                "staging": staging_url,
                "prod": prod_url
            }
        }

        # Show project details including all configuration
        console.print("\n")
        project_details = f"📁 [bold]Name:[/bold] {name}\n" \
                          f"🎯 [bold]Type:[/bold] {project_type}\n" \
                          f"💻 [bold]Language:[/bold] {language}\n" \
                          f"📂 [bold]Output:[/bold] {output_dir_path}"

        if api_spec_file:
            project_details += f"\n📄 [bold]API Spec:[/bold] {api_spec_file}"

        if base_url:
            project_details += f"\n🌐 [bold]Base URL:[/bold] {base_url}"

        if auth_type and auth_type != 'none':
            project_details += f"\n🔐 [bold]Auth Type:[/bold] {auth_type}"
            if api_key_header:
                project_details += f"\n📋 [bold]API Key Header:[/bold] {api_key_header}"

        if any([dev_url, staging_url, prod_url]):
            project_details += f"\n🌍 [bold]Environments:[/bold] Configured"

        project_panel = Panel(
            project_details,
            title="[bold cyan]Creating Project[/bold cyan]",
            box=box.ROUNDED
        )
        console.print(project_panel)

        # Confirm creation
        if not Confirm.ask("\n🚀 [bold]Create this project?[/bold]"):
            print_info("Project creation cancelled")
            return

        try:
            # Import here to avoid circular imports
            from orchestrator.core import get_orchestrator, ProjectType, ProjectLanguage

            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
            ) as progress:

                # Initialize orchestrator
                init_task = progress.add_task("Initializing orchestrator...", total=100)
                orchestrator = get_orchestrator()
                progress.update(init_task, advance=15)

                # Create project
                progress.update(init_task, description="Creating project structure...", advance=15)
                project = await orchestrator.create_new_project(
                    name=name,
                    project_type=ProjectType(project_type),
                    language=ProjectLanguage(language),
                    output_path=output_dir_path,
                    api_spec_file=api_spec_file,
                    project_config=project_config  # Pass configuration
                )
                progress.update(init_task, advance=20)

                # Execute project creation workflow
                progress.update(init_task, description="Analyzing requirements...", advance=20)
                result = await orchestrator.execute_project_creation(project)
                progress.update(init_task, advance=20)

                # Complete
                progress.update(init_task, description="Project creation completed!", completed=100)

            # Show security warnings if any
            security_warnings = []
            for task_result in result.get('results', []):
                if isinstance(task_result, dict) and 'security_warnings' in task_result:
                    security_warnings.extend(task_result['security_warnings'])

            if security_warnings:
                print_security_warning(security_warnings)

            # Show results
            console.print("\n")
            print_success("Project creation completed!")

            # Results table
            results_table = Table(box=box.ROUNDED)
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", style="bold")

            results_table.add_row("Project ID", project.id)
            results_table.add_row("Status", result['status'])
            results_table.add_row("Tasks Completed", f"{result['tasks_completed']}/{result['total_tasks']}")

            if security_warnings:
                results_table.add_row("Security Issues", f"🔴 {len(security_warnings)} secrets replaced")

            if api_spec_file:
                results_table.add_row("API Spec Parsed", "✅ Yes")
                # Check if parsed data is available in result
                parsed_data = None
                for task_result in result.get('results', []):
                    if isinstance(task_result, dict) and 'parsed_data' in task_result:
                        parsed_data = task_result['parsed_data']
                        break

                if parsed_data:
                    endpoints_count = parsed_data.get('endpoints_count', len(parsed_data.get('endpoints', [])))
                    results_table.add_row("API Endpoints", str(endpoints_count))

            if 'analysis' in result and result['analysis']:
                analysis = result['analysis']
                results_table.add_row("Complexity", analysis.get('complexity', 'unknown'))
                results_table.add_row("Estimated Time", f"{analysis.get('total_estimated_minutes', 'unknown')} minutes")
                results_table.add_row("Required Agents", ', '.join(analysis.get('required_agents', [])))

            console.print(results_table)

            # Show additional info if API spec was processed
            if api_spec_file:
                console.print("\n")

                # Find parsed data from results
                parsed_info = "Not available"
                endpoints_info = "Not parsed"
                auth_info = "Unknown"

                for task_result in result.get('results', []):
                    if isinstance(task_result, dict) and 'parsed_data' in task_result:
                        parsed_data = task_result['parsed_data']
                        endpoints_info = str(len(parsed_data.get('endpoints', [])))
                        auth_info = parsed_data.get('authentication', {}).get('type', 'none')
                        break

                api_info_panel = Panel(
                    f"📄 [bold]API Specification:[/bold] {os.path.basename(api_spec_file)}\n"
                    f"🔗 [bold]Endpoints:[/bold] {endpoints_info}\n"
                    f"🔐 [bold]Authentication:[/bold] {auth_info}\n"
                    f"📊 [bold]Test Scenarios:[/bold] Generated automatically\n"
                    f"🌍 [bold]Environments:[/bold] {len(project_config['environments'])} configured",
                    title="[bold green]API Analysis Results[/bold green]",
                    box=box.ROUNDED
                )
                console.print(api_info_panel)

            logger.info(f"Project creation completed successfully: {name}")

        except Exception as e:
            print_error(f"Project creation failed: {str(e)}")
            logger.error(f"Project creation failed: {str(e)}")

    # Run async function
    asyncio.run(create_project())


@project.command()
@click.pass_context
def list(ctx):
    """List all projects"""

    async def list_projects():
        logger = ctx.obj['logger']

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
        ) as progress:

            task = progress.add_task("Loading projects...", total=None)

            try:
                from orchestrator.core import get_orchestrator

                orchestrator = get_orchestrator()
                projects = orchestrator.list_projects()

            except Exception as e:
                print_error(f"Failed to load projects: {str(e)}")
                logger.error(f"Failed to load projects: {str(e)}")
                return

        console.print("\n")

        if not projects:
            console.print(Panel(
                Align.center(
                    "No projects found\n\nUse [bold cyan]project create[/bold cyan] to create your first project"),
                title="[bold]Projects[/bold]",
                box=box.ROUNDED
            ))
            return

        # Show projects table
        projects_table = create_projects_table(projects)
        console.print(projects_table)

        console.print(f"\n[dim]Total projects: {len(projects)}[/dim]")
        logger.info(f"Listed {len(projects)} projects")

    asyncio.run(list_projects())


@cli.command()
@click.pass_context
def stats(ctx):
    """Show beautiful system statistics"""

    async def show_statistics():
        logger = ctx.obj['logger']

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
        ) as progress:

            task = progress.add_task("Collecting statistics...", total=None)

            try:
                from orchestrator.core import get_orchestrator

                orchestrator = get_orchestrator()
                stats = orchestrator.storage.get_statistics()

            except Exception as e:
                print_error(f"Failed to get statistics: {str(e)}")
                logger.error(f"Failed to get statistics: {str(e)}")
                return

        console.print("\n")

        # Create statistics layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )

        # Header
        layout["header"].update(Panel(
            Align.center("📊 System Statistics"),
            box=box.HEAVY
        ))

        # Stats tables
        projects_stats = Table(title="Projects", box=box.ROUNDED)
        projects_stats.add_column("Metric", style="cyan")
        projects_stats.add_column("Count", style="bold green")

        projects_stats.add_row("Total Projects", str(stats['total_projects']))

        for status, count in stats.get('projects_by_status', {}).items():
            status_icons = {
                'pending': '⏳ Pending',
                'in_progress': '🔄 In Progress',
                'completed': '✅ Completed',
                'failed': '❌ Failed'
            }
            projects_stats.add_row(status_icons.get(status, status), str(count))

        console.print(projects_stats)

        # Tasks stats
        console.print("\n")
        tasks_stats = Table(title="Tasks", box=box.ROUNDED)
        tasks_stats.add_column("Metric", style="cyan")
        tasks_stats.add_column("Count", style="bold blue")

        tasks_stats.add_row("Total Tasks", str(stats['total_tasks']))

        for status, count in stats.get('tasks_by_status', {}).items():
            status_icons = {
                'pending': '⏳ Pending',
                'in_progress': '🔄 In Progress',
                'completed': '✅ Completed',
                'failed': '❌ Failed'
            }
            tasks_stats.add_row(status_icons.get(status, status), str(count))

        console.print(tasks_stats)

        logger.info("System statistics displayed")

    asyncio.run(show_statistics())


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information"""

    console.print("\n")

    # Version panel
    version_info = Panel(
        """🤖 [bold]AI Test Orchestrator[/bold] v0.1.0 Initial

[bold cyan]Components:[/bold cyan]
• Agent Orchestrator ✅
• API Agent (Enhanced with Code Validation) ✅
• DevOps Agent (Production Ready) ✅
• Parser Agent (Security Enhanced) 🚀
• UI Agent (Coming soon) ⏳
• Database Agent (Coming soon) ⏳

[bold yellow]Current Features:[/bold yellow]
• AI-powered project analysis
• API test automation (Java/RestAssured)
• Real project file generation
• Persistent project storage
• Beautiful CLI interface
• API specification parsing ✅
• Swagger/Postman/YAML support ✅
• Security hardcoded secrets detection 🆕
• Multi-environment configuration 🆕
• Authentication setup automation 🆕
• Code validation and auto-fixing 🆕

[bold blue]Coming Soon:[/bold blue]
• UI test automation support
• Python language support
• Database testing capabilities
• Advanced reporting system

[dim]Built with Python, Claude AI, and modern CLI tools[/dim]""",
        title="[bold]Version Information[/bold]",
        box=box.DOUBLE_EDGE
    )

    console.print(version_info)


if __name__ == '__main__':
    cli()