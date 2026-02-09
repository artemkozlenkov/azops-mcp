"""Container management tools."""

import logging
import subprocess

from ..utils.helpers import format_error_message

logger = logging.getLogger(__name__)


async def list_containers() -> str:
    """List running Docker containers.

    Returns:
        Formatted list of containers with their status
    """
    try:
        # Use docker CLI to list containers
        # In production, you might want to use docker-py library instead
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            if "docker" in result.stderr.lower() or "command not found" in result.stderr.lower():
                return "Docker is not installed or not available. Please ensure Docker is installed and running."
            return f"Error listing containers: {result.stderr}"

        if not result.stdout.strip():
            return "No running containers found."

        lines = result.stdout.strip().split("\n")
        formatted_containers = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 4:
                container_id, name, status, image = parts[0], parts[1], parts[2], parts[3]
                formatted_containers.append(f"ID: {container_id[:12]}\nName: {name}\nStatus: {status}\nImage: {image}")

        return "Running Containers:\n\n" + "\n---\n".join(formatted_containers)

    except FileNotFoundError:
        return "Docker is not installed or not in PATH. Please install Docker to use container tools."
    except subprocess.TimeoutExpired:
        return "Timeout while listing containers. Docker may be unresponsive."
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list containers")
        logger.error(error_msg)
        return error_msg


async def get_container_logs(container_id: str, lines: int = 50) -> str:
    """Retrieve logs from a Docker container.

    Args:
        container_id: Container ID or name
        lines: Number of log lines to retrieve (default: 50)

    Returns:
        Container logs
    """
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_id],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return f"Error retrieving logs: {result.stderr}"

        if not result.stdout.strip():
            return f"No logs found for container {container_id}"

        return f"Logs for container {container_id} (last {lines} lines):\n\n{result.stdout}"

    except FileNotFoundError:
        return "Docker is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return "Timeout while retrieving logs. The container may be unresponsive."
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to get logs for container {container_id}")
        logger.error(error_msg)
        return error_msg


async def restart_container(container_id: str) -> str:
    """Restart a Docker container.

    Args:
        container_id: Container ID or name to restart

    Returns:
        Restart operation result
    """
    try:
        result = subprocess.run(
            ["docker", "restart", container_id],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return f"Error restarting container: {result.stderr}"

        return f"Container {container_id} restarted successfully."

    except FileNotFoundError:
        return "Docker is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return "Timeout while restarting container. The container may be unresponsive."
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to restart container {container_id}")
        logger.error(error_msg)
        return error_msg
