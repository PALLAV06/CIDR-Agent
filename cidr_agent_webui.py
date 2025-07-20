import streamlit as st
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
import ipaddress
import os
import pandas as pd

def extract_resource_group_from_id(resource_id):
    parts = resource_id.split("/")
    try:
        rg_index = parts.index("resourceGroups")
        return parts[rg_index + 1]
    except (ValueError, IndexError):
        return None

st.set_page_config(page_title="Azure CIDR Agent", layout="wide")
st.title("Azure CIDR Agent Dashboard")

# Helper to authenticate and create client
def get_network_client(subscription_id):
    credential = DefaultAzureCredential()
    return NetworkManagementClient(credential, subscription_id)

def fetch_subscriptions():
    from azure.mgmt.resource import SubscriptionClient
    credential = DefaultAzureCredential()
    sub_client = SubscriptionClient(credential)
    return [(sub.subscription_id, sub.display_name) for sub in sub_client.subscriptions.list()]

def fetch_vnets_and_subnets(client):
    vnets = list(client.virtual_networks.list_all())
    vnet_data = []
    for vnet in vnets:
        rg_name = extract_resource_group_from_id(vnet.id)
        vnet_name = vnet.name
        vnet_cidrs = vnet.address_space.address_prefixes
        subnets = list(client.subnets.list(rg_name, vnet_name))
        for subnet in subnets:
            subnet_cidr = subnet.address_prefix
            subnet_name = subnet.name
            # Calculate total IPs in subnet
            try:
                net = ipaddress.ip_network(subnet_cidr)
                total_ips = net.num_addresses
            except Exception:
                total_ips = None
            # Used IPs: Not directly available, so set as None (could be fetched with more API calls)
            used_ips = None
            vnet_data.append({
                "VNet Name": vnet_name,
                "VNet CIDR": ", ".join(vnet_cidrs),
                "Subnet Name": subnet_name,
                "Subnet CIDR": subnet_cidr,
                "Total IPs": total_ips,
                "Used IPs": used_ips
            })
    return vnet_data

def fetch_used_cidrs(client):
    used_cidrs = set()
    vnets = client.virtual_networks.list_all()
    for vnet in vnets:
        used_cidrs.update(vnet.address_space.address_prefixes)
        rg_name = extract_resource_group_from_id(vnet.id)
        for subnet in client.subnets.list(rg_name, vnet.name):
            used_cidrs.add(subnet.address_prefix)
    return used_cidrs

def freeup_suggestions(client):
    vnets = list(client.virtual_networks.list_all())
    unused_vnets = []
    for vnet in vnets:
        rg_name = extract_resource_group_from_id(vnet.id)
        subnets = list(client.subnets.list(rg_name, vnet.name))
        if not subnets:
            unused_vnets.append((vnet.name, vnet.address_space.address_prefixes, rg_name))
    return unused_vnets

def suggest_cidr(client, netmask):
    used_cidrs = set(fetch_used_cidrs(client))
    private_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
    ]
    for parent in private_ranges:
        for subnet in parent.subnets(new_prefix=netmask):
            if str(subnet) not in used_cidrs:
                overlap = False
                for used in used_cidrs:
                    if ipaddress.IPv4Network(used).overlaps(subnet):
                        overlap = True
                        break
                if not overlap:
                    return str(subnet)
    return None

def suggest_vnet_cidr(client, subnet_netmask, num_subnets):
    used_cidrs = set(fetch_used_cidrs(client))
    private_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
    ]
    # Calculate the minimum VNet prefix length that can fit num_subnets of subnet_netmask
    needed_addresses = 2 ** (32 - subnet_netmask) * num_subnets
    for parent in private_ranges:
        for vnet_prefix in range(subnet_netmask, parent.prefixlen - 1, -1):
            vnet_block_size = 2 ** (32 - vnet_prefix)
            if vnet_block_size < needed_addresses:
                break
            for vnet in parent.subnets(new_prefix=vnet_prefix):
                # Check if this VNet CIDR is available
                if str(vnet) in used_cidrs:
                    continue
                overlap = False
                for used in used_cidrs:
                    if ipaddress.IPv4Network(used).overlaps(vnet):
                        overlap = True
                        break
                if not overlap:
                    # Check if we can carve out num_subnets subnets of subnet_netmask from this VNet
                    subnets = list(vnet.subnets(new_prefix=subnet_netmask))
                    if len(subnets) >= num_subnets:
                        return str(vnet), [str(s) for s in subnets[:num_subnets]]
    return None, []

def get_vnet_choices(client):
    vnets = list(client.virtual_networks.list_all())
    return [(vnet.name, extract_resource_group_from_id(vnet.id), vnet.address_space.address_prefixes) for vnet in vnets]

def suggest_subnets_in_vnet(client, vnet_cidr, existing_subnet_cidrs, subnet_netmask, num_subnets):
    vnet_network = ipaddress.ip_network(vnet_cidr)
    used_networks = [ipaddress.ip_network(c) for c in existing_subnet_cidrs]
    possible_subnets = [s for s in vnet_network.subnets(new_prefix=subnet_netmask)
                        if not any(s.overlaps(u) for u in used_networks)]
    if len(possible_subnets) >= num_subnets:
        return [str(s) for s in possible_subnets[:num_subnets]]
    return []

