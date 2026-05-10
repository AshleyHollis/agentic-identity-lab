output "resource_group_name" {
  description = "Resource group name for this environment."
  value       = module.resource_group.name
}

output "container_apps_env_name" {
  description = "Container Apps environment name placeholder."
  value       = module.container_apps_env.name
}

output "container_app_name" {
  description = "Container App name placeholder."
  value       = module.container_app.name
}
