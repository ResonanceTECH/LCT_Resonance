from app.core.config import get_settings
from app.integrations.fsp.mock import MockFSPAdapter
from app.integrations.fsp.real import RealFSPAdapter


def get_fsp_adapter():
    provider = get_settings().fsp_provider.lower()
    if provider == "real":
        return RealFSPAdapter()
    return MockFSPAdapter()
