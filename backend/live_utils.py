import asyncio
import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("TaskMancer.LiveUtils")

class PortScanner:
    """提供非同步埠口活體偵測功能"""
    
    # 全域備用掃描埠口 (僅在無明確配置時使用)
    COMMON_DEV_PORTS = [3000, 3001, 3002, 5000, 5001, 5173, 5174, 5175, 8000, 8001, 8080, 8081, 4200, 3333, 8888]

    @staticmethod
    async def get_port_status(host: str, port: int, label: str = "", timeout: float = 1.5) -> Dict[str, Any]:
        """非同步檢查特定埠口是否正在被佔用"""
        try:
            # v9.7: 優先嘗試 IPv4 (127.0.0.1)，若失敗且 host 為預設值則嘗試 IPv6 (::1)
            # Windows Vite 默認可能綁定在 ::1
            target_host = host
            if host == "localhost": 
                target_host = "127.0.0.1"
                
            try:
                conn = asyncio.open_connection(target_host, port)
                _, writer = await asyncio.wait_for(conn, timeout=timeout)
                writer.close()
                await writer.wait_closed()
                return {"port": port, "label": label, "status": "online"}
            except:
                # 如果是預設 host 且第一次嘗試失敗，嘗試 IPv6 Loopback
                if target_host == "127.0.0.1":
                    conn = asyncio.open_connection("::1", port)
                    _, writer = await asyncio.wait_for(conn, timeout=timeout)
                    writer.close()
                    await writer.wait_closed()
                    return {"port": port, "label": label, "status": "online"}
                raise
        except:
            return {"port": port, "label": label, "status": "offline"}

    @classmethod
    async def scan_ports(cls, host: str = "127.0.0.1", explicit_ports: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """並行掃描埠口。"""
        if explicit_ports is not None:
            # 執行精確掃描 (返回所有定義的埠口狀態)
            if not explicit_ports:
                return []
            tasks = [cls.get_port_status(host, p['port'], p['label']) for p in explicit_ports]
            results = await asyncio.gather(*tasks)
            return results
        else:
            # v9.3: 移除全域備用掃描，避免在無配置專案誤報其他專案的埠口
            return []

class DependencyAuditor:
    """提供依賴健康偵測功能"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path

    def audit_node_dependencies(self) -> Dict[str, Any]:
        """分析 package.json 中的依賴狀況"""
        pkg_path = os.path.join(self.project_path, "package.json")
        if not os.path.exists(pkg_path):
            return {"status": "none"}
            
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                deps = data.get('dependencies', {})
                dev_deps = data.get('devDependencies', {})
                
                return {
                    "status": "ok",
                    "dep_count": len(deps),
                    "dev_dep_count": len(dev_deps),
                    "total_count": len(deps) + len(dev_deps),
                    "has_package_lock": os.path.exists(os.path.join(self.project_path, "package-lock.json"))
                }
        except Exception as e:
            logger.error(f"Error auditing dependencies: {e}")
            return {"status": "error", "message": str(e)}

async def get_live_report_async(project_path: str, explicit_ports: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """獲取專案的即時活體報告 (非同步版)"""
    # 埠口檢測 (並行掃描)
    ports_data = await PortScanner.scan_ports(explicit_ports=explicit_ports)
    
    # 依賴檢查
    auditor = DependencyAuditor(project_path)
    dep_audit = auditor.audit_node_dependencies()
    
    return {
        "active_ports": ports_data, 
        "dependency_audit": dep_audit
    }
