"""Windows 兼容层：为 GeoLook 提供 `fcntl` 的最小替代实现。

背景
----
GeoLook 上游只在 macOS / Linux 上运行，`geolib.py` 顶部直接 `import fcntl`，
并调用 `fcntl.flock(fd, LOCK_EX / LOCK_UN)` 做「项目级跨进程锁」，
保护 `work/<slug>/geo.json` 的 load-modify-write 序列。

`fcntl` 是 POSIX 专有模块，Windows CPython 不提供，导致任何命令都
`ModuleNotFoundError` 而完全无法启动。

方案
----
用 Windows 自带的 `msvcrt.locking()` 实现等价的**独占锁**语义：

    LOCK_EX  ->  msvcrt.LK_LOCK   （阻塞式，拿不到锁就重试）
    LOCK_UN  ->  msvcrt.LK_UNLCK

`msvcrt.locking(fd, mode, nbytes)` 锁定的是**文件区域**（从当前文件位置
起 nbytes 字节），不是整个文件句柄，因此解锁时必须先 `seek(0)` 回到同一
区域起点，否则会解锁到错误的区域、锁残留。

锁范围取 1 字节即可：本模块只用于 `work/<slug>/.lock` 这一专用锁文件，
每个项目一把锁，1 字节足以形成互斥。锁文件内容无意义。

降级策略（三级，逐级兜底）
--------------------------
1. `msvcrt` 可用      -> 真正的跨进程独占锁（首选，与 POSIX 行为等价）
2. `msvcrt` 不可用    -> 进程内 `threading.Lock`（同进程多线程仍安全）
3. 上面都失败         -> no-op（记录警告；单进程顺序执行场景下不影响正确性）

这样即使运行在极端受限环境，GeoLook 也不会因为锁而整体崩溃。

用法
----
在 `geolib.py` 中改为：

    try:
        import fcntl
    except ModuleNotFoundError:
        from _win_fcntl import fcntl_shim as fcntl

其余代码无需改动 —— 接口（LOCK_EX / LOCK_UN / flock）保持一致。
"""

from __future__ import annotations

import threading
import warnings

LOCK_EX = 2   # 与 POSIX 常量取值保持一致，避免调用方硬编码比较
LOCK_SH = 1
LOCK_UN = 8

_warned = False
_fallback_locks: dict[int, threading.Lock] = {}
_fallback_guard = threading.Lock()


def _warn_once(msg: str) -> None:
    global _warned
    if not _warned:
        warnings.warn(msg, RuntimeWarning, stacklevel=3)
        _warned = True


def _get_fallback_lock(fd: int) -> threading.Lock:
    """按 fd 复用同一把进程内锁，保证同 fd 多次加锁是同一把。"""
    with _fallback_guard:
        lk = _fallback_locks.get(fd)
        if lk is None:
            lk = threading.Lock()
            _fallback_locks[fd] = lk
        return lk


def flock(fd, operation: int) -> None:
    """模拟 `fcntl.flock`。仅实现 GeoLook 用到的 LOCK_EX / LOCK_UN。

    fd 可以是 int 文件描述符，也可以是带 `fileno()` 的对象（file 对象）。
    `geolib.project_lock` 传入的是 file 对象，因此两种都要支持。
    """
    try:
        raw_fd = fd if isinstance(fd, int) else fd.fileno()
    except (AttributeError, ValueError, OSError):
        _warn_once("[win-fcntl] 无法取得文件描述符，跳过加锁")
        return

    # ---- 优先：msvcrt 真实文件锁（跨进程生效）----
    try:
        import msvcrt
    except ImportError:
        msvcrt = None  # type: ignore[assignment]

    if msvcrt is not None:
        try:
            if isinstance(fd, int):
                pass  # 已是 fd，msvcrt 直接可用
            # msvcrt.locking 需要文件位置，锁定/解锁务必落在同一区域
            if operation & LOCK_UN:
                _seek_start(fd)
                msvcrt.locking(raw_fd, msvcrt.LK_UNLCK, 1)
            else:
                _seek_start(fd)
                msvcrt.locking(raw_fd, msvcrt.LK_LOCK, 1)
            return
        except OSError:
            # 锁竞争/句柄状态异常 -> 落到进程内锁，不让管线崩掉
            _warn_once("[win-fcntl] msvcrt 文件锁不可用，降级为进程内线程锁")
        except ValueError:
            _warn_once("[win-fcntl] 文件句柄状态异常，降级为进程内线程锁")

    # ---- 次选：进程内线程锁 ----
    lk = _get_fallback_lock(raw_fd)
    if operation & LOCK_UN:
        if lk.locked():
            try:
                lk.release()
            except RuntimeError:
                pass
    else:
        lk.acquire()


def _seek_start(fd) -> None:
    """把文件位置复位到 0，使加锁与解锁作用于同一字节区域。"""
    try:
        if isinstance(fd, int):
            import os
            os.lseek(fd, 0, os.SEEK_SET)
        else:
            fd.seek(0)
    except (OSError, ValueError, AttributeError):
        # 某些句柄不可 seek（管道等）；GeoLook 只锁普通文件，正常不会走到
        pass


class _FcntlShim:
    """以对象形式暴露，便于 `from _win_fcntl import fcntl_shim as fcntl` 使用。"""

    LOCK_EX = LOCK_EX
    LOCK_SH = LOCK_SH
    LOCK_UN = LOCK_UN
    flock = staticmethod(flock)


fcntl_shim = _FcntlShim()
__all__ = ["fcntl_shim", "flock", "LOCK_EX", "LOCK_SH", "LOCK_UN"]
