"""青柠 Booking — 统一业务异常与错误码。

错误码规范（见设计文档 §15）：
    POINT_ALREADY_LOCKED      -> 409  （层①/③ 预检冲突）
    PROTECTION_RULE_VIOLATED  -> 409  （层④ 排他冲突 / 23P01 包装）
    LOCK_QUOTA_EXCEEDED       -> 422  （续期次数用尽）
    BOOKING_NOT_FOUND         -> 404
    IDEMPOTENT_DUPLICATE      -> 200  （CT-03，返回既有单）
    OFFLINE_OPERATION_FORBIDDEN -> 503

``QinglinError`` 同时携带 ``error_code`` / ``http_status`` / ``extra``（如冲突单号），
由 main.py 的全局异常处理器统一映射为 HTTP 响应。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# 错误码 -> HTTP 状态码
ERROR_HTTP: Dict[str, int] = {
    "POINT_ALREADY_LOCKED": 409,
    "PROTECTION_RULE_VIOLATED": 409,
    "LOCK_QUOTA_EXCEEDED": 422,
    "BOOKING_NOT_FOUND": 404,
    "IDEMPOTENT_DUPLICATE": 200,
    "OFFLINE_OPERATION_FORBIDDEN": 503,
    "INVALID_PARAM": 400,
}

DEFAULT_MESSAGE = {
    "POINT_ALREADY_LOCKED": "该点位当前档期已被锁定，无法重复占用。",
    "PROTECTION_RULE_VIOLATED": "档期排他约束拦截：与已有占用重叠（防超卖）。",
    "LOCK_QUOTA_EXCEEDED": "已达该档位最大续期次数，无法继续续期。",
    "BOOKING_NOT_FOUND": "未找到对应的锁位单。",
    "IDEMPOTENT_DUPLICATE": "幂等命中：返回既有锁位单。",
    "OFFLINE_OPERATION_FORBIDDEN": "离线操作被禁止（资源不可用）。",
    "INVALID_PARAM": "请求参数非法。",
}


class QinglinError(Exception):
    """青柠业务异常。

    Attributes:
        error_code: 业务错误码（见 ``ERROR_HTTP``）。
        http_status: 对应 HTTP 状态码。
        message: 面向调用方的文案。
        extra: 附加结构化信息（如 ``conflict_booking_no``）。
    """

    def __init__(
        self,
        error_code: str,
        message: Optional[str] = None,
        http_status: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.error_code = error_code
        self.http_status = http_status if http_status is not None else ERROR_HTTP.get(error_code, 400)
        self.message = message or DEFAULT_MESSAGE.get(error_code, error_code)
        self.extra: Dict[str, Any] = extra or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            **self.extra,
        }


def make_error(
    error_code: str,
    message: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> QinglinError:
    """便捷工厂：按错误码构造 ``QinglinError``。"""
    return QinglinError(error_code, message=message, extra=extra)


# 语义化工厂（降低调用处认知负担）
def point_already_locked(conflict_booking_no: Optional[str] = None) -> QinglinError:
    return make_error("POINT_ALREADY_LOCKED", extra={"conflict_booking_no": conflict_booking_no})


def protection_rule_violated() -> QinglinError:
    return make_error("PROTECTION_RULE_VIOLATED")


def lock_quota_exceeded() -> QinglinError:
    return make_error("LOCK_QUOTA_EXCEEDED")


def booking_not_found() -> QinglinError:
    return make_error("BOOKING_NOT_FOUND")
