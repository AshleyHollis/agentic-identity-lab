variable "environment" {
  type        = string
  description = "Environment name (dev, test, prod)."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region."
  default     = "eastus"
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID. Use placeholder in public config; supply at deploy time."
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "tenant_id" {
  type        = string
  description = "Azure Entra tenant ID. Use placeholder in public config; supply at deploy time."
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name for this ACA environment."
  default     = "rg-agent-identity-lab-dev-aca"
}

variable "bff_image" {
  type        = string
  description = "BFF container image (registry/image:tag). Set at deploy time."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "bff_target_port" {
  type        = number
  description = "BFF container ingress target port. The live workflow may use 80 for the public bootstrap placeholder before image rollout switches to 8000."
  default     = 8000
}

variable "agent_execution_image" {
  type        = string
  description = "Agent Execution Service container image. Set at deploy time."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "agent_execution_target_port" {
  type        = number
  description = "Agent Execution Service container ingress target port. The live workflow may use 80 for the public bootstrap placeholder before image rollout switches to 8000."
  default     = 8000
}

variable "mcp_image" {
  type        = string
  description = "MCP Protected API container image. Set at deploy time."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "mcp_target_port" {
  type        = number
  description = "MCP Protected API container ingress target port. The live workflow may use 80 for the public bootstrap placeholder before image rollout switches to 8000."
  default     = 8000
}

variable "otel_endpoint" {
  type        = string
  description = "Azure Monitor OTLP ingestion endpoint (https://{region}.otel.monitor.azure.com/v1/traces). Set at deploy time."
  default     = ""
}

variable "apim_sku_name" {
  type        = string
  description = "APIM SKU for the lab. Consumption_0 keeps the protected live lab lower cost than Developer_1."
  default     = "Consumption_0"
}

variable "auth_issuer" {
  type        = string
  description = "Strict auth issuer URL supplied at deploy time."
  default     = "https://login.microsoftonline.com/{tenant_id}/v2.0"
}

variable "auth_jwks_url" {
  type        = string
  description = "Strict auth JWKS URL supplied at deploy time."
  default     = "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
}

variable "trusted_tenants" {
  type        = string
  description = "Comma-separated trusted tenant IDs supplied at deploy time."
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "bff_allowed_audiences" {
  type        = string
  description = "Comma-separated BFF allowed audiences supplied at deploy time."
  default     = "api://agent-identity-lab-dev-bff"
}

variable "agent_execution_allowed_audiences" {
  type        = string
  description = "Comma-separated Agent Execution Service allowed audiences supplied at deploy time."
  default     = "api://agent-identity-lab-dev-agent-execution"
}

variable "mcp_allowed_audiences" {
  type        = string
  description = "Comma-separated MCP Protected API allowed audiences supplied at deploy time."
  default     = "api://agent-identity-lab-dev-mcp"
}

variable "blueprint_audience" {
  type        = string
  description = "Blueprint audience expected by Agent Execution Service in strict mode."
  default     = "api://agent-identity-lab-dev-bff"
}

variable "bff_obo_token_url" {
  type        = string
  description = "OAuth2 token endpoint for BFF OBO exchange to Agent Execution Service."
  default     = ""
}

variable "bff_obo_client_id" {
  type        = string
  description = "Confidential client ID used by BFF for OBO exchange."
  default     = ""
}

variable "bff_obo_client_secret" {
  type        = string
  description = "Confidential client secret used by BFF for OBO exchange."
  sensitive   = true
  default     = ""
}

variable "bff_obo_required_scopes" {
  type        = string
  description = "Space-delimited downstream delegated scopes BFF requests from Agent Execution Service."
  default     = ""
}

variable "agent_execution_obo_token_url" {
  type        = string
  description = "OAuth2 token endpoint for Agent Execution Service OBO exchange to MCP."
  default     = ""
}

variable "agent_execution_obo_client_id" {
  type        = string
  description = "Confidential client ID used by Agent Execution Service for OBO exchange."
  default     = ""
}

variable "agent_execution_obo_client_secret" {
  type        = string
  description = "Confidential client secret used by Agent Execution Service for OBO exchange."
  sensitive   = true
  default     = ""
}

variable "agent_execution_obo_required_scopes" {
  type        = string
  description = "Space-delimited downstream delegated scopes Agent Execution Service requests from MCP."
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to all resources."
  default = {
    project     = "agentic-identity-lab"
    environment = "dev"
    deployment  = "single-tenant-aca"
    milestone   = "M6"
  }
}
