"""Azure AD (Entra ID) management tools."""

import logging
from typing import Optional

from ..config import config

logger = logging.getLogger(__name__)

# Azure AD/MS Graph client (lazy loaded)
_aad_client = None


def set_aad_subscription(subscription_id: str) -> None:
    """Set the subscription ID and clear AAD client cache."""
    global _aad_client
    from .cloud import set_subscription_id
    set_subscription_id(subscription_id)
    _aad_client = None
    logger.info("Azure AD client cache cleared")


def get_aad_subscription() -> Optional[str]:
    """Get the active subscription ID."""
    from .cloud import get_subscription_id
    return get_subscription_id()


def clear_aad_subscription() -> None:
    """Clear the runtime subscription ID override."""
    from .cloud import clear_subscription_id
    clear_subscription_id()


def _get_aad_client():
    """Get Azure AD (Microsoft Graph) client for Azure AD operations.
    
    Uses Microsoft Graph API for Azure AD operations.
    """
    global _aad_client
    if _aad_client is None:
        try:
            from azure.identity import ChainedTokenCredential
            from msgraph import GraphServiceClient
            
            from .cloud import _get_azure_credential, get_subscription_id
            
            credential = _get_azure_credential()
            
            # Microsoft Graph requires a different scope
            scopes = ["https://graph.microsoft.com/.default"]
            
            _aad_client = GraphServiceClient(
                credential=credential,
                scopes=scopes,
            )
        except ImportError as e:
            # Try alternative import paths
            try:
                from microsoft_graph import GraphServiceClient
                credential = _get_azure_credential()
                scopes = ["https://graph.microsoft.com/.default"]
                _aad_client = GraphServiceClient(credential=credential, scopes=scopes)
            except ImportError:
                raise ImportError(
                    "Microsoft Graph SDK not installed. "
                    "Run: pip install msgraph-sdk azure-identity"
                )
    return _aad_client


def reset_aad_client() -> None:
    """Reset cached Azure AD client."""
    global _aad_client
    _aad_client = None
    logger.info("Azure AD client cache cleared")


