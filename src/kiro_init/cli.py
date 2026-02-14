import typer
from pathlib import Path
from typing import Optional
from .validators import validate_project_name
from .generator import generate_project

app = typer.Typer(name="kiro-init", help="Scaffold KIRO v05 projects", add_completion=False)

@app.command()
def main(
    project_name: Optional[str] = typer.Option(None, "--project-name", "-n", help="Project name (kebab-case)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite .kiro/ if exists"),
):
    """Initialize KIRO v05 project (7 agents, 8 steering files, swarm_state.md)"""
    try:
        if not project_name:
            project_name = Path.cwd().name
            typer.echo(f"Using: {project_name}")
        project_name = validate_project_name(project_name)
        generate_project(project_name, force=force)
    except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as e:
        typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
