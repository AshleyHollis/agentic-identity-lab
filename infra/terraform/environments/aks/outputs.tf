output "aks_cluster_id" {
  description = "Resource ID of the provisioned AKS cluster. Null until aks module resources are implemented."
  value       = module.aks.cluster_id
}

output "oidc_issuer_url" {
  description = "OIDC issuer URL of the AKS cluster. Null until aks module resources are implemented."
  value       = module.aks.oidc_issuer_url
}

output "kube_config" {
  description = "Kubernetes cluster configuration. Null until aks module resources are implemented."
  value       = module.aks.kube_config
  sensitive   = true
}

output "federated_credential_id" {
  description = "Resource ID of the Entra federated identity credential. Null until workload-identity module resources are implemented."
  value       = module.workload_identity.federated_credential_id
}

output "k8s_namespace" {
  description = "Kubernetes namespace configured for Agentic Layer workloads."
  value       = module.k8s_bootstrap.namespace
}

output "k8s_service_account_name" {
  description = "Kubernetes service account name configured for workload identity."
  value       = module.k8s_bootstrap.service_account_name
}
