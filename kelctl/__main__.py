import os
import sys
import time

import click
import yaml

from . import configure


@click.group()
@click.option("--version", "show_version", is_flag=True, default=False, help="Show version and exit.")
def cli(show_version):
    if show_version:
        click.echo("kelctl v0.0.1")
        sys.exit(0)


@cli.command("generate-keys")
def generate_keys():
    """
    Generate keys to be used in Kel Layer 0.
    """
    click.echo("Generating keys...")
    time.sleep(1)
    click.echo("    admin")
    time.sleep(1)
    click.echo("    admin")
    time.sleep(1)
    click.echo("    admin")
    time.sleep(5)
    click.echo("")
    click.echo("Keys were written to ./keys")
    click.echo("")


@cli.command("configure")
@click.option(
    "--name",
    help="Name of cluster to configure.",
)
@click.option(
    "--channel",
    default="dev",
    help="Name of cluster to configure.",
)
@click.option(
    "--layer",
    type=click.Choice(["0", "1"]),
    help="Kel layer to configure.",
)
@click.option(
    "--provider",
    type=click.Choice(["gce"]),
    help="[Layer 0] Cloud provider to configure.",
)
@click.option(
    "--gce-project-id",
    "gce_project_id",
    help="[Layer 0] GCE Project ID to use.",
)
@click.option(
    "--gce-region",
    "gce_region",
    help="[Layer 0] GCE region to use.",
)
@click.option(
    "--gce-zone",
    "gce_zone",
    help="[Layer 0] GCE zone to use.",
)
def cmd_configure(name, channel, layer, provider, gce_project_id, gce_region, gce_zone):
    """
    Configure a Kel cluster.
    """
    if os.path.exists("cluster.yml"):
        error("already configured. Delete cluster.yml to re-configure.")
    if name is None:
        error("--name was not given.")
    if layer is None:
        error("--layer was not given.")
    if provider is None:
        error("--provider was not given.")
    if provider == "gce":
        if gce_project_id is None:
            error("--gce-project-id was not given.")
        if gce_region is None:
            error("--gce-region was not given.")
        if gce_zone is None:
            error("--gce-zone was not given.")
        config = {}
        configure.name(config, name)
        configure.release(config, channel)
        configure.gce(config, gce_project_id, gce_region, gce_zone)
        configure.resources_std(config)
    with open("cluster.yml", "w") as fp:
        fp.write(yaml.safe_dump(config, default_flow_style=False))


@cli.command()
def provision():
    """
    Provision Kel Layer 0.
    """
    if not os.path.exists("cluster.yml"):
        error("cluster.yml does not exist. Did you configure?")
    click.echo("Provisioning...")
    time.sleep(10)
    click.echo("Done.")


@cli.command("set-kubectl-credentials")
def set_kubectl_credentials():
    """
    Configure kubectl to use Layer 0.
    """
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    if os.path.exists(kubeconfig_path):
        with open(os.path.expanduser("~/.kube/config")) as fp:
            config = yaml.load(fp.read())
    else:
        config = {}
        os.makedirs(os.path.dirname(kubeconfig_path))
    with open(kubeconfig_path, "w") as fp:
        fp.write(yaml.safe_dump(config, default_flow_style=False))


def error(msg):
    click.echo("{}: {}".format(click.style("Error", fg="red"), msg))
    sys.exit(1)
