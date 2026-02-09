"""Infrastructure monitoring tools."""

import logging
import platform
import subprocess

from ..utils.helpers import format_error_message

logger = logging.getLogger(__name__)


async def get_system_metrics() -> str:
    """Get system metrics (CPU, memory, disk usage).

    Returns:
        Formatted system metrics
    """
    try:
        # Get CPU usage (simplified - in production, use psutil or similar)
        if platform.system() == "Linux":
            # Linux CPU usage
            result = subprocess.run(
                ["top", "-bn1", "|", "grep", "Cpu(s)"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5,
            )
            cpu_info = "CPU usage: Unable to determine"
            if result.returncode == 0:
                cpu_info = f"CPU: {result.stdout.strip()}"
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["top", "-l", "1", "|", "grep", "CPU usage"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5,
            )
            cpu_info = "CPU usage: Unable to determine"
            if result.returncode == 0:
                cpu_info = f"CPU: {result.stdout.strip()}"
        else:
            cpu_info = "CPU usage: Platform not supported for detailed metrics"

        # Get memory usage
        if platform.system() == "Linux":
            result = subprocess.run(
                ["free", "-h"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            memory_info = result.stdout if result.returncode == 0 else "Memory: Unable to determine"
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            memory_info = result.stdout if result.returncode == 0 else "Memory: Unable to determine"
        else:
            memory_info = "Memory: Platform not supported for detailed metrics"

        # Get disk usage
        result = subprocess.run(
            ["df", "-h"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        disk_info = result.stdout if result.returncode == 0 else "Disk: Unable to determine"

        return f"System Metrics:\n\n{cpu_info}\n\nMemory:\n{memory_info}\n\nDisk Usage:\n{disk_info}"

    except Exception as e:
        error_msg = format_error_message(e, "Failed to get system metrics")
        logger.error(error_msg)
        return error_msg


async def check_service_health(service_name: str) -> str:
    """Check health of a system service.

    Args:
        service_name: Name of the service to check

    Returns:
        Service health status
    """
    try:
        # Check service status using systemctl (Linux) or launchctl (macOS)
        if platform.system() == "Linux":
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                status = result.stdout.strip()
                return f"Service '{service_name}' is {status}."
            else:
                # Try to get more details
                result = subprocess.run(
                    ["systemctl", "status", service_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return f"Service '{service_name}' status:\n{result.stdout}"

        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["launchctl", "list", "|", "grep", service_name],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return f"Service '{service_name}' appears to be running."
            else:
                return f"Service '{service_name}' not found or not running."
        else:
            return f"Service health check not supported on {platform.system()}"

    except FileNotFoundError:
        return f"Unable to check service '{service_name}'. System service manager not available."
    except subprocess.TimeoutExpired:
        return f"Timeout while checking service '{service_name}'."
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to check health for service {service_name}")
        logger.error(error_msg)
        return error_msg


async def get_infrastructure_status() -> str:
    """Get overall infrastructure health status.

    Returns:
        Summary of infrastructure health
    """
    try:
        status_items = []

        # Check Docker if available
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                status_items.append("✓ Docker: Available and running")
            else:
                status_items.append("✗ Docker: Not available or not running")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            status_items.append("✗ Docker: Not installed or not accessible")

        # Check system load
        if platform.system() in ["Linux", "Darwin"]:
            try:
                result = subprocess.run(
                    ["uptime"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    status_items.append(f"✓ System Uptime: {result.stdout.strip()}")
            except Exception:
                pass

        # Overall status
        if not status_items:
            return "Infrastructure Status: Unable to determine (limited platform support)"

        return "Infrastructure Status:\n\n" + "\n".join(status_items)

    except Exception as e:
        error_msg = format_error_message(e, "Failed to get infrastructure status")
        logger.error(error_msg)
        return error_msg
