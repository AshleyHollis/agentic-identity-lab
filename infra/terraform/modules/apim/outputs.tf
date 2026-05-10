output "name" {
  description = "APIM instance name."
  value       = azurerm_api_management.this.name
}

output "id" {
  description = "APIM instance resource ID."
  value       = azurerm_api_management.this.id
}

output "gateway_url" {
  description = "APIM gateway URL (public endpoint for API consumers)."
  value       = azurerm_api_management.this.gateway_url
}

output "principal_id" {
  description = "System-assigned managed identity principal ID. NOT used in forwarded Authorization headers (C2)."
  value       = azurerm_api_management.this.identity[0].principal_id
}
