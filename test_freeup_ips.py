from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
import time

SUBSCRIPTION_ID = "a5ce5ea7-6aba-4b4e-b0d7-bbbe8aec91d0"
RESOURCE_GROUP = "TestCIDRAgentFreeUpRG"
LOCATION = "eastus"
VNET_NAME = "TestCIDRFreeUpVNet"
SUBNET_NAME = "testsubnet"

credential = DefaultAzureCredential()
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)

# 1. Create resource group
resource_client.resource_groups.create_or_update(RESOURCE_GROUP, {"location": LOCATION})

# 2. Create VNet
vnet_params = {
    "location": LOCATION,
    "address_space": {"address_prefixes": ["10.2.0.0/16"]},
}
network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP, VNET_NAME, vnet_params).result()

# 3. Create a subnet
subnet_params = {"address_prefix": "10.2.0.0/24"}
network_client.subnets.begin_create_or_update(RESOURCE_GROUP, VNET_NAME, SUBNET_NAME, subnet_params).result()

print("Subnet created. Waiting for propagation...")
time.sleep(10)

# 4. Delete the subnet to simulate freeing up IPs
network_client.subnets.begin_delete(RESOURCE_GROUP, VNET_NAME, SUBNET_NAME).result()
print("Subnet deleted. Waiting for propagation...")
time.sleep(10)

# 5. At this point, the VNet has no subnets and should show up in the 'free up suggestions' in the web UI
print(f"Test VNet '{VNET_NAME}' in resource group '{RESOURCE_GROUP}' should now appear as a candidate for freeing up CIDRs in the web UI.") 