async def list_users(filter: str = "", top: int = 50) -> str:
    """List Azure AD users (similar to 'az ad user list').
    
    Args:
        filter: OData filter query (e.g., 'displayName eq 'John Doe'')
        top: Maximum number of users to return (default 50)
        
    Returns:
        Formatted list of Azure AD users
    """
    try:
        client = _get_aad_client()
        
        # Use select to limit fields returned
        request_config = {"timeout": 30}
        if filter:
            request_config["$filter"] = filter
        request_config["$top"] = top
        
        # Fetch users
        users = await client.users.get(request_config=request_config)
        
        if not users or not users.value:
            return "No users found."
        
        formatted_users = []
        for user in users.value[:top]:
            user_info = [
                f"Display Name: {user.display_name or 'N/A'}",
                f"User Principal Name: {user.user_principal_name or 'N/A'}",
                f"Object ID: {user.id or 'N/A'}",
                f"Account Enabled: {user.account_enabled if hasattr(user, 'account_enabled') else 'N/A'}",
            ]
            if hasattr(user, 'job_title') and user.job_title:
                user_info.append(f"Job Title: {user.job_title}")
            if hasattr(user, 'department') and user.department:
                user_info.append(f"Department: {user.department}")
            if hasattr(user, 'mail') and user.mail:
                user_info.append(f"Email: {user.mail}")
            formatted_users.append("\n".join(user_info))
        
        return f"Azure AD Users ({len(formatted_users)} found):\n\n" + "\n---\n".join(formatted_users)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to list users: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def show_user(user_id: str, user_principal_name: str = "") -> str:
    """Get details of an Azure AD user (similar to 'az ad user show').
    
    Args:
        user_id: Object ID of the user
        user_principal_name: User principal name (alternative lookup)
        
    Returns:
        User details
    """
    if not user_id and not user_principal_name:
        return "Error: user_id or user_principal_name is required"
    
    try:
        client = _get_aad_client()
        
        # Determine which identifier to use
        if user_principal_name:
            user = await client.users.by_user_id(user_principal_name).get()
        else:
            user = await client.users.by_user_id(user_id).get()
        
        details = [
            f"Display Name: {user.display_name or 'N/A'}",
            f"User Principal Name: {user.user_principal_name or 'N/A'}",
            f"Object ID: {user.id or 'N/A'}",
            f"Account Enabled: {user.account_enabled if hasattr(user, 'account_enabled') else 'N/A'}",
        ]
        
        # Add optional fields
        optional_fields = [
            'job_title', 'department', 'mail', 'mobile_phone',
            'business_phones', 'office_location', 'preferred_language'
        ]
        for field in optional_fields:
            if hasattr(user, field) and getattr(user, field):
                field_name = field.replace('_', ' ').title()
                details.append(f"{field_name}: {getattr(user, field)}")
        
        # Add address if present
        if hasattr(user, 'address') and user.address:
            addr = user.address
            address_str = ", ".join(str(v) for v in vars(addr).values() if v)
            if address_str:
                details.append(f"Address: {address_str}")
        
        return f"Azure AD User:\n{'='*50}\n" + "\n".join(details)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to get user details: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def create_user(
    display_name: str,
    user_principal_name: str,
    password: str,
    mail_nick_name: str = "",
    department: str = "",
    job_title: str = "",
) -> str:
    """Create a new Azure AD user (similar to 'az ad user create').
    
    Args:
        display_name: Display name for the user
        user_principal_name: UserPrincipalName (UPN) for the user (e.g., user@contoso.com)
        password: Initial password for the user
        mail_nick_name: Mail alias (default: extracted from UPN)
        department: Department name (optional)
        job_title: Job title (optional)
        
    Returns:
        Created user details with temporary password
    """
    if not display_name or not user_principal_name or not password:
        return "Error: display_name, user_principal_name, and password are required"
    
    try:
        client = _get_aad_client()
        
        # Build user object
        user_params = {
            "display_name": display_name,
            "user_principal_name": user_principal_name,
            "password_profile": {
                "password": password,
                "force_change_password_next_sign_in": True,
            },
            "account_enabled": True,
        }
        
        if mail_nick_name:
            user_params["mail_nickname"] = mail_nick_name
        else:
            # Extract mail nickname from UPN
            mail_nick_name = user_principal_name.split("@")[0] if "@" in user_principal_name else user_principal_name
            user_params["mail_nickname"] = mail_nick_name
        
        if department:
            user_params["department"] = department
        if job_title:
            user_params["job_title"] = job_title
        
        # Create user
        new_user = await client.users.post(body=user_params)
        
        return (
            f"User created successfully!\n"
            f"{'='*50}\n"
            f"Display Name: {new_user.display_name or 'N/A'}\n"
            f"User Principal Name: {new_user.user_principal_name or 'N/A'}\n"
            f"Object ID: {new_user.id or 'N/A'}\n"
            f"Account Enabled: {new_user.account_enabled if hasattr(new_user, 'account_enabled') else 'N/A'}\n"
            f"\nNote: Temporary password provided. User must change password on first sign-in."
        )
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to create user: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def delete_user(user_id: str, user_principal_name: str = "") -> str:
    """Delete an Azure AD user (similar to 'az ad user delete').
    
    Args:
        user_id: Object ID of the user to delete
        user_principal_name: User principal name (alternative lookup)
        
    Returns:
        Deletion confirmation
    """
    if not user_id and not user_principal_name:
        return "Error: user_id or user_principal_name is required"
    
    try:
        client = _get_aad_client()
        
        # Determine which identifier to use
        user_id_to_delete = user_id
        if not user_id_to_delete and user_principal_name:
            # First find the user by UPN
            users = await client.users.get(
                query_params={"$filter": f"userPrincipalName eq '{user_principal_name}'"}
            )
            if users and users.value:
                user_id_to_delete = users.value[0].id
            else:
                return f"Error: User '{user_principal_name}' not found"
        
        # Delete user
        await client.users.by_user_id(user_id_to_delete).delete()
        
        upn_info = f" (UPN: {user_principal_name})" if user_principal_name else ""
        return f"User '{user_id_to_delete}'{upn_info} deleted successfully."
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to delete user: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def list_applications(filter: str = "", top: int = 50) -> str:
    """List Azure AD applications (similar to 'az ad app list').
    
    Args:
        filter: OData filter query
        top: Maximum number of applications to return
        
    Returns:
        Formatted list of applications
    """
    try:
        client = _get_aad_client()
        
        request_config = {"timeout": 30}
        if filter:
            request_config["$filter"] = filter
        request_config["$top"] = top
        
        apps = await client.applications.get(request_config=request_config)
        
        if not apps or not apps.value:
            return "No applications found."
        
        formatted_apps = []
        for app in apps.value[:top]:
            app_info = [
                f"Display Name: {app.display_name or 'N/A'}",
                f"App ID: {app.app_id or 'N/A'}",
                f"Object ID: {app.id or 'N/A'}",
                f"Publisher Domain: {app.publisher_domain or 'N/A'}",
            ]
            formatted_apps.append("\n".join(app_info))
        
        return f"Azure AD Applications ({len(formatted_apps)} found):\n\n" + "\n---\n".join(formatted_apps)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to list applications: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def create_application(
    display_name: str,
    sign_in_audience: str = "AzureADMyOrg",
) -> str:
    """Create a new Azure AD application (similar to 'az ad app create').
    
    Args:
        display_name: Display name for the application
        sign_in_audience: Who can sign in (AzureADMyOrg, AzureADMultipleOrgs, AzureADandPersonalMicrosoftAccount, PersonalMicrosoftAccount)
        
    Returns:
        Created application details
    """
    if not display_name:
        return "Error: display_name is required"
    
    try:
        client = _get_aad_client()
        
        # Build application object
        app_params = {
            "display_name": display_name,
            "sign_in_audience": sign_in_audience,
            "api": {
                "requested_access_token_version": 2,
            },
            "app_roles": [],
            "oauth2_permissions": [],
        }
        
        new_app = await client.applications.post(body=app_params)
        
        return (
            f"Application created successfully!\n"
            f"{'='*50}\n"
            f"Display Name: {new_app.display_name or 'N/A'}\n"
            f"App ID: {new_app.app_id or 'N/A'}\n"
            f"Object ID: {new_app.id or 'N/A'}\n"
            f"Publisher Domain: {new_app.publisher_domain or 'N/A'}\n"
            f"\nNote: You can now configure redirects, secrets, and permissions for this application."
        )
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to create application: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def list_groups(filter: str = "", top: int = 50) -> str:
    """List Azure AD groups (similar to 'az ad group list').
    
    Args:
        filter: OData filter query
        top: Maximum number of groups to return
        
    Returns:
        Formatted list of groups
    """
    try:
        client = _get_aad_client()
        
        request_config = {"timeout": 30}
        if filter:
            request_config["$filter"] = filter
        request_config["$top"] = top
        
        groups = await client.groups.get(request_config=request_config)
        
        if not groups or not groups.value:
            return "No groups found."
        
        formatted_groups = []
        for group in groups.value[:top]:
            group_info = [
                f"Display Name: {group.display_name or 'N/A'}",
                f"Object ID: {group.id or 'N/A'}",
                f"Mail: {group.mail or 'N/A'}",
                f"Description: {group.description or 'N/A'}",
                f"Group Type: {', '.join(group.group_types or []) if group.group_types else 'N/A'}",
            ]
            formatted_groups.append("\n".join(group_info))
        
        return f"Azure AD Groups ({len(formatted_groups)} found):\n\n" + "\n---\n".join(formatted_groups)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to list groups: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def verify_tenant() -> str:
    """Verify Azure AD tenant information.
    
    Returns:
        Tenant verification details
    """
    try:
        client = _get_aad_client()
        
        # Get tenant details
        tenant = await client.directory.get()
        
        return (
            f"Azure AD Tenant Information:\n"
            f"{'='*50}\n"
            f"Tenant ID: {tenant.id or 'N/A'}\n"
            f"Display Name: {tenant.display_name or 'N/A'}\n"
            f"Country: {tenant.country or 'N/A'}\n"
            f"Country Locale: {tenant.country_locale or 'N/A'}\n"
            f"Default Domain: {tenant.default_domain or 'N/A'}\n"
            f"Tenant Type: {tenant.tenant_type or 'N/A'}\n"
            f"Verified Domains: {len(tenant.verified_domains or []) if hasattr(tenant, 'verified_domains') else 0}"
        )
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = f"Failed to verify tenant: {str(e)}"
        logger.error(error_msg)
        return error_msg
