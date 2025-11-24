"""Load balancing strategies."""

import logging
from typing import List, Optional
from enum import Enum
import random

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"
    IP_HASH = "ip_hash"


class ServerInstance:
    """Server instance for load balancing."""

    def __init__(self, host: str, port: int, weight: int = 1):
        """Initialize server instance.

        Args:
            host: Server host
            port: Server port
            weight: Load balancing weight
        """
        self.host = host
        self.port = port
        self.weight = weight
        self.connections = 0
        self.healthy = True

    def get_url(self) -> str:
        """Get server URL."""
        return f"http://{self.host}:{self.port}"

    def increment_connections(self):
        """Increment connection count."""
        self.connections += 1

    def decrement_connections(self):
        """Decrement connection count."""
        self.connections = max(0, self.connections - 1)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "weight": self.weight,
            "connections": self.connections,
            "healthy": self.healthy,
            "url": self.get_url(),
        }


class LoadBalancer:
    """Load balancer for distributing requests."""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        """Initialize load balancer.

        Args:
            strategy: Load balancing strategy
        """
        self.strategy = strategy
        self.servers: List[ServerInstance] = []
        self.current_index = 0

    def add_server(self, host: str, port: int, weight: int = 1):
        """Add server to load balancer."""
        server = ServerInstance(host, port, weight)
        self.servers.append(server)

        logger.info(f"Server added to load balancer: {server.get_url()}")

    def remove_server(self, host: str, port: int):
        """Remove server from load balancer."""
        self.servers = [s for s in self.servers if not (s.host == host and s.port == port)]

        logger.info(f"Server removed from load balancer: {host}:{port}")

    def get_healthy_servers(self) -> List[ServerInstance]:
        """Get all healthy servers."""
        return [s for s in self.servers if s.healthy]

    def select_server(self, client_ip: str = None) -> Optional[ServerInstance]:
        """Select server based on strategy.

        Args:
            client_ip: Client IP address (for IP_HASH strategy)

        Returns:
            Selected server instance
        """
        healthy = self.get_healthy_servers()

        if not healthy:
            logger.warning("No healthy servers available")
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            server = healthy[self.current_index % len(healthy)]
            self.current_index += 1
            return server

        if self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy, key=lambda s: s.connections)

        if self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy)

        if self.strategy == LoadBalancingStrategy.WEIGHTED:
            # Weighted random selection
            total_weight = sum(s.weight for s in healthy)
            choice = random.uniform(0, total_weight)

            current = 0
            for server in healthy:
                current += server.weight
                if choice <= current:
                    return server

            return healthy[0]

        if self.strategy == LoadBalancingStrategy.IP_HASH:
            if client_ip:
                index = hash(client_ip) % len(healthy)
                return healthy[index]
            else:
                return healthy[self.current_index % len(healthy)]

        return healthy[0]

    def mark_healthy(self, host: str, port: int):
        """Mark server as healthy."""
        for server in self.servers:
            if server.host == host and server.port == port:
                server.healthy = True
                logger.info(f"Server marked healthy: {server.get_url()}")
                break

    def mark_unhealthy(self, host: str, port: int):
        """Mark server as unhealthy."""
        for server in self.servers:
            if server.host == host and server.port == port:
                server.healthy = False
                logger.warning(f"Server marked unhealthy: {server.get_url()}")
                break

    def get_stats(self) -> dict:
        """Get load balancer statistics."""
        healthy = self.get_healthy_servers()
        total_connections = sum(s.connections for s in self.servers)

        return {
            "strategy": self.strategy.value,
            "total_servers": len(self.servers),
            "healthy_servers": len(healthy),
            "unhealthy_servers": len(self.servers) - len(healthy),
            "total_connections": total_connections,
            "servers": [s.to_dict() for s in self.servers],
        }


class AdaptiveLoadBalancer(LoadBalancer):
    """Adaptive load balancer that adjusts based on performance."""

    def __init__(self):
        """Initialize adaptive load balancer."""
        super().__init__(LoadBalancingStrategy.LEAST_CONNECTIONS)
        self.response_times = {}

    def record_response_time(self, host: str, port: int, response_time: float):
        """Record response time for server."""
        key = f"{host}:{port}"

        if key not in self.response_times:
            self.response_times[key] = []

        self.response_times[key].append(response_time)

        # Keep last 100 measurements
        if len(self.response_times[key]) > 100:
            self.response_times[key].pop(0)

    def get_average_response_time(self, host: str, port: int) -> float:
        """Get average response time for server."""
        key = f"{host}:{port}"

        if key not in self.response_times or not self.response_times[key]:
            return 0.0

        times = self.response_times[key]
        return sum(times) / len(times)

    def get_slowest_server(self) -> Optional[ServerInstance]:
        """Get slowest server."""
        if not self.servers:
            return None

        return max(
            self.servers,
            key=lambda s: self.get_average_response_time(s.host, s.port),
        )

    def get_fastest_server(self) -> Optional[ServerInstance]:
        """Get fastest server."""
        if not self.servers:
            return None

        return min(
            self.servers,
            key=lambda s: self.get_average_response_time(s.host, s.port),
        )

    def get_stats(self) -> dict:
        """Get adaptive load balancer statistics."""
        base_stats = super().get_stats()

        response_times = {}
        for server in self.servers:
            key = f"{server.host}:{server.port}"
            avg_time = self.get_average_response_time(server.host, server.port)
            response_times[key] = round(avg_time, 4)

        base_stats["response_times"] = response_times

        return base_stats
