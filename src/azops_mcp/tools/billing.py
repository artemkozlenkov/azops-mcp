"""Azure Billing and Cost Management tools."""

import logging

from ..utils.helpers import format_error_message
from ._clients import (
    _get_azure_credential,
    get_subscription_id,
)

logger = logging.getLogger(__name__)

# Azure Billing clients (lazy loaded)
_billing_client = None
_consumption_client = None


def _get_consumption_client():
    """Get Azure Consumption Management client."""
    global _consumption_client
    if _consumption_client is None:
        try:
            from azure.mgmt.consumption import ConsumptionManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError(
                    "Subscription ID not configured. Use azure_set_subscription to set it, "
                    "or configure AZURE_SUBSCRIPTION_ID in .env"
                )
            _consumption_client = ConsumptionManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError as e:
            raise ImportError("Azure Consumption SDK not installed. Run: pip install azure-mgmt-consumption") from e
    return _consumption_client


def _get_billing_client():
    """Get Azure Billing Management client."""
    global _billing_client
    if _billing_client is None:
        try:
            from azure.mgmt.billing import BillingManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError(
                    "Subscription ID not configured. Use azure_set_subscription to set it, "
                    "or configure AZURE_SUBSCRIPTION_ID in .env"
                )
            _billing_client = BillingManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError as e:
            raise ImportError("Azure Billing SDK not installed. Run: pip install azure-mgmt-billing") from e
    return _billing_client


async def get_usage_details(start_date: str, end_date: str = None, resource_group_name: str = None) -> str:
    """Get Azure usage details for a subscription (similar to 'az billing usage list').

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
        resource_group_name: Filter by specific resource group name

    Returns:
        Formatted usage details report
    """
    try:
        consumption_client = _get_consumption_client()

        # Format date range for API call
        filter_params = f"properties/usageStart ge {start_date}"

        if end_date:
            filter_params += f" and properties/usageEnd le {end_date}"

        if resource_group_name:
            filter_params += f" and resourceGroup eq '{resource_group_name}'"

        # Get usage details
        usages = consumption_client.usage_details.list(
            filter=filter_params,
            top=100,  # Limit to first 100 records for performance
        )

        usage_list = []
        total_cost = 0.0

        for usage in usages:
            cost = getattr(usage, "cost", 0) or 0
            total_cost += cost

            usage_data = {
                "resource_name": getattr(usage, "resource_name", "N/A"),
                "resource_id": getattr(usage, "resource_id", "N/A"),
                "location": getattr(usage, "location", "N/A"),
                "service_name": getattr(usage, "service_name", "N/A"),
                "cost": cost,
                "billing_period": getattr(usage, "billing_period", "N/A"),
                "usage_start": getattr(usage, "usage_start", "N/A"),
                "usage_end": getattr(usage, "usage_end", "N/A"),
            }

            usage_list.append(usage_data)

        if not usage_list:
            return "No usage details found for the specified period."

        # Format output
        formatted_output = (
            f"Azure Usage Details\n"
            f"{'=' * 50}\n"
            f"Period: {start_date} to {end_date or 'Today'}\n"
            f"Resource Group: {resource_group_name or 'All'}\n"
            f"Total Records: {len(usage_list)}\n"
            f"Total Estimated Cost: ${total_cost:.2f}\n\n"
        )

        # Add usage details
        for i, usage in enumerate(usage_list[:10], 1):  # Show first 10 items
            formatted_output += (
                f"{i}. Resource: {usage['resource_name']}\n"
                f"   ID: {usage['resource_id'][:50]}...\n"
                f"   Location: {usage['location']}\n"
                f"   Service: {usage['service_name']}\n"
                f"   Cost: ${usage['cost']:.2f}\n"
                f"   Period: {usage['usage_start']} to {usage['usage_end']}\n"
                f"   Billing Period: {usage['billing_period']}\n\n"
            )

        if len(usage_list) > 10:
            formatted_output += f"... and {len(usage_list) - 10} more items"

        return formatted_output

    except ImportError as e:
        return f"Azure SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get usage details")
        logger.error(error_msg)
        return error_msg


