variable "namespace" {
  type        = string
  description = "Kubernetes namespace for Agentic Layer workloads."
}

variable "service_account_name" {
  type        = string
  description = "Name of the Kubernetes service account annotated for workload identity."
}

variable "blueprint_client_id" {
  type        = string
  description = "Client ID of the Entra blueprint application; written as a service account annotation for the Azure Workload Identity webhook."
}
