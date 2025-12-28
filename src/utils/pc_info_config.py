from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set


@dataclass
class PCInfoCollectorConfig:
    collect_os_info: bool = True
    collect_cpu_info: bool = True
    collect_ram_info: bool = True
    collect_disk_info: bool = True
    collect_network_info: bool = False
    collect_env_vars: bool = False
    collect_python_info: bool = True
    collect_process_info: bool = False

    sensitive_fields: Set[str] = field(
        default_factory=lambda: {
            "network_info",
            "env_vars",
            "process_info",
        }
    )

    def get_warnings(self) -> list[str]:
        warnings = []

        if self.collect_network_info:
            warnings.append(
                "WARNING: Network information may contain sensitive data (IP addresses, network topology). "
                "Consider if this is necessary for your use case."
            )

        if self.collect_env_vars:
            warnings.append(
                "WARNING: Environment variables may contain sensitive data (passwords, API keys, tokens). "
                "Review before sharing this information."
            )

        if self.collect_process_info:
            warnings.append(
                "WARNING: Process information may contain sensitive data (command line arguments with passwords). "
                "Ensure you understand security implications."
            )

        return warnings

    @staticmethod
    def get_safe_default() -> PCInfoCollectorConfig:
        return PCInfoCollectorConfig(
            collect_os_info=True,
            collect_cpu_info=True,
            collect_ram_info=True,
            collect_disk_info=True,
            collect_network_info=False,
            collect_env_vars=False,
            collect_python_info=True,
            collect_process_info=False,
        )

    @staticmethod
    def get_full() -> PCInfoCollectorConfig:
        return PCInfoCollectorConfig(
            collect_os_info=True,
            collect_cpu_info=True,
            collect_ram_info=True,
            collect_disk_info=True,
            collect_network_info=True,
            collect_env_vars=True,
            collect_python_info=True,
            collect_process_info=True,
        )
