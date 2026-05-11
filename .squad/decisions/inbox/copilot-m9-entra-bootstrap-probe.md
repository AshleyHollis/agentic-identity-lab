### 2026-05-11: M9 Entra bootstrap protected probe
**By:** Copilot  
**Scope:** Protected deploy probe for real strict/live Entra API audience bootstrap and OBO wiring.

**Result:** Blocked at Entra app bootstrap. Protected deploy run `25648744951` reached the deploy identity and Terraform apply boundary, but `tools/ci/m9_entra_app_bootstrap.py` failed on the first `az ad app list` call. This confirms the deploy identity can authenticate to Azure but lacks the Microsoft Graph application permissions required to read/create/update app registrations.

**No live E2E success claimed:** The run did not reach Terraform apply, app rollout, browser smoke, Azure Monitor positive proof, or final shutdown verification for the real delegated path.

**Remaining unblockers:** Grant the protected deploy identity Microsoft Graph application registration permissions sufficient for idempotent app bootstrap, then provide or generate the BFF and Agent Execution OBO client credentials under protected execution before rerunning the live deploy/smoke path.
