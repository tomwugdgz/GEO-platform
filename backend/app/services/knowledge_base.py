"""
MCP 知识库管理模块 (Knowledge Base Manager)

当外部通过 MCP 调用系统后，自动将生成的结果归档到知识库目录，
支持按日期/工具类型/城市分类存储，提供知识库检索能力。

目录结构:
  data/knowledge/
  ├── 2026-06-09/                          # 按日期分类
  │   ├── pdooh_query_screens/             # 按工具名分类
  │   │   ├── 广州市.json                   # 按关键参数分类
  │   │   └── 深圳市.json
  │   ├── pdooh_audience_insight/
  │   │   ├── 广州_高端白酒.json
  │   │   └── 深圳_母婴.json
  │   └── pdooh_create_campaign/
  │       └── 高端白酒-天河城-周投.json
  ├── index.json                           # 全局索引（快速检索）
  ├── stats.json                           # 知识库统计
  └── call_logs.jsonl                      # 调用日志（每条独立记录）
"""

import os
import json
import hashlib
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

# 知识库根目录
KNOWLEDGE_ROOT = Path(__file__).parent.parent.parent.parent / "data" / "knowledge"
KNOWLEDGE_ROOT.mkdir(parents=True, exist_ok=True)

CALL_LOG_FILE = KNOWLEDGE_ROOT / "call_logs.jsonl"  # JSON Lines 格式


