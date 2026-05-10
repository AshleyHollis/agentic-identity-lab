variable "name" {
  type        = string
  description = "Application Insights resource name."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "log_analytics_workspace_id" {
  type        = string
  description = "Log Analytics workspace resource ID for workspace-based Application Insights."
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to the resource."
  default     = {}
}
