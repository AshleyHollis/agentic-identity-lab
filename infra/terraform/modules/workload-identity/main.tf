# TODO: Implement workload identity federated credential resources.
#
# Planned resources:
#   - azuread_application_federated_identity_credential.this
#       application_id = var.blueprint_client_id  (Entra app)
#       display_name   = "aks-workload-identity"
#       issuer         = var.oidc_issuer
#       subject        = var.subject
#       audiences      = [var.audience]
#
# All resource bodies are stubs — no live Entra credentials required to validate.
