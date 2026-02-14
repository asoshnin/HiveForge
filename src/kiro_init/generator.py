from pathlib import Path
from datetime import datetime

def generate_project(project_name: str, force: bool = False) -> None:
    cwd = Path.cwd()
    kiro_dir = cwd / ".kiro"
    
    if kiro_dir.exists() and not force:
        raise FileExistsError(f".kiro/ exists. Use --force to overwrite.")
    
    # Create dirs
    (kiro_dir / "agents").mkdir(parents=True, exist_ok=True)
    (kiro_dir / "steering").mkdir(parents=True, exist_ok=True)
    (cwd / ".swarm" / "plan").mkdir(parents=True, exist_ok=True)
    (cwd / ".swarm" / "audit_logs").mkdir(parents=True, exist_ok=True)
    
    template_dir = Path(__file__).parent / "templates"
    
    # Validate templates exist
    if not (template_dir / "agents").exists():
        raise FileNotFoundError(f"Agent templates not found at {template_dir / 'agents'}")
    if not (template_dir / "steering").exists():
        raise FileNotFoundError(f"Steering templates not found at {template_dir / 'steering'}")
    
    # Copy agents
    agents = list((template_dir / "agents").glob("*.md"))
    if len(agents) == 0:
        raise RuntimeError("No agent templates found (expected 7 .md files)")
    for f in agents:
        (kiro_dir / "agents" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    
    # Copy steering
    steering = list((template_dir / "steering").glob("*.md"))
    if len(steering) == 0:
        raise RuntimeError("No steering templates found (expected 8 .md files)")
    for f in steering:
        (kiro_dir / "steering" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    
    # Process swarm_state.md
    swarm_template = template_dir / "swarm_state.md"
    if not swarm_template.exists():
        raise FileNotFoundError(f"swarm_state.md template not found at {swarm_template}")
    swarm = swarm_template.read_text(encoding="utf-8")
    swarm = swarm.replace("{PROJECT_NAME}", project_name)
    swarm = swarm.replace("{ISO_TIMESTAMP}", datetime.utcnow().isoformat() + "Z")
    (cwd / "swarm_state.md").write_text(swarm, encoding="utf-8")
    
    print(f"✅ KIRO v05 '{project_name}' initialized!")
    print(f"📁 .kiro/agents/ ({len(agents)}), .kiro/steering/ ({len(steering)}), swarm_state.md")
    print("\n🚀 Next: Reload Kiro IDE → Fill swarm_state.md → Act as Orchestrator")
