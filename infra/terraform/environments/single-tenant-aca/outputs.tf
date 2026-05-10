output "resource_group_name" {
  description = "Resource group name for this ACA environment."
  value       = module.resource_group.name
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace resource ID."
  value       = module.log_analytics.workspace_id
}

output "container_apps_env_name" {
  description = "Container Apps environment name."
  value       = module.container_apps_env.name
}

output "container_apps_environment_id" {
  description = "Container Apps environment resource ID."
  value       = module.container_apps_env.environment_id
}

output "bff_fqdn" {
  description = "BFF container app ingress FQDN."
  value       = module.container_app_bff.fqdn
}

output "agent_execution_fqdn" {
  description = "Agent Execution Service container app ingress FQDN."
  value       = module.container_app_agent_execution.fqdn
}

output "mcp_protected_api_fqdn" {
  description = "MCP Protected API container app ingress FQDN."
  value       = module.container_app_mcp_protected_api.fqdn
}

output "apim_gateway_url" {
  description = "APIM gateway URL (public endpoint for API consumers)."
  value       = module.apim.gateway_url
}

output "managed_identity_bff_principal_id" {
  description = "BFF user-assigned managed identity principal ID."
  value       = module.managed_identity_bff.principal_id
}

output "managed_identity_agent_execution_principal_id" {
  description = "Agent Execution Service user-assigned managed identity principal ID."
  value       = module.managed_identity_agent_execution.principal_id
}

output "managed_identity_mcp_principal_id" {
  description = "MCP Protected API user-assigned managed identity principal ID."
  value       = module.managed_identity_mcp_protected_api.principal_id
}
