"""青柠 Booking — Redis 分布式锁（四层防护之层②）。

基于 ``redis.asyncio`` 的 ``SET key token NX PX`` 实现：
- 原子获取（仅当 key 不存在时成功），保证并发串行化；
- 写入随机 ``token``，释放时校验 token 防误删他人锁；
- 自带 ``PX`` 自动过期兜底（进程崩溃不残留）；
- 提供异步上下文管理器 ``DistributedLock`` 与函数式 ``acquire_lock`` / ``release_lock``。

锁键约定（见设计文档 §15）：``qinglin:lock:booking:{media_resource_id}:{lock_start}:{lock_end}``
"""
from __future__ import annotations

import secrets
from typing import NamedTuple

import redis.asyncio as aioredis

from app.config import settings

_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

# 释放脚本：仅当 value 匹配 token（或强制 '*'）才删除，原子防误删。
_RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] or ARGV[1] == '*' then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


class LockResult(NamedTuple):
    acquired: bool
    token: str


def lock_key(media_resource_id, lock_start, lock_end) -> str:
    """生成层② Redis 锁键（同点位 + 同档期共享一把锁，实现串行化）。"""
    return f"qinglin:lock:booking:{media_resource_id}:{lock_start}:{lock_end}"


async def acquire_lock(key: str, px_ms: int, token: str | None = None) -> LockResult:
    """尝试获取分布式锁。成功返回 (acquired=True, token)，失败 (acquired=False, token)。"""
    token = token or secrets.token_hex(16)
    ok = await _redis.set(key, token, nx=True, px=px_ms)
    return LockResult(acquired=bool(ok), token=token)


async def release_lock(key: str, token: str, *, force: bool = False) -> int:
    """释放锁。token 不匹配则跳过（防误删）；force=True 或 token='*' 强制删除。

    返回删除的 key 数（0 表示未删，best-effort，不抛异常）。
    """
    try:
        arg = "*" if force else token
        return await _redis.eval(_RELEASE_LUA, 1, key, arg)
    except Exception:  # noqa: BLE001
        return 0


async def clear_lock(key: str) -> int:
    """强制清理指定锁键（用于测试/诊断）。"""
    try:
        return await _redis.delete(key)
    except Exception:  # noqa: BLE001
        return 0


class DistributedLock:
    """异步上下文管理器：进入时获取锁，退出时（无论成败）释放（token 校验）。"""

    def __init__(self, key: str, px_ms: int = 5000) -> None:
        self.key = key
        self.px_ms = px_ms
        self.token: str | None = None
        self.acquired = False

    async def __aenter__(self) -> "DistributedLock":
        res = await acquire_lock(self.key, self.px_ms)
        self.token = res.token
        self.acquired = res.acquired
        if not self.acquired:
            raise RuntimeError(f"未能获取分布式锁: {self.key}")
        return self

    async def __aexit__(self, *exc) -> bool:
        if self.token:
            await release_lock(self.key, self.token)
        return False
