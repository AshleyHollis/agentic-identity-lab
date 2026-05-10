output "namespace" {
  description = "Kubernetes namespace name configured for Agentic Layer workloads."
  value       = var.namespace
}

output "service_account_name" {
  description = "Name of the Kubernetes service account configured for workload identity."
  value       = var.service_account_name
}
