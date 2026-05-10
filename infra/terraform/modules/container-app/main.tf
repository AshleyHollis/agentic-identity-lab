# AUTH_MODE is hardcoded to "strict" in the container template env block below.
# It MUST NOT be a variable — this prevents accidental mock-mode deployment to ACA.
# See design.md §Security Design and ADR-M6-03.

resource "azurerm_container_app" "this" {
  name                         = var.name
  container_app_environment_id = var.container_apps_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  # ADR-M6-03: user-assigned managed identity per service (Option A).
  identity {
    type         = "UserAssigned"
    identity_ids = [var.managed_identity_id]
  }

  template {
    container {
      name   = var.name
      image  = var.image
      cpu    = var.cpu
      memory = var.memory

      # AUTH_MODE hardcoded to strict — no variable, no override path.
      # AUTH_MODE=mock MUST NOT appear in any deployed container app.
      env {
        name  = "AUTH_MODE"
        value = "strict"
      }

      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = var.otel_endpoint
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Additional env vars (AUTH_ISSUER, AUTH_JWKS_URL, ALLOWED_AUDIENCES, etc.)
      # are injected at deploy time via tfvars and are NOT committed to this repository.
    }
  }

  ingress {
    external_enabled = var.external_enabled
    target_port      = var.target_port

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}
