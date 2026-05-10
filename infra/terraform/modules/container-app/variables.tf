variable "name" {
  type        = string
  description = "Resource name or prefix."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name when applicable."
  default     = null
}

variable "location" {
  type        = string
  description = "Azure region when applicable."
  default     = null
}

variable "container_apps_environment_id" {
  type        = string
  description = "Resource ID of the Container Apps environment."
}

variable "image" {
  type        = string
  description = "Container image to deploy (registry/image:tag)."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "cpu" {
  type        = number
  description = "vCPU allocation per container replica."
  default     = 0.25
}

variable "memory" {
  type        = string
  description = "Memory allocation per container replica (e.g., '0.5Gi')."
  default     = "0.5Gi"
}

variable "managed_identity_id" {
  type        = string
  description = "Resource ID of the user-assigned managed identity to attach (ADR-M6-03)."
}

variable "external_enabled" {
  type        = bool
  description = "Whether to enable external (public) ingress. Default false (internal ACA networking only)."
  default     = false
}

variable "target_port" {
  type        = number
  description = "Container port exposed by the service."
  default     = 8000
}

variable "otel_endpoint" {
  type        = string
  description = "OTLP exporter endpoint (e.g., Azure Monitor OTLP URL). Empty string disables export."
  default     = ""
}

variable "env_vars" {
  type        = map(string)
  description = "Additional non-secret environment variables for the container."
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply when applicable."
  default     = {}
}
