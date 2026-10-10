from functools import lru_cache

from app.core.config import get_settings
from app.integrations.fsp.base import FSPAdapter, FSPUnavailableError
from app.integrations.fsp.mock import MockFSPAdapter
from app.integrations.fsp.real import RealFSPAdapter


@lru_cache
def get_fsp_adapter() -> FSPAdapter:
    if get_settings().fsp_provider.lower() == "real":
        return RealFSPAdapter()
    return MockFSPAdapter()


__all__ = ["FSPAdapter", "FSPUnavailableError", "get_fsp_adapter"]
