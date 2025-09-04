#!/usr/bin/env python3
"""
EKS Cluster Validator - Comprehensive AWS EKS Environment Testing Tool

This tool performs comprehensive validation of AWS EKS clusters across different
environments (test, UAT, production) and generates detailed markdown reports.
"""

import click
import sys
import time
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from eks_validator.core.validator import EKSValidator  # noqa: E402
from eks_validator.config.settings import Settings  # noqa: E402
from eks_validator.utils.report_generator import ReportGenerator  # noqa: E402

console = Console()


def setup_logging(verbose: bool):
    """Configure logging based on verbosity level."""
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Also configure rich console for better output
    console.print(
        Panel.fit(
            Text("🚀 EKS Cluster Validator", style="bold blue"),
            title="Starting Validation",
            border_style="blue",
        )
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--config",
    "-c",
    help="Path to configuration file (optional, will use env vars if not provided)",
)
@click.option(
    "--env-only",
    is_flag=True,
    help="Load configuration only from environment variables",
)
@click.pass_context
def cli(ctx, verbose, config, env_only):
    """EKS Cluster Validator - Comprehensive AWS EKS Environment Testing Tool"""
    setup_logging(verbose)

    # Load configuration
    if env_only or not config:
        console.print(
            "[blue]🔧 Loading configuration from environment variables[/blue]"
        )
        try:
            settings = Settings.from_env()
            ctx.obj = {"settings": settings, "verbose": verbose}
        except Exception as e:
            console.print(
                f"[red]❌ Failed to load configuration from environment: {e}[/red]"
            )
            sys.exit(1)
    else:
        config_path = Path(config)
        if not config_path.exists():
            console.print(f"[red]❌ Configuration file not found: {config_path}[/red]")
            console.print(
                "[yellow]💡 Try using --env-only to load from environment "
                "variables[/yellow]"
            )
            sys.exit(1)

        try:
            settings = Settings.from_yaml(config_path)
            ctx.obj = {"settings": settings, "verbose": verbose}
        except Exception as e:
            console.print(f"[red]❌ Failed to load configuration: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.argument("environment", type=click.Choice(["test", "uat", "prod"]))
@click.option("--output", "-o", help="Output file path for the report")
@click.option(
    "--format",
    "-f",
    default="markdown",
    type=click.Choice(["markdown", "json", "html"]),
)
@click.pass_context
def validate(ctx, environment, output, format):
    """Validate EKS cluster for the specified environment"""
    settings = ctx.obj["settings"]

    console.print(f"[blue]🔍 Starting validation for environment: {environment}[/blue]")

    try:
        # Initialize validator
        validator = EKSValidator(settings, environment)

        # Run comprehensive validation
        console.print("[yellow]📊 Running infrastructure checks...[/yellow]")
        infra_results = validator.check_infrastructure()

        console.print("[yellow]🌐 Running networking checks...[/yellow]")
        network_results = validator.check_networking()

        console.print("[yellow]💾 Running storage checks...[/yellow]")
        storage_results = validator.check_storage()

        console.print("[yellow]🔧 Running addon checks...[/yellow]")
        addon_results = validator.check_addons()

        console.print("[yellow]📈 Running monitoring checks...[/yellow]")
        monitoring_results = validator.check_monitoring()

        console.print("[yellow]🚀 Running application checks...[/yellow]")
        app_results = validator.check_applications()

        # Combine all results
        all_results = {
            "infrastructure": infra_results,
            "networking": network_results,
            "storage": storage_results,
            "addons": addon_results,
            "monitoring": monitoring_results,
            "applications": app_results,
        }

        # Generate report
        console.print("[green]📝 Generating report...[/green]")
        report_gen = ReportGenerator()
        env_config = settings.get_environment_config(environment)

        # Generate timestamped report file automatically
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        auto_report_file = f"reports/eks_validation_{environment}_{timestamp}.md"

        report = report_gen.generate_report(all_results, env_config, auto_report_file)

        # Save automatic report
        auto_output_path = Path(auto_report_file)
        auto_output_path.parent.mkdir(parents=True, exist_ok=True)
        auto_output_path.write_text(report)
        console.print(f"[green]✅ Report saved to: {auto_output_path}[/green]")

        # Save to user-specified output if provided
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            console.print(
                f"[green]✅ Additional report saved to: {output_path}[/green]"
            )
        else:
            # Display summary on console
            console.print("\n[bold blue]📊 Validation Summary:[/bold blue]")
            summary = report_gen._generate_summary(all_results)
            console.print(f"Total Checks: {summary['total_checks']}")
            console.print(f"✅ Passed: {summary['passed_checks']}")
            console.print(f"⚠️ Warnings: {summary['warning_checks']}")
            console.print(f"❌ Failed: {summary['failed_checks']}")
            console.print(f"⏭️ Skipped: {summary['skipped_checks']}")
            console.print(f"\n📄 Full report available at: {auto_output_path}")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("environment", type=click.Choice(["test", "uat", "prod"]))
@click.pass_context
def quick_check(ctx, environment):
    """Perform a quick health check of the EKS cluster"""
    settings = ctx.obj["settings"]

    console.print(f"[blue]⚡ Quick check for environment: {environment}[/blue]")

    try:
        validator = EKSValidator(settings, environment)

        # Quick checks
        cluster_status = validator.quick_cluster_check()
        node_status = validator.quick_node_check()

        console.print(f"[green]✅ Cluster Status: {cluster_status}[/green]")
        console.print(f"[green]✅ Node Status: {node_status}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Quick check failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("environment", type=click.Choice(["test", "uat", "prod"]))
@click.option(
    "--component",
    type=click.Choice(["infra", "network", "storage", "addons", "monitoring", "apps"]),
)
@click.pass_context
def check_component(ctx, environment, component):
    """Check a specific component of the EKS cluster"""
    settings = ctx.obj["settings"]

    console.print(
        f"[blue]🔍 Checking {component} for environment: {environment}[/blue]"
    )

    try:
        validator = EKSValidator(settings, environment)

        if component == "infra":
            results = validator.check_infrastructure()
        elif component == "network":
            results = validator.check_networking()
        elif component == "storage":
            results = validator.check_storage()
        elif component == "addons":
            results = validator.check_addons()
        elif component == "monitoring":
            results = validator.check_monitoring()
        elif component == "apps":
            results = validator.check_applications()

        console.print_json(data=results)

    except Exception as e:
        console.print(f"[red]❌ Component check failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def list_environments():
    """List available environments"""
    console.print("[blue]📋 Available Environments:[/blue]")
    console.print("  • test  - Test environment")
    console.print("  • uat   - User Acceptance Testing environment")
    console.print("  • prod  - Production environment")


@cli.command()
def version():
    """Show version information"""
    console.print("[blue]EKS Cluster Validator v1.0.0[/blue]")
    console.print("Built for comprehensive AWS EKS environment validation")


if __name__ == "__main__":
    cli()
