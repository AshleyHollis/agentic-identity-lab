output "name" {
  description = "Container App resource name."
  value       = azurerm_container_app.this.name
}

output "id" {
  description = "Container App resource ID."
  value       = azurerm_container_app.this.id
}

output "fqdn" {
  description = "Container App ingress FQDN (design name per ADR-M6-01). Used by APIM as backend_url."
  value       = try(azurerm_container_app.this.ingress[0].fqdn, "")
}

output "identity_id" {
  description = "Resource ID of the user-assigned managed identity attached to this container app."
  value       = var.managed_identity_id
}

output "latest_revision_fqdn" {
  description = "FQDN of the latest revision (may differ from stable ingress FQDN during blue/green)."
  value       = azurerm_container_app.this.latest_revision_fqdn
}
