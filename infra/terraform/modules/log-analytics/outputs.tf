output "name" {
  description = "Log Analytics workspace name."
  value       = azurerm_log_analytics_workspace.this.name
}

output "id" {
  description = "Log Analytics workspace resource ID (alias for workspace_id)."
  value       = azurerm_log_analytics_workspace.this.id
}

output "workspace_id" {
  description = "Log Analytics workspace resource ID (design name per ADR-M6-01)."
  value       = azurerm_log_analytics_workspace.this.id
}
