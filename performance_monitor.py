#!/usr/bin/env python3
"""
Performance Monitor for AMD Ryzen 9 9950X + RTX 4090 System
Monitors CPU, RAM, GPU usage during LAM operations
"""

import psutil
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
import torch

class PerformanceMonitor:
    """Real-time performance monitoring for the LAM system"""
    
    def __init__(self, monitor_interval: float = 1.0):
        self.monitor_interval = monitor_interval
        self.monitoring = False
        self.monitor_thread = None
        self.performance_log = []
        self.start_time = None
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # 80% CPU usage
        self.ram_threshold = 85.0  # 85% RAM usage
        self.gpu_threshold = 90.0  # 90% GPU usage
        
    def start_monitoring(self):
        """Start performance monitoring in background thread"""
        if not self.monitoring:
            self.monitoring = True
            self.start_time = datetime.now()
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print(f"🔍 Performance monitoring started at {self.start_time}")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print(f"🛑 Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.performance_log.append(metrics)
                
                # Check for performance warnings
                self._check_thresholds(metrics)
                
                time.sleep(self.monitor_interval)
            except Exception as e:
                print(f"⚠️ Performance monitoring error: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_avg = sum(cpu_percent) / len(cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # GPU metrics
        gpu_metrics = self._get_gpu_metrics()
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            'timestamp': timestamp,
            'cpu': {
                'overall': cpu_avg,
                'per_core': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percent': memory.percent,
                'process_mb': process_memory.rss / (1024**2)
            },
            'gpu': gpu_metrics,
            'disk': {
                'read_bytes': psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                'write_bytes': psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
            }
        }
    
    def _get_gpu_metrics(self) -> Dict:
        """Get GPU metrics if CUDA is available"""
        try:
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_stats()
                gpu_allocated = torch.cuda.memory_allocated() / (1024**3)
                gpu_reserved = torch.cuda.memory_reserved() / (1024**3)
                gpu_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                
                return {
                    'available': True,
                    'name': torch.cuda.get_device_name(0),
                    'memory_gb': gpu_total,
                    'allocated_gb': gpu_allocated,
                    'reserved_gb': gpu_reserved,
                    'utilization_percent': (gpu_allocated / gpu_total) * 100
                }
            else:
                return {'available': False}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def _check_thresholds(self, metrics: Dict):
        """Check if performance metrics exceed thresholds"""
        warnings = []
        
        # CPU threshold check
        if metrics['cpu']['overall'] > self.cpu_threshold:
            warnings.append(f"⚠️ High CPU usage: {metrics['cpu']['overall']:.1f}%")
        
        # Memory threshold check
        if metrics['memory']['percent'] > self.ram_threshold:
            warnings.append(f"⚠️ High RAM usage: {metrics['memory']['percent']:.1f}%")
        
        # GPU threshold check
        if metrics['gpu'].get('available') and metrics['gpu'].get('utilization_percent', 0) > self.gpu_threshold:
            warnings.append(f"⚠️ High GPU usage: {metrics['gpu']['utilization_percent']:.1f}%")
        
        if warnings:
            print(f"🚨 Performance Warnings at {metrics['timestamp'].strftime('%H:%M:%S')}:")
            for warning in warnings:
                print(f"   {warning}")
    
    def get_current_metrics(self) -> Optional[Dict]:
        """Get the most recent performance metrics"""
        if self.performance_log:
            return self.performance_log[-1]
        return None
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary since monitoring started"""
        if not self.performance_log:
            return {}
        
        cpu_values = [m['cpu']['overall'] for m in self.performance_log]
        memory_values = [m['memory']['percent'] for m in self.performance_log]
        
        summary = {
            'monitoring_duration': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'samples_collected': len(self.performance_log),
            'cpu': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            }
        }
        
        # GPU summary if available
        gpu_utilizations = [m['gpu'].get('utilization_percent', 0) for m in self.performance_log if m['gpu'].get('available')]
        if gpu_utilizations:
            summary['gpu'] = {
                'average': sum(gpu_utilizations) / len(gpu_utilizations),
                'max': max(gpu_utilizations),
                'min': min(gpu_utilizations)
            }
        
        return summary
    
    def print_performance_summary(self):
        """Print a formatted performance summary"""
        summary = self.get_performance_summary()
        if not summary:
            print("📊 No performance data available")
            return
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Monitoring Duration: {summary['monitoring_duration']:.1f} seconds")
        print(f"Samples Collected: {summary['samples_collected']}")
        print()
        
        print("CPU Usage:")
        print(f"  Average: {summary['cpu']['average']:.1f}%")
        print(f"  Maximum: {summary['cpu']['max']:.1f}%")
        print(f"  Minimum: {summary['cpu']['min']:.1f}%")
        print()
        
        print("Memory Usage:")
        print(f"  Average: {summary['memory']['average']:.1f}%")
        print(f"  Maximum: {summary['memory']['max']:.1f}%")
        print(f"  Minimum: {summary['memory']['min']:.1f}%")
        print()
        
        if 'gpu' in summary:
            print("GPU Usage:")
            print(f"  Average: {summary['gpu']['average']:.1f}%")
            print(f"  Maximum: {summary['gpu']['max']:.1f}%")
            print(f"  Minimum: {summary['gpu']['min']:.1f}%")
        
        print("="*60)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def start_performance_monitoring():
    """Start performance monitoring"""
    performance_monitor.start_monitoring()

def stop_performance_monitoring():
    """Stop performance monitoring"""
    performance_monitor.stop_monitoring()

def get_performance_metrics():
    """Get current performance metrics"""
    return performance_monitor.get_current_metrics()

def print_performance_summary():
    """Print performance summary"""
    performance_monitor.print_performance_summary()

# Export functions
__all__ = [
    'PerformanceMonitor', 
    'performance_monitor',
    'start_performance_monitoring',
    'stop_performance_monitoring',
    'get_performance_metrics',
    'print_performance_summary'
]
