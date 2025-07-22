"""
Main CLI interface for AI Test Orchestrator
"""

import click
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config import get_config, reload_config
from common.logger import setup_logging, get_agent_logger
from common.ai_connector import AIConnectorFactory, AIProvider


@click.group()
@click.option('--config-file', help='Configuration file path')
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config_file, log_level, verbose):
    """AI Test Orchestrator - Automated test generation and management system"""

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

    except Exception as e:
        click.echo(f"❌ Error initializing system: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', help='Path where to create projects directory')
@click.pass_context
def setup_workspace(ctx, path):
    """Setup workspace directory for projects"""
    logger = ctx.obj['logger']
    config = ctx.obj['config']

    if not path:
        path = config.project.output_path

    try:
        workspace_path = Path(path)
        workspace_path.mkdir(parents=True, exist_ok=True)

        click.echo(f"✅ Workspace created: {workspace_path}")
        click.echo("📁 Directory structure:")
        click.echo(f"   {path}\\")
        click.echo(f"   ├── (your API projects will be created here)")
        click.echo(f"   ├── (your UI projects will be created here)")
        click.echo(f"   └── (your full projects will be created here)")

        # Update config if needed
        if path != config.project.output_path:
            click.echo(f"\n💡 Tip: Update DEFAULT_OUTPUT_PATH in .env to: {path}")

        logger.info(f"Workspace setup completed: {path}")

    except Exception as e:
        click.echo(f"❌ Failed to create workspace: {str(e)}")
        logger.error(f"Failed to create workspace: {str(e)}")


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration"""
    logger = ctx.obj['logger']
    config = ctx.obj['config']

    click.echo("🤖 AI Test Orchestrator - System Status")
    click.echo("=" * 50)

    # Configuration status
    click.echo(f"📋 Configuration:")
    click.echo(f"   • AI Provider: {config.ai.default_provider}")
    click.echo(f"   • Log Level: {config.system.log_level}")
    click.echo(f"   • Database: {config.database.db_path}")
    click.echo(f"   • Max Agents: {config.system.max_concurrent_agents}")

    # API Keys status
    click.echo(f"🔑 API Keys:")
    anthropic_status = "✅" if config.ai.anthropic_api_key else "❌"
    openai_status = "✅" if config.ai.openai_api_key else "❌"
    click.echo(f"   • Anthropic: {anthropic_status}")
    click.echo(f"   • OpenAI: {openai_status}")

    # Directory status
    click.echo(f"📁 Directories:")
    dirs_to_check = [
        ("Database", os.path.dirname(config.database.db_path)),
        ("Templates", config.project.templates_path),
        ("Output", config.project.output_path),
        ("Logs", os.path.dirname(config.system.log_file))
    ]

    for name, path in dirs_to_check:
        status_icon = "✅" if os.path.exists(path) else "❌"
        click.echo(f"   • {name}: {status_icon} {path}")

    logger.info("System status check completed")


@cli.command()
@click.option('--provider', type=click.Choice(['anthropic', 'openai']), help='AI provider to test')
@click.pass_context
def test_ai(ctx, provider):
    """Test AI connectivity"""
    logger = ctx.obj['logger']
    config = ctx.obj['config']

    async def test_connection():
        click.echo("🧪 Testing AI Connection...")

        try:
            # Determine provider
            if provider:
                ai_provider = AIProvider(provider)
            else:
                ai_provider = AIProvider(config.ai.default_provider)

            click.echo(f"Using provider: {ai_provider.value}")

            # Create connector
            connector = AIConnectorFactory.create_connector(ai_provider)

            # Test simple request
            test_prompt = "Respond with exactly: 'AI connection test successful'"
            response = await connector.generate_response(test_prompt)

            click.echo(f"✅ AI Response: {response}")
            logger.info(f"AI connection test successful with {ai_provider.value}")

        except Exception as e:
            click.echo(f"❌ AI Connection failed: {str(e)}")
            logger.error(f"AI connection test failed: {str(e)}")
            sys.exit(1)

    # Run async function
    asyncio.run(test_connection())


@cli.group()
@click.pass_context
def project(ctx):
    """Project management commands"""
    pass


@project.command()
@click.option('--name', prompt='Project name', help='Name of the new project')
@click.option('--type', 'project_type',
              type=click.Choice(['api', 'ui', 'full']),
              default='api',
              help='Type of project to create')
@click.option('--language',
              type=click.Choice(['java', 'python']),
              default='java',
              help='Programming language')
@click.option('--output-dir',
              help='Full path where project should be created (default: C:\\Users\\user\\test-projects)')
@click.pass_context
def create(ctx, name, project_type, language, output_dir):
    """Create a new test automation project"""

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
            click.echo("❌ Error: Cannot create projects inside AI Test Orchestrator directory")
            click.echo(f"   Orchestrator path: {orchestrator_path}")
            click.echo(f"   Suggested path: C:\\Users\\user\\test-projects\\{name}")
            return

        click.echo(f"🚀 Creating new {project_type} project: {name}")
        click.echo(f"   Language: {language}")
        click.echo(f"   Output: {output_dir_path}")

        try:
            # Import here to avoid circular imports
            from orchestrator.core import get_orchestrator, ProjectType, ProjectLanguage

            orchestrator = get_orchestrator()

            # Create project
            project = await orchestrator.create_new_project(
                name=name,
                project_type=ProjectType(project_type),
                language=ProjectLanguage(language),
                output_path=output_dir_path
            )

            click.echo(f"📋 Project created with ID: {project.id}")
            click.echo("🔄 Executing project creation workflow...")

            # Execute project creation
            result = await orchestrator.execute_project_creation(project)

            click.echo(f"✅ Project creation completed!")
            click.echo(f"   Status: {result['status']}")
            click.echo(f"   Tasks completed: {result['tasks_completed']}/{result['total_tasks']}")

            # Show analysis results
            if 'analysis' in result and result['analysis']:
                analysis = result['analysis']
                click.echo(f"📊 Project Analysis:")
                click.echo(f"   • Complexity: {analysis.get('complexity', 'unknown')}")
                click.echo(f"   • Estimated time: {analysis.get('total_estimated_minutes', 'unknown')} minutes")
                click.echo(f"   • Required agents: {', '.join(analysis.get('required_agents', []))}")

            logger.info(f"Project creation completed successfully: {name}")

        except Exception as e:
            click.echo(f"❌ Project creation failed: {str(e)}")
            logger.error(f"Project creation failed: {str(e)}")
            sys.exit(1)

    # Run async function
    asyncio.run(create_project())


@project.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.pass_context
def analyze(ctx, project_path):
    """Analyze existing project"""
    logger = ctx.obj['logger']

    click.echo(f"🔍 Analyzing project: {project_path}")

    # This will be implemented when we create agents
    click.echo("⚠️  Project analysis not yet implemented - coming in next steps!")

    logger.info(f"Project analysis requested: {project_path}")


@project.command()
@click.pass_context
def list(ctx):
    """List all projects"""

    async def list_projects():
        logger = ctx.obj['logger']

        try:
            from orchestrator.core import get_orchestrator

            orchestrator = get_orchestrator()
            projects = orchestrator.list_projects()

            if not projects:
                click.echo("📁 No projects found")
                return

            click.echo("📁 Active Projects:")
            click.echo("=" * 50)

            for project in projects:
                status_icon = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(project['status'], '❓')

                click.echo(f"{status_icon} {project['name']} ({project['id']})")
                click.echo(f"   Type: {project['type']} | Language: {project['language']}")
                click.echo(f"   Created: {project['created_at'][:19].replace('T', ' ')}")
                click.echo(f"   Path: {project['output_path']}")
                click.echo()

            logger.info(f"Listed {len(projects)} projects")

        except Exception as e:
            click.echo(f"❌ Failed to list projects: {str(e)}")
            logger.error(f"Failed to list projects: {str(e)}")

    asyncio.run(list_projects())


@project.command()
@click.argument('project_id')
@click.pass_context
def status_cmd(ctx, project_id):
    """Show detailed project status"""

    async def show_project_status():
        logger = ctx.obj['logger']

        try:
            from orchestrator.core import get_orchestrator

            orchestrator = get_orchestrator()
            status_info = orchestrator.get_project_status(project_id)

            if not status_info:
                click.echo(f"❌ Project not found: {project_id}")
                return

            project = status_info['project']
            tasks = status_info['tasks']
            summary = status_info['summary']

            click.echo(f"📋 Project Status: {project['name']}")
            click.echo("=" * 50)

            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(project['status'], '❓')

            click.echo(f"Status: {status_icon} {project['status']}")
            click.echo(f"Type: {project['type']} | Language: {project['language']}")
            click.echo(f"Output Path: {project['output_path']}")
            click.echo(f"Created: {project['created_at'][:19].replace('T', ' ')}")
            click.echo(f"Updated: {project['updated_at'][:19].replace('T', ' ')}")

            click.echo(f"\n📊 Task Summary:")
            click.echo(f"   Total: {summary['total_tasks']}")
            click.echo(f"   Completed: {summary['completed']} ✅")
            click.echo(f"   Failed: {summary['failed']} ❌")
            click.echo(f"   Pending: {summary['pending']} ⏳")

            if tasks:
                click.echo(f"\n📝 Tasks:")
                for task in tasks:
                    task_icon = {
                        'pending': '⏳',
                        'in_progress': '🔄',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(task['status'], '❓')

                    click.echo(f"   {task_icon} {task['agent_type']}: {task['operation']}")
                    if task['status'] == 'failed' and task['error_message']:
                        click.echo(f"      Error: {task['error_message']}")

            logger.info(f"Showed status for project: {project_id}")

        except Exception as e:
            click.echo(f"❌ Failed to get project status: {str(e)}")
            logger.error(f"Failed to get project status: {str(e)}")

    asyncio.run(show_project_status())


@project.command()
@click.argument('project_id')
@click.confirmation_option(prompt='Are you sure you want to delete this project?')
@click.pass_context
def delete(ctx, project_id):
    """Delete a project and all its data"""

    async def delete_project():
        logger = ctx.obj['logger']

        try:
            from orchestrator.core import get_orchestrator

            orchestrator = get_orchestrator()

            # Check if project exists
            if project_id not in orchestrator.active_projects:
                click.echo(f"❌ Project not found: {project_id}")
                return

            project = orchestrator.active_projects[project_id]

            # Delete from storage
            if orchestrator.storage.delete_project(project_id):
                # Remove from memory
                del orchestrator.active_projects[project_id]

                click.echo(f"✅ Project '{project.name}' deleted successfully")
                logger.info(f"Deleted project: {project_id}")
            else:
                click.echo(f"❌ Failed to delete project: {project_id}")

        except Exception as e:
            click.echo(f"❌ Failed to delete project: {str(e)}")
            logger.error(f"Failed to delete project: {str(e)}")

    asyncio.run(delete_project())


@cli.command()
@click.pass_context
def stats(ctx):
    """Show system statistics"""

    async def show_statistics():
        logger = ctx.obj['logger']

        try:
            from orchestrator.core import get_orchestrator

            orchestrator = get_orchestrator()
            stats = orchestrator.storage.get_statistics()

            click.echo("📊 System Statistics")
            click.echo("=" * 50)

            click.echo(f"📁 Projects: {stats['total_projects']}")
            if stats['projects_by_status']:
                for status, count in stats['projects_by_status'].items():
                    status_icon = {
                        'pending': '⏳',
                        'in_progress': '🔄',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(status, '❓')
                    click.echo(f"   {status_icon} {status}: {count}")

            click.echo(f"\n🔧 Project Types:")
            for ptype, count in stats.get('projects_by_type', {}).items():
                click.echo(f"   • {ptype}: {count}")

            click.echo(f"\n💻 Languages:")
            for lang, count in stats.get('projects_by_language', {}).items():
                click.echo(f"   • {lang}: {count}")

            click.echo(f"\n📋 Tasks: {stats['total_tasks']}")
            if stats['tasks_by_status']:
                for status, count in stats['tasks_by_status'].items():
                    status_icon = {
                        'pending': '⏳',
                        'in_progress': '🔄',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(status, '❓')
                    click.echo(f"   {status_icon} {status}: {count}")

            logger.info("System statistics displayed")

        except Exception as e:
            click.echo(f"❌ Failed to get statistics: {str(e)}")
            logger.error(f"Failed to get statistics: {str(e)}")

    asyncio.run(show_statistics())


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information"""
    click.echo("🤖 AI Test Orchestrator v0.1.0-MVP")
    click.echo("Components:")
    click.echo("  • Agent Orchestrator ✅")
    click.echo("  • API Agent (simulated) 🔄")
    click.echo("  • DevOps Agent (simulated) 🔄")
    click.echo("  • UI Agent (planned) ⏳")
    click.echo("  • Database Agent (planned) ⏳")


if __name__ == '__main__':
    cli()