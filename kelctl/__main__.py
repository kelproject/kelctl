import collections
import json
import os
import sys

import click
import yaml

from kel.cluster import (
    Cluster,
    KubeDNS,
    KelSystem,
    Router,
    ApiCache,
    ApiDatabase,
    ApiWeb,
)

from . import configure


@click.group()
@click.option("--version", "show_version", is_flag=True, default=False, help="Show version and exit.")
def cli(show_version):
    if show_version:
        click.echo("kelctl v0.0.1")
        sys.exit(0)


@cli.command("configure")
@click.option(
    "--name",
    help="Name of cluster to configure.",
)
@click.option(
    "--domain",
    help="Domain of cluster to configure.",
)
@click.option(
    "--managed-by",
    "managed_by",
    default="kelproject.com",
    help="Entity whom manages the cluster.",
)
@click.option(
    "--channel",
    default="dev",
    help="Release channel to configure.",
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
    help="[Layer 0] GCE Project ID.",
)
@click.option(
    "--gce-region",
    "gce_region",
    help="[Layer 0] GCE region.",
)
@click.option(
    "--gce-zone",
    "gce_zone",
    help="[Layer 0] GCE zone.",
)
@click.option(
    "--master-ip",
    help="IP address of Kubernetes master.",
)
@click.option(
    "--pod-network",
    default="192.168.0.0/16",
    help="IP address network for Kubernetes pod network.",
)
@click.option(
    "--service-network",
    default="10.96.0.0/12",
    help="IP address network for Kubernetes service network.",
)
@click.option(
    "--dns-service-ip",
    default=None,
    help="IP address for Kubernetes kube-dns service.",
)
@click.option(
    "--identity-url",
    default="https://identity.kelproject.com",
    help="[Layer 1] URL for identity service.",
)
@click.option(
    "--api-subdomain",
    default="api",
    help="[Layer 1] Subdomain to use for API (relative to cluster.domain)",
)
@click.option(
    "--router-ip",
    help="[Layer 1] IP to use for HTTP/TLS routing.",
)
@click.option(
    "--api-cache-disk-type",
    default="pd-standard",
    help="[Layer 1 / GCE] API cache disk type (pd-ssd or pd-standard; pd-standard is default).",
)
@click.option(
    "--api-cache-disk-size",
    default=100,
    type=int,
    help="[Layer 1 / GCE] API cache disk size (in GB; 100 is default).",
)
@click.option(
    "--api-database-disk-type",
    default="pd-standard",
    help="[Layer 1 / GCE] API database disk type (pd-ssd or pd-standard; pd-standard is default).",
)
@click.option(
    "--api-database-disk-size",
    default=100,
    type=int,
    help="[Layer 1 / GCE] API database disk size (in GB; 100 is default).",
)
def cmd_configure(name, domain, managed_by, channel, layer, provider, gce_project_id, gce_region, gce_zone, master_ip, pod_network, service_network, dns_service_ip, identity_url, api_subdomain, router_ip, api_cache_disk_size, api_cache_disk_type, api_database_disk_size, api_database_disk_type):
    """
    Configure a Kel cluster.
    """
    if layer is None:
        error("--layer was not given.")
    if layer == "0":
        if os.path.exists("cluster.yml"):
            error("already configured. Delete cluster.yml to re-configure.")
        if name is None:
            error("--name was not given.")
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
            configure.domain(config, domain, managed_by)
            configure.release(config, channel)
            configure.gce(config, gce_project_id, gce_region, gce_zone)
            configure.layer0(config, pod_network, service_network, dns_service_ip)
            configure.resources_std(config, master_ip)
    elif layer == "1":
        if not os.path.exists("cluster.yml"):
            error("no cluster.yml found. Did you configure layer 0?")
        with open("cluster.yml") as fp:
            config = yaml.load(fp.read())
        if "layer-1" in config:
            error("already configured. Remove layer-1 configuration to re-configure.")
        configure.layer1(config, identity_url, api_subdomain, router_ip, api_cache_disk_size, api_cache_disk_type, api_database_disk_size, api_database_disk_type)
    with open("cluster.yml", "w") as fp:
        fp.write(yaml.safe_dump(config, default_flow_style=False))


