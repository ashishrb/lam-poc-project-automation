#!/usr/bin/env python3
"""
System Configuration for AMD Ryzen 9 9950X + RTX 4090 + 128GB RAM
Optimized settings for high-performance autonomous LAM operations
"""

import os
import torch
from typing import Dict, Any

class SystemConfig:
    """System-specific configuration for optimal performance"""
    
    def __init__(self):
        self.detect_hardware()
        self.set_environment_variables()
        self.configure_torch()
    
    def detect_hardware(self):
        """Detect and configure hardware-specific settings"""
        # CPU Configuration
        self.cpu_cores = os.cpu_count() or 32  # Ryzen 9 9950X has 32 cores
        self.ram_gb = 128
        
        # GPU Configuration
        self.has_cuda = torch.cuda.is_available()
        self.gpu_count = torch.cuda.device_count() if self.has_cuda else 0
        
        if self.has_cuda:
            self.gpu_name = torch.cuda.get_device_name(0)
            self.gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🚀 GPU Detected: {self.gpu_name} with {self.gpu_memory:.1f}GB VRAM")
        else:
            print("⚠️ No CUDA GPU detected, using CPU mode")
        
        # Memory Configuration
        self.max_memory_gb = min(self.ram_gb * 0.8, 100)  # Use 80% of RAM, max 100GB
        self.batch_size_multiplier = 6 if self.has_cuda else 1  # Increased for RTX 5090
    
    def set_environment_variables(self):
        """Set environment variables for optimal performance"""
        # PyTorch optimizations
        os.environ['OMP_NUM_THREADS'] = str(self.cpu_cores)
        os.environ['MKL_NUM_THREADS'] = str(self.cpu_cores)
        os.environ['NUMEXPR_NUM_THREADS'] = str(self.cpu_cores)
        
        # Memory management
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
        
        # AMD-specific optimizations
        os.environ['AMDGPU_FORCE_64BIT_PTR'] = '1'
        
        # Streamlit optimizations
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
        os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'true'
        
        print(f"🔧 Environment configured for {self.cpu_cores} CPU cores and {self.max_memory_gb:.0f}GB RAM")
        print(f"🚀 Optimized for RTX 5090 with {self.gpu_memory:.1f}GB VRAM")
    
    def configure_torch(self):
        """Configure PyTorch for optimal performance"""
        if self.has_cuda:
            # CUDA optimizations
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            
            # Memory management
            torch.cuda.empty_cache()
            
            print("✅ PyTorch configured for CUDA acceleration")
        else:
            # CPU optimizations
            torch.set_num_threads(self.cpu_cores)
            print("✅ PyTorch configured for CPU optimization")
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration optimized for this system"""
        return {
            'device': 'cuda' if self.has_cuda else 'cpu',
            'torch_dtype': torch.float16 if self.has_cuda else torch.float32,
            'max_memory': f'{self.max_memory_gb:.0f}GB',
            'batch_size': 8 * self.batch_size_multiplier,
            'num_workers': min(self.cpu_cores, 8),
            'pin_memory': self.has_cuda,
            'prefetch_factor': 2 if self.cpu_cores >= 8 else 1
        }
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """Get Streamlit configuration for this system"""
        return {
            'theme_base': 'light'
        }
    
    def get_streamlit_server_config(self) -> Dict[str, Any]:
        """Get Streamlit server configuration for this system"""
        return {
            'server_port': 8501,
            'server_address': '0.0.0.0',
            'server_max_upload_size': 200,
            'server_enable_static_serving': True,
            'browser_gather_usage_stats': False,
            'global_developmentMode': False
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration optimized for this system"""
        return {
            'max_connections': min(self.cpu_cores * 2, 32),
            'timeout': 30,
            'check_same_thread': False,
            'isolation_level': None
        }
    
    def print_system_info(self):
        """Print comprehensive system information"""
        print("\n" + "="*60)
        print("🖥️  SYSTEM CONFIGURATION")
        print("="*60)
        print(f"CPU: AMD Ryzen 9 9950X ({self.cpu_cores} cores)")
        print(f"RAM: {self.ram_gb}GB (Max usable: {self.max_memory_gb:.0f}GB)")
        
        if self.has_cuda:
            print(f"GPU: {self.gpu_name}")
            print(f"VRAM: {self.gpu_memory:.1f}GB")
            print("CUDA: ✅ Available")
        else:
            print("CUDA: ❌ Not available")
        
        print(f"PyTorch: {torch.__version__}")
        print(f"Device: {torch.device('cuda' if self.has_cuda else 'cpu')}")
        print("="*60 + "\n")

# Global configuration instance
system_config = SystemConfig()

# Export configuration for other modules
__all__ = ['system_config', 'SystemConfig']
