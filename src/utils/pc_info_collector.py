# StartAllScript/src/utility/pc_info_collector.py

"""
PC Information Collector Module.

This module provides functionality to collect detailed system information
for diagnostics purposes, including OS, CPU, RAM, disk, network, environment
variables, Python environment, and process information.
"""

from os import environ as os_environ
from os.path import exists as os_path_exists

from sys import version as sys_version
from sys import platform as sys_platform
from sys import executable as sys_executable
from sys import version_info as sys_version_info

from json import dump as json_dump
from json import loads as json_loads
from json import JSONDecodeError as json_JSONDecodeError

from platform import system as platform_system
from platform import platform as platform_platform
from platform import release as platform_release
from platform import version as platform_version
from platform import machine as platform_machine
from platform import processor as platform_processor
from platform import architecture as platform_architecture

from psutil import Process as psutil_Process
from psutil import NoSuchProcess as psutil_NoSuchProcess
from psutil import AccessDenied as psutil_AccessDenied
from psutil import cpu_count as psutil_cpu_count
from psutil import cpu_percent as psutil_cpu_percent
from psutil import virtual_memory as psutil_virtual_memory
from psutil import disk_usage as psutil_disk_usage
from psutil import disk_partitions as psutil_disk_partitions
from psutil import net_if_addrs as psutil_net_if_addrs
from psutil import net_connections as psutil_net_connections
from psutil import process_iter as psutil_process_iter

# cpu_freq is not available on all platforms (e.g., macOS in some psutil versions)
# Import it conditionally to handle platform differences
try:
    import psutil

    if hasattr(psutil, "cpu_freq"):
        psutil_cpu_freq = psutil.cpu_freq
    else:
        psutil_cpu_freq = None
except (ImportError, AttributeError):
    # Fallback: cpu_freq not available on this platform/psutil version
    psutil_cpu_freq = None

from subprocess import TimeoutExpired as subprocess_TimeoutExpired

from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .pc_info_config import PCInfoCollectorConfig


IS_WINDOWS = platform_system() == "Windows"


