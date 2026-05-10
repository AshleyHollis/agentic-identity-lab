# TODO: Implement AKS cluster resources.
#
# Planned resources:
#   - azurerm_kubernetes_cluster.this
#       name                      = var.cluster_name
#       location                  = var.location
#       resource_group_name       = var.resource_group_name
#       oidc_issuer_enabled       = var.oidc_issuer_enabled
#       workload_identity_enabled = true
#       default_node_pool { node_count = var.node_count }
#       tags                      = var.tags
#
# All resource bodies are stubs — no live Azure credentials required to validate.
