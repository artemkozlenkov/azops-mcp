"""Azure infrastructure management tools organized by logical category.

Modules grouped by Azure service area:

  _clients             – Shared auth & Azure SDK client factories
  subscription         – Subscription, auth, tenants, locations
  resource_groups      – Resource groups, tags, locks, activity log
  compute              – VMs, VMSS, resource listing
  storage              – (via compute.list_resources for now)
  networking           – VNets, subnets, peerings
  authorization        – RBAC roles & assignments
  management_groups    – Management group hierarchy
  app_configuration    – App Configuration stores & key-values
  app_service          – App Service plans & web apps (basic CRUD)
  container_registry   – Azure Container Registry (ACR)
  active_directory     – Azure AD / Entra ID
  webapp_deployment    – Web App for Containers deployment
  docker               – Local Docker container runtime
  monitoring           – System metrics & health
  billing              – Azure Billing and Cost Management
"""

from . import (
    active_directory,
    app_configuration,
    app_service,
    authorization,
    billing,
    compute,
    container_registry,
    docker,
    management_groups,
    monitoring,
    networking,
    resource_groups,
    subscription,
    webapp_deployment,
)

__all__ = [
    "subscription",
    "resource_groups",
    "compute",
    "networking",
    "authorization",
    "management_groups",
    "app_configuration",
    "app_service",
    "container_registry",
    "active_directory",
    "webapp_deployment",
    "docker",
    "monitoring",
    "billing",
]
