from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient

SUBSCRIPTION_ID = "a5ce5ea7-6aba-4b4e-b0d7-bbbe8aec91d0"  # Replace with your subscription ID
RESOURCE_GROUP = "TestCIDRAgentRG"
LOCATION = "eastus"
VNET_NAME = "TestCIDRAgentVNet"
SUBNETS = [
    {"name": "default", "prefix": "10.1.0.0/24"},
    {"name": "delegated", "prefix": "10.1.1.0/24", "delegation": {
        "name": "webappdelegation",
        "service_name": "Microsoft.Web/serverFarms"
    }},
]

credential = DefaultAzureCredential()
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)

# Create resource group
resource_client.resource_groups.create_or_update(RESOURCE_GROUP, {"location": LOCATION})

# Create VNet
vnet_params = {
    "location": LOCATION,
    "address_space": {"address_prefixes": ["10.1.0.0/16"]},
}
network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP, VNET_NAME, vnet_params).result()

# Create subnets
for subnet in SUBNETS:
    subnet_params = {"address_prefix": subnet["prefix"]}
    if "delegation" in subnet:
        subnet_params["delegations"] = [{
            "name": subnet["delegation"]["name"],
            "service_name": subnet["delegation"]["service_name"]
        }]
    network_client.subnets.begin_create_or_update(
        RESOURCE_GROUP, VNET_NAME, subnet["name"], subnet_params
    ).result()

print("Test VNets and subnets created.") 