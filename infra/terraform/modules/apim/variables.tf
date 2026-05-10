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

variable "publisher_name" {
  type        = string
  description = "APIM publisher display name."
  default     = "Agent Identity Lab"
}

variable "publisher_email" {
  type        = string
  description = "APIM publisher contact email."
  default     = "admin@example.com"
}

variable "sku_name" {
  type        = string
  description = "APIM SKU (e.g., Developer_1, Premium_1). Developer_1 for non-prod scaffolds."
  default     = "Developer_1"
}

variable "backend_url" {
  type        = string
  description = "Backend URL for the BFF Container App (full https:// FQDN). Set at deploy time via tfvars."
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply when applicable."
  default     = {}
}
