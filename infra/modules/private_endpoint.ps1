param(
    [string]$RESOURCE_GROUP_NAME,
    [string]$PRIVATE_CONNECTION_RESOURCE_ID,
    [string]$SUBNET_NAME,
    [string]$GROUP_ID,
    [string]$VIRTUAL_NETWORK_NAME,
    [string]$RESOURCE_NAME,
    [string]$TYPE
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$VerbosePreference = 'Continue'
$InformationPreference = 'Continue'

Write-Information "Creating private endpoint pe-$RESOURCE_NAME-$GROUP_ID"
$privateEndpoint = $(az network private-endpoint create `
  --connection-name "pe-$RESOURCE_NAME-$GROUP_ID" `
  --name "pe-$RESOURCE_NAME-$GROUP_ID" `
  --resource-group $RESOURCE_GROUP_NAME `
  --private-connection-resource-id $PRIVATE_CONNECTION_RESOURCE_ID `
  --subnet $SUBNET_NAME `
  --group-id $GROUP_ID `
  --vnet-name $VIRTUAL_NETWORK_NAME) | ConvertFrom-Json

# Write-Information "Approving private endpoint connection for $($privateEndpoint.id)"
# az network private-endpoint-connection approve `
#   --resource-group $RESOURCE_GROUP_NAME `
#   --name "pe-$RESOURCE_NAME" `
#   --resource-name $RESOURCE_NAME `
#   --type $TYPE

return $privateEndpoint
