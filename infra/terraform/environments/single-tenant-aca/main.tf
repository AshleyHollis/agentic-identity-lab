# M6 ACA deployment baseline — single-tenant-aca environment
# Default path per ADR-M6-01. AKS optional skeleton in environments/aks/ is unchanged.
#
# No terraform apply is run from this public repository (NFR-02).
# Run: terraform init -backend=false && terraform validate
#
# Placeholder values only. Supply real values via tfvars at deploy time (not committed).

locals {
  name_prefix = "agent-identity-lab-${var.environment}"
}

module "resource_group" {
  source   = "../../modules/resource-group"
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

module "log_analytics" {
  source              = "../../modules/log-analytics"
  name                = "${local.name_prefix}-logs"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

# T02: workspace-based App Insights — OTLP ingestion endpoint swap (ADR-M6-02).
module "app_insights" {
  source                     = "../../modules/app-insights"
  name                       = "${local.name_prefix}-appi"
  resource_group_name        = module.resource_group.name
  location                   = var.location
  log_analytics_workspace_id = module.log_analytics.workspace_id
  tags                       = var.tags
}

module "container_apps_env" {
  source                     = "../../modules/container-apps-env"
  name                       = "${local.name_prefix}-acae"
  resource_group_name        = module.resource_group.name
  location                   = var.location
  log_analytics_workspace_id = module.log_analytics.workspace_id
  tags                       = var.tags
}

# T05: user-assigned managed identity per service (ADR-M6-03, Trinity C2).
module "managed_identity_bff" {
  source              = "../../modules/managed-identity"
  name                = "${local.name_prefix}-id-bff"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "managed_identity_agent_execution" {
  source              = "../../modules/managed-identity"
  name                = "${local.name_prefix}-id-agent-execution"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "managed_identity_mcp_protected_api" {
  source              = "../../modules/managed-identity"
  name                = "${local.name_prefix}-id-mcp"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

# T03: container app per service — AUTH_MODE=strict hardcoded in module.
module "container_app_bff" {
  source                        = "../../modules/container-app"
  name                          = "${local.name_prefix}-bff"
  resource_group_name           = module.resource_group.name
  location                      = var.location
  container_apps_environment_id = module.container_apps_env.environment_id
  image                         = var.bff_image
  managed_identity_id           = module.managed_identity_bff.identity_id
  external_enabled              = true
  otel_endpoint                 = var.otel_endpoint
  env_vars = {
    SERVICE_NAME      = "identity-lab-bff"
    AUTH_ISSUER       = var.auth_issuer
    AUTH_JWKS_URL     = var.auth_jwks_url
    TRUSTED_TENANTS   = var.trusted_tenants
    ALLOWED_AUDIENCES = var.bff_allowed_audiences
    REQUIRED_SCOPES   = "mcp.access"
  }
  tags = var.tags
}

module "container_app_agent_execution" {
  source                        = "../../modules/container-app"
  name                          = "${local.name_prefix}-agent"
  resource_group_name           = module.resource_group.name
  location                      = var.location
  container_apps_environment_id = module.container_apps_env.environment_id
  image                         = var.agent_execution_image
  managed_identity_id           = module.managed_identity_agent_execution.identity_id
  otel_endpoint                 = var.otel_endpoint
  env_vars = {
    SERVICE_NAME            = "identity-lab-agent-execution"
    AUTH_ISSUER             = var.auth_issuer
    AUTH_JWKS_URL           = var.auth_jwks_url
    TRUSTED_TENANTS         = var.trusted_tenants
    ALLOWED_AUDIENCES       = var.agent_execution_allowed_audiences
    REQUIRED_SCOPES         = "mcp.access,mcp.write"
    BLUEPRINT_AUDIENCE      = var.blueprint_audience
    OBO_DOWNSTREAM_AUDIENCE = var.mcp_allowed_audiences
    OBO_REQUIRED_SCOPES     = "mcp.access,mcp.write"
  }
  tags = var.tags
}

module "container_app_mcp_protected_api" {
  source                        = "../../modules/container-app"
  name                          = "${local.name_prefix}-mcp"
  resource_group_name           = module.resource_group.name
  location                      = var.location
  container_apps_environment_id = module.container_apps_env.environment_id
  image                         = var.mcp_image
  managed_identity_id           = module.managed_identity_mcp_protected_api.identity_id
  otel_endpoint                 = var.otel_endpoint
  env_vars = {
    SERVICE_NAME      = "identity-lab-mcp-protected-api"
    AUTH_ISSUER       = var.auth_issuer
    AUTH_JWKS_URL     = var.auth_jwks_url
    TRUSTED_TENANTS   = var.trusted_tenants
    ALLOWED_AUDIENCES = var.mcp_allowed_audiences
    REQUIRED_SCOPES   = "mcp.access,mcp.write"
  }
  tags = var.tags
}

# T04: APIM wired to BFF FQDN. C2: APIM MI must not substitute delegated user token.
module "apim" {
  source              = "../../modules/apim"
  name                = "${local.name_prefix}-apim"
  resource_group_name = module.resource_group.name
  location            = var.location
  backend_url         = "https://${module.container_app_bff.fqdn}"
  sku_name            = var.apim_sku_name
  tags                = var.tags
}

# =============================================================================
# T05: Role assignment placeholders — apply post-M6 with live subscription scope.
# These are commented out because role assignments require a real subscription ID
# and are not applied from this public repository (NFR-02).
#
# resource "azurerm_role_assignment" "agent_execution_obo" {
#   scope                = "/subscriptions/{subscription-id}/resourceGroups/${var.resource_group_name}"
#   role_definition_name = "Managed Identity Operator"
#   principal_id         = module.managed_identity_agent_execution.principal_id
# }
#
# resource "azurerm_role_assignment" "bff_app_insights" {
#   scope                = "/subscriptions/{subscription-id}/resourceGroups/${var.resource_group_name}"
#   role_definition_name = "Monitoring Metrics Publisher"
#   principal_id         = module.managed_identity_bff.principal_id
# }
#
# resource "azurerm_role_assignment" "agent_execution_app_insights" {
#   scope                = "/subscriptions/{subscription-id}/resourceGroups/${var.resource_group_name}"
#   role_definition_name = "Monitoring Metrics Publisher"
#   principal_id         = module.managed_identity_agent_execution.principal_id
# }
#
# resource "azurerm_role_assignment" "mcp_app_insights" {
#   scope                = "/subscriptions/{subscription-id}/resourceGroups/${var.resource_group_name}"
#   role_definition_name = "Monitoring Metrics Publisher"
#   principal_id         = module.managed_identity_mcp_protected_api.principal_id
# }
# =============================================================================
