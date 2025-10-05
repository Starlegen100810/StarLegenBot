# src/core/pu/pu32_backup.py
from __future__ import annotations

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# ----------------------------
# Small, safe utilities
# ----------------------------

def _now_ts() -> str:
    # 2025-09-13_02-45-30 style
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _safe_serialize(obj: Any) -> Any:
    """
    Try to convert common objects to JSON-serializable primitives.
    Falls back to string if needed. Keeps it ultra-defensive.
    """
    # Common “catalog” patterns:
    for attr in ("to_dict", "dict", "export", "as_dict", "model_dump"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass

    # If it's already JSON-safe-ish, return as is
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in obj.items()}

    # Fallback
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)


def _resolve_backup_dir() -> Path:
    """
    Choose a sensible backups folder:
      1) env BACKUP_DIR if set
      2) <project_root>/backups  (best effort: go 3 parents up from this file)
      3) ./backups (cwd)
    """
    env_dir = os.environ.get("BACKUP_DIR")
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    # Try project root (…/project_root/backups)
    try:
        here = Path(__file__).resolve()
        project_root = here.parents[3]  # pu -> core -> src -> project_root
        p = (project_root / "backups").resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        pass

    # Fallback to current working dir
    p = (Path.cwd() / "backups").resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


# ----------------------------
# Public API implementation
# ----------------------------

def _make_backup(
    *, 
    catalog: Any,
    shop_state: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    keep: int = 10,
) -> Dict[str, Any]:
    """
    Create a timestamped JSON backup file with checksum.
    Returns a small manifest dict with file path & checksum.
    """
    backup_dir = _resolve_backup_dir()

    # build payload
    payload: Dict[str, Any] = {
        "version": 1,
        "created_at": _now_ts(),
        "meta": meta or {},
        "state": {
            # Let the host app provide richer snapshots, if available:
            # e.g. shop_state.get("snapshot") -> dict
            "shop_state_user": _safe_serialize(
                shop_state.get("user_data") or shop_state.get("state") or {}
            ),
            "catalog": _safe_serialize(catalog),
        },
    }

    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    checksum = _sha256_bytes(raw)

    filename = f"starl_backup_{payload['created_at']}_{checksum[:8]}.json"
    fpath = backup_dir / filename
    fpath.write_bytes(raw)

    # Ring buffer – keep only N newest
    _prune_old_backups(backup_dir, keep=keep)

    return {"path": str(fpath), "checksum": checksum, "created_at": payload["created_at"]}


def _prune_old_backups(backup_dir: Path, *, keep: int = 10) -> None:
    files = sorted(
        [p for p in backup_dir.glob("starl_backup_*.json") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for extra in files[keep:]:
        try:
            extra.unlink(missing_ok=True)
        except Exception:
            # do not break on filesystem issues
            pass


def _list_backups() -> List[Dict[str, Any]]:
    backup_dir = _resolve_backup_dir()
    out: List[Dict[str, Any]] = []
    for p in sorted(backup_dir.glob("starl_backup_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            raw = p.read_bytes()
            data = json.loads(raw.decode("utf-8"))
            out.append({
                "path": str(p),
                "created_at": data.get("created_at"),
                "checksum": _sha256_bytes(raw),
                "size_bytes": p.stat().st_size,
            })
        except Exception:
            # Skip corrupted files
            continue
    return out


def _restore_backup(
    *, 
    shop_state: Dict[str, Any],
    path: Optional[str] = None,
    on_apply: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """
    Load a backup (latest if path=None), verify checksum, and apply via `on_apply`
    or an optional hook inside shop_state["backup"]["on_restore"].
    """
    # choose file
    if path is None:
        backups = _list_backups()
        if not backups:
            raise FileNotFoundError("No backups found.")
        path = backups[0]["path"]

    p = Path(path).expanduser().resolve()
    raw = p.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    checksum = _sha256_bytes(raw)

    # validate minimal structure
    if "state" not in data:
        raise ValueError("Invalid backup file: missing 'state' section")

    # pick apply hook
    handler = on_apply
    if handler is None:
        handler = (
            shop_state.get("backup", {}).get("on_restore")
            if isinstance(shop_state.get("backup"), dict)
            else None
        )

    # Apply only if a handler is provided; otherwise just return payload.
    if callable(handler):
        try:
            handler(data["state"])
        except Exception as e:
            # surface but keep the payload for inspection
            raise RuntimeError(f"Restore handler failed: {e}") from e

    return {
        "path": str(p),
        "created_at": data.get("created_at"),
        "checksum": checksum,
        "applied": bool(callable(handler)),
        "state_preview_keys": list(data["state"].keys()),
    }


# ----------------------------
# Entry point (wired into bot)
# ----------------------------

def init(bot, resolve_lang, catalog, shop_state):
    """
    Wires a minimal, safe backup/restore API into shop_state["backup"].

    Exposed methods:
      shop_state["backup"]["make_backup"](meta: dict|None, keep: int=10) -> manifest
      shop_state["backup"]["list_backups"]() -> list[manifest]
      shop_state["backup"]["restore_last"]() -> manifest
      shop_state["backup"]["restore_path"](path: str) -> manifest

    Optional hooks you may set from your app BEFORE restore:
      shop_state["backup"]["on_restore"] = callable(dict_state) -> None
        where dict_state ≈ {"shop_state_user": ..., "catalog": ...}
    """
    # Provide a lightweight default on_restore (no-op) only if not set.
    backup_ns = shop_state.get("backup")
    if not isinstance(backup_ns, dict):
        backup_ns = {}
        shop_state["backup"] = backup_ns

    # Don’t overwrite if user already injected a custom handler earlier.
    backup_ns.setdefault("on_restore", None)

    def make_backup(meta: Optional[Dict[str, Any]] = None, keep: int = 10) -> Dict[str, Any]:
        try:
            # Allow KEEP from env override
            keep_env = os.environ.get("BACKUP_KEEP")
            if keep_env:
                try:
                    keep = max(1, int(keep_env))
                except Exception:
                    pass
            return _make_backup(catalog=catalog, shop_state=shop_state, meta=meta, keep=keep)
        except Exception as e:
            return {"error": str(e)}

    def list_backups() -> List[Dict[str, Any]]:
        try:
            return _list_backups()
        except Exception as e:
            return [{"error": str(e)}]

    def restore_last() -> Dict[str, Any]:
        try:
            return _restore_backup(shop_state=shop_state)
        except Exception as e:
            return {"error": str(e)}

    def restore_path(path: str) -> Dict[str, Any]:
        try:
            return _restore_backup(shop_state=shop_state, path=path)
        except Exception as e:
            return {"error": str(e)}

    # attach API
    backup_ns["make_backup"] = make_backup
    backup_ns["list_backups"] = list_backups
    backup_ns["restore_last"] = restore_last
    backup_ns["restore_path"] = restore_path

    # Optionally expose the resolved folder for UI buttons
    backup_ns["dir"] = str(_resolve_backup_dir())


def init(bot, ctx):
    def feature(bot, m):
        bot.send_message(m.chat.id, "✅ pu32_backup աշխատեց")
    ctx["shop_state"].setdefault("api", {})["backup"] = feature




