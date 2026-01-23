import re
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("TaskMancer.ConfigParser")

class ConfigParser:
    """解析專案目錄下的 config.md"""
    
    # 支援格式: Port : [Label] : [Number] (更寬鬆的匹配)
    PORT_PATTERN = re.compile(r'Port\s*:\s*(?P<label>[^:]+)\s*:\s*(?P<port>\d+)', re.IGNORECASE)
    # 支援格式: [Link]: URL
    LINK_PATTERN = re.compile(r'\[Link\]:\s*(?P<url>https?://[^\s]+)', re.IGNORECASE)

    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        """解析 config.md 並返回配置數據"""
        config = {
            "explicit_ports": [], # List of {label: str, port: int}
            "links": []
        }
        
        if not os.path.exists(file_path):
            return config

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 匹配 Port
                    port_match = cls.PORT_PATTERN.search(line)
                    if port_match:
                        label = port_match.group('label').strip()
                        port_num = int(port_match.group('port'))
                        config["explicit_ports"].append({
                            "label": label,
                            "port": port_num
                        })
                        continue
                        
                    # 匹配 Link
                    link_match = cls.LINK_PATTERN.search(line)
                    if link_match:
                        url = link_match.group('url').strip()
                        config["links"].append(url)
                        
        except Exception as e:
            logger.error(f"Error parsing config file {file_path}: {e}")
            
        return config

    @classmethod
    def get_env_vars(cls, file_path: str) -> Dict[str, str]:
        """將配置轉換為環境變數字典 (TM_PORT_[LABEL])"""
        config = cls.parse_file(file_path)
        envs = {}
        for item in config.get("explicit_ports", []):
            # 將標籤轉為大寫並處理空格
            clean_label = re.sub(r'[^A-Z0-9]', '_', item['label'].upper())
            envs[f"TM_PORT_{clean_label}"] = str(item['port'])
        return envs