class KnowledgeManager:
    """MCP 知识库管理器"""

    def __init__(self, root: Path = KNOWLEDGE_ROOT):
        self.root = root
        self.index_file = root / "index.json"
        self.stats_file = root / "stats.json"

    def _serialize(self, obj: Any) -> Any:
        """序列化特殊类型（Decimal → float）"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize(i) for i in obj]
        return obj

    def _extract_key_params(self, arguments: dict) -> str:
        """从调用参数中提取关键标识（用于文件名）"""
        parts = []
        for key in ["city", "district", "name", "target_city", "brand"]:
            if key in arguments:
                parts.append(str(arguments[key]))
        filename = "_".join(parts) if parts else "default"
        # 限制文件名长度
        return filename[:80]

    def _file_safe_name(self, name: str) -> str:
        """确保文件名安全（去除非法字符）"""
        invalid = set(r'\/:*?"<>|')
        return "".join(c if c not in invalid else "_" for c in name)

    def store(
        self,
        tool_name: str,
        arguments: dict,
        result: Any,
        extra_meta: Optional[dict] = None,
    ) -> dict:
        """
        存储一次 MCP 调用结果到知识库

        Args:
            tool_name: 工具名称（如 pdooh_query_screens）
            arguments: 调用参数
            result: 调用结果
            extra_meta: 额外元数据

        Returns:
            存储信息（包含文件路径、ID 等）
        """
        today = date.today().isoformat()  # "2026-06-09"
        key_name = self._extract_key_params(arguments)
        key_name = self._file_safe_name(key_name)

        # 构建目录: data/knowledge/2026-06-09/pdooh_query_screens/
        tool_dir = self.root / today / tool_name
        tool_dir.mkdir(parents=True, exist_ok=True)

        # 文件路径
        filename = f"{key_name}.json"
        file_path = tool_dir / filename

        # 生成唯一 ID
        content_str = json.dumps({"tool": tool_name, "args": arguments}, sort_keys=True)
        record_id = hashlib.md5(content_str.encode()).hexdigest()[:12]

        # 构建记录
        record = {
            "id": record_id,
            "tool": tool_name,
            "arguments": self._serialize(arguments),
            "result": self._serialize(result),
            "meta": {
                "stored_at": datetime.now().isoformat(),
                "date": today,
                "file": str(file_path.relative_to(self.root)),
                "source": "mcp_call",
                **(extra_meta or {}),
            },
        }

        # 如果文件已存在，追加到数组
        if file_path.exists():
            existing = json.loads(file_path.read_text("utf-8"))
            if isinstance(existing, dict):
                existing = [existing]
            existing.append(record)
            file_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), "utf-8")
        else:
            file_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), "utf-8")

        # 更新全局索引
        self._update_index(record)
        # 更新统计
        self._update_stats(tool_name, today)
        # 写入调用日志 (JSONL 格式)
        self._write_call_log(tool_name, arguments, result, record_id, extra_meta)

        return {
            "status": "stored",
            "record_id": record_id,
            "file": str(file_path.relative_to(self.root)),
            "date": today,
            "tool": tool_name,
        }

    def _write_call_log(self, tool_name: str, arguments: dict, result: Any, record_id: str, extra_meta: Optional[dict]):
        """
        写入调用日志 (JSONL 格式)
        每行一条记录，支持高效追加和检索
        """
        log_entry = {
            "id": record_id,
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "tool": tool_name,
            "arguments": self._serialize(arguments),
            "result_summary": self._summarize_result(result),
            "source": (extra_meta or {}).get("source", "mcp_call"),
            "ip": (extra_meta or {}).get("ip", ""),
            "user_agent": (extra_meta or {}).get("user_agent", ""),
        }
        try:
            with open(CALL_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"[Knowledge Base] 写入调用日志失败: {e}")

    def _summarize_result(self, result: Any) -> str:
        """从结果中提取摘要（便于日志快速浏览）"""
        if isinstance(result, dict):
            content = result.get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
                # 取前 200 字符作为摘要
                return text[:200] + ("..." if len(text) > 200 else "")
        return str(result)[:200]

    def get_call_logs(
        self,
        tool_name: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """
        检索调用日志

        Args:
            tool_name: 按工具名筛选
            date_from: 起始日期
            date_to: 结束日期
            limit: 每页数量
            offset: 偏移量

        Returns:
            {total, logs: [...]}
        """
        if not CALL_LOG_FILE.exists():
            return {"total": 0, "logs": []}

        all_logs = []
        with open(CALL_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # 过滤条件
                if tool_name and entry.get("tool") != tool_name:
                    continue
                if date_from and entry.get("date", "") < date_from:
                    continue
                if date_to and entry.get("date", "") > date_to:
                    continue

                all_logs.append(entry)

        # 按时间倒序（最新的在前）
        all_logs.reverse()

        total = len(all_logs)
        page_logs = all_logs[offset:offset + limit]

        return {"total": total, "logs": page_logs}

    def get_call_log_detail(self, log_id: str) -> Optional[dict]:
        """根据 ID 获取调用日志完整详情（含完整 result）"""
        # 先找到摘要
        if not CALL_LOG_FILE.exists():
            return None
        with open(CALL_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("id") == log_id:
                        # 找到对应的完整记录
                        full_record = self.get_record(log_id)
                        if full_record:
                            entry["full_result"] = full_record.get("result")
                        return entry
                except json.JSONDecodeError:
                    continue
        return None

    def _update_index(self, record: dict):
        """更新全局索引"""
        index = self._load_index()
        record_id = record["id"]
        if record_id not in index:
            index[record_id] = {
                "tool": record["tool"],
                "date": record["meta"]["date"],
                "file": record["meta"]["file"],
                "arguments": record["arguments"],
            }
            self.index_file.write_text(
                json.dumps(index, ensure_ascii=False, indent=2), "utf-8"
            )

    def _load_index(self) -> dict:
        """加载全局索引"""
        if self.index_file.exists():
            return json.loads(self.index_file.read_text("utf-8"))
        return {}

    def _update_stats(self, tool_name: str, today: str):
        """更新知识库统计"""
        stats = self._load_stats()
        stats["total_records"] = stats.get("total_records", 0) + 1
        stats["by_tool"] = stats.get("by_tool", {})
        stats["by_tool"][tool_name] = stats["by_tool"].get(tool_name, 0) + 1
        stats["by_date"] = stats.get("by_date", {})
        stats["by_date"][today] = stats["by_date"].get(today, 0) + 1
        stats["last_updated"] = datetime.now().isoformat()
        self.stats_file.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), "utf-8"
        )

    def _load_stats(self) -> dict:
        """加载统计"""
        if self.stats_file.exists():
            return json.loads(self.stats_file.read_text("utf-8"))
        return {"total_records": 0, "by_tool": {}, "by_date": {}}

    def search(
        self,
        tool_name: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        city: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        检索知识库

        Args:
            tool_name: 按工具名筛选
            date_from: 起始日期
            date_to: 结束日期
            city: 按城市筛选
            keyword: 关键词搜索（匹配 arguments 和 result）
            limit: 返回数量上限

        Returns:
            匹配的记录列表
        """
        index = self._load_index()
        results = []

        for record_id, meta in index.items():
            # 过滤条件
            if tool_name and meta["tool"] != tool_name:
                continue
            if date_from and meta["date"] < date_from:
                continue
            if date_to and meta["date"] > date_to:
                continue
            if city and city not in json.dumps(meta["arguments"]):
                continue
            if keyword:
                content = json.dumps(meta["arguments"]) + json.dumps(meta)
                if keyword not in content:
                    continue

            results.append(meta)
            if len(results) >= limit:
                break

        return results

    def get_record(self, record_id: str) -> Optional[dict]:
        """根据 ID 获取完整记录"""
        index = self._load_index()
        if record_id not in index:
            return None
        meta = index[record_id]
        file_path = self.root / meta["file"]
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text("utf-8"))
        if isinstance(data, list):
            for item in data:
                if item.get("id") == record_id:
                    return item
            return None
        return data if data.get("id") == record_id else None

    def list_by_date(self, date_str: str) -> list[dict]:
        """按日期列出所有记录"""
        date_dir = self.root / date_str
        if not date_dir.exists():
            return []
        records = []
        for json_file in date_dir.rglob("*.json"):
            data = json.loads(json_file.read_text("utf-8"))
            if isinstance(data, dict):
                records.append(data)
            elif isinstance(data, list):
                records.extend(data)
        return records

    def list_by_tool(self, tool_name: str, limit: int = 100) -> list[dict]:
        """按工具名列出所有记录"""
        return self.search(tool_name=tool_name, limit=limit)

    def get_stats(self) -> dict:
        """获取知识库统计"""
        return self._load_stats()

    def list_dates(self) -> list[str]:
        """列出所有有数据的日期"""
        dates = []
        if self.root.exists():
            for item in sorted(self.root.iterdir(), reverse=True):
                if item.is_dir() and len(item.name) == 10:  # YYYY-MM-DD
                    dates.append(item.name)
        return dates

    def list_tools(self) -> list[str]:
        """列出所有已使用过的工具名"""
        stats = self._load_stats()
        return list(stats.get("by_tool", {}).keys())

    def export_by_date(self, date_str: str) -> list[dict]:
        """
        按日期批量导出知识库记录

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            该日期所有记录列表
        """
        return self.list_by_date(date_str)

    def export_by_tool(self, tool_name: str) -> list[dict]:
        """
        按工具名批量导出知识库记录

        Args:
            tool_name: 工具名

        Returns:
            该工具所有记录列表
        """
        return self.list_by_tool(tool_name)

    def cleanup_old_records(self, days: int = 90) -> dict:
        """
        清理指定天数前的知识库记录

        Args:
            days: 保留天数（默认 90 天）

        Returns:
            清理统计
        """
        from datetime import timedelta
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        index = self._load_index()
        to_delete = []
        for record_id, meta in index.items():
            if meta["date"] < cutoff:
                to_delete.append((record_id, meta))

        for record_id, meta in to_delete:
            # 删除文件
            file_path = self.root / meta["file"]
            if file_path.exists():
                data = json.loads(file_path.read_text("utf-8"))
                if isinstance(data, list):
                    # 从数组中移除该记录
                    new_data = [item for item in data if item.get("id") != record_id]
                    if new_data:
                        file_path.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), "utf-8")
                    else:
                        file_path.unlink()
                else:
                    file_path.unlink()
            # 删除索引
            del index[record_id]

        # 保存更新后的索引
        self.index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), "utf-8")

        return {
            "status": "cleaned",
            "deleted_count": len(to_delete),
            "cutoff_date": cutoff,
        }

    def rebuild_index(self) -> dict:
        """
        重建知识库索引（从文件系统扫描）

        Returns:
            重建统计
        """
        new_index = {}
        total_files = 0
        total_records = 0

        if self.root.exists():
            for json_file in self.root.rglob("*.json"):
                if json_file.name in ("index.json", "stats.json"):
                    continue
                total_files += 1
                try:
                    data = json.loads(json_file.read_text("utf-8"))
                    if isinstance(data, list):
                        for item in data:
                            if item.get("id"):
                                new_index[item["id"]] = {
                                    "tool": item.get("tool", ""),
                                    "date": item.get("meta", {}).get("date", ""),
                                    "file": str(json_file.relative_to(self.root)),
                                    "arguments": item.get("arguments", {}),
                                }
                                total_records += 1
                    elif isinstance(data, dict) and data.get("id"):
                        new_index[data["id"]] = {
                            "tool": data.get("tool", ""),
                            "date": data.get("meta", {}).get("date", ""),
                            "file": str(json_file.relative_to(self.root)),
                            "arguments": data.get("arguments", {}),
                        }
                        total_records += 1
                except (json.JSONDecodeError, KeyError):
                    continue

        self.index_file.write_text(json.dumps(new_index, ensure_ascii=False, indent=2), "utf-8")

        return {
            "status": "rebuilt",
            "total_files": total_files,
            "total_records": total_records,
        }


# 全局单例
kb = KnowledgeManager()


def auto_store_mcp_result(
    tool_name: str, arguments: dict, result: Any,
    ip: str = "", user_agent: str = "", **kwargs
) -> dict:
    """
    便捷函数：自动存储 MCP 调用结果

    在每个 MCP 工具调用后调用此函数，即可自动归档到知识库。
    同时记录调用日志（含 IP、User-Agent）。
    """
    kwargs["ip"] = ip
    kwargs["user_agent"] = user_agent
    return kb.store(tool_name, arguments, result, extra_meta=kwargs)
