"""
公共模块 — 提供统一的日志、错误处理、性能监控、缓存和重试机制

本模块为 pDOOH 后端服务提供基础设施支持，包括：
- 统一日志配置
- 自定义异常类
- 错误响应格式化
- 性能监控装饰器
- 缓存装饰器
- 重试机制装饰器
"""

import functools
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, Type
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# 日志配置
# ─────────────────────────────────────────────

def setup_logging(
    name: str = "pdooh",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    设置统一的日志配置
    
    Args:
        name: 日志名称（通常是模块名）
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日志文件路径（如果为 None，则只输出到控制台）
        max_bytes: 日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
        
    Returns:
        logging.Logger: 配置好的日志器
        
    Example:
        >>> logger = setup_logging("roi_agent", log_file="logs/roi_agent.log")
        >>> logger.info("ROI 计算开始")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件 handler（如果指定了日志文件）
    if log_file:
        import os
        from logging.handlers import RotatingFileHandler
        
        # 创建日志目录
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ─────────────────────────────────────────────
# 自定义异常类
# ─────────────────────────────────────────────

class PDOOHError(Exception):
    """pDOOH 基础异常类"""
    
    def __init__(
        self,
        message: str = "pDOOH 服务错误",
        error_code: str = "PDOOH_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化 pDOOH 异常
        
        Args:
            message: 错误信息
            error_code: 错误代码（用于前端识别错误类型）
            status_code: HTTP 状态码
            details: 详细错误信息（用于调试）
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典（用于 JSON 响应）
        
        Returns:
            Dict[str, Any]: 包含错误信息的字典
        """
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp,
            }
        }


class ValidationError(PDOOHError):
    """参数验证错误"""
    
    def __init__(self, message: str = "参数验证失败", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class ResourceNotFoundError(PDOOHError):
    """资源未找到错误"""
    
    def __init__(self, resource: str = "资源", resource_id: Optional[Any] = None):
        message = f"{resource} 未找到"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id},
        )


class ExternalServiceError(PDOOHError):
    """外部服务调用错误"""
    
    def __init__(self, service_name: str = "外部服务", details: Optional[Dict] = None):
        message = f"{service_name} 调用失败"
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details=details,
        )


class DatabaseError(PDOOHError):
    """数据库操作错误"""
    
    def __init__(self, message: str = "数据库操作失败", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


# ─────────────────────────────────────────────
# 错误响应格式化
# ─────────────────────────────────────────────

def format_error_response(
    error: Exception,
    include_details: bool = True,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    格式化错误响应（统一格式）
    
    Args:
        error: 异常对象
        include_details: 是否包含详细错误信息（生产环境应设为 False）
        request_id: 请求 ID（用于追踪）
        
    Returns:
        Dict[str, Any]: 统一格式的错误响应
        
    Example:
        >>> try:
        >>>     ...
        >>> except Exception as e:
        >>>     return format_error_response(e, request_id="req_123")
    """
    if isinstance(error, PDOOHError):
        response = error.to_dict()
    else:
        # 未知异常
        response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(error),
                "timestamp": datetime.now().isoformat(),
            }
        }
        if include_details:
            import traceback
            response["error"]["traceback"] = traceback.format_exc()
    
    if request_id:
        response["request_id"] = request_id
    
    response["success"] = False
    return response


# ─────────────────────────────────────────────
# 性能监控装饰器
# ─────────────────────────────────────────────

T = TypeVar("T")


