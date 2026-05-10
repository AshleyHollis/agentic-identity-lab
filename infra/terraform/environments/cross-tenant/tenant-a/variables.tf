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
  description = "Azure subscription ID (placeholder by default)."
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "tenant_id" {
  type        = string
  description = "Azure Entra tenant ID (placeholder by default)."
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
  default     = "rg-agentic-identity-dev-tenant-a"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to resources."
  default = {
    project     = "agentic-identity-lab"
    environment = "dev"
    deployment  = "cross-tenant"
    tenant      = "tenant-a"
  }
}
variable "tenant_name" {
  type        = string
  description = "Tenant label used in names."
  default     = "tenant-a"
}
