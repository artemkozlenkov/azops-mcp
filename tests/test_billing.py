"""Tests for Azure Billing tools."""

from unittest.mock import AsyncMock, patch
import pytest

from azops_mcp import server


class TestBillingUsageDetails:
    """Tests for the billing_usage_details tool."""

    @pytest.mark.asyncio
    async def test_get_usage_details_success(self):
        """Test get_usage_details returns usage information."""
        with patch.object(server.billing, "get_usage_details", new_callable=AsyncMock) as mock_usage:
            mock_usage.return_value = (
                "Azure Usage Details\n"
                "==================================================\n"
                "Period: 2024-01-01 to 2024-01-31\n"
                "Resource Group: All\n"
                "Total Records: 2\n"
                "Total Estimated Cost: $150.00\n\n"
                "1. Resource: vm-test-1\n"
                "   ID: /subscriptions/xxx/resourceGroups/test/providers/Microsoft.Compute/virtualMachines/vm-test-1\n"
                "   Location: eastus\n"
                "   Service: Microsoft.Compute\n"
                "   Cost: $100.00\n"
                "   Period: 2024-01-01 to 2024-01-31\n"
                "   Billing Period: 2024-01-Billing\n\n"
            )

            result = await server.billing_usage_details("2024-01-01", "2024-01-31")

            assert "Error" not in result
            mock_usage.assert_called_once_with("2024-01-01", "2024-01-31", None)

    @pytest.mark.asyncio
    async def test_get_usage_details_handles_exception(self):
        """Test get_usage_details handles exceptions gracefully."""
        with patch.object(server.billing, "get_usage_details", new_callable=AsyncMock) as mock_usage:
            mock_usage.side_effect = Exception("Failed to get usage details")
            result = await server.billing_usage_details("2024-01-01", "2024-01-31")

            assert "Error" in result
            assert "Failed to get usage details" in result


class TestBillingBudgets:
    """Tests for the billing_budgets tool."""

    @pytest.mark.asyncio
    async def test_list_budgets_success(self):
        """Test list_budgets returns budget information."""
        with patch.object(server.billing, "list_budgets", new_callable=AsyncMock) as mock_budgets:
            mock_budgets.return_value = (
                "Azure Budgets\n"
                "==================================================\n"
                "Total Budgets: 1\n\n"
                "1. Name: cost-budget-1\n"
                "   Amount: $500.00\n"
                "   Category: Cost\n"
                "   Time Granularity: Monthly\n\n"
            )

            result = await server.billing_budgets()

            assert "Error" not in result
            mock_budgets.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_list_budgets_specific(self):
        """Test list_budgets with specific budget name."""
        with patch.object(server.billing, "list_budgets", new_callable=AsyncMock) as mock_budgets:
            mock_budgets.return_value = (
                "Budget Details:\n"
                "==================================================\n"
                "Name: cost-budget-1\n"
                "Amount: $500.00\n"
                "Time Granularity: Monthly\n"
                "Time Period: 2024-01-01 to 2024-01-31\n"
                "Category: Cost\n"
            )

            result = await server.billing_budgets("cost-budget-1")

            assert "Error" not in result
            mock_budgets.assert_called_once_with("cost-budget-1")

    @pytest.mark.asyncio
    async def test_list_budgets_handles_exception(self):
        """Test list_budgets handles exceptions gracefully."""
        with patch.object(server.billing, "list_budgets", new_callable=AsyncMock) as mock_budgets:
            mock_budgets.side_effect = Exception("Failed to list budgets")
            result = await server.billing_budgets()

            assert "Error" in result
            assert "Failed to list budgets" in result


class TestBillingReservations:
    """Tests for the billing_reservations tool."""

    @pytest.mark.asyncio
    async def test_get_reservation_details_success(self):
        """Test get_reservation_details returns reservation information."""
        with patch.object(server.billing, "get_reservation_details", new_callable=AsyncMock) as mock_reservations:
            mock_reservations.return_value = (
                "Azure Reservation Details\n"
                "==================================================\n"
                "Reservation Summaries:\n"
                "------------------------------\n"
                "1. Name: reservation-1\n"
                "   ID: /providers/Microsoft.Reservation/reservations/reservation-1...\n"
                "   Utilization: 75.0%\n\n"
            )

            result = await server.billing_reservations()

            assert "Error" not in result
            mock_reservations.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_reservation_details_handles_exception(self):
        """Test get_reservation_details handles exceptions gracefully."""
        with patch.object(server.billing, "get_reservation_details", new_callable=AsyncMock) as mock_reservations:
            mock_reservations.side_effect = Exception("Failed to get reservation details")
            result = await server.billing_reservations()

            assert "Error" in result
            assert "Failed to get reservation details" in result


