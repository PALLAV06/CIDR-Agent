import typer
from rich.console import Console
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
import ipaddress
import os

app = typer.Typer()
console = Console()

# Helper to authenticate and create client
def get_network_client():
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        console.print("[red]Please set the AZURE_SUBSCRIPTION_ID environment variable.[/red]")
        raise typer.Exit(1)
    credential = DefaultAzureCredential()
    return NetworkManagementClient(credential, subscription_id)

# List all used CIDRs in VNets and Subnets
def fetch_used_cidrs(client):
    used_cidrs = set()
    vnets = client.virtual_networks.list_all()
    for vnet in vnets:
        used_cidrs.update(vnet.address_space.address_prefixes)
        for subnet in client.subnets.list(vnet.resource_group_name, vnet.name):
            used_cidrs.add(subnet.address_prefix)
    return used_cidrs

@app.command()
def show_used_cidrs():
    """Display all currently used CIDRs in Azure."""
    client = get_network_client()
    used_cidrs = fetch_used_cidrs(client)
    console.print("[bold green]Currently used CIDRs:[/bold green]")
    for cidr in sorted(used_cidrs):
        console.print(f"- {cidr}")
    console.print(f"\n[bold]Total in use:[/bold] {len(used_cidrs)}")

@app.command()
def freeup_suggestions():
    """Suggest actions to free up CIDRs."""
    client = get_network_client()
    vnets = list(client.virtual_networks.list_all())
    unused_vnets = []
    for vnet in vnets:
        subnets = list(client.subnets.list(vnet.resource_group_name, vnet.name))
        if not subnets:
            unused_vnets.append(vnet)
    if unused_vnets:
        console.print("[yellow]VNets with no subnets (can be deleted to free CIDRs):[/yellow]")
        for vnet in unused_vnets:
            console.print(f"- {vnet.name} ({vnet.address_space.address_prefixes}) in {vnet.resource_group_name}")
    else:
        console.print("[green]No unused VNets found. All CIDRs are in use.[/green]")

@app.command()
def suggest_cidr(netmask: int = typer.Argument(..., help="Netmask for the new VNet (e.g., 24 for /24)")):
    """Suggest the optimal CIDR for a new VNet with the given netmask, with zero IP wastage."""
    client = get_network_client()
    used_cidrs = set(fetch_used_cidrs(client))
    # Azure private address space
    private_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
    ]
    block_size = 2 ** (32 - netmask)
    for parent in private_ranges:
        for subnet in parent.subnets(new_prefix=netmask):
            if str(subnet) not in used_cidrs:
                # Check for overlap
                overlap = False
                for used in used_cidrs:
                    if ipaddress.IPv4Network(used).overlaps(subnet):
                        overlap = True
                        break
                if not overlap:
                    console.print(f"[bold green]Suggested CIDR:[/bold green] {subnet}")
                    return
    console.print("[red]No available CIDR found with the given netmask and zero IP wastage.[/red]")

if __name__ == "__main__":
    app() 