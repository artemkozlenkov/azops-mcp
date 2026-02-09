---
title: Tools Reference
layout: default
nav_order: 4
---

# Tools Reference
{: .no_toc }

Complete reference for all 93 tools exposed by azops-mcp, organized by Azure service category.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 1. Health & Status (1 tool)

### `health_check`

Check MCP server health and Azure SDK availability.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | JSON dict with `status`, `dependencies`, `timestamp`, `version` |

Reports which Azure SDK packages are installed (`ok` or `missing`).

---

## 2. Subscription & Authentication (8 tools)

### `list_subscriptions`

List all Azure subscriptions you have access to.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Formatted list of subscription names, IDs, and states |

Marks the currently active subscription with `(current)`.

### `set_subscription`

Set the Azure subscription to use for this session.

| | |
|:--|:--|
| **Parameters** | `subscription_id` (str, required) — UUID format |
| **Returns** | Confirmation with subscription name and state |

Validates the UUID format and clears cached Azure SDK clients so they use the new subscription. Persists for the session only (not written to `.env`).

### `auth_status`

Check Azure authentication status and method.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Authentication method, validity, token expiry, subscription source |

Distinguishes between Service Principal and Azure CLI authentication. Attempts to fetch a token to verify credentials are working.

### `account_show`

Get details of the current Azure subscription (similar to `az account show`).

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Subscription name, ID, tenant ID, state, and environment details |

### `account_clear`

Clear cached Azure credentials and subscription override (similar to `az account clear`).

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Confirmation message |

Resets the runtime subscription override and clears all cached Azure SDK clients and credentials so the next operation re-authenticates from scratch.

### `account_get_access_token`

Get an Azure access token (similar to `az account get-access-token`).

| | |
|:--|:--|
| **Parameters** | `resource` (str, optional, default `https://management.azure.com/.default`) — the resource/scope to obtain a token for |
| **Returns** | Masked token, expiry, subscription, tenant, and resource info |

The full token is masked for security. Useful for verifying credentials and checking token expiry.

### `list_locations`

List all Azure regions available for the subscription.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | List of region names, display names, and types |

### `list_tenants`

List Azure AD tenants you have access to.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Tenant IDs, display names, domains, and types |

---

## 3. Management Groups (2 tools)

### `list_management_groups`

List all Azure management groups.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Management group names, IDs, and types |

### `get_management_group`

Get details of a management group including its children.

| | |
|:--|:--|
| **Parameters** | `group_id` (str, required) |
| **Returns** | Display name, tenant ID, children (subscriptions & child groups) |

---

## 4. RBAC (4 tools)

### `list_role_definitions`

List available Azure role definitions (built-in roles).

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Role names, IDs, and truncated descriptions (max 15) |

### `create_role_assignment`

Create a new role assignment (RBAC).

| | |
|:--|:--|
| **Parameters** | `principal_id` (str, required), `role_definition_name` (str, required), `resource_group` (str, optional), `scope` (str, optional) |
| **Returns** | Assignment details including role, principal, and scope |

### `delete_role_assignment`

Delete a role assignment.

| | |
|:--|:--|
| **Parameters** | `assignment_id` (str, required) |
| **Returns** | Deletion confirmation |

### `list_role_assignments_for_principal`

List role assignments for a specific principal.

| | |
|:--|:--|
| **Parameters** | `principal_id` (str, required), `resource_group` (str, optional) |
| **Returns** | Role assignments for the principal |

---

## 5. Governance (3 tools)

### `list_resource_locks`

List resource locks in subscription or resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Lock names, levels, and notes |

### `list_tags`

List tags in subscription or on a resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Tag key/value pairs or subscription tag names with sample values |

### `get_activity_log`

Get recent Azure activity log (audit log).

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional), `days` (int, default `1`, range 1-7) |
| **Returns** | Timestamps, operations, statuses, and callers (max 20 entries) |

Uses the Azure Monitor SDK to query the activity log.

---

## 6. Resource Groups (2 tools)

### `list_resource_groups`

List all resource groups in the subscription.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Names, locations, and provisioning states |

### `list_resources`

List resources in a resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `resource_type` (str, default `"all"`) |
| **Returns** | Resource types, names, locations, statuses, and sizes |

`resource_type` can be: `all`, `vm`, `storage`, `webapp`, `sql`.

---

## 7. Virtual Machines (7 tools)

### `list_vms`

