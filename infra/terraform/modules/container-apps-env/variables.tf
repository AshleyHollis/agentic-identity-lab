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

variable "log_analytics_workspace_id" {
  type        = string
  description = "Log Analytics workspace resource ID to link to this environment (optional)."
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply when applicable."
  default     = {}
}