def monitor_performance(
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.INFO,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    性能监控装饰器：记录函数执行时间、成功/失败状态
    
    Args:
        logger: 日志器（如果为 None，则使用默认日志器）
        log_level: 日志级别
        
    Returns:
        装饰器函数
        
    Example:
        >>> @monitor_performance(logger=logger)
        >>> def calculate_roi(cost: float) -> float:
        >>>     ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            if logger is None:
                logger = setup_logging(func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_time = (time.time() - start_time) * 1000  # 毫秒
                logger.log(
                    log_level,
                    f"性能监控: {func.__name__} 执行成功，耗时 {elapsed_time:.2f}ms",
                )
                return result
            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000
                logger.error(
                    f"性能监控: {func.__name__} 执行失败，耗时 {elapsed_time:.2f}ms，"
                    f"错误: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def monitor_performance_async(
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.INFO,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    性能监控装饰器（异步版本）
    
    Args:
        logger: 日志器
        log_level: 日志级别
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            if logger is None:
                logger = setup_logging(func.__module__)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed_time = (time.time() - start_time) * 1000
                logger.log(
                    log_level,
                    f"性能监控: {func.__name__} 执行成功，耗时 {elapsed_time:.2f}ms",
                )
                return result
            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000
                logger.error(
                    f"性能监控: {func.__name__} 执行失败，耗时 {elapsed_time:.2f}ms，"
                    f"错误: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# 缓存装饰器
# ─────────────────────────────────────────────

def cached(
    ttl: Optional[int] = None,
    maxsize: Optional[int] = 128,
    key_func: Optional[Callable] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    缓存装饰器：使用 functools.lru_cache 或自定义缓存
    
    Args:
        ttl: 缓存过期时间（秒），如果为 None，则永不过期
        maxsize: 最大缓存条目数（仅对 lru_cache 有效）
        key_func: 自定义缓存 key 生成函数
        
    Returns:
        装饰器函数
        
    Example:
        >>> @cached(ttl=60, maxsize=100)  # 缓存 60 秒，最多 100 条
        >>> def query_database(query: str) -> List[Dict]:
        >>>     ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 使用 lru_cache（简单场景）
        if ttl is None and key_func is None:
            @functools.lru_cache(maxsize=maxsize)
            @functools.wraps(func)
            def cached_func(*args: Any, **kwargs: Any) -> T:
                return func(*args, **kwargs)
            return cached_func
        
        # 使用自定义缓存（支持 TTL）
        cache: Dict[str, Any] = {}
        cache_times: Dict[str, float] = {}
        
        @functools.wraps(func)
        def cached_func(*args: Any, **kwargs: Any) -> T:
            # 生成缓存 key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认 key：函数名 + 参数哈希
                key_str = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = hashlib.md5(key_str.encode()).hexdigest()
            
            # 检查缓存是否过期
            current_time = time.time()
            if cache_key in cache:
                if ttl is None or (current_time - cache_times[cache_key]) < ttl:
                    return cache[cache_key]
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
                    del cache_times[cache_key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = current_time
            
            # 限制缓存大小（简单 LRU 策略）
            if maxsize and len(cache) > maxsize:
                oldest_key = min(cache_times, key=cache_times.get)
                del cache[oldest_key]
                del cache_times[oldest_key]
            
            return result
        
        return cached_func
    return decorator


# ─────────────────────────────────────────────
# 重试机制装饰器
# ─────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    重试机制装饰器：在失败时自动重试
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数（每次重试延迟乘以 backoff）
        exceptions: 需要捕获的异常类型
        logger: 日志器
        
    Returns:
        装饰器函数
        
    Example:
        >>> @retry(max_attempts=3, delay=1.0, exceptions=(httpx.TimeoutException,))
        >>> async def call_external_api(url: str) -> Dict:
        >>>     ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            if logger is None:
                logger = setup_logging(func.__module__)
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"重试 {func.__name__}: 第 {attempt} 次尝试失败，"
                            f"{current_delay:.1f}秒后重试。错误: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"重试 {func.__name__}: 已达到最大重试次数 {max_attempts}，"
                            f"放弃重试。最后错误: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    重试机制装饰器（异步版本）
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        exceptions: 需要捕获的异常类型
        logger: 日志器
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            if logger is None:
                logger = setup_logging(func.__module__)
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"重试 {func.__name__}: 第 {attempt} 次尝试失败，"
                            f"{current_delay:.1f}秒后重试。错误: {str(e)}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"重试 {func.__name__}: 已达到最大重试次数 {max_attempts}，"
                            f"放弃重试。最后错误: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# 参数验证工具
# ─────────────────────────────────────────────

def validate_params(
    params: Dict[str, Any],
    rules: Dict[str, Dict[str, Any]],
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    参数验证工具：验证参数字典是否符合规则
    
    Args:
        params: 待验证的参数（通常是 request.query_params 或 request.json）
        rules: 验证规则字典，格式：
            {
                "param_name": {
                    "type": str/int/float/bool/list,
                    "required": True/False,
                    "default": ...,
                    "min": 最小值（数值类型）,
                    "max": 最大值（数值类型）,
                    "allowed_values": [...],  # 允许的值列表
                    "validator": callable,  # 自定义验证函数
                }
            }
        logger: 日志器
        
    Returns:
        Dict[str, Any]: 验证并清洗后的参数（包含默认值）
        
    Raises:
        ValidationError: 参数验证失败
        
    Example:
        >>> rules = {
        >>>     "city": {"type": str, "required": True},
        >>>     "budget": {"type": float, "required": False, "default": 100000, "min": 0},
        >>> }
        >>> validated = validate_params(request.query_params, rules)
    """
    if logger is None:
        logger = setup_logging("validate_params")
    
    validated: Dict[str, Any] = {}
    
    for param_name, rule in rules.items():
        param_value = params.get(param_name)
        
        # 检查必需参数
        if rule.get("required", False) and param_value is None:
            raise ValidationError(
                message=f"缺少必需参数: {param_name}",
                details={"param": param_name, "rule": rule},
            )
        
        # 使用默认值
        if param_value is None:
            validated[param_name] = rule.get("default")
            continue
        
        # 类型转换和验证
        expected_type = rule.get("type", str)
        try:
            if expected_type == int:
                param_value = int(param_value)
            elif expected_type == float:
                param_value = float(param_value)
            elif expected_type == bool:
                if isinstance(param_value, str):
                    param_value = param_value.lower() in ("true", "1", "yes", "on")
                else:
                    param_value = bool(param_value)
            elif expected_type == list:
                if isinstance(param_value, str):
                    # 假设逗号分隔的列表
                    param_value = [item.strip() for item in param_value.split(",")]
        except (ValueError, TypeError) as e:
            raise ValidationError(
                message=f"参数类型错误: {param_name} 应为 {expected_type.__name__}",
                details={"param": param_name, "value": param_value, "error": str(e)},
            )
        
        # 数值范围验证
        if expected_type in (int, float):
            if "min" in rule and param_value < rule["min"]:
                raise ValidationError(
                    message=f"参数值过小: {param_name} 应 ≥ {rule['min']}",
                    details={"param": param_name, "value": param_value, "min": rule["min"]},
                )
            if "max" in rule and param_value > rule["max"]:
                raise ValidationError(
                    message=f"参数值过大: {param_name} 应 ≤ {rule['max']}",
                    details={"param": param_name, "value": param_value, "max": rule["max"]},
                )
        
        # 允许值验证
        if "allowed_values" in rule and param_value not in rule["allowed_values"]:
            raise ValidationError(
                message=f"参数值无效: {param_name} 应为 {rule['allowed_values']} 之一",
                details={
                    "param": param_name,
                    "value": param_value,
                    "allowed_values": rule["allowed_values"],
                },
            )
        
        # 自定义验证函数
        if "validator" in rule:
            validator_func = rule["validator"]
            if not validator_func(param_value):
                raise ValidationError(
                    message=f"参数验证失败: {param_name}",
                    details={"param": param_name, "value": param_value},
                )
        
        validated[param_name] = param_value
        logger.debug(f"参数验证通过: {param_name}={param_value}")
    
    return validated


# ─────────────────────────────────────────────
# 请求 ID 生成
# ─────────────────────────────────────────────

def generate_request_id(prefix: str = "req") -> str:
    """
    生成唯一的请求 ID（用于追踪请求）
    
    Args:
        prefix: ID 前缀
        
    Returns:
        str: 唯一请求 ID
        
    Example:
        >>> request_id = generate_request_id("roi")
        >>> # 返回类似 "roi_1623456789_abc123"
    """
    import uuid
    timestamp = int(time.time())
    random_str = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{random_str}"


# ─────────────────────────────────────────────
# 导出
# ─────────────────────────────────────────────

__all__ = [
    # 日志
    "setup_logging",
    # 异常类
    "PDOOHError",
    "ValidationError",
    "ResourceNotFoundError",
    "ExternalServiceError",
    "DatabaseError",
    # 错误处理
    "format_error_response",
    # 性能监控
    "monitor_performance",
    "monitor_performance_async",
    # 缓存
    "cached",
    # 重试
    "retry",
    "retry_async",
    # 参数验证
    "validate_params",
    # 工具
    "generate_request_id",
]
