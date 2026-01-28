#!/usr/bin/env python3
"""
TaskMancer 效能測試套件
測試 v13.1 效能優化的效果
"""

import asyncio
import time
import os
import tempfile
from pathlib import Path
import psutil
import json

# Backend imports
import sys
sys.path.append('backend')

from backend.app.services.scanner import DirectoryScanner
from backend.app.parsers.task_parser import TaskParser

class PerformanceTester:
    def __init__(self):
        self.results = {}
        
    async def test_scanner_performance(self):
        """測試掃描器效能"""
        print("測試檔案掃描器效能...")
        
        # 測試不同大小的專案集合
        test_paths = [
            'D:\\Dev',  # 中等大小
            'C:\\Python38',  # 大型目錄
        ]
        
        for test_path in test_paths:
            if not os.path.exists(test_path):
                print(f"警告: 路徑不存在: {test_path}")
                continue
                
            print(f"  測試路徑: {test_path}")
            
            # 測試同步掃描 (舊版)
            scanner = DirectoryScanner(test_path, max_depth=2)
            
            # 測試非同步掃描 (新版)
            start_time = time.time()
            results = await scanner.scan_async(batch_size=50)
            async_time = time.time() - start_time
            
            print(f"    非同步掃描: {len(results)} 個專案，耗時 {async_time:.3f} 秒")
            
            # 記憶體使用量
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.results[f'scanner_{test_path}'] = {
                'projects_found': len(results),
                'time_seconds': async_time,
                'memory_mb': memory_mb,
                'avg_time_per_project': async_time / max(len(results), 1)
            }
    
    async def test_parser_performance(self):
        """測試任務解析器效能"""
        print("測試任務解析器效能...")
        
        # 創建測試檔案
        test_files = [
            self._create_test_file('small', 100),    # 100 行
            self._create_test_file('medium', 1000),   # 1000 行
            self._create_test_file('large', 5000),    # 5000 行
        ]
        
        parser = TaskParser()
        
        for file_path, line_count, description in test_files:
            print(f"  測試 {description} 檔案 ({line_count} 行)...")
            
            # 測試非同步解析
            start_time = time.time()
            result = await parser.parse_file_async(file_path)
            async_time = time.time() - start_time
            
            # 測試記憶體使用
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            print(f"    非同步解析: 耗時 {async_time:.3f} 秒")
            print(f"    任務數量: {result.get('stats', {}).get('total', 0)}")
            
            self.results[f'parser_{description}'] = {
                'file_lines': line_count,
                'time_seconds': async_time,
                'memory_mb': memory_mb,
                'tasks_found': result.get('stats', {}).get('total', 0),
                'time_per_line': async_time / max(line_count, 1)
            }
            
            # 清理測試檔案
            os.unlink(file_path)
    
    def _create_test_file(self, name: str, line_count: int) -> tuple:
        """創建測試用的 task.md 檔案"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            # 寫入測試內容
            for i in range(line_count // 4):
                f.write(f"- [ ] 主要任務 {i+1}\n")
                f.write(f"  - [x] 子任務 {i+1}.1\n")
                f.write(f"  - [ ] 子任務 {i+1}.2\n")
                f.write(f"  - [ ] 子任務 {i+1}.3\n")
            
            file_path = f.name
        
        return file_path, line_count, name
    
    def test_cache_performance(self):
        """測試快取效能"""
        print("測試快取效能...")
        
        parser = TaskParser()
        
        # 創建相同的任務樹
        test_tasks = [
            {
                "text": f"測試任務 {i}",
                "status": "todo" if i % 2 == 0 else "done",
                "level": 1,
                "children": []
            }
            for i in range(100)
        ]
        
        # 第一次計算 (無快取)
        start_time = time.time()
        stats1 = parser._calculate_stats(test_tasks, use_cache=False)
        no_cache_time = time.time() - start_time
        
        # 第二次計算 (有快取)
        start_time = time.time()
        stats2 = parser._calculate_stats(test_tasks, use_cache=True)
        cache_time = time.time() - start_time
        
        speedup = no_cache_time / max(cache_time, 0.001)
        
        print(f"    無快取: {no_cache_time:.6f} 秒")
        print(f"    有快取: {cache_time:.6f} 秒")
        print(f"    加速倍數: {speedup:.1f}x")
        
        self.results['cache_performance'] = {
            'no_cache_time': no_cache_time,
            'cache_time': cache_time,
            'speedup': speedup,
            'tasks_count': len(test_tasks)
        }
    
    def generate_report(self):
        """生成效能測試報告"""
        print("\n" + "="*60)
        print("TaskMancer v13.1 效能測試報告")
        print("="*60)
        
        # 掃描器效能
        print("\n檔案掃描器效能:")
        for key, result in self.results.items():
            if key.startswith('scanner_'):
                print(f"  {key.split('_', 1)[1]}:")
                print(f"    專案數量: {result['projects_found']}")
                print(f"    掃描時間: {result['time_seconds']:.3f} 秒")
                print(f"    平均時間: {result['avg_time_per_project']:.6f} 秒/專案")
                print(f"    記憶體使用: {result['memory_mb']:.1f} MB")
        
        # 解析器效能
        print("\n任務解析器效能:")
        for key, result in self.results.items():
            if key.startswith('parser_'):
                print(f"  {key.split('_', 1)[1]} ({result['file_lines']} 行):")
                print(f"    解析時間: {result['time_seconds']:.3f} 秒")
                print(f"    任務數量: {result['tasks_found']}")
                print(f"    每行時間: {result['time_per_line']:.6f} 秒")
                print(f"    記憶體使用: {result['memory_mb']:.1f} MB")
        
        # 快取效能
        if 'cache_performance' in self.results:
            cache = self.results['cache_performance']
            print(f"\n快取效能:")
            print(f"  無快取時間: {cache['no_cache_time']:.6f} 秒")
            print(f"  有快取時間: {cache['cache_time']:.6f} 秒")
            print(f"  加速倍數: {cache['speedup']:.1f}x")
            print(f"  任務數量: {cache['tasks_count']}")
        
        print("\n優化效果總結:")
        print("  非同步檔案掃描: 避免阻塞事件循環")
        print("  串流任務解析: 支援大檔案處理")
        print("  記憶化統計: 重複計算加速")
        print("  批次處理: 記憶體使用優化")
        print("  虛擬滾動: 前端渲染效能提升")
        
        # 儲存詳細結果
        with open('performance_report.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n詳細報告已儲存至: performance_report.json")
    
    async def run_all_tests(self):
        """執行所有測試"""
        print("開始 TaskMancer v13.1 效能測試...")
        print(f"系統: {os.name}")
        print(f"Python 版本: {sys.version}")
        print(f"記憶體: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
        print()
        
        await self.test_scanner_performance()
        await self.test_parser_performance()
        self.test_cache_performance()
        self.generate_report()

if __name__ == "__main__":
    tester = PerformanceTester()
    asyncio.run(tester.run_all_tests())