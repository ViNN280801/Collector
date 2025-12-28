from __future__ import annotations

from typing import List
from subprocess import run as subprocess_run
from subprocess import CompletedProcess, TimeoutExpired


class ProcessManager:
    @staticmethod
    def run_command(
        cmd: List[str],
        capture_output: bool = True,
        text: bool = True,
        timeout: int = 2,
        check: bool = False,
    ) -> CompletedProcess:
        try:
            return subprocess_run(
                cmd,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                check=check,
            )
        except TimeoutExpired as e:
            return CompletedProcess(args=cmd, returncode=-1, stdout="", stderr=str(e))
        except Exception as e:
            return CompletedProcess(args=cmd, returncode=-1, stdout="", stderr=str(e))
