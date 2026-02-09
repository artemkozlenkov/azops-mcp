---
title: Tools Reference
layout: default
nav_order: 4
---

# Tools Reference
{: .no_toc }

Complete reference for all 26 tools exposed by azops-mcp.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 1. Health & Status

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

## 4. RBAC — Role Definitions (1 tool)

### `list_role_definitions`

List available Azure role definitions (built-in roles).

| | |
|:--|:--|
| **Parameters** | None |
| **Returns** | Role names, IDs, and truncated descriptions (max 15) |

---

## 5. Resource Locks (1 tool)

### `list_resource_locks`

List resource locks in subscription or resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Lock names, levels, and notes |

---

## 6. Tags (1 tool)

### `list_tags`

List tags in subscription or on a resource group.

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Tag key/value pairs or subscription tag names with sample values |

---

## 7. Activity Log (1 tool)

### `get_activity_log`

Get recent Azure activity log (audit log).

| | |
|:--|:--|
| **Parameters** | `resource_group` (str, optional), `days` (int, default `1`, range 1-7) |
| **Returns** | Timestamps, operations, statuses, and callers (max 20 entries) |

Uses the Azure Monitor SDK to query the activity log.

---

## 8. Resource Groups (2 tools)

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

## 9. Virtual Machines (7 tools)

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

## 10. Storage Accounts (2 tools)

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
