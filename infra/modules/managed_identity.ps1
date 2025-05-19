param(
    [string]$MANAGED_IDENTITY_NAME,
    [string]$RESOURCE_GROUP_NAME,
    [string]$LOCATION
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$VerbosePreference = 'Continue'
$InformationPreference = 'Continue'

Write-Information "Creating managed identity $MANAGED_IDENTITY_NAME"
$managedIdentity = $(az identity create `
  --name $MANAGED_IDENTITY_NAME `
  --resource-group $RESOURCE_GROUP_NAME `
  --location $LOCATION) | ConvertFrom-Json

return $managedIdentity
