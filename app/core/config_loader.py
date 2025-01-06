import os
import yaml
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, base_dir: str = "app/instances"):
        # 获取工作目录的绝对路径
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.base_dir = os.path.normpath(os.path.join(root_dir, base_dir))
        
    def _resolve_path(self, path: str) -> str:
        """解析相对路径为绝对路径"""
        if os.path.isabs(path):
            return path
        # 如果路径已经包含 base_dir，直接返回
        if path.startswith(self.base_dir):
            return path
        # 如果路径以 base_dir 的最后一部分开头，去掉这部分
        base_name = os.path.basename(self.base_dir)
        if path.startswith(base_name):
            path = path[len(base_name)+1:]
        return os.path.normpath(os.path.join(self.base_dir, path))
        
    def _load_yaml(self, file_path: str) -> Optional[Dict[str, Any]]:
        """加载单个 YAML 文件"""
        try:
            with open(self._resolve_path(file_path), 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading YAML file {file_path}: {e}")
            return None
            
    def _merge_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个配置"""
        merged = {"models": [], "tools": []}
        for config in configs:
            if not config:
                continue
            for key in merged:
                if key in config and isinstance(config[key], list):
                    merged[key].extend(config[key])
        return merged
        
    def load_config(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件，支持 includes"""
        # 首先解析主配置文件的路径
        resolved_path = self._resolve_path(file_path)
        config = self._load_yaml(resolved_path)
        if not config:
            return {}
            
        # 如果有 includes，加载所有包含的文件
        if "includes" in config:
            included_configs = []
            base_dir = os.path.dirname(resolved_path)  # 使用解析后的路径
            
            for include in config["includes"]:
                # 使用相对于主配置文件的路径
                include_path = os.path.join(base_dir, include)
                included_config = self._load_yaml(include_path)
                if included_config:
                    included_configs.append(included_config)
                    
            return self._merge_configs(included_configs)
            
        return config 