"""Ensure the Windows python3 Jupyter kernel resolves to the active project interpreter."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys
import tempfile

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from jupyter_client import KernelManager


def main() -> int:
    child_env = os.environ.copy()
    child_env["PATH"] = str(Path(sys.executable).resolve().parent) + os.pathsep + child_env.get("PATH", "")
    child_env["IPYTHONDIR"] = str(Path(tempfile.gettempdir()) / "xoaif_ipython")
    manager = KernelManager(kernel_name="python3")
    client = None
    try:
        manager.start_kernel(env=child_env)
        client = manager.client()
        client.start_channels()
        client.wait_for_ready(timeout=30)
        message_id = client.execute("import sys; print(sys.executable)")
        actual = None
        while True:
            message = client.get_iopub_msg(timeout=30)
            if message.get("parent_header", {}).get("msg_id") != message_id:
                continue
            if message.get("msg_type") == "stream":
                actual = message.get("content", {}).get("text", "").strip()
            if message.get("msg_type") == "status" and message.get("content", {}).get("execution_state") == "idle":
                break
        if not actual:
            raise RuntimeError("kernel did not report its interpreter")
        if os.path.normcase(os.path.realpath(actual)) != os.path.normcase(os.path.realpath(sys.executable)):
            raise RuntimeError("kernel resolved a different Python interpreter")
        print(f"Jupyter kernel verified: {actual}")
        return 0
    except Exception as exc:
        print(f"Jupyter kernel verification failed ({type(exc).__name__}).")
        return 1
    finally:
        if client is not None:
            client.stop_channels()
        try:
            manager.shutdown_kernel(now=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
