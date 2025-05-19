$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$VerbosePreference = 'Continue'
$InformationPreference = 'Continue'

$RESOURCE_GROUP_NAME = "rg-sk-agents-pf-fastapi"
$LOCATION = "eastus2"

$EVENT_HUB_NAMESPACE_NAME = "ehn-sk-agents-pf-fastapi-eus2-dev"
$EVENT_HUB_NAME = "alarm-events"
$EVENT_HUB_CONSUMER_GROUP_NAME = "agent-alarm-events"

$MANAGED_IDENTITY_NAME = "mi-sk-agents-pf-fastapi"

$PUBLIC_NETWORK_ACCESS = "Enabled"
$VIRTUAL_NETWORK_NAME = "vnet-sk-agents-pf-fastapi"
$VIRTUAL_NETWORK_PRIVATE_ENDPOINT_SUBNET_NAME = "private-endpoint"
$VIRTUAL_NETWORK_CONTAINER_APP_SUBNET_NAME = "container-app"

$STORAGE_ACCOUNT_NAME = "saskagentspffastapi"
$EVENT_HUB_CHECKPOINT_CONTAINER_NAME = "event-hub-checkpoint-container"

# Create managed identity
$managedIdentityParams = @{
    MANAGED_IDENTITY_NAME = $MANAGED_IDENTITY_NAME
    RESOURCE_GROUP_NAME   = $RESOURCE_GROUP_NAME
    LOCATION              = $LOCATION
}
$managedIdentity = & ./modules/managed_identity.ps1 @managedIdentityParams

# Create Event Hub namespace, Event Hub, and Consumer Group together
$eventHubParams = @{
    EVENT_HUB_NAMESPACE_NAME              = $EVENT_HUB_NAMESPACE_NAME
    RESOURCE_GROUP_NAME                   = $RESOURCE_GROUP_NAME
    LOCATION                              = $LOCATION
    PUBLIC_NETWORK_ACCESS                 = $PUBLIC_NETWORK_ACCESS
    MANAGED_IDENTITY_ID                   = $managedIdentity.id
    EVENT_HUB_NAME                        = $EVENT_HUB_NAME
    EVENT_HUB_CONSUMER_GROUP_NAME         = $EVENT_HUB_CONSUMER_GROUP_NAME
    VIRTUAL_NETWORK_PRIVATE_ENDPOINT_SUBNET_NAME = $VIRTUAL_NETWORK_PRIVATE_ENDPOINT_SUBNET_NAME
    VIRTUAL_NETWORK_NAME                  = $VIRTUAL_NETWORK_NAME
}
$eventHubResults = & ./modules/event_hub_all.ps1 @eventHubParams

$eventHubNamespace = $eventHubResults.eventHubNamespace
$eventHub = $eventHubResults.eventHub
$eventHubConsumerGroup = $eventHubResults.eventHubConsumerGroup

# Create storage account, blob container, and private endpoints
$storageAccountParams = @{
    STORAGE_ACCOUNT_NAME        = $STORAGE_ACCOUNT_NAME
    RESOURCE_GROUP_NAME         = $RESOURCE_GROUP_NAME
    LOCATION                    = $LOCATION
    BLOB_CONTAINER_NAME         = $EVENT_HUB_CHECKPOINT_CONTAINER_NAME
    VIRTUAL_NETWORK_NAME        = $VIRTUAL_NETWORK_NAME
    PRIVATE_ENDPOINT_SUBNET_NAME= $VIRTUAL_NETWORK_PRIVATE_ENDPOINT_SUBNET_NAME
    PUBLIC_NETWORK_ACCESS       = $PUBLIC_NETWORK_ACCESS
}
$storageAccountResults = & ./modules/storage_account.ps1 @storageAccountParams

$storageAccount = $storageAccountResults.storageAccount
$blobContainer = $storageAccountResults.blobContainer

Write-Information ""
Write-Information "EVENT_HUB_FULLY_QUALIFIED_NAMESPACE=$($eventHubNamespace.serviceBusEndpoint)"
Write-Information "EVENT_HUB_NAME=$($eventHub.name)"
Write-Information "EVENT_HUB_CONSUMER_GROUP=$($eventHubConsumerGroup.name)"
Write-Information "BLOB_STORAGE_ACCOUNT_URL=$($storageAccount.primaryEndpoints.blob)"
Write-Information "BLOB_CONTAINER_NAME=$EVENT_HUB_CHECKPOINT_CONTAINER_NAME"