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
"""

from . import subscription
from . import resource_groups
from . import compute
from . import networking
from . import authorization
from . import management_groups
from . import app_configuration
from . import app_service
from . import container_registry
from . import active_directory
from . import webapp_deployment
from . import docker
from . import monitoring

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
]
