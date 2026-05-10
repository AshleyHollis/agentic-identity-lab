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

variable "agent_execution_image" {
  type        = string
  description = "Agent Execution Service container image. Set at deploy time."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "mcp_image" {
  type        = string
  description = "MCP Protected API container image. Set at deploy time."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "otel_endpoint" {
  type        = string
  description = "Azure Monitor OTLP ingestion endpoint (https://{region}.otel.monitor.azure.com/v1/traces). Set at deploy time."
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
