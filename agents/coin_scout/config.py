import yaml
from dataclasses import dataclass
from typing import Dict, List
from .dex_scanner import DEXConfig

@dataclass
class DetectionConfig:
    min_liquidity: int
    max_age_hours: int
    volume_threshold: float
    blacklisted_tokens: List[str]

@dataclass
class CoinScoutConfig:
    grpc_port: int
    scan_interval: int
    dex_list: List[str]
    dex_config: DEXConfig
    detection_config: DetectionConfig
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'CoinScoutConfig':
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        dex_config = DEXConfig(**config_data['dex_config'])
        detection_config = DetectionConfig(**config_data['detection_config'])
        
        return cls(
            grpc_port=config_data['grpc_port'],
            scan_interval=config_data['scan_interval'],
            dex_list=config_data['dex_list'],
            dex_config=dex_config,
            detection_config=detection_config
        )
