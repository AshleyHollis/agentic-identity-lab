# =============================================================================
# SECURITY BINDING C2 (Trinity T12, ADR-M6-03):
#
# APIM system-assigned managed identity (declared below) MUST NOT be injected
# as the Authorization header when forwarding requests to the BFF container app.
#
# The delegated user token validated by the ingress policy XML
# (infra/terraform/policies/apim/ingress-validate-user-token.xml) passes through
# to BFF UNCHANGED. APIM does not perform OBO; it does not substitute the user
# token with its own managed identity token.
#
# OBO token exchange is performed exclusively by Agent Execution Service.
# BFF receives the original delegated user token — not an APIM MI token.
#
# The APIM system-assigned identity is reserved for future use (e.g., Key Vault
# access for named values) and is provisioned here per the scaffold only.
# =============================================================================

resource "azurerm_api_management" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  publisher_name      = var.publisher_name
  publisher_email     = var.publisher_email
  sku_name            = var.sku_name
  tags                = var.tags

  # System-assigned identity provisioned for future Key Vault / named value access.
  # SECURITY BINDING C2: This identity MUST NOT appear in any Authorization header
  # forwarded to BFF. See comment block above.
  identity {
    type = "SystemAssigned"
  }
}

# APIM backend — points to BFF Container App ingress FQDN.
# backend_url is supplied at deploy time via tfvars (not committed).
# Ingress JWT policy: infra/terraform/policies/apim/ingress-validate-user-token.xml
resource "azurerm_api_management_backend" "bff" {
  name                = "bff-backend"
  resource_group_name = var.resource_group_name
  api_management_name = azurerm_api_management.this.name
  protocol            = "http"
  url                 = var.backend_url
}
