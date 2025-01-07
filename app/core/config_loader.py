import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache
import os

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, base_dir: str = "app/instances"):
        # 获取工作目录的绝对路径
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.base_dir = os.path.normpath(os.path.join(root_dir, base_dir))
        self._config_cache = {}
        
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
        
    @lru_cache(maxsize=32)
    def _load_yaml(self, file_path: str) -> Optional[Dict[str, Any]]:
        """加载单个 YAML 文件，使用 LRU 缓存"""
        try:
            cache_key = os.path.abspath(file_path)
            if cache_key in self._config_cache:
                logger.debug(f"Using cached config for {file_path}")
                return self._config_cache[cache_key]

            with open(self._resolve_path(file_path), 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # 应用环境变量覆盖
                config = self._apply_env_overrides(config)
                self._config_cache[cache_key] = config
                return config
        except Exception as e:
            logger.error(f"Error loading YAML file {file_path}: {e}")
            return None
            
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖配置"""
        if not config:
            return config

        def process_value(key: str, value: Any) -> Any:
            env_key = f"CONFIG_{key.upper()}"
            if isinstance(value, dict):
                return {k: process_value(f"{key}_{k}", v) for k, v in value.items()}
            elif isinstance(value, list):
                return value  # 列表暂时不支持环境变量覆盖
            else:
                env_value = os.getenv(env_key)
                if env_value is not None:
                    logger.info(f"Overriding config value {key} with environment variable {env_key}")
                    # 尝试转换环境变量值为原始值的类型
                    try:
                        if isinstance(value, bool):
                            return env_value.lower() in ('true', '1', 'yes')
                        elif isinstance(value, int):
                            return int(env_value)
                        elif isinstance(value, float):
                            return float(env_value)
                        else:
                            return env_value
                    except ValueError:
                        logger.warning(f"Failed to convert environment variable {env_key} to type {type(value)}")
                        return value
                return value

        return {k: process_value(k, v) for k, v in config.items()}
            
    def _merge_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个配置"""
        merged = {"models": [], "tools": []}
        for config in configs:
            if not config:
                continue
            logger.info(f"Merging config: {config}")
            for key in merged:
                if key in config and isinstance(config[key], list):
                    merged[key].extend(config[key])
                    logger.info(f"Added {len(config[key])} items to {key}")
        logger.info(f"Final merged config: {merged}")
        return merged
        
    def load_config(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件，支持 includes"""
        logger.info(f"Loading config from: {file_path}")
        # 首先解析主配置文件的路径
        resolved_path = self._resolve_path(file_path)
        config = self._load_yaml(resolved_path)
        if not config:
            logger.warning(f"No config found in {file_path}")
            return {}
            
        logger.info(f"Main config: {config}")
            
        # 如果有 includes，加载所有包含的文件
        if "includes" in config:
            included_configs = []
            base_dir = os.path.dirname(resolved_path)
            
            for include in config["includes"]:
                # 使用相对于主配置文件的路径
                include_path = os.path.join(base_dir, include)
                logger.info(f"Loading included config from: {include_path}")
                included_config = self._load_yaml(include_path)
                if included_config:
                    included_configs.append(included_config)
                    logger.info(f"Loaded included config: {included_config}")
                else:
                    logger.warning(f"Failed to load included config: {include_path}")
                    
            merged = self._merge_configs(included_configs)
            logger.info(f"Returning merged config: {merged}")
            return merged
            
        logger.info(f"Returning main config: {config}")
        return config

    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._config_cache.clear()
        self._load_yaml.cache_clear()  # 清除 lru_cache 