class PCInfoCollector:
    """
    Collects detailed system information for diagnostics.

    This class provides methods to gather comprehensive system information
    including operating system details, CPU specifications, memory usage,
    disk information, network interfaces, environment variables, Python
    environment, and process information related to some processes.

    This class is thread-safe for read-only operations. Multiple threads
    can safely call collect_* methods concurrently.

    Attributes:
        _info (Dict[str, Any]): Collected system information dictionary.
        _module_name (str): Module name for logging purposes.

    Example:
        >>> collector = PCInfoCollector()
        >>> info = collector.collect_all()
        >>> collector.save_to_file("pc_info.json", format="json")
    """

    def __init__(self, config: Optional["PCInfoCollectorConfig"] = None) -> None:
        """
        Initialize PCInfoCollector.

        Creates a new instance of PCInfoCollector with empty information
        dictionary ready for data collection.
        """
        from .pc_info_config import PCInfoCollectorConfig

        self._info: Dict[str, Any] = {}
        self._module_name = "PCInfoCollector"
        self._config = config if config else PCInfoCollectorConfig.get_safe_default()

        for warning in self._config.get_warnings():
            import sys

            print(f"[PCInfoCollector WARNING] {warning}", file=sys.stderr)

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all available system information.

        Gathers comprehensive system information from all available sources
        including OS, CPU, RAM, disks, network, environment variables,
        Python environment.

        This method is exception-safe: if any collection step fails, it
        continues with other steps and returns partial information.

        Returns:
            Dict[str, Any]: Dictionary containing all collected system
                information with the following keys:
                - collection_timestamp: ISO format timestamp
                - os: Operating system information
                - cpu: CPU specifications and usage
                - ram: Memory information
                - disks: Disk partition information
                - network: Network interfaces and connections
                - environment: Environment variables
                - python: Python environment details
                - processes: specified processes

        Note:
            If a collection step fails, the corresponding key will contain
            an empty dictionary or list, but the method will not raise.
        """
        try:
            self._info = {
                "collection_timestamp": datetime.now().isoformat(),
            }

            if self._config.collect_os_info:
                self._info["os"] = self.collect_os_info()

            if self._config.collect_cpu_info:
                self._info["cpu"] = self.collect_cpu_info()

            if self._config.collect_ram_info:
                self._info["ram"] = self.collect_ram_info()

            if self._config.collect_disk_info:
                self._info["disks"] = self.collect_disk_info()

            if self._config.collect_network_info:
                self._info["network"] = self.collect_network_info()

            if self._config.collect_env_vars:
                self._info["environment"] = self.collect_env_vars()

            if self._config.collect_python_info:
                self._info["python"] = self.collect_python_info()

            if self._config.collect_process_info:
                self._info["processes"] = self.collect_process_info(processes_list=[])
        except Exception:
            # If collect_all itself fails, return at least timestamp
            self._info = {
                "collection_timestamp": datetime.now().isoformat(),
                "error": "Failed to collect system information",
            }
        return self._info

    def collect_os_info(self) -> Dict[str, Any]:
        """
        Collect detailed operating system information.

        Gathers platform-specific OS information including version, build
        numbers, and distribution details. On Windows, retrieves build
        number, edition, and SDK version from registry. On Linux, reads
        distribution information from /etc/os-release and kernel version.

        Returns:
            Dict[str, Any]: Dictionary containing OS information with keys:
                - system: Operating system name
                - platform: Platform identifier
                - release: OS release version
                - version: OS version string
                - machine: Machine architecture
                - processor: Processor identifier
                - architecture: System architecture
                - Additional platform-specific keys (Windows/Linux)

        Note:
            Platform-specific information collection may fail silently
            if registry/files are not accessible. Basic platform info
            is always returned.
        """
        info: Dict[str, Any] = {}
        try:
            info = {
                "system": platform_system(),
                "platform": platform_platform(),
                "release": platform_release(),
                "version": platform_version(),
                "machine": platform_machine(),
                "processor": platform_processor(),
                "architecture": platform_architecture()[0],
            }
        except (AttributeError, OSError, ValueError) as e:
            # Fallback to minimal info if platform calls fail
            info = {
                "system": platform_system(),
                "error": f"Failed to collect full OS info: {e}",
            }
            return info

        # Platform-specific information (isolated to prevent cross-platform issues)
        try:
            if IS_WINDOWS:
                windows_info = self._collect_windows_os_info()
                info.update(windows_info)
            else:
                linux_info = self._collect_linux_os_info()
                info.update(linux_info)
        except Exception:
            # Platform-specific info is optional, continue without it
            pass

        return info

    def _collect_windows_os_info(self) -> Dict[str, Any]:
        """
        Collect Windows-specific OS information from registry.

        Returns:
            Dict[str, Any]: Dictionary with Windows-specific OS information.
                Returns empty dict if registry access fails or winreg is
                unavailable.

        Note:
            This method is Windows-only and will not execute on other
            platforms due to IS_WINDOWS check in caller.
        """
        info: Dict[str, Any] = {}
        try:
            import winreg
        except ImportError:
            # winreg not available (shouldn't happen on Windows, but safe)
            return info

        # Get Windows build number
        try:
            key = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
            )
            try:
                info["build_number"] = winreg.QueryValueEx(key, "CurrentBuild")[0]  # type: ignore[attr-defined]
                info["build_string"] = winreg.QueryValueEx(key, "BuildLabEx")[0]  # type: ignore[attr-defined]
                info["display_version"] = winreg.QueryValueEx(key, "DisplayVersion")[0]  # type: ignore[attr-defined]
                info["edition"] = winreg.QueryValueEx(key, "EditionID")[0]  # type: ignore[attr-defined]
                info["product_name"] = winreg.QueryValueEx(key, "ProductName")[0]  # type: ignore[attr-defined]
            finally:
                winreg.CloseKey(key)  # type: ignore[attr-defined]
        except (OSError, FileNotFoundError, PermissionError):
            # Registry key doesn't exist or no permission
            pass
        except Exception:
            # Other registry errors (shouldn't happen, but be safe)
            pass

        # Get Windows SDK version if available
        try:
            key = winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                r"SOFTWARE\WOW6432Node\Microsoft\Microsoft SDKs\Windows\v10.0",
            )
            try:
                info["sdk_version"] = winreg.QueryValueEx(key, "ProductVersion")[0]  # type: ignore[attr-defined]
            finally:
                winreg.CloseKey(key)  # type: ignore[attr-defined]
        except (OSError, FileNotFoundError, PermissionError):
            # SDK registry key doesn't exist or no permission
            pass
        except Exception:
            # Other registry errors
            pass

        return info

    def _collect_linux_os_info(self) -> Dict[str, Any]:
        """
        Collect Linux-specific OS information.

        Returns:
            Dict[str, Any]: Dictionary with Linux-specific OS information.
                Returns empty dict if files are not accessible.

        Note:
            This method is Linux-only and will not execute on Windows
            due to IS_WINDOWS check in caller.
        """
        from .process_manager import ProcessManager

        info: Dict[str, Any] = {}

        # Try to get distribution info
        try:
            if os_path_exists("/etc/os-release"):
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            try:
                                key, value = line.split("=", 1)
                                value = value.strip('"').strip("'")
                                info[f"os_{key.lower()}"] = value
                            except ValueError:
                                # Malformed line, skip
                                continue
        except (OSError, PermissionError, UnicodeDecodeError):
            # File doesn't exist, no permission, or encoding issue
            pass
        except Exception:
            # Other file reading errors
            pass

        # Get kernel version
        try:
            result = ProcessManager.run_command(
                ["uname", "-r"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                info["kernel_version"] = result.stdout.strip()
        except (subprocess_TimeoutExpired, FileNotFoundError):
            # uname not found or timeout
            pass
        except Exception:
            # Other subprocess errors
            pass

        # Get libc version
        try:
            result = ProcessManager.run_command(
                ["ldd", "--version"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.split("\n")
                if lines:
                    info["libc_version"] = lines[0].strip()
        except (subprocess_TimeoutExpired, FileNotFoundError):
            # ldd not found or timeout
            pass
        except Exception:
            # Other subprocess errors
            pass

        return info

    def collect_cpu_info(self) -> Dict[str, Any]:
        """
        Collect CPU information.

        Gathers CPU specifications including physical and logical core counts,
        frequency information, and CPU model name. Uses psutil when available
        for accurate hardware information.

        Returns:
            Dict[str, Any]: Dictionary containing CPU information with keys:
                - physical_cores: Number of physical CPU cores (None if unavailable)
                - logical_cores: Number of logical CPU cores (None if unavailable)
                - max_frequency: Maximum CPU frequency (MHz, None if unavailable)
                - min_frequency: Minimum CPU frequency (MHz, None if unavailable)
                - current_frequency: Current CPU frequency (MHz, None if unavailable)
                - architecture: CPU architecture
                - cpu_percent: Current CPU usage percentage (None if unavailable)
                - model: CPU model name (None if unavailable)
        """
        info: Dict[str, Any] = {
            "physical_cores": None,
            "logical_cores": None,
            "max_frequency": None,
            "min_frequency": None,
            "current_frequency": None,
            "architecture": platform_machine(),
        }

        try:
            physical_cores = psutil_cpu_count(logical=False)
            logical_cores = psutil_cpu_count(logical=True)
            info["physical_cores"] = physical_cores
            info["logical_cores"] = logical_cores

            try:
                if psutil_cpu_freq is not None:
                    cpu_freq = psutil_cpu_freq()
                    if cpu_freq is not None:
                        info["max_frequency"] = cpu_freq.max
                        info["min_frequency"] = cpu_freq.min
                        info["current_frequency"] = cpu_freq.current
            except Exception:
                # CPU frequency not available on all systems (e.g., macOS, some Linux systems)
                pass

            try:
                info["cpu_percent"] = psutil_cpu_percent(interval=0.1)
            except Exception:
                # CPU percent may fail in some environments
                pass
        except (AttributeError, OSError) as e:
            # psutil API changed or system call failed
            info["psutil_error"] = str(e)
        except Exception:
            # Other psutil errors
            pass

        # Get CPU model name (platform-specific, isolated)
        try:
            if IS_WINDOWS:
                cpu_model = self._get_windows_cpu_model()
            else:
                cpu_model = self._get_linux_cpu_model()
            if cpu_model:
                info["model"] = cpu_model
        except Exception:
            # CPU model detection failed, continue without it
            pass

        return info

    def _get_windows_cpu_model(self) -> Optional[str]:
        """
        Get CPU model name on Windows using wmic.

        Returns:
            Optional[str]: CPU model name if found, None otherwise.

        Note:
            This method is Windows-specific and should only be called
            when IS_WINDOWS is True.
        """
        from .process_manager import ProcessManager

        try:
            result = ProcessManager.run_command(
                ["wmic", "cpu", "get", "name"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
                if len(lines) > 1:
                    # First line is header, second is value
                    return lines[1] if len(lines) > 1 else None
        except (subprocess_TimeoutExpired, FileNotFoundError):
            # wmic not found or timeout
            pass
        except Exception:
            # Other subprocess errors
            pass
        return None

    def _get_linux_cpu_model(self) -> Optional[str]:
        """
        Get CPU model name on Linux from /proc/cpuinfo.

        Returns:
            Optional[str]: CPU model name if found, None otherwise.

        Note:
            This method is Linux-specific and should only be called
            when IS_WINDOWS is False.
        """
        try:
            if os_path_exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                    for line in f:
                        line_lower = line.lower()
                        if "model name" in line_lower and ":" in line:
                            try:
                                return line.split(":", 1)[1].strip()
                            except (IndexError, ValueError):
                                # Malformed line
                                continue
        except (OSError, PermissionError, UnicodeDecodeError):
            # File doesn't exist, no permission, or encoding issue
            pass
        except Exception:
            # Other file reading errors
            pass
        return None

    def collect_ram_info(self) -> Dict[str, Any]:
        """
        Collect RAM (memory) information.

        Gathers memory statistics including total, available, used memory,
        and memory usage percentage using psutil.

        Returns:
            Dict[str, Any]: Dictionary containing RAM information with keys:
                - total: Total physical memory (bytes, None if unavailable)
                - available: Available memory (bytes, None if unavailable)
                - used: Used memory (bytes, None if unavailable)
                - percent: Memory usage percentage (None if unavailable)
        """
        info: Dict[str, Any] = {
            "total": None,
            "available": None,
            "used": None,
            "percent": None,
        }

        try:
            mem = psutil_virtual_memory()
            info["total"] = mem.total
            info["available"] = mem.available
            info["used"] = mem.used
            info["percent"] = mem.percent
        except (AttributeError, OSError) as e:
            # psutil API changed or system call failed
            info["error"] = str(e)
        except Exception:
            # Other psutil errors
            pass

        return info

    def collect_disk_info(self) -> List[Dict[str, Any]]:
        """
        Collect disk partition information.

        Gathers information about all disk partitions including device name,
        mount point, filesystem type, and usage statistics.

        Returns:
            List[Dict[str, Any]]: List of dictionaries, each containing:
                - device: Device name
                - mountpoint: Mount point path
                - fstype: Filesystem type
                - total: Total disk space (bytes)
                - used: Used disk space (bytes)
                - free: Free disk space (bytes)
                - percent: Disk usage percentage
            Empty list if psutil is unavailable or all partitions fail.
        """
        disks: List[Dict[str, Any]] = []

        try:
            partitions = psutil_disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil_disk_usage(partition.mountpoint)
                    disks.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                        }
                    )
                except PermissionError:
                    # Skip partitions we can't access
                    continue
                except OSError:
                    # Partition may have been unmounted or is invalid
                    continue
                except Exception:
                    # Other errors accessing partition
                    continue
        except (AttributeError, OSError):
            # psutil API changed or system call failed
            pass
        except Exception:
            # Other psutil errors
            pass

        return disks

    def collect_network_info(self) -> Dict[str, Any]:
        """
        Collect network interface and connection information.

        Gathers network interface addresses and active network connections.
        Limited to 50 connections to avoid excessive data collection.

        Returns:
            Dict[str, Any]: Dictionary containing network information with:
                - interfaces: List of network interfaces with addresses
                - connections: List of active network connections (max 50)
            Both lists may be empty if psutil is unavailable or access denied.
        """
        info: Dict[str, Any] = {
            "interfaces": [],
            "connections": [],
        }

        try:
            # Get network interfaces
            try:
                net_if_addrs = psutil_net_if_addrs()
                for interface_name, addresses in net_if_addrs.items():
                    interface_info: Dict[str, Any] = {
                        "name": interface_name,
                        "addresses": [],
                    }
                    for addr in addresses:
                        try:
                            interface_info["addresses"].append(
                                {
                                    "family": str(addr.family),
                                    "address": addr.address,
                                    "netmask": addr.netmask,
                                    "broadcast": addr.broadcast,
                                }
                            )
                        except (AttributeError, ValueError):
                            # Address object malformed
                            continue
                    info["interfaces"].append(interface_info)
            except (AttributeError, OSError):
                # psutil API changed or system call failed
                pass
            except Exception:
                # Other errors
                pass

            # Get active connections (limited to avoid too much data)
            try:
                connections = psutil_net_connections(kind="inet")
                connection_count = 0
                max_connections = 50
                for conn in connections:
                    if connection_count >= max_connections:
                        break
                    try:
                        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None
                        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
                        info["connections"].append(
                            {
                                "status": str(conn.status),
                                "local_address": local_addr,
                                "remote_address": remote_addr,
                                "family": str(conn.family),
                                "type": str(conn.type),
                            }
                        )
                        connection_count += 1
                    except (AttributeError, ValueError):
                        # Connection object malformed
                        continue
            except (psutil_AccessDenied, PermissionError):
                # May require elevated privileges
                pass
            except (AttributeError, OSError):
                # psutil API changed or system call failed
                pass
            except Exception:
                # Other errors
                pass
        except Exception:
            # Top-level exception handler for safety
            pass

        return info

    def collect_env_vars(self) -> Dict[str, str]:
        """
        Collect relevant environment variables.

        Gathers platform-specific environment variables that are relevant
        for diagnostics. Windows and Linux have different sets of important
        environment variables.

        Returns:
            Dict[str, str]: Dictionary mapping environment variable names
                to their values. Only includes variables that are set.
                Empty dict if environment access fails.
        """
        env_vars: Dict[str, str] = {}

        try:
            if IS_WINDOWS:
                windows_vars = [
                    "HOME",
                    "PATH",
                    "TEMP",
                    "TMP",
                    "USERPROFILE",
                    "APPDATA",
                    "LOCALAPPDATA",
                    "PROGRAMFILES",
                    "PROGRAMFILES(X86)",
                    "SYSTEMROOT",
                    "WINDIR",
                    "COMPUTERNAME",
                    "USERNAME",
                ]
                for var in windows_vars:
                    try:
                        value = os_environ.get(var)
                        if value is not None:
                            env_vars[var] = value
                    except (KeyError, TypeError):
                        # Environment variable access failed
                        continue
            else:
                linux_vars = [
                    "HOME",
                    "PATH",
                    "LD_LIBRARY_PATH",
                    "USER",
                    "SHELL",
                    "DISPLAY",
                    "XDG_RUNTIME_DIR",
                    "DBUS_SESSION_BUS_ADDRESS",
                    "PKEXEC_UID",
                    "LOGNAME",
                    "LANG",
                    "LC_ALL",
                ]
                for var in linux_vars:
                    try:
                        value = os_environ.get(var)
                        if value is not None:
                            env_vars[var] = value
                    except (KeyError, TypeError):
                        # Environment variable access failed
                        continue
        except Exception:
            # Environment access completely failed
            pass

        return env_vars

    def collect_python_info(self) -> Dict[str, Any]:
        """
        Collect Python environment information.

        Gathers Python version, executable path, and relevant installed
        packages. Only includes packages related to dependencies
        to avoid excessive data.

        Returns:
            Dict[str, Any]: Dictionary containing Python information with:
                - version: Python version string
                - version_info: Python version tuple as list
                - executable: Python executable path
                - platform: Python platform identifier
                - relevant_packages: List of relevant installed packages
                  (may be missing if pip is unavailable)
        """
        from .process_manager import ProcessManager

        info: Dict[str, Any] = {
            "version": sys_version,
            "version_info": list(sys_version_info),
            "executable": sys_executable,
            "platform": sys_platform,
        }

        # Try to get installed packages (optional, may be slow)
        try:
            result = ProcessManager.run_command(
                [sys_executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                try:
                    packages = json_loads(result.stdout)
                    if isinstance(packages, list):
                        # Only include relevant packages
                        relevant_keywords = [
                            "psutil",
                            "pyyaml",
                            "requests",
                            "pyserial",
                            "screeninfo",
                        ]
                        relevant_packages = [
                            pkg
                            for pkg in packages
                            if isinstance(pkg, dict)
                            and "name" in pkg
                            and any(keyword in pkg["name"].lower() for keyword in relevant_keywords)
                        ]
                        if relevant_packages:
                            info["relevant_packages"] = relevant_packages
                except (json_JSONDecodeError, TypeError, KeyError):
                    # Invalid JSON or malformed package data
                    pass
        except (subprocess_TimeoutExpired, FileNotFoundError):
            # pip not found or timeout
            pass
        except Exception:
            # Other subprocess errors
            pass

        return info

    def collect_process_info(self, processes_list: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        """
        Collect information about specified list of related processes.

        Scans running processes and collects detailed information about
        processes related to specified list, including Node.js, Electron,
        RabbitMQ, and Erlang processes.

        Returns:
            List[Dict[str, Any]]: List of process information dictionaries
                containing:
                - pid: Process ID
                - name: Process name
                - cmdline: Command line arguments
                - status: Process status
                - cpu_percent: CPU usage percentage
                - memory_info: Memory usage (RSS, VMS)
                - memory_percent: Memory usage percentage
                - create_time: Process creation time (ISO format)
                - username: Process owner username
            Empty list if psutil is unavailable or process iteration fails.
        """
        processes: List[Dict[str, Any]] = []

        try:
            for proc in psutil_process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_info = proc.info
                    if not proc_info:
                        continue

                    name = proc_info.get("name", "")
                    if not isinstance(name, str):
                        name = str(name)
                    name = name.lower()

                    cmdline_list = proc_info.get("cmdline", [])
                    if not isinstance(cmdline_list, list):
                        cmdline_list = []
                    cmdline = " ".join(str(arg) for arg in cmdline_list).lower()

                    # Check if process is related to specified keywords
                    if processes_list is None:
                        processes_list = []
                    is_related = any(keyword in name or keyword in cmdline for keyword in processes_list)

                    if not is_related:
                        continue

                    try:
                        proc_obj = psutil_Process(proc_info["pid"])
                        process_data: Dict[str, Any] = {
                            "pid": proc_info["pid"],
                            "name": proc_info.get("name", "unknown"),
                            "cmdline": cmdline_list,
                            "status": str(proc_obj.status()),
                        }

                        try:
                            process_data["cpu_percent"] = proc_obj.cpu_percent(interval=0.1)
                        except Exception:
                            process_data["cpu_percent"] = None

                        try:
                            mem_info = proc_obj.memory_info()
                            process_data["memory_info"] = {
                                "rss": mem_info.rss,
                                "vms": mem_info.vms,
                            }
                            process_data["memory_percent"] = proc_obj.memory_percent()
                        except Exception:
                            process_data["memory_info"] = None
                            process_data["memory_percent"] = None

                        try:
                            create_time = proc_obj.create_time()
                            process_data["create_time"] = datetime.fromtimestamp(create_time).isoformat()
                        except (OSError, ValueError):
                            process_data["create_time"] = None

                        try:
                            process_data["username"] = proc_obj.username()
                        except Exception:
                            process_data["username"] = None

                        processes.append(process_data)
                    except (psutil_NoSuchProcess, psutil_AccessDenied):
                        # Process may have terminated or no access
                        processes.append(
                            {
                                "pid": proc_info["pid"],
                                "name": proc_info.get("name", "unknown"),
                                "cmdline": cmdline_list,
                                "status": "unavailable",
                            }
                        )
                except (psutil_NoSuchProcess, psutil_AccessDenied):
                    # Process disappeared or no access
                    continue
                except (AttributeError, ValueError, TypeError):
                    # Process info malformed
                    continue
                except Exception:
                    # Other errors processing individual process
                    continue
        except (AttributeError, OSError):
            # psutil API changed or system call failed
            pass
        except Exception:
            # Other errors in process iteration
            pass

        return processes

    def save_to_file(self, filepath: str, format: str = "json") -> None:
        """
        Save collected information to file.

        Writes the collected system information to a file in either JSON
        or human-readable text format. Creates parent directories if needed.

        Args:
            filepath: Path to output file where information will be saved.
            format: Output format, either "json" or "text". Defaults to "json".

        Raises:
            OSError: If file cannot be written (permissions, disk space, etc.).
            ValueError: If format is not "json" or "text".
            TypeError: If filepath is not a string.

        Example:
            >>> collector = PCInfoCollector()
            >>> collector.collect_all()
            >>> collector.save_to_file("pc_info.json", format="json")
            >>> collector.save_to_file("pc_info.txt", format="text")
        """
        if not isinstance(filepath, str):
            raise TypeError(f"filepath must be a string, got {type(filepath)}")

        if not self._info:
            self.collect_all()

        filepath_obj = Path(filepath)
        try:
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise OSError(f"Cannot create parent directory for {filepath}: {e}") from e

        if format.lower() == "json":
            try:
                with open(filepath_obj, "w", encoding="utf-8") as f:
                    json_dump(self._info, f, indent=2, ensure_ascii=False)
            except (OSError, PermissionError) as e:
                raise OSError(f"Cannot write to file {filepath}: {e}") from e
            except (TypeError, ValueError) as e:
                raise ValueError(f"Cannot serialize data to JSON: {e}") from e
        elif format.lower() == "text":
            try:
                self._save_text_format(filepath_obj)
            except (OSError, PermissionError) as e:
                raise OSError(f"Cannot write to file {filepath}: {e}") from e
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'text'.")

    def _save_text_format(self, filepath_obj: Path) -> None:
        """
        Save information in human-readable text format.

        Args:
            filepath_obj: Path object for output file.

        Raises:
            OSError: If file cannot be written.
        """
        try:
            with open(filepath_obj, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("System Information\n")
                f.write("=" * 80 + "\n\n")
                timestamp = self._info.get("collection_timestamp", "unknown")
                f.write(f"Collection Time: {timestamp}\n\n")

                for section, data in self._info.items():
                    if section == "collection_timestamp":
                        continue
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"{section.upper()}\n")
                    f.write(f"{'=' * 80}\n")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            f.write(f"{key}: {value}\n")
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                f.write("\n")
                                for key, value in item.items():
                                    f.write(f"  {key}: {value}\n")
                            else:
                                f.write(f"{item}\n")
                    else:
                        f.write(f"{data}\n")
        except (OSError, PermissionError) as e:
            raise OSError(f"Cannot write text format to {filepath_obj}: {e}") from e
