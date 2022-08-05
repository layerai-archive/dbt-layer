from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LayerCredentials:
    # Layer config json creds
    layer_configfile: Optional[str] = None
    layer_configfile_json: Optional[Dict[str, Any]] = None
    layer_project: Optional[str] = None
    layer_api_key: Optional[str] = None
