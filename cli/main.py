"""
Beautiful CLI interface for AI Test Orchestrator with Rich formatting
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
        subtitle="[italic]v0.1.0-MVP[/italic]"
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

        table.add_row(
            project['id'],
            project['name'],
            project_type,
            project_language,
            status,
            created
        )

    return table


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
              type=click.Choice(['api', 'ui', 'full']),
              help='Type of project to create')
@click.option('--language',
              type=click.Choice(['java', 'python']),
              help='Programming language')
@click.option('--output-dir', help='Full path where project should be created')
@click.pass_context
def create(ctx, name, project_type, language, output_dir):
    """Create a new test automation project"""

    # Interactive prompts if not provided
    if not name:
        name = Prompt.ask("🏷️  [bold]Project name[/bold]")

    if not project_type:
        project_type = Prompt.ask(
            "🎯 [bold]Project type[/bold]",
            choices=['api', 'ui', 'full'],
            default='api'
        )

    if not language:
        language = Prompt.ask(
            "💻 [bold]Programming language[/bold]",
            choices=['java', 'python'],
            default='java'
        )

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

        # Show project details
        console.print("\n")
        project_panel = Panel(
            f"📁 [bold]Name:[/bold] {name}\n"
            f"🎯 [bold]Type:[/bold] {project_type}\n"
            f"💻 [bold]Language:[/bold] {language}\n"
            f"📂 [bold]Output:[/bold] {output_dir_path}",
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
                progress.update(init_task, advance=20)

                # Create project
                progress.update(init_task, description="Creating project structure...", advance=20)
                project = await orchestrator.create_new_project(
                    name=name,
                    project_type=ProjectType(project_type),
                    language=ProjectLanguage(language),
                    output_path=output_dir_path
                )
                progress.update(init_task, advance=20)

                # Execute project creation workflow
                progress.update(init_task, description="Analyzing requirements...", advance=20)
                result = await orchestrator.execute_project_creation(project)
                progress.update(init_task, advance=20)

                # Complete
                progress.update(init_task, description="Project creation completed!", completed=100)

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

            if 'analysis' in result and result['analysis']:
                analysis = result['analysis']
                results_table.add_row("Complexity", analysis.get('complexity', 'unknown'))
                results_table.add_row("Estimated Time", f"{analysis.get('total_estimated_minutes', 'unknown')} minutes")
                results_table.add_row("Required Agents", ', '.join(analysis.get('required_agents', [])))

            console.print(results_table)

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
        """🤖 [bold]AI Test Orchestrator[/bold] v0.1.0-MVP

[bold cyan]Components:[/bold cyan]
• Agent Orchestrator ✅
• API Agent (Enhanced) 🚀
• DevOps Agent (Planned) ⏳
• UI Agent (Planned) ⏳
• Database Agent (Planned) ⏳

[bold yellow]Features:[/bold yellow]
• AI-powered project analysis
• Intelligent agent coordination
• Real project file generation
• Persistent project storage
• Beautiful CLI interface

[dim]Built with Python, Claude AI, and modern CLI tools[/dim]""",
        title="[bold]Version Information[/bold]",
        box=box.DOUBLE_EDGE
    )

    console.print(version_info)


if __name__ == '__main__':
    cli()