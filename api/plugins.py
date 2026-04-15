"""
Plugin dispatcher: resolves task.tool_name to a callable and executes it.

Layout expected on disk::

    plugins/
        ocr_tool.py          # must define handle(task) -> dict
        summarise_tool.py
        ...

``run(task)`` is the only public entry-point.  It never raises; every
failure path transitions the task to ``failed`` and records a structured
error in ``output_data``.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import types
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

logger = logging.getLogger(__name__)

# Resolved once at import time.  All path-safety checks are relative to this.
PLUGINS_DIR: Path = (settings.BASE_DIR / "plugins").resolve()

# Loaded modules are cached so each plugin file is exec'd only once per process.
_cache: dict[str, types.ModuleType] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_module(tool_name: str) -> types.ModuleType:
    """
    Import the plugin module for *tool_name* and return it.

    The result is stored in ``_cache`` so subsequent calls are free.

    Raises
    ------
    ImportError
        If the file cannot be loaded (syntax error, bad import, etc.).
    ImproperlyConfigured
        If the module loads successfully but does not define a callable
        ``handle`` function.
    """
    if tool_name in _cache:
        return _cache[tool_name]

    plugin_path = PLUGINS_DIR / f"{tool_name}.py"

    spec = importlib.util.spec_from_file_location(
        f"plugins.{tool_name}", plugin_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot build import spec for {plugin_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    if not callable(getattr(module, "handle", None)):
        raise ImproperlyConfigured(
            f"Plugin '{plugin_path}' must define a callable handle(task) function."
        )

    _cache[tool_name] = module
    return module


def _fail_task(task, output: dict) -> None:
    """Transition *task* to failed and write *output* as JSON to output_data."""
    task.status = "failed"
    task.completed_at = timezone.now()
    task.output_data = json.dumps(output)
    task.save(update_fields=["status", "completed_at", "output_data"])


def _is_safe_tool_name(name: str) -> bool:
    """
    Return True only if *name* is a plain Python identifier and not a
    private/dunder name.  This rejects path separators, dots, hyphens,
    and anything else that could be used to escape the plugins directory.
    """
    return bool(name) and name.isidentifier() and not name.startswith("_")


# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def validate_all_plugins() -> None:
    """
    Scan ``plugins/`` and pre-validate every plugin that is present now.

    Called from ``ApiConfig.ready()`` so broken plugins are caught at server
    startup rather than at the moment a task is first dispatched.

    Raises
    ------
    ImproperlyConfigured
        Immediately on the first plugin that is missing ``handle`` or that
        fails to import.
    """
    if not PLUGINS_DIR.exists():
        logger.debug("plugins/ directory not found — skipping plugin validation")
        return

    for plugin_file in sorted(PLUGINS_DIR.glob("*.py")):
        if not _is_safe_tool_name(plugin_file.stem):
            # Skip __init__.py, _private.py, etc.
            continue

        tool_name = plugin_file.stem
        try:
            _load_module(tool_name)
            logger.debug("Plugin loaded OK: %s", tool_name)
        except ImproperlyConfigured:
            raise  # already has a clear message — let it propagate
        except Exception as exc:
            raise ImproperlyConfigured(
                f"Plugin '{plugin_file.name}' failed to import: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def run(task) -> None:
    """
    Resolve ``task.tool_name`` to a plugin and execute it.

    Outcome A — success:
        ``handle(task)`` returns a JSON-serialisable dict.
        ``task.status`` is set to ``"completed"`` and the result is stored
        in ``task.output_data``.

    Outcome B — any failure:
        ``task.status`` is set to ``"failed"`` and a structured error dict
        is stored in ``task.output_data``.  This function never raises.

    Failure sub-cases
    -----------------
    * No plugin file for the tool_name → ``{"error": "unknown_tool"}``
    * Plugin raises an exception      → ``{"error": "plugin_error"}``   (full traceback logged)
    * Result is not JSON-serialisable → ``{"error": "non_serializable_result"}``
    """
    tool_name = task.tool_name

    # --- Safety gate -------------------------------------------------------
    # isidentifier() rejects "/", ".", "-", spaces, and all other characters
    # that could be used to form a path traversal.  The startswith("_") check
    # also blocks attempts to load __init__ or private modules.
    if not _is_safe_tool_name(tool_name):
        logger.error(
            "Task %s: tool_name %r is not a safe identifier — rejecting",
            task.task_id,
            tool_name,
        )
        _fail_task(task, {"error": "unknown_tool"})
        return

    plugin_path = PLUGINS_DIR / f"{tool_name}.py"

    # Belt-and-suspenders: even after the identifier check, verify the
    # resolved path stays inside PLUGINS_DIR (guards against exotic symlinks).
    if plugin_path.resolve().parent != PLUGINS_DIR:
        logger.error(
            "Task %s: resolved plugin path %s escapes plugins dir",
            task.task_id,
            plugin_path,
        )
        _fail_task(task, {"error": "unknown_tool"})
        return

    # --- Plugin lookup ------------------------------------------------------
    if not plugin_path.exists():
        logger.warning(
            "Task %s: no plugin found for tool_name %r", task.task_id, tool_name
        )
        _fail_task(task, {"error": "unknown_tool"})
        return

    # --- Import (cached) ----------------------------------------------------
    try:
        module = _load_module(tool_name)
    except Exception:
        logger.exception(
            "Task %s: failed to import plugin %r", task.task_id, tool_name
        )
        _fail_task(task, {"error": "plugin_error", "tool_name": tool_name})
        return

    # --- Execute ------------------------------------------------------------
    try:
        result = module.handle(task)
    except Exception:
        logger.exception(
            "Task %s: plugin %r raised an exception during handle()",
            task.task_id,
            tool_name,
        )
        _fail_task(task, {"error": "plugin_error", "tool_name": tool_name})
        return

    # --- Serialise ----------------------------------------------------------
    try:
        output_json = json.dumps(result)
    except TypeError:
        logger.exception(
            "Task %s: plugin %r returned a non-JSON-serialisable value: %r",
            task.task_id,
            tool_name,
            result,
        )
        _fail_task(task, {"error": "non_serializable_result", "tool_name": tool_name})
        return

    # --- Persist ------------------------------------------------------------
    task.status = "completed"
    task.completed_at = timezone.now()
    task.output_data = output_json
    task.save(update_fields=["status", "completed_at", "output_data"])
    logger.info("Task %s completed via plugin %r", task.task_id, tool_name)