def find_unused_subnets(client):
    # Get all NICs and build a set of subnet IDs in use
    nics = list(client.network_interfaces.list_all())
    used_subnet_ids = set()
    for nic in nics:
        for ipconf in nic.ip_configurations:
            if ipconf.subnet and ipconf.subnet.id:
                used_subnet_ids.add(ipconf.subnet.id.lower())
    # Find all subnets and check if they are unused
    unused_subnets = []
    vnets = list(client.virtual_networks.list_all())
    for vnet in vnets:
        rg_name = extract_resource_group_from_id(vnet.id)
        for subnet in client.subnets.list(rg_name, vnet.name):
            if subnet.id.lower() not in used_subnet_ids:
                unused_subnets.append({
                    "VNet Name": vnet.name,
                    "Subnet Name": subnet.name,
                    "Subnet CIDR": subnet.address_prefix,
                    "Resource Group": rg_name
                })
    return unused_subnets

# UI: Subscription selection
st.sidebar.header("Azure Subscription")
subscriptions = fetch_subscriptions()
if not subscriptions:
    st.error("No Azure subscriptions found or authentication failed. Please login with Azure CLI or set up your credentials.")
    st.stop()

sub_ids = {name: sid for sid, name in subscriptions}
selected_sub = st.sidebar.selectbox("Select Subscription", list(sub_ids.keys()))
subscription_id = sub_ids[selected_sub]

client = get_network_client(subscription_id)

# Tabs for features
tab1, tab2, tab3 = st.tabs(["Used CIDRs", "Free Up Suggestions", "Suggest CIDR"])

with tab1:
    st.subheader("VNet and Subnet CIDR Usage Table")
    vnet_data = fetch_vnets_and_subnets(client)
    if vnet_data:
        df = pd.DataFrame(vnet_data)
        st.dataframe(df, use_container_width=True)
        st.subheader("Subnet IP Utilization (Total IPs)")
        chart_df = df[["VNet Name", "Subnet Name", "Total IPs"]].copy()
        chart_df = chart_df.dropna(subset=["Total IPs"])
        chart_df["Label"] = chart_df["VNet Name"] + "/" + chart_df["Subnet Name"]
        st.bar_chart(chart_df.set_index("Label")["Total IPs"])
    else:
        st.info("No VNets or subnets found in this subscription.")

with tab2:
    st.subheader("Suggestions to Free Up CIDRs")
    unused_vnets = freeup_suggestions(client)
    unused_subnets = find_unused_subnets(client)
    if unused_vnets:
        st.write("VNets with no subnets (can be deleted to free CIDRs):")
        st.table(unused_vnets)
    else:
        st.success("No unused VNets found. All CIDRs are in use.")
    if unused_subnets:
        st.write("Subnets with no connected devices (0 IPs used, can be deleted to free IP space):")
        st.table(unused_subnets)
    else:
        st.success("No unused subnets found. All subnets have connected devices.")

with tab3:
    st.subheader("Suggest Optimal CIDR for New VNet or Subnets in Existing VNet")
    vnet_choices = get_vnet_choices(client)
    vnet_options = [f"{name} ({', '.join(cidrs)})" for name, _, cidrs in vnet_choices]
    vnet_options.insert(0, "[Create new VNet]")
    selected_vnet = st.selectbox("Select VNet (or create new)", vnet_options)
    netmask = st.number_input("Subnet Netmask (e.g., 24 for /24)", min_value=8, max_value=30, value=24)
    num_subnets = st.number_input("Number of subnets needed", min_value=1, max_value=256, value=1)
    if st.button("Suggest CIDR"):
        if selected_vnet == "[Create new VNet]":
            if num_subnets == 1:
                suggestion = suggest_cidr(client, netmask)
                if suggestion:
                    st.success(f"Suggested CIDR: {suggestion}")
                else:
                    st.error("No available CIDR found with the given netmask and zero IP wastage.")
            else:
                vnet_cidr, subnets = suggest_vnet_cidr(client, netmask, num_subnets)
                if vnet_cidr:
                    st.success(f"Suggested VNet CIDR: {vnet_cidr}")
                    st.write(f"Subnets of /{netmask} you can create:")
                    st.code("\n".join(subnets))
                else:
                    st.error("No available VNet CIDR found that can fit the requested number of subnets with the given netmask and zero IP wastage.")
        else:
            idx = vnet_options.index(selected_vnet) - 1
            vnet_name, vnet_rg, vnet_cidrs = vnet_choices[idx]
            # For simplicity, use the first CIDR block of the VNet
            vnet_cidr = vnet_cidrs[0]
            subnets = list(client.subnets.list(vnet_rg, vnet_name))
            existing_subnet_cidrs = [s.address_prefix for s in subnets]
            suggested = suggest_subnets_in_vnet(client, vnet_cidr, existing_subnet_cidrs, netmask, num_subnets)
            if suggested:
                st.success(f"Suggested subnets in {vnet_name} ({vnet_cidr}):")
                st.code("\n".join(suggested))
            else:
                st.error(f"No available subnets of /{netmask} found in {vnet_name} ({vnet_cidr}) that do not overlap with existing subnets.") 