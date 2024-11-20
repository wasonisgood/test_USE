import subprocess
import logging
import psutil
import shutil

logger = logging.getLogger(__name__)

class HardwareChecker:
    @staticmethod
    def is_cpu_sufficient(min_cores: int = 4, min_memory_gb: int = 16) -> bool:
        """
        檢查 CPU 核心數和內存是否足夠
        """
        try:
            cores = psutil.cpu_count(logical=False)
            memory = psutil.virtual_memory().total // (1024 ** 3)  # 轉為 GB
            if cores >= min_cores and memory >= min_memory_gb:
                logger.info(f"硬件檢測通過：{cores} 核心, {memory} GB 內存")
                return True
            else:
                logger.warning(f"硬件不足：{cores} 核心, {memory} GB 內存，要求至少 {min_cores} 核心和 {min_memory_gb} GB 內存")
                return False
        except Exception as e:
            logger.error(f"檢查 CPU 和內存時出錯: {e}")
            return False

    @staticmethod
    def is_cuda_available() -> bool:
        """
        檢查是否存在支持 CUDA 的 GPU
        """
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=True)
            if "CUDA Version" in result.stdout:
                logger.info("CUDA 可用")
                return True
            else:
                logger.warning("未檢測到 CUDA 支持")
                return False
        except FileNotFoundError:
            logger.warning("未安裝 NVIDIA 驅動或 nvidia-smi 不可用")
            return False
        except Exception as e:
            logger.error(f"檢查 CUDA 時出錯: {e}")
            return False

    @staticmethod
    def is_ollama_installed() -> bool:
        """
        檢查是否安裝 Ollama CLI
        """
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, check=True)
            logger.info(f"Ollama 安裝版本: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Ollama CLI 不可用: {e}")
            return False

    @staticmethod
    def is_local_environment_ready() -> bool:
        """
        確定是否滿足本地運行條件（硬件+依賴）
        """
        return (
            HardwareChecker.is_cpu_sufficient() and
            HardwareChecker.is_ollama_installed() and
            HardwareChecker.is_cuda_available()
        )