class TestBillingCostEstimate:
    """Tests for the billing_estimate_cost tool."""

    @pytest.mark.asyncio
    async def test_estimate_cost_success(self):
        """Test estimate_cost returns cost estimation."""
        with patch.object(server.billing, "estimate_cost", new_callable=AsyncMock) as mock_estimate:
            mock_estimate.return_value = (
                "Cost Estimation\n"
                "==================================================\n"
                "This feature would analyze usage patterns to estimate costs\n"
                "based on current resource utilization.\n\n"
                "Parameters:\n"
                "- Resource Name: test-vm\n"
                "- Resource Type: Microsoft.Compute/virtualMachines\n\n"
                "Note: Actual cost estimation requires detailed cost analysis API\n"
                "(not yet implemented in this tool)"
            )

            result = await server.billing_estimate_cost("test-vm")

            assert "Error" not in result
            mock_estimate.assert_called_once_with("test-vm", None)

    @pytest.mark.asyncio
    async def test_estimate_cost_with_type(self):
        """Test estimate_cost with resource type."""
        with patch.object(server.billing, "estimate_cost", new_callable=AsyncMock) as mock_estimate:
            mock_estimate.return_value = "Cost Estimation"
            result = await server.billing_estimate_cost("test-vm", "Microsoft.Compute/virtualMachines")

            assert "Error" not in result
            mock_estimate.assert_called_once_with("test-vm", "Microsoft.Compute/virtualMachines")

    @pytest.mark.asyncio
    async def test_estimate_cost_handles_exception(self):
        """Test estimate_cost handles exceptions gracefully."""
        with patch.object(server.billing, "estimate_cost", new_callable=AsyncMock) as mock_estimate:
            mock_estimate.side_effect = Exception("Failed to estimate cost")
            result = await server.billing_estimate_cost()

            assert "Error" in result
            assert "Failed to estimate cost" in result


class TestBillingPeriods:
    """Tests for the billing_periods tool."""

    @pytest.mark.asyncio
    async def test_get_billing_periods_success(self):
        """Test get_billing_periods returns billing period information."""
        with patch.object(server.billing, "get_billing_periods", new_callable=AsyncMock) as mock_periods:
            mock_periods.return_value = (
                "Azure Billing Periods\n"
                "==================================================\n"
                "Billing period information requires billing account permissions.\n\n"
                "Sample structure (not actual data):\n"
                "- Name: 2024-01-Billing\n"
                "- ID: /providers/Microsoft.Billing/billingPeriods/2024-01-Billing\n"
                "- Period: 2024-01-01 to 2024-01-31"
            )

            result = await server.billing_periods()

            assert "Error" not in result
            mock_periods.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_billing_periods_handles_exception(self):
        """Test get_billing_periods handles exceptions gracefully."""
        with patch.object(server.billing, "get_billing_periods", new_callable=AsyncMock) as mock_periods:
            mock_periods.side_effect = Exception("Failed to get billing periods")
            result = await server.billing_periods()

            assert "Error" in result
            assert "Failed to get billing periods" in result


class TestBillingCharges:
    """Tests for the billing_charges tool."""

    @pytest.mark.asyncio
    async def test_list_charges_success(self):
        """Test list_charges returns charge information."""
        with patch.object(server.billing, "list_charges", new_callable=AsyncMock) as mock_charges:
            mock_charges.return_value = (
                "Charges Report\n"
                "==================================================\n"
                "Period: 2024-01-01 to 2024-01-31\n\n"
                "This would show detailed transaction information including:\n"
                "- Usage charges for services\n"
                "- Refunds and credits\n"
                "- Tax information\n"
                "- Subscription charges\n\n"
                "Note: Full transaction details require billing account permissions."
            )

            result = await server.billing_charges("2024-01-01", "2024-01-31")

            assert "Error" not in result
            mock_charges.assert_called_once_with("2024-01-01", "2024-01-31")

    @pytest.mark.asyncio
    async def test_list_charges_handles_exception(self):
        """Test list_charges handles exceptions gracefully."""
        with patch.object(server.billing, "list_charges", new_callable=AsyncMock) as mock_charges:
            mock_charges.side_effect = Exception("Failed to list charges")
            result = await server.billing_charges("2024-01-01", "2024-01-31")

            assert "Error" in result
            assert "Failed to list charges" in result