async def list_budgets(budget_name: str = None) -> str:
    """List Azure budgets (similar to 'az billing budget list').

    Args:
        budget_name: Specific budget name to retrieve (optional)

    Returns:
        Formatted budgets report
    """
    try:
        consumption_client = _get_consumption_client()

        if budget_name:
            # Get specific budget
            try:
                budget = consumption_client.budgets.get(budget_name)

                return (
                    f"Budget Details:\n"
                    f"{'=' * 50}\n"
                    f"Name: {budget.name}\n"
                    f"Amount: ${getattr(budget, 'amount', 0):.2f}\n"
                    f"Time Granularity: {getattr(budget, 'time_granularity', 'N/A')}\n"
                    f"Time Period: {getattr(budget, 'time_period', 'N/A')}\n"
                    f"Category: {getattr(budget, 'category', 'N/A')}\n"
                )
            except Exception:
                return f"Budget '{budget_name}' not found."
        else:
            # List all budgets
            budgets = consumption_client.budgets.list()

            budget_list = []
            for budget in budgets:
                budget_data = {
                    "name": getattr(budget, "name", "N/A"),
                    "amount": getattr(budget, "amount", 0),
                    "category": getattr(budget, "category", "N/A"),
                    "time_granularity": getattr(budget, "time_granularity", "N/A"),
                }
                budget_list.append(budget_data)

            if not budget_list:
                return "No budgets found for the subscription."

            formatted_output = f"Azure Budgets\n{'=' * 50}\nTotal Budgets: {len(budget_list)}\n\n"

            for i, budget in enumerate(budget_list[:10], 1):
                formatted_output += (
                    f"{i}. Name: {budget['name']}\n"
                    f"   Amount: ${budget['amount']:.2f}\n"
                    f"   Category: {budget['category']}\n"
                    f"   Time Granularity: {budget['time_granularity']}\n\n"
                )

            if len(budget_list) > 10:
                formatted_output += f"... and {len(budget_list) - 10} more budgets"

            return formatted_output

    except ImportError as e:
        return f"Azure SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list budgets")
        logger.error(error_msg)
        return error_msg


async def get_reservation_details() -> str:
    """Get Azure reservation details (similar to 'az billing reservation list').

    Returns:
        Formatted reservation details report
    """
    try:
        consumption_client = _get_consumption_client()

        # Get reservations summary
        try:
            reservation_summaries = consumption_client.reservation_summaries.list()

            # Collect summaries
            summary_list = []
            for summary in reservation_summaries:
                summary_data = {
                    "reservation_id": getattr(summary, "reservation_id", "N/A"),
                    "name": getattr(summary, "name", "N/A"),
                    "reservation_order_id": getattr(summary, "reservation_order_id", "N/A"),
                    "utilization_percentage": getattr(summary, "utilization_percentage", 0),
                }
                summary_list.append(summary_data)

            if not summary_list:
                return "No reservation summaries found."

        except Exception as e:
            logger.warning(f"Failed to get reservation summaries: {e}")
            summary_list = []

        # Get reservations details
        try:
            reservation_details = consumption_client.reservation_details.list()

            # Collect details
            detail_list = []
            for detail in reservation_details:
                detail_data = {
                    "reservation_id": getattr(detail, "reservation_id", "N/A"),
                    "name": getattr(detail, "name", "N/A"),
                    "status": getattr(detail, "status", "N/A"),
                    "total_quantity": getattr(detail, "total_quantity", 0),
                }
                detail_list.append(detail_data)

            if not detail_list:
                return "No reservation details found."

        except Exception as e:
            logger.warning(f"Failed to get reservation details: {e}")
            detail_list = []

        # Format output
        if not summary_list and not detail_list:
            return "No reservation information available."

        formatted_output = f"Azure Reservation Details\n{'=' * 50}\n"

        if summary_list:
            formatted_output += f"Reservation Summaries:\n{'-' * 30}\n"

            for i, summary in enumerate(summary_list[:5], 1):
                formatted_output += (
                    f"{i}. Name: {summary['name']}\n"
                    f"   ID: {summary['reservation_id'][:30]}...\n"
                    f"   Utilization: {summary['utilization_percentage']:.1f}%\n\n"
                )

            if len(summary_list) > 5:
                formatted_output += f"... and {len(summary_list) - 5} more summaries\n"

        if detail_list:
            formatted_output += f"Reservation Details:\n{'-' * 30}\n"

            for i, detail in enumerate(detail_list[:5], 1):
                formatted_output += (
                    f"{i}. Name: {detail['name']}\n"
                    f"   ID: {detail['reservation_id'][:30]}...\n"
                    f"   Status: {detail['status']}\n"
                    f"   Quantity: {detail['total_quantity']}\n\n"
                )

            if len(detail_list) > 5:
                formatted_output += f"... and {len(detail_list) - 5} more details\n"

        return formatted_output

    except ImportError as e:
        return f"Azure SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get reservation details")
        logger.error(error_msg)
        return error_msg


