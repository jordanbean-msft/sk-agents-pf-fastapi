param(
    [string]$EVENT_HUB_NAMESPACE_NAME,
    [string]$RESOURCE_GROUP_NAME,
    [string]$LOCATION,
    [string]$PUBLIC_NETWORK_ACCESS,
    [string]$MANAGED_IDENTITY_ID,
    [string]$EVENT_HUB_NAME,
    [string]$EVENT_HUB_CONSUMER_GROUP_NAME,
    [string]$VIRTUAL_NETWORK_PRIVATE_ENDPOINT_SUBNET_NAME,
    [string]$VIRTUAL_NETWORK_NAME
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$VerbosePreference = 'Continue'
$InformationPreference = 'Continue'

# Create Event Hub namespace
Write-Information "Creating Event Hub namespace $EVENT_HUB_NAMESPACE_NAME"
$eventHubNamespace = $(az eventhubs namespace create `
  --name $EVENT_HUB_NAMESPACE_NAME `
  --resource-group $RESOURCE_GROUP_NAME `
  --location $LOCATION `
  --sku Standard `
  --public-network-access $PUBLIC_NETWORK_ACCESS `
  --mi-user-assigned $MANAGED_IDENTITY_ID) | ConvertFrom-Json

# Create Event Hub
Write-Information "Creating Event Hub $EVENT_HUB_NAME"
$eventHub = $(az eventhubs eventhub create --name $EVENT_HUB_NAME `
  --resource-group $RESOURCE_GROUP_NAME `
  --namespace-name $EVENT_HUB_NAMESPACE_NAME) | ConvertFrom-Json

# Create Event Hub consumer group
Write-Information "Creating Event Hub consumer group $EVENT_HUB_CONSUMER_GROUP_NAME"
$eventHubConsumerGroup = $(az eventhubs eventhub consumer-group create --name $EVENT_HUB_CONSUMER_GROUP_NAME `
  --resource-group $RESOURCE_GROUP_NAME `
  --namespace-name $EVENT_HUB_NAMESPACE_NAME `
  --eventhub-name $EVENT_HUB_NAME) | ConvertFrom-Json

# Create private endpoint for Event Hub namespace using the private_endpoint.ps1 module
Write-Information "Creating private endpoint for Event Hub namespace $EVENT_HUB_NAMESPACE_NAME"
$privateEndpointParams = @{
    RESOURCE_GROUP_NAME                = $RESOURCE_GROUP_NAME
    PRIVATE_CONNECTION_RESOURCE_ID     = $eventHubNamespace.id
    SUBNET_NAME                        = $VIRTUAL_NETWORK_PRIVATE_ENDPOINT_SUBNET_NAME
    GROUP_ID                           = "namespace"
    VIRTUAL_NETWORK_NAME               = $VIRTUAL_NETWORK_NAME
    RESOURCE_NAME                      = $EVENT_HUB_NAMESPACE_NAME
    TYPE                               = "Microsoft.EventHub/namespaces"
}
$eventHubNamespacePrivateEndpoint = & "$PSScriptRoot/private_endpoint.ps1" @privateEndpointParams

# Return all created resources as a hashtable
return @{ 
    eventHubNamespace = $eventHubNamespace
    eventHub = $eventHub
    eventHubConsumerGroup = $eventHubConsumerGroup
    eventHubNamespacePrivateEndpoint = $eventHubNamespacePrivateEndpoint
}