param(
    [string]$STORAGE_ACCOUNT_NAME,
    [string]$RESOURCE_GROUP_NAME,
    [string]$LOCATION,
    [string]$BLOB_CONTAINER_NAME,
    [string]$VIRTUAL_NETWORK_NAME,
    [string]$PRIVATE_ENDPOINT_SUBNET_NAME,
    [string]$PUBLIC_NETWORK_ACCESS = "Enabled"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$VerbosePreference = 'Continue'
$InformationPreference = 'Continue'

Write-Information "Creating storage account $STORAGE_ACCOUNT_NAME"
$storageAccount = $(az storage account create `
  --name $STORAGE_ACCOUNT_NAME `
  --resource-group $RESOURCE_GROUP_NAME `
  --location $LOCATION `
  --sku Standard_LRS `
  --kind StorageV2 `
  --public-network-access $PUBLIC_NETWORK_ACCESS) | ConvertFrom-Json

Write-Information "Creating blob container $BLOB_CONTAINER_NAME"
$blobContainer = $(az storage container create `
  --name $BLOB_CONTAINER_NAME `
  --account-name $STORAGE_ACCOUNT_NAME) | ConvertFrom-Json

# Create private endpoint for storage account (blob service)
Write-Information "Creating private endpoint for Storage Account $STORAGE_ACCOUNT_NAME (blob)"
$blobPrivateEndpointParams = @{
    RESOURCE_GROUP_NAME            = $RESOURCE_GROUP_NAME
    PRIVATE_CONNECTION_RESOURCE_ID = $storageAccount.id
    SUBNET_NAME                    = $PRIVATE_ENDPOINT_SUBNET_NAME
    GROUP_ID                       = "blob"
    VIRTUAL_NETWORK_NAME           = $VIRTUAL_NETWORK_NAME
    RESOURCE_NAME                  = $STORAGE_ACCOUNT_NAME
    TYPE                           = "Microsoft.Storage/storageAccounts"
}
$storageAccountBlobPrivateEndpoint = & "$PSScriptRoot/private_endpoint.ps1" @blobPrivateEndpointParams

# Create private endpoint for storage account (file service)
Write-Information "Creating private endpoint for Storage Account $STORAGE_ACCOUNT_NAME (file)"
$filePrivateEndpointParams = @{
    RESOURCE_GROUP_NAME            = $RESOURCE_GROUP_NAME
    PRIVATE_CONNECTION_RESOURCE_ID = $storageAccount.id
    SUBNET_NAME                    = $PRIVATE_ENDPOINT_SUBNET_NAME
    GROUP_ID                       = "file"
    VIRTUAL_NETWORK_NAME           = $VIRTUAL_NETWORK_NAME
    RESOURCE_NAME                  = $STORAGE_ACCOUNT_NAME
    TYPE                           = "Microsoft.Storage/storageAccounts"
}
$storageAccountFilePrivateEndpoint = & "$PSScriptRoot/private_endpoint.ps1" @filePrivateEndpointParams

# Create private endpoint for storage account (table service)
Write-Information "Creating private endpoint for Storage Account $STORAGE_ACCOUNT_NAME (table)"
$tablePrivateEndpointParams = @{
    RESOURCE_GROUP_NAME            = $RESOURCE_GROUP_NAME
    PRIVATE_CONNECTION_RESOURCE_ID = $storageAccount.id
    SUBNET_NAME                    = $PRIVATE_ENDPOINT_SUBNET_NAME
    GROUP_ID                       = "table"
    VIRTUAL_NETWORK_NAME           = $VIRTUAL_NETWORK_NAME
    RESOURCE_NAME                  = $STORAGE_ACCOUNT_NAME
    TYPE                           = "Microsoft.Storage/storageAccounts"
}
$storageAccountTablePrivateEndpoint = & "$PSScriptRoot/private_endpoint.ps1" @tablePrivateEndpointParams

# Create private endpoint for storage account (queue service)
Write-Information "Creating private endpoint for Storage Account $STORAGE_ACCOUNT_NAME (queue)"
$queuePrivateEndpointParams = @{
    RESOURCE_GROUP_NAME            = $RESOURCE_GROUP_NAME
    PRIVATE_CONNECTION_RESOURCE_ID = $storageAccount.id
    SUBNET_NAME                    = $PRIVATE_ENDPOINT_SUBNET_NAME
    GROUP_ID                       = "queue"
    VIRTUAL_NETWORK_NAME           = $VIRTUAL_NETWORK_NAME
    RESOURCE_NAME                  = $STORAGE_ACCOUNT_NAME
    TYPE                           = "Microsoft.Storage/storageAccounts"
}
$storageAccountQueuePrivateEndpoint = & "$PSScriptRoot/private_endpoint.ps1" @queuePrivateEndpointParams

return @{
    storageAccount = $storageAccount
    blobContainer = $BLOB_CONTAINER_NAME
    storageAccountBlobPrivateEndpoint = $storageAccountBlobPrivateEndpoint
    storageAccountFilePrivateEndpoint = $storageAccountFilePrivateEndpoint
    storageAccountTablePrivateEndpoint = $storageAccountTablePrivateEndpoint
    storageAccountQueuePrivateEndpoint = $storageAccountQueuePrivateEndpoint
}
