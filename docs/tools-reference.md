---
title: Tools Reference
layout: default
nav_order: 4
---

# Tools Reference
{: .no_toc }

Complete reference for all tools exposed by azops-mcp.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Tier Legend

| Badge | Meaning |
|:------|:--------|
| **Free** | Always registered — no license needed |
| **Premium** | Only registered when the license server grants the matching feature flag. Invisible without a valid `AUTH_TOKEN`. |

### Feature Flags

Premium tools are grouped by feature flag. The license server returns which flags are granted for a given token.

| Flag | Controls |
|:-----|:---------|
| `rg_write` | `create_resource_group`, `delete_resource_group` |
| `rbac` | `list_role_assignments` |
| `locks_write` | `create_resource_lock`, `delete_resource_lock` |
| `tags_write` | `set_resource_group_tags` |
| `mg_write` | `create_management_group`, `delete_management_group` |

---

## 1. Health & Status

### `health_check`

Check MCP server health and Azure SDK availability.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | JSON dict with `status`, `dependencies`, `license_tier`, `timestamp`, `version` |

Reports which Azure SDK packages are installed (`ok` or `missing`) and the current license tier (`free` or `pro`).

---

## 2. Subscription & Authentication (5 tools)

### `list_subscriptions`

List all Azure subscriptions you have access to.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | Formatted list of subscription names, IDs, and states |

Marks the currently active subscription with `(current)`.

### `set_subscription`

Set the Azure subscription to use for this session.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `subscription_id` (str, required) — UUID format |
| **Returns** | Confirmation with subscription name and state |

Validates the UUID format and clears cached Azure SDK clients so they use the new subscription. Persists for the session only (not written to `.env`).

### `auth_status`

Check Azure authentication status and method.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | Authentication method, validity, token expiry, subscription source |

Distinguishes between Service Principal and Azure CLI authentication. Attempts to fetch a token to verify credentials are working.

### `list_locations`

List all Azure regions available for the subscription.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | List of region names, display names, and types |

### `list_tenants`

List Azure AD tenants you have access to.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | Tenant IDs, display names, domains, and types |

---

## 3. Management Groups (4 tools)

### `list_management_groups`

List all Azure management groups.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | Management group names, IDs, and types |

### `get_management_group`

Get details of a management group including its children.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `group_id` (str, required) |
| **Returns** | Display name, tenant ID, children (subscriptions & child groups) |

### `create_management_group`

Create a new management group.

| | |
|:--|:--|
| **Tier** | **Premium** (`mg_write`) |
| **Parameters** | `group_id` (str, required), `display_name` (str, required), `parent_id` (str, optional) |
| **Returns** | Created group details |

Long-running Azure operation — waits for completion before returning.

### `delete_management_group`

Delete a management group. Must be empty (no children).

| | |
|:--|:--|
| **Tier** | **Premium** (`mg_write`) |
| **Parameters** | `group_id` (str, required) |
| **Returns** | Success confirmation |

---

## 4. RBAC — Role Assignments (2 tools)

### `list_role_assignments`

List role assignments (RBAC) for subscription or resource group.

| | |
|:--|:--|
| **Tier** | **Premium** (`rbac`) |
| **Parameters** | `resource_group` (str, optional) — scope filter |
| **Returns** | Principal IDs, types, role definition IDs, scopes (max 20) |

### `list_role_definitions`

List available Azure role definitions (built-in roles).

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | Role names, IDs, and truncated descriptions (max 15) |

---

## 5. Resource Locks (3 tools)

### `list_resource_locks`

List resource locks in subscription or resource group.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Lock names, levels, and notes |

### `create_resource_lock`

Create a lock on a resource group to prevent deletion or modification.

| | |
|:--|:--|
| **Tier** | **Premium** (`locks_write`) |
| **Parameters** | `resource_group` (str, required), `lock_name` (str, required), `lock_level` (str, default `"CanNotDelete"`) |
| **Returns** | Created lock details |

`lock_level` must be `CanNotDelete` or `ReadOnly`.

### `delete_resource_lock`

Delete a resource lock from a resource group.

| | |
|:--|:--|
| **Tier** | **Premium** (`locks_write`) |
| **Parameters** | `resource_group` (str, required), `lock_name` (str, required) |
| **Returns** | Success confirmation |

---

## 6. Tags (2 tools)

### `list_tags`

List tags in subscription or on a resource group.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, optional) |
| **Returns** | Tag key/value pairs or subscription tag names with sample values |

### `set_resource_group_tags`

Set tags on a resource group. Merges with existing tags.

| | |
|:--|:--|
| **Tier** | **Premium** (`tags_write`) |
| **Parameters** | `resource_group` (str, required), `tags` (str, required) — format: `key1=value1,key2=value2` |
| **Returns** | Updated tag list |

---

## 7. Activity Log (1 tool)

### `get_activity_log`

Get recent Azure activity log (audit log).

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, optional), `days` (int, default `1`, range 1-7) |
| **Returns** | Timestamps, operations, statuses, and callers (max 20 entries) |

Uses the Azure Monitor SDK to query the activity log.

---

## 8. Resource Groups (4 tools)

### `list_resource_groups`

List all resource groups in the subscription.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | None |
| **Returns** | Names, locations, and provisioning states |

### `create_resource_group`

Create a new Azure resource group.

| | |
|:--|:--|
| **Tier** | **Premium** (`rg_write`) |
| **Parameters** | `name` (str, required), `location` (str, required) |
| **Returns** | Created group details including resource ID |

### `delete_resource_group`

Delete a resource group and ALL its resources. Irreversible.

| | |
|:--|:--|
| **Tier** | **Premium** (`rg_write`) |
| **Parameters** | `name` (str, required) |
| **Returns** | Success confirmation |

Long-running operation — waits for Azure to finish deleting everything.

### `list_resources`

List resources in a resource group.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `resource_type` (str, default `"all"`) |
| **Returns** | Resource types, names, locations, statuses, and sizes |

`resource_type` can be: `all`, `vm`, `storage`, `webapp`, `sql`.

---

## 9. Virtual Machines (7 tools)

### `list_vms`

List virtual machines in a resource group.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required) |
| **Returns** | VM names, locations, power states, and sizes |

### `get_vm_status`

Get detailed status of a virtual machine.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Name, location, VM size, power state, provisioning state, OS type |

### `start_vm`

Start a virtual machine.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `stop_vm`

Stop a virtual machine. VM stays allocated — charges continue.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `restart_vm`

Restart a virtual machine.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `deallocate_vm`

Deallocate a VM — stops and releases compute resources. No compute charges.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `vm_name` (str, required) |
| **Returns** | Success confirmation |

### `scale_vmss`

Scale a Virtual Machine Scale Set.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `vmss_name` (str, required), `capacity` (int, required, >= 0) |
| **Returns** | Previous and new capacity |

---

## 10. Storage Accounts (2 tools)

### `list_storage_accounts`

List storage accounts in a resource group.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required) |
| **Returns** | Account names, locations, provisioning states, and kinds |

### `get_storage_status`

Get status of a storage account.

| | |
|:--|:--|
| **Tier** | Free |
| **Parameters** | `resource_group` (str, required), `account_name` (str, required) |
| **Returns** | Name, location, kind, SKU, provisioning state, primary endpoints |