List virtual machines in a resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required) |
| **Returns** | VM names, locations, power states, and sizes |

### `get_vm_status`

Get detailed status of a virtual machine.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Name, location, VM size, power state, provisioning state, OS type |

### `start_vm`

Start a virtual machine.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `stop_vm`

Stop a virtual machine. VM stays allocated — charges continue.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `restart_vm`

Restart a virtual machine.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `deallocate_vm`

Deallocate a VM — stops and releases compute resources. No compute charges.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `scale_vmss`

Scale a Virtual Machine Scale Set.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `vmss_name` (str, required), `capacity` (int, required, >= 0) |
| **Returns** | Previous and new capacity |

---

## 8. Storage Accounts (2 tools)

### `list_storage_accounts`

List storage accounts in a resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required) |
| **Returns** | Account names, locations, provisioning states, and kinds |

### `get_storage_status`

Get status of a storage account.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `account_name` (str, required) |
| **Returns** | Name, location, kind, SKU, provisioning state, primary endpoints |

---

## 9. App Configuration (6 tools)

### `appconfig_list`

List App Configuration stores in the subscription or resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Store names, locations, endpoints, SKUs, and provisioning states |

### `appconfig_show`

Show details of an App Configuration store.

| | |
|:--|:--|
| **Parameters** | `store_name` (str, required), `resource_group` (str, required) |
| **Returns** | Full store details including endpoint, SKU, creation date, and tags |

### `appconfig_kv_list`

List key-values in an App Configuration store.

| | |
|:--|:--|
| **Parameters** | `store_name` (str, required), `resource_group` (str, optional), `key_filter` (str, default `"*"`), `label_filter` (str, optional) |
| **Returns** | Keys, values (truncated), labels, content types (max 50 entries) |

### `appconfig_kv_show`

Show a specific key-value from an App Configuration store.

| | |
|:--|:--|
| **Parameters** | `store_name` (str, required), `key` (str, required), `resource_group` (str, optional), `label` (str, optional) |
| **Returns** | Key, value, label, content type, last modified, read-only status, etag |

### `appconfig_kv_set`

Set a key-value in an App Configuration store.

| | |
|:--|:--|
| **Parameters** | `store_name` (str, required), `key` (str, required), `value` (str, required), `resource_group` (str, optional), `label` (str, optional), `content_type` (str, optional) |
| **Returns** | Confirmation with key, value, and label |

### `appconfig_kv_delete`

Delete a key-value from an App Configuration store.

| | |
|:--|:--|
| **Parameters** | `store_name` (str, required), `key` (str, required), `resource_group` (str, optional), `label` (str, optional) |
| **Returns** | Deletion confirmation |

---

## 10. App Service (7 tools)

### `appservice_plan_list`

List App Service plans in the subscription or resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Plan names, locations, SKUs, status, and worker counts |

### `appservice_plan_show`

Show details of an App Service plan.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Full plan details including SKU, capacity, workers, and number of sites |

### `webapp_list`

List web apps in the subscription or resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Web app names, locations, states, hostnames, and kinds |

### `webapp_show`

Show details of a web app.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Full web app details including state, hostname, plan, HTTPS settings, and outbound IPs |

### `webapp_start`

Start a web app.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Success confirmation |

### `webapp_stop`

Stop a web app.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Success confirmation |

### `webapp_restart`

Restart a web app.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Success confirmation |

---

## 11. Web Apps for Containers (7 tools)

### `webapp_create_for_container`

Create a Web App for Containers on Azure App Service.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required), `plan_name` (str, required), `plan_sku` (str, default `"P1v2"`), `plan_tier` (str, default `"PremiumV2"`), `location` (str, optional), `image` (str, optional), `registry_url` (str, optional), `registry_username` (str, optional), `registry_password` (str, optional), `os_type` (str, default `"linux"`), `multi_container` (bool, default `false`), `startup_command` (str, optional), `env_variables` (str, optional JSON), `vnet_subnet_id` (str, optional), `assign_identity` (bool, default `false`) |
| **Returns** | Full deployment details including hostname, App Service plan, container config, and connection strings |

Creates App Service plan (if needed), web app, container config, optional VNet integration, and optional managed identity.

### `webapp_grant_cr_access`

Grant Web App access to Container Registry via RBAC.

| | |
|:--|:--|
| **Parameters** | `webapp_name` (str, required), `resource_group` (str, required), `registry_name` (str, required), `registry_resource_group` (str, required), `role` (str, default `"AcrPull"`) |
| **Returns** | RBAC assignment details |

