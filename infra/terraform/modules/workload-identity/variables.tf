variable "blueprint_client_id" {
  type        = string
  description = "Client ID of the Entra application registration used as the blueprint audience (placeholder: 00000000-0000-0000-0000-000000000201)."
}

variable "oidc_issuer" {
  type        = string
  description = "OIDC issuer URL from the AKS cluster (output of the aks module or top-level variable)."
}

variable "subject" {
  type        = string
  description = "Federated credential subject claim in the form system:serviceaccount:<namespace>:<service-account-name>."
}

variable "audience" {
  type        = string
  description = "Token audience for the federated credential exchange."
  default     = "api://AzureADTokenExchange"
}
