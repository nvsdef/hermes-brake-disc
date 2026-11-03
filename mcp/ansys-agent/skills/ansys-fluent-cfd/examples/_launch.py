"""
Fluent launch helper with retry logic for transient gRPC port conflicts.

When Fluent sessions launch back-to-back, the OS sometimes hasn't released
the previous session's RPC port yet, causing 'Connection refused'.
This helper retries with a wait to work around it.
"""
import time


def launch_fluent_with_retry(mode="solver", max_retries=3, retry_wait=15, **kwargs):
    """
    Launch Fluent, retrying on transient connection failures.

    Args:
        mode: "solver" or "meshing".
        max_retries: Total attempts (default 3).
        retry_wait: Seconds between attempts (default 15).
        **kwargs: Passed through to pyfluent.launch_fluent().

    Returns:
        Fluent session.
    """
    import ansys.fluent.core as pyfluent

    defaults = {
        "product_version": "26.1.0",
        "ui_mode": "no_gui",
        "precision": "double",
        "processor_count": 2,
    }
    defaults.update(kwargs)
    defaults["mode"] = mode

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[launch] Attempt {attempt}/{max_retries}: Fluent {mode}...")
            session = pyfluent.launch_fluent(**defaults)
            if attempt > 1:
                print(f"[launch] Succeeded on attempt {attempt}")
            return session
        except Exception as e:
            last_err = e
            err_name = type(e).__name__
            print(f"[launch] Attempt {attempt} failed: {err_name}")
            if attempt < max_retries:
                print(f"[launch] Waiting {retry_wait}s before retry...")
                time.sleep(retry_wait)

    raise RuntimeError(
        f"Failed to launch Fluent ({mode}) after {max_retries} attempts. "
        f"Last error: {last_err}"
    )
