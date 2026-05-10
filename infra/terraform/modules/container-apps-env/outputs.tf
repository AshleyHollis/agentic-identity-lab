output "name" {
  description = "Container Apps environment name."
  value       = azurerm_container_app_environment.this.name
}

output "id" {
  description = "Container Apps environment resource ID (alias for environment_id)."
  value       = azurerm_container_app_environment.this.id
}

output "environment_id" {
  description = "Container Apps environment resource ID (design name per ADR-M6-01)."
  value       = azurerm_container_app_environment.this.id
}
