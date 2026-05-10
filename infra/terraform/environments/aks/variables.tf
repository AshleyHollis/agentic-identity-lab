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
  description = "Resource group name for AKS resources."
  default     = "rg-agentic-identity-dev-aks"
}

variable "node_count" {
  type        = number
  description = "Number of nodes in the AKS default node pool."
  default     = 1
}

variable "blueprint_client_id" {
  type        = string
  description = "Client ID of the Entra blueprint application (placeholder by default)."
  default     = "00000000-0000-0000-0000-000000000201"
}

variable "oidc_issuer_url" {
  type        = string
  description = "OIDC issuer URL for the AKS cluster (set after cluster is created; placeholder by default)."
  default     = "https://placeholder.oidc.issuer/00000000-0000-0000-0000-000000000000"
}

variable "workload_identity_subject" {
  type        = string
  description = "Federated credential subject claim (system:serviceaccount:<namespace>:<service-account>)."
  default     = "system:serviceaccount:agentic-lab:agentic-layer-sa"
}

variable "workload_identity_audience" {
  type        = string
  description = "Federated credential audience for workload identity token exchange."
  default     = "api://AzureADTokenExchange"
}

variable "k8s_namespace" {
  type        = string
  description = "Kubernetes namespace for Agentic Layer workloads."
  default     = "agentic-lab"
}

variable "k8s_service_account_name" {
  type        = string
  description = "Name of the Kubernetes service account for the Agentic Layer pod."
  default     = "agentic-layer-sa"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to all resources."
  default = {
    project     = "agentic-identity-lab"
    environment = "dev"
    deployment  = "aks"
  }
}