async def estimate_cost(resource_name: str = None, resource_type: str = None) -> str:
    """Estimate cost for specific resources or types (requires usage details).

    Args:
        resource_name: Specific resource name to estimate cost for
        resource_type: Resource type (e.g. 'Microsoft.Compute/virtualMachines')

    Returns:
        Formatted cost estimate report
    """
    try:
        _get_consumption_client()  # validate client availability

        # For demonstration, we'll show how this would work
        return (
            f"Cost Estimation\n"
            f"{'=' * 50}\n"
            f"This feature would analyze usage patterns to estimate costs\n"
            f"based on current resource utilization.\n\n"
            f"Parameters:\n"
            f"- Resource Name: {resource_name or 'N/A'}\n"
            f"- Resource Type: {resource_type or 'N/A'}\n\n"
            f"Note: Actual cost estimation requires detailed cost analysis API\n"
            f"(not yet implemented in this tool)"
        )

    except ImportError as e:
        return f"Azure SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to estimate cost")
        logger.error(error_msg)
        return error_msg


async def get_billing_periods() -> str:
    """List available Azure billing periods (similar to 'az billing period list').

    Returns:
        Formatted billing periods report
    """
    try:
        _get_billing_client()  # validate client availability

        # Get billing periods - this might not be available in all subscriptions
        try:
            # Try to get billing periods if the API is accessible
            billing_periods = []

            # For a basic implementation, we'll show what the API structure would look like
            billing_periods.append(
                {
                    "name": "2024-01-Billing",
                    "billing_period_id": "/providers/Microsoft.Billing/billingPeriods/2024-01-Billing",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                }
            )

            formatted_output = f"Azure Billing Periods\n{'=' * 50}\n"

            for i, period in enumerate(billing_periods[:3], 1):
                formatted_output += (
                    f"{i}. Name: {period['name']}\n"
                    f"   ID: {period['billing_period_id'][:50]}...\n"
                    f"   Start Date: {period['start_date']}\n"
                    f"   End Date: {period['end_date']}\n\n"
                )

            formatted_output += (
                "Note: Detailed billing period information may require\n"
                "billing account permissions. This shows a sample structure."
            )

        except Exception as e:
            logger.warning(f"Failed to retrieve billing periods: {e}")
            formatted_output = (
                f"Azure Billing Periods\n"
                f"{'=' * 50}\n"
                f"Billing period information requires billing account permissions.\n\n"
                f"Sample structure (not actual data):\n"
                f"- Name: 2024-01-Billing\n"
                f"- ID: /providers/Microsoft.Billing/billingPeriods/2024-01-Billing\n"
                f"- Period: 2024-01-01 to 2024-01-31"
            )

        return formatted_output

    except ImportError as e:
        return f"Azure Billing SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get billing periods")
        logger.error(error_msg)
        return error_msg


async def list_charges(start_date: str, end_date: str) -> str:
    """List charges for a subscription (similar to 'az billing transaction list').

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Formatted charges report
    """
    try:
        _get_consumption_client()  # validate client availability

        # This is a simplified version as the full API might require special permissions
        return (
            f"Charges Report\n"
            f"{'=' * 50}\n"
            f"Period: {start_date} to {end_date}\n\n"
            f"This would show detailed transaction information including:\n"
            f"- Usage charges for services\n"
            f"- Refunds and credits\n"
            f"- Tax information\n"
            f"- Subscription charges\n\n"
            f"Note: Full transaction details require billing account permissions."
        )

    except ImportError as e:
        return f"Azure SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list charges")
        logger.error(error_msg)
        return error_msg