### `webapp_configure_vnet_integration`

Configure Virtual Network integration for a web app.

| | |
|:--|:--|
| **Parameters** | `webapp_name` (str, required), `resource_group` (str, required), `subnet_id` (str, required) |
| **Returns** | VNet integration details |

### `webapp_assign_identity`

Assign a system-assigned managed identity to a web app.

| | |
|:--|:--|
| **Parameters** | `webapp_name` (str, required), `resource_group` (str, required) |
| **Returns** | Principal ID, tenant ID, identity type |

### `webapp_view_logs`

View web app logs from Azure Monitor.

| | |
|:--|:--|
| **Parameters** | `webapp_name` (str, required), `resource_group` (str, required), `days` (int, default `1`, range 1-7) |
| **Returns** | Activity log entries for the web app |

### `webapp_set_container_registry_credentials`

Set container registry credentials for a web app.

| | |
|:--|:--|
| **Parameters** | `webapp_name` (str, required), `resource_group` (str, required), `registry_url` (str, required), `username` (str, required), `password` (str, required), `os_type` (str, default `"linux"`) |
| **Returns** | Credential configuration confirmation |

### `webapp_delete`

Delete a web app.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Deletion confirmation |

---

## 12. Container Registry (20 tools)

### `acr_list_registries`

List container registries in a resource group or subscription.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Registry names, locations, SKUs, admin status, login servers |

### `acr_show_registry`

Get details of a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Full registry details |

### `acr_create_registry`

Create a new container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `location` (str, default `"eastus"`), `sku` (str, default `"Basic"`), `admin_enabled` (bool, default `false`) |
| **Returns** | Created registry details |

### `acr_delete_registry`

Delete a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Deletion confirmation |

### `acr_update_registry`

Update a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `admin_enabled` (bool, optional) |
| **Returns** | Updated registry details |

### `acr_get_credentials`

Get login credentials for a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Username and passwords |

### `acr_get_login_server`

Get the login server URL for a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Login server URL |

### `acr_list_repositories`

List repositories in a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Repository names |

### `acr_list_tags`

List tags in a container registry repository.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `repository` (str, required) |
| **Returns** | Tag names and metadata |

### `acr_show_task`

Get details of a container registry task.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `task_name` (str, required) |
| **Returns** | Task details |

### `acr_list_tasks`

List tasks in a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Task names and statuses |

### `acr_create_task`

Create a container registry task.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `task_name` (str, required), `platform_os` (str, default `"Linux"`), `platform_architecture` (str, default `"amd64"`), `platform_variant` (str, optional) |
| **Returns** | Created task details |

### `acr_delete_task`

Delete a container registry task.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `task_name` (str, required) |
| **Returns** | Deletion confirmation |

### `acr_run_task`

Run a container registry task.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `task_name` (str, required) |
| **Returns** | Run details |

### `acr_list_builds`

List build tasks in a subscription or specific registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional), `registry_name` (str, optional) |
| **Returns** | Build task names and statuses |

### `acr_show_quotas`

Show quota information for a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Quota limits and usage |

### `acr_show_usage`

Show usage information for a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Storage usage details |

### `acr_list_network_rules`

List network rules for a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required) |
| **Returns** | Default action, IP rules, and VNet rules |

### `acr_update_network_rules`

Update network rules for a container registry.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, required), `registry_name` (str, required), `default_action` (str, default `"Allow"`) |
| **Returns** | Updated network rule details |

### `acr_reset_client`

Reset cached ACR client and force re-authentication.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Cache cleared confirmation |

---

## 13. Virtual Networks (9 tools)

### `vnet_list`

List virtual networks in the subscription or resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | VNet names, locations, address spaces, subnet counts |

### `vnet_show`

Show details of a virtual network including subnets and peerings.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Address space, DNS servers, DDoS protection, subnets, peerings, tags |

### `vnet_create`

Create a virtual network with a default subnet.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required), `address_prefix` (str, default `"10.0.0.0/16"`), `location` (str, optional) |
| **Returns** | Created VNet details |

### `vnet_delete`

Delete a virtual network. Removes all subnets and peerings.

| | |
|:--|:--|
| **Parameters** | `name` (str, required), `resource_group` (str, required) |
| **Returns** | Deletion confirmation |

### `vnet_subnet_list`

List subnets in a virtual network.

