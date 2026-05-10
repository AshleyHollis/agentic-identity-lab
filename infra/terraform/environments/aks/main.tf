locals {
  name_prefix = "agentic-identity-${var.environment}-aks"
}

module "aks" {
  source              = "../../modules/aks"
  cluster_name        = "${local.name_prefix}-cluster"
  location            = var.location
  resource_group_name = var.resource_group_name
  node_count          = var.node_count
  oidc_issuer_enabled = true
  tags                = var.tags
}

module "workload_identity" {
  source              = "../../modules/workload-identity"
  blueprint_client_id = var.blueprint_client_id
  oidc_issuer         = var.oidc_issuer_url
  subject             = var.workload_identity_subject
  audience            = var.workload_identity_audience
}

module "k8s_bootstrap" {
  source               = "../../modules/k8s-bootstrap"
  namespace            = var.k8s_namespace
  service_account_name = var.k8s_service_account_name
  blueprint_client_id  = var.blueprint_client_id
}
