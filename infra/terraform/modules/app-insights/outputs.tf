output "name" {
  description = "Application Insights resource name."
  value       = azurerm_application_insights.this.name
}

output "id" {
  description = "Application Insights resource ID."
  value       = azurerm_application_insights.this.id
}

output "app_id" {
  description = "Application ID (instrumentation key alias, used for OTLP resource attribution)."
  value       = azurerm_application_insights.this.app_id
}

output "instrumentation_key" {
  description = "Application Insights instrumentation key. Sensitive — not committed to state."
  value       = azurerm_application_insights.this.instrumentation_key
  sensitive   = true
}

output "connection_string" {
  description = "Application Insights connection string. Sensitive — not committed to state."
  value       = azurerm_application_insights.this.connection_string
  sensitive   = true
}