| | |
|:--|:--|
| **Parameters** | `vnet_name` (str, required), `resource_group` (str, required) |
| **Returns** | Subnet names, prefixes, NSGs, delegations, provisioning states |

### `vnet_subnet_show`

Show details of a subnet including NSG, route table, and delegations.

| | |
|:--|:--|
| **Parameters** | `vnet_name` (str, required), `subnet_name` (str, required), `resource_group` (str, required) |
| **Returns** | Full subnet details |

### `vnet_subnet_create`

Create a subnet in a virtual network.

| | |
|:--|:--|
| **Parameters** | `vnet_name` (str, required), `subnet_name` (str, required), `resource_group` (str, required), `address_prefix` (str, required) |
| **Returns** | Created subnet details |

### `vnet_subnet_delete`

Delete a subnet from a virtual network.

| | |
|:--|:--|
| **Parameters** | `vnet_name` (str, required), `subnet_name` (str, required), `resource_group` (str, required) |
| **Returns** | Deletion confirmation |

### `vnet_peering_list`

List peerings for a virtual network.

| | |
|:--|:--|
| **Parameters** | `vnet_name` (str, required), `resource_group` (str, required) |
| **Returns** | Peering names, states, remote VNets, access/traffic/gateway settings |

---

## 14. Azure AD / Entra ID (9 tools)

### `aad_list_users`

List Azure AD users.

| | |
|:--|:--|
| **Parameters** | `filter` (str, optional — OData filter), `top` (int, default `50`) |
| **Returns** | Display names, UPNs, object IDs, account status, job titles, departments |

### `aad_show_user`

Get details of an Azure AD user.

| | |
|:--|:--|
| **Parameters** | `user_id` (str, required), `user_principal_name` (str, optional) |
| **Returns** | Full user profile including optional fields (phone, office, address) |

### `aad_create_user`

Create a new Azure AD user.

| | |
|:--|:--|
| **Parameters** | `display_name` (str, required), `user_principal_name` (str, required), `password` (str, required), `mail_nick_name` (str, optional), `department` (str, optional), `job_title` (str, optional) |
| **Returns** | Created user details with temporary password note |

### `aad_delete_user`

Delete an Azure AD user.

| | |
|:--|:--|
| **Parameters** | `user_id` (str, required), `user_principal_name` (str, optional) |
| **Returns** | Deletion confirmation |

### `aad_list_applications`

List Azure AD applications.

| | |
|:--|:--|
| **Parameters** | `filter` (str, optional), `top` (int, default `50`) |
| **Returns** | Application display names, app IDs, object IDs, publisher domains |

### `aad_create_application`

Create a new Azure AD application.

| | |
|:--|:--|
| **Parameters** | `display_name` (str, required), `sign_in_audience` (str, default `"AzureADMyOrg"`) |
| **Returns** | Created application details |

### `aad_list_groups`

List Azure AD groups.

| | |
|:--|:--|
| **Parameters** | `filter` (str, optional), `top` (int, default `50`) |
| **Returns** | Group display names, object IDs, mail, descriptions, group types |

### `aad_verify_tenant`

Verify Azure AD tenant information.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Tenant ID, display name, country, default domain, tenant type, verified domain count |

### `aad_reset_client`

Reset cached Azure AD client and force re-authentication.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Cache cleared confirmation |

---

## 15. Docker Runtime (3 tools)

### `list_containers`

List running Docker containers on the local machine.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Container IDs, names, statuses, and images |

Uses the Docker CLI (`docker ps`) under the hood.

### `get_container_logs`

Retrieve logs from a Docker container.

| | |
|:--|:--|
| **Parameters** | `container_id` (str, required), `lines` (int, default `50`) |
| **Returns** | Container log output |

### `restart_container`

Restart a Docker container.

| | |
|:--|:--|
| **Parameters** | `container_id` (str, required) |
| **Returns** | Restart confirmation |

---

## 16. Monitoring (3 tools)

### `get_system_metrics`

Get system metrics (CPU, memory, disk usage).

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | CPU usage, memory stats, disk usage |

Uses OS-level commands (`top`, `free`, `df`, `vm_stat`) depending on platform.

### `check_service_health`

Check health of a system service.

| | |
|:--|:--|
| **Parameters** | `service_name` (str, required) |
| **Returns** | Service status (active/inactive) |

Uses `systemctl` on Linux or `launchctl` on macOS.

### `get_infrastructure_status`

Get overall infrastructure health status.

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Docker availability, system uptime |
