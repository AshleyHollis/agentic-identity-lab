locals {
  name_prefix = "agentic-identity-vendor-${var.environment}"
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
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

module "container_apps_env" {
  source              = "../../modules/container-apps-env"
  name                = "${local.name_prefix}-acae"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

module "container_app" {
  source              = "../../modules/container-app"
  name                = "${local.name_prefix}-app"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}
