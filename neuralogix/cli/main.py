import click
import os
import sys
import json
from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator
from neuralogix.core.packs.loader import PackLoader

@click.group()
@click.version_option(version="0.7.1")
def cli():
    """NeuraLogix VOR: Discrete, auditable cognition runtime."""
    pass

@cli.command()
@click.option("--pack", type=click.Path(exists=True), required=True, help="Path to the corpus pack.")
@click.option("--seed", type=int, default=42, help="Seed for sampling (if --fast is used).")
@click.option("--multi-seed", is_flag=True, help="Run across seeds 0..4 for certification.")
@click.option("--fast", is_flag=True, help="Run a subset of questions.")
def qa(pack, seed, multi_seed, fast):
    """Run Pilot I Grounded QA on a pack."""
    evaluator = PilotIEvaluator(pack)
    seeds = [0, 1, 2, 3, 4] if multi_seed else [seed]
    report = evaluator.run_all(fast=fast, seeds=seeds)
    # The evaluator already prints summaries and writes JSON.

@cli.command()
@click.option("--pack", type=click.Path(exists=True), help="Path to a specific pack to audit.")
@click.option("--fast", is_flag=True, help="Run audit in fast mode (1 seed, subset).")
def audit(pack, fast):
    """Run the certified VOR audit."""
    from neuralogix.core.audit.vor import audit_vor
    packs = [pack] if pack else None
    audit_vor(fast=fast, packs=packs)

@cli.group()
def pack():
    """Pack management utilities."""
    pass

@pack.command("validate")
@click.option("--pack", type=click.Path(exists=True), required=True, help="Path to the pack directory.")
def validate_pack(pack):
    """Validate pack schema and print byte-level hashes."""
    try:
        loader = PackLoader()
        pack_data = loader.load_pack(pack)
        click.echo(f"✅ Pack validated: {pack_data['metadata']['pack_name']} (v{pack_data['metadata']['version']})")
        click.echo("-" * 40)
        for f in pack_data["metadata"]["files"]:
            click.echo(f"{f['path']}: {f['sha256']}")
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)

@cli.group()
def api():
    """API management subcommands."""
    pass

@api.command("serve")
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=8000, help="Port to bind to.")
def serve(host, port):
    """Start the minimal HTTP service (Powered by FastAPI)."""
    import uvicorn
    from neuralogix.api.server import app
    click.echo(f"🚀 Starting NeuraLogix VOR API on {host}:{port}...")
    click.echo("⚠️  Note: This service is for local/demo use and is not production-hardened.")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    cli()
