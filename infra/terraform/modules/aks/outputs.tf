output "cluster_id" {
  description = "Resource ID of the AKS cluster. Null until resources are implemented."
  value       = null
}

output "oidc_issuer_url" {
  description = "OIDC issuer URL of the AKS cluster (used by workload identity federation). Null until resources are implemented."
  value       = null
}

output "kube_config" {
  description = "Kubernetes configuration block for connecting to the cluster. Null until resources are implemented."
  value       = null
  sensitive   = true
}
