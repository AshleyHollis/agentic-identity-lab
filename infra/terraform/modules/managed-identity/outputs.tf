output "name" {
  description = "User-assigned managed identity name."
  value       = azurerm_user_assigned_identity.this.name
}

output "id" {
  description = "User-assigned managed identity resource ID (alias for identity_id)."
  value       = azurerm_user_assigned_identity.this.id
}

output "identity_id" {
  description = "User-assigned managed identity resource ID (design name per ADR-M6-03)."
  value       = azurerm_user_assigned_identity.this.id
}

output "principal_id" {
  description = "Service principal (object) ID of the managed identity (design name per ADR-M6-03)."
  value       = azurerm_user_assigned_identity.this.principal_id
}

output "client_id" {
  description = "Client ID (application ID) of the managed identity."
  value       = azurerm_user_assigned_identity.this.client_id
}