@cli.command("update-release")
@click.option(
    "--channel",
    help="Release channel.",
)
def update_release(channel):
    """
    Update release manifests.
    """
    if not os.path.exists("cluster.yml"):
        error("no cluster.yml found. Did you configure?")
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    if channel is None:
        channel = config["release"]["channel"]
    current_version = config["release"]["version"]
    configure.release(config, channel)
    if current_version == config["release"]["version"]:
        click.echo("No updates available for {} channel".format(channel))
        sys.exit(0)
    with open("cluster.yml", "w") as fp:
        fp.write(yaml.safe_dump(config, default_flow_style=False))
    click.echo("Updated config to {} in {} channel".format(config["release"]["version"], config["release"]["channel"]))


@cli.command()
def provision():
    """
    Provision Kel Layer 0.
    """
    if not os.path.exists("cluster.yml"):
        error("cluster.yml does not exist. Did you configure?")
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    cluster = Cluster(config)
    click.echo("Provisioning...")
    cluster.create()
    click.echo("Done.")
    with open("cluster.yml", "w") as fp:
        fp.write(yaml.safe_dump(cluster.config, default_flow_style=False))


@cli.command()
def destroy():
    """
    Destroy Kel Layer 0.
    """
    if not os.path.exists("cluster.yml"):
        error("cluster.yml does not exist. Did you configure?")
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    cluster = Cluster(config)
    click.echo("Destroying...")
    cluster.destroy()
    click.echo("Done.")


@cli.command("set-kubectl-credentials")
def set_kubectl_credentials():
    """
    Configure kubectl to use Layer 0.
    """
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    cluster = Cluster(config)
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    if os.path.exists(kubeconfig_path):
        with open(os.path.expanduser("~/.kube/config")) as fp:
            kubeconfig = yaml.load(fp.read())
    else:
        kubeconfig = {}
        os.makedirs(os.path.dirname(kubeconfig_path))
    kubeconfig.setdefault("clusters", []).append(
        {
            "name": cluster.config["name"],
            "cluster": {
                "server": "https://{}".format(cluster.master_ip),
            },
        }
    )
    kubeconfig.setdefault("users", []).append(
        {
            "name": cluster.config["name"],
            "user": {},
        }
    )
    kubeconfig.setdefault("contexts", []).append(
        {
            "name": cluster.config["name"],
            "context": {
                "cluster": cluster.config["name"],
                "user": cluster.config["name"],
            },
        }
    )
    with open(kubeconfig_path, "w") as fp:
        fp.write(yaml.safe_dump(kubeconfig, default_flow_style=False))


COMPONENTS = collections.OrderedDict([
    ("kube-dns", KubeDNS),
    ("kel-system", KelSystem),
    ("router", Router),
    ("api-cache", ApiCache),
    ("api-database", ApiDatabase),
    ("api-web", ApiWeb),
])


@cli.command()
@click.option(
    "--component",
    "-c",
    help="Specify component to bring online.",
    multiple=True,
)
def up(component):
    """
    Bring Layer 1 online.
    """
    if not os.path.exists("cluster.yml"):
        error("cluster.yml does not exist. Did you configure?")
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    cluster = Cluster(config)
    if not component:
        components = COMPONENTS.values()
    else:
        components = []
        for c in component:
            try:
                components.append(COMPONENTS[c])
            except KeyError:
                error("\"{}\" is not an available component.".format(c))
    for Component in components:
        Component(cluster).create()
    click.echo("Done.")


@cli.command("show-obj")
@click.argument("group")
@click.argument("manifest")
@click.argument("kind")
def show_obj(group, manifest, kind):
    """
    Write a Layer 1 object to stdout.
    """
    if not os.path.exists("cluster.yml"):
        error("cluster.yml does not exist. Did you configure?")
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    cluster = Cluster(config)
    Resource = COMPONENTS.get(manifest)
    if Resource is None:
        click.echo('No component named "{}"'.format(manifest))
        sys.exit(1)
    objs = Resource(cluster).get_api_objs(group, manifest)[kind]
    for obj in objs:
        click.echo(json.dumps(obj.obj, indent=2))


@cli.command("startup-script")
@click.argument("component")
def startup_script(component):
    if not os.path.exists("cluster.yml"):
        error("cluster.yml does not exist. Did you configure?")
    with open("cluster.yml") as fp:
        config = yaml.load(fp.read())
    cluster = Cluster(config)
    r = cluster.get_provider_resource(component)
    kwargs = {}
    if component == "etcd":
        kwargs["i"] = "0"
    if component == "master":
        cluster.get_provider_resource("etcd")
    print(r.get_startup_script(**kwargs))


def error(msg):
    click.echo("{}: {}".format(click.style("Error", fg="red"), msg))
    sys.exit(1)
