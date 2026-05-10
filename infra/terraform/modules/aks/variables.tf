variable "cluster_name" {
  type        = string
  description = "Name of the AKS cluster."
}

variable "location" {
  type        = string
  description = "Azure region in which the AKS cluster is deployed."
}

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group that contains the AKS cluster."
}

variable "node_count" {
  type        = number
  description = "Number of nodes in the default node pool."
  default     = 1
}

variable "oidc_issuer_enabled" {
  type        = bool
  description = "Enable the OIDC issuer on the AKS cluster (required for workload identity)."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to AKS cluster resources."
  default     = {}
}
