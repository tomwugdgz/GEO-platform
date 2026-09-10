"""
GeoLook 引擎 FastAPI 适配层
提供 REST API 接口，调用移植的 GeoLook 算法
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import time
from pathlib import Path
import subprocess
import json

router = APIRouter(prefix="/geolook", tags=["GeoLook 引擎"])

# GeoLook 引擎路径
GEOLOOK_DIR = Path(__file__).resolve().parent.parent.parent / "geolook"
GEOLOOK_PY = GEOLOOK_DIR / "geo.py"
PYTHON_ENV = r"C:\Users\wolf2\.workbuddy\binaries\python\envs\geolook\Scripts\python.exe"


class ProjectInit(BaseModel):
    url: str
    name: Optional[str] = None
    slug: Optional[str] = None
    market: Optional[str] = "cn"
    max_pages: Optional[int] = 25


class ProjectResponse(BaseModel):
    slug: str
    brand_name: str
    site: str
    market: str
    created_at: str
    question_count: int
    competitor_count: int


def run_geolook_command(*args, timeout: int = 300) -> Dict[str, Any]:
    """
    执行 GeoLook CLI 命令
    返回: {"success": bool, "stdout": str, "stderr": str, "returncode": int}
    """
    try:
        result = subprocess.run(
            [PYTHON_ENV, str(GEOLOOK_PY), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(GEOLOOK_DIR),
            encoding='utf-8',
            errors='replace'
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"命令超时（{timeout}秒）", "returncode": -1}
    except Exception as e:
        return {"success": False, "error": str(e), "returncode": -1}


# ═══════════════════════════════════════════════════════════════
# 公共工具：项目定位 / 安全读取 / 空态返回
# ═══════════════════════════════════════════════════════════════

#: GeoLook verify.py 的判定词 → 前端统一状态码
VERDICT_MAP = {"通过": "passed", "未达标": "failed", "待人工": "pending"}

#: 工单状态 → 中文标签
TASK_STATUS_LABEL = {
    "todo": "待办", "doing": "进行中", "done": "已完成",
    "blocked": "受阻", "wontfix": "不修复",
}


def project_dir(slug: str) -> Path:
    """项目产物目录：work/<slug>/（原样保留 GeoLook 的目录结构，零改写）"""
    return GEOLOOK_DIR / "work" / slug


def project_exists(slug: str) -> bool:
    return (project_dir(slug) / "geo.json").exists()


def require_project(slug: str) -> Path:
    """项目不存在才 404；数据未生成一律走空态（避免前端整页报错）"""
    pdir = project_dir(slug)
    if not (pdir / "geo.json").exists():
        raise HTTPException(status_code=404, detail=f"项目 {slug} 不存在")
    return pdir


def read_json_safe(path: Path, default: Any = None) -> Any:
    """容错读取 JSON：文件缺失或损坏都返回默认值"""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def latest_file(directory: Path, pattern: str = "*.json") -> Optional[Path]:
    """取目录内最新文件（按 mtime，其次文件名）"""
    if not directory.exists():
        return None
    files = [f for f in directory.glob(pattern) if f.is_file()]
    if not files:
        return None
    return sorted(files, key=lambda f: (f.stat().st_mtime, f.name))[-1]


def clean_error(result: Dict[str, Any], fallback: str) -> str:
    """从 CLI 结果里挑一句可读的失败原因"""
    text = (result.get("stderr") or "").strip() or (result.get("error") or "")
    if not text:
        text = (result.get("stdout") or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else fallback


def build_verify_payload(
    slug: str,
    report: Optional[Dict[str, Any]] = None,
    recheck: Optional[bool] = None,
    load_latest: bool = True,
) -> Dict[str, Any]:
    """
    把 verify.py 的原始报告（零改写保留在 results/summary 里）
    额外投影出前端统一口径的字段：total_tasks / passed_tasks / details 等。
    """
    if report is None and load_latest:
        report = read_json_safe(latest_file(project_dir(slug) / "verify"), None)

    if not report:
        return {
            "exists": False,
            "slug": slug,
            "verify_time": None,
            "recheck": recheck,
            "total_tasks": 0,
            "passed_tasks": 0,
            "failed_tasks": 0,
            "manual_tasks": 0,
            "pass_rate": 0,
            "changed": 0,
            "details": [],
            "tasks": [],
            "results": [],
            "summary": {},
            "notes": "尚未执行验收，点击「运行验收」开始重抓 + 自动判定",
        }

    results = report.get("results") or []
    details: List[Dict[str, Any]] = []
    for r in results:
        status = VERDICT_MAP.get(r.get("verdict"), "pending")
        details.append({
            "task_id": r.get("id"),
            "id": r.get("id"),
            "title": r.get("title"),
            "status": status,
            "verdict": r.get("verdict"),
            "reason": r.get("note"),
            "evidence": r.get("note"),
            "priority": r.get("priority"),
            "package": r.get("package"),
            "market": r.get("market"),
            "was": r.get("was"),
            "now": r.get("now"),
            "progress": r.get("progress"),
            "progress_first": r.get("progress_first"),
        })

    total = len(details)
    passed = sum(1 for d in details if d["status"] == "passed")
    failed = sum(1 for d in details if d["status"] == "failed")
    manual = sum(1 for d in details if d["status"] == "pending")

    return {
        "exists": True,
        "slug": report.get("slug", slug),
        "verify_time": report.get("verified_at"),
        "recheck": recheck,
        "total_tasks": total,
        "passed_tasks": passed,
        "failed_tasks": failed,
        "manual_tasks": manual,
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "changed": report.get("changed", 0),
        "audit_avg_score": report.get("audit_avg_score"),
        "metrics_date": report.get("metrics_date"),
        "summary": report.get("summary", {}),
        "notes": f"通过 {passed} / 未达标 {failed} / 待人工 {manual}；状态变更 {report.get('changed', 0)} 条",
        "details": details,
        "tasks": details,       # 兼容前端 tasks 字段名
        "results": results,     # GeoLook 原始结果，零改写
    }


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """列出所有 GeoLook 项目"""
    result = run_geolook_command("list")
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "命令执行失败"))
    
    projects = []
    for line in result["stdout"].strip().split("\n"):
        if not line.strip():
            continue
        # 解析格式: slug  brand_name  问题 N  最近报告 YYYY-MM-DD
        parts = line.split()
        if len(parts) >= 4:
            slug = parts[0]
            brand = parts[1]
            # 尝试读取 geo.json 获取更多信息
            geo_json = GEOLOOK_DIR / "work" / slug / "geo.json"
            if geo_json.exists():
                with open(geo_json, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    projects.append(ProjectResponse(
                        slug=slug,
                        brand_name=cfg.get("brand", {}).get("name", brand),
                        site=cfg.get("brand", {}).get("site", ""),
                        market=cfg.get("market", "cn"),
                        created_at=cfg.get("created_at", ""),
                        question_count=len(cfg.get("questions", [])),
                        competitor_count=len(cfg.get("competitors", []))
                    ))
    
    return projects


@router.post("/projects/init")
async def init_project(project: ProjectInit, background_tasks: BackgroundTasks):
    """初始化新项目"""
    args = ["init", "--url", project.url]
    
    if project.name:
        args.extend(["--name", project.name])
    if project.slug:
        args.extend(["--slug", project.slug])
    if project.market:
        args.extend(["--market", project.market])
    if project.max_pages:
        args.extend(["--max-pages", str(project.max_pages)])
    
    result = run_geolook_command(*args)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("stderr", "初始化失败"))
    
    # 提取 slug
    slug = project.slug or project.url.split("//")[1].split("/")[0].replace("www.", "")
    
    return {"message": "项目初始化成功", "slug": slug, "output": result["stdout"]}


@router.post("/projects/{slug}/crawl")
async def crawl_project(slug: str, max_pages: Optional[int] = 25):
    """抓取项目官网"""
    args = ["crawl", "--slug", slug, "--max-pages", str(max_pages)]
    result = run_geolook_command(*args, timeout=600)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "抓取失败"))
    
    return {"message": "抓取完成", "output": result["stdout"]}


@router.post("/projects/{slug}/audit")
async def audit_project(slug: str):
    """执行六维体检"""
    args = ["audit", "--slug", slug]
    result = run_geolook_command(*args, timeout=300)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "体检失败"))
    
    # 读取体检结果
    audit_json = GEOLOOK_DIR / "work" / slug / "audit.json"
    if audit_json.exists():
        with open(audit_json, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        return {"message": "体检完成", "output": result["stdout"], "data": audit_data}
    
    return {"message": "体检完成", "output": result["stdout"]}


@router.post("/projects/{slug}/plan")
async def plan_project(slug: str):
    """生成工单"""
    args = ["plan", "--slug", slug]
    result = run_geolook_command(*args, timeout=300)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "生成工单失败"))
    
    # 读取工单
    tasks_json = GEOLOOK_DIR / "work" / slug / "tasks.json"
    if tasks_json.exists():
        with open(tasks_json, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        return {"message": "工单生成完成", "output": result["stdout"], "data": tasks_data}
    
    return {"message": "工单生成完成", "output": result["stdout"]}


@router.post("/projects/{slug}/generate")
async def generate_assets(slug: str):
    """生成资产（llms.txt、JSON-LD 等）"""
    args = ["generate", "--slug", slug]
    result = run_geolook_command(*args, timeout=300)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "生成资产失败"))
    
    return {"message": "资产生成完成", "output": result["stdout"]}


@router.post("/projects/{slug}/report")
async def generate_report(slug: str):
    """生成报告"""
    args = ["report", "--slug", slug]
    result = run_geolook_command(*args, timeout=300)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "生成报告失败"))
    
    return {"message": "报告生成完成", "output": result["stdout"]}


@router.post("/projects/{slug}/full-cycle")
async def full_cycle(slug: str, max_pages: Optional[int] = 25):
    """执行完整周期：抓取 → 体检 → 工单 → 资产 → 报告"""
    steps = [
        ("crawl", ["crawl", "--slug", slug, "--max-pages", str(max_pages)]),
        ("audit", ["audit", "--slug", slug]),
        ("plan", ["plan", "--slug", slug]),
        ("generate", ["generate", "--slug", slug]),
        ("report", ["report", "--slug", slug]),
    ]
    
    results = {}
    for step_name, args in steps:
        result = run_geolook_command(*args, timeout=600)
        results[step_name] = {
            "success": result["success"],
            "output": result.get("stdout", ""),
            "error": result.get("stderr", "")
        }
        if not result["success"]:
            return {"message": f"{step_name} 步骤失败", "results": results}
    
    return {"message": "完整周期执行完成", "results": results}


@router.get("/projects/{slug}/status")
async def get_project_status(slug: str):
    """
    获取项目状态。
    结构化字段来自 work/<slug>/ 的原始产物（零改写），
    同时保留 GeoLook CLI 的文本看板输出供对照。
    """
    pdir = require_project(slug)

    cfg = read_json_safe(pdir / "geo.json", {}) or {}
    tasks = (read_json_safe(pdir / "tasks.json", {}) or {}).get("tasks", []) or []
    audit = read_json_safe(pdir / "audit.json", {}) or {}
    verify_report = read_json_safe(latest_file(pdir / "verify"), None)

    done = sum(1 for t in tasks if t.get("status") == "done")
    stages = {
        "crawl": (pdir / "crawl").exists() or (pdir / "pages").exists(),
        "audit": bool(audit),
        "sample": (pdir / "metrics").exists() and any((pdir / "metrics").glob("*.json")),
        "plan": bool(tasks),
        "generate": (pdir / "assets").exists(),
        "report": (pdir / "reports").exists(),
        "verify": bool(verify_report),
        "deliverables": (pdir / "deliverables").exists(),
        "blueprint": (pdir / "blueprint.json").exists(),
    }

    result = run_geolook_command("status", "--slug", slug, timeout=120) if project_exists(slug) else {}

    return {
        "exists": True,
        "slug": slug,
        "brand": cfg.get("brand", {}),
        "market": cfg.get("market"),
        "site": cfg.get("site"),
        "stages": stages,
        "progress": {
            "completed_stages": sum(1 for v in stages.values() if v),
            "total_stages": len(stages),
            "percent": round(sum(1 for v in stages.values() if v) / len(stages) * 100, 1),
        },
        "tasks": {"total": len(tasks), "done": done,
                  "percent": round(done / len(tasks) * 100, 1) if tasks else 0},
        "audit": {"avg_score": audit.get("avg_score"), "page_count": audit.get("page_count")},
        "verify": {"exists": bool(verify_report),
                   "verified_at": (verify_report or {}).get("verified_at")},
        "output": (result or {}).get("stdout", ""),
    }


@router.get("/projects/{slug}/audit-data")
async def get_audit_data(slug: str):
    """获取体检数据（未体检时返回空态，不报错）"""
    pdir = require_project(slug)
    audit = read_json_safe(pdir / "audit.json", None)
    if audit is None:
        return {
            "exists": False,
            "avg_score": None,
            "page_count": 0,
            "grade_distribution": {},
            "layers": [],
            "site_issues": [],
            "pages": [],
            "message": "体检数据不存在，请先执行体检",
        }
    audit["exists"] = True
    return audit


@router.get("/projects/{slug}/tasks")
async def get_tasks(slug: str):
    """获取工单列表（未生成时返回空态，不报错）"""
    pdir = require_project(slug)
    data = read_json_safe(pdir / "tasks.json", None)
    if not data:
        return {
            "exists": False,
            "slug": slug,
            "generated_at": None,
            "tasks": [],
            "summary": {},
            "stats": {"total": 0, "done": 0, "doing": 0, "todo": 0, "blocked": 0, "wontfix": 0,
                      "completion_rate": 0},
            "message": "工单不存在，请先点击「生成工单」",
        }

    tasks = data.get("tasks", []) or []
    stats = {"total": len(tasks), "done": 0, "doing": 0, "todo": 0, "blocked": 0, "wontfix": 0}
    for t in tasks:
        st = t.get("status", "todo")
        stats[st] = stats.get(st, 0) + 1
        t.setdefault("status_label", TASK_STATUS_LABEL.get(st, st))
    stats["completion_rate"] = round(stats["done"] / len(tasks) * 100, 1) if tasks else 0

    return {
        "exists": True,
        "slug": slug,
        "generated_at": data.get("generated_at"),
        "tasks": tasks,
        "summary": data.get("summary", {}),
        "stats": stats,
    }


@router.get("/projects/{slug}/assets")
async def list_assets(slug: str):
    """列出已生成的资产"""
    assets_dir = GEOLOOK_DIR / "work" / slug / "assets"
    if not assets_dir.exists():
        return {"assets": []}
    
    assets = []
    for f in assets_dir.rglob("*"):
        if f.is_file():
            assets.append({
                "name": f.name,
                "path": str(f.relative_to(assets_dir)),
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
    
    return {"assets": assets}


@router.get("/projects/{slug}/reports")
async def list_reports(slug: str):
    """列出已生成的报告"""
    reports_dir = GEOLOOK_DIR / "work" / slug / "reports"
    if not reports_dir.exists():
        return {"reports": []}
    
    reports = []
    for f in reports_dir.rglob("*.html"):
        if f.is_file():
            reports.append({
                "name": f.name,
                "path": str(f.relative_to(reports_dir)),
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
    
    return {"reports": sorted(reports, key=lambda x: x["modified"], reverse=True)}


# ═══════════════════════════════════════════════════════════════
# 扩展 API - 覆盖全部 18 个模块
# ═══════════════════════════════════════════════════════════════

@router.post("/projects/{slug}/bootstrap")
async def bootstrap_project(slug: str, skip_llm: Optional[bool] = False):
    """从官网自动推导品牌事实、竞品与问题库"""
    args = ["bootstrap", "--slug", slug]
    if skip_llm:
        args.append("--skip-llm")
    result = run_geolook_command(*args, timeout=600)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "引导失败"))
    
    return {"message": "引导完成", "output": result["stdout"]}


@router.post("/projects/{slug}/sample")
async def sample_project(slug: str, platforms: Optional[str] = None, repeat: Optional[int] = 1, limit: Optional[int] = None):
    """AI 答案采样"""
    args = ["sample", "--slug", slug, "--repeat", str(repeat)]
    if platforms:
        args.extend(["--platforms", platforms])
    if limit:
        args.extend(["--limit", str(limit)])
    
    result = run_geolook_command(*args, timeout=1800)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "采样失败"))
    
    return {"message": "采样完成", "output": result["stdout"]}


@router.get("/projects/{slug}/samples")
async def list_samples(slug: str, platform: Optional[str] = None, limit: Optional[int] = 100):
    """列出采样样本"""
    samples_dir = GEOLOOK_DIR / "work" / slug / "samples"
    if not samples_dir.exists():
        return {"samples": []}
    
    samples = []
    for f in samples_dir.glob("*.json"):
        if f.is_file():
            data = json.loads(f.read_text(encoding="utf-8"))
            if platform and data.get("platform") != platform:
                continue
            samples.append(data)
            if len(samples) >= limit:
                break
    
    return {"samples": samples}


@router.post("/projects/{slug}/expand")
async def expand_keywords(slug: str, no_llm: Optional[bool] = False):
    """拓词：百度下拉 + Google suggest"""
    args = ["expand", "--slug", slug]
    if no_llm:
        args.append("--no-llm")
    
    result = run_geolook_command(*args, timeout=600)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "拓词失败"))
    
    return {"message": "拓词完成", "output": result["stdout"]}


@router.get("/projects/{slug}/blueprint")
async def get_blueprint(slug: str):
    """获取建设蓝图（未生成时返回空态，不报错）"""
    pdir = require_project(slug)
    blueprint = read_json_safe(pdir / "blueprint.json", None)
    if blueprint is None:
        return {
            "exists": False,
            "slug": slug,
            "channels": [],
            "message": "蓝图不存在，请先生成蓝图",
        }
    blueprint["exists"] = True
    return blueprint


@router.get("/projects/{slug}/verify")
async def get_verify_result(slug: str):
    """
    获取最近一次验收结果（未验收过返回空态，不报错）。
    原始报告字段（results/summary/changed）原样透出，另投影统一口径字段供前端渲染。
    """
    require_project(slug)
    return build_verify_payload(slug)


@router.post("/projects/{slug}/verify")
async def verify_project(slug: str, no_recrawl: Optional[bool] = False):
    """验收闭环：重抓 + 自动判定工单，返回结构化验收报告"""
    require_project(slug)
    args = ["verify", "--slug", slug]
    if no_recrawl:
        args.append("--no-recrawl")

    result = run_geolook_command(*args, timeout=600)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=clean_error(result, "验收失败"))

    payload = build_verify_payload(slug, recheck=not no_recrawl)
    payload["message"] = "验收完成"
    payload["output"] = result.get("stdout", "")
    return payload


@router.post("/projects/{slug}/deliverables")
async def generate_deliverables(slug: str):
    """生成三份正式交付物（诊断/优化/执行）"""
    args = ["deliverables", "--slug", slug]
    result = run_geolook_command(*args, timeout=600)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "生成交付物失败"))
    
    return {"message": "交付物生成完成", "output": result["stdout"]}


@router.post("/projects/{slug}/deliver")
async def deliver_project(slug: str):
    """打包客户交付物"""
    args = ["deliver", "--slug", slug]
    result = run_geolook_command(*args, timeout=600)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "打包失败"))
    
    return {"message": "交付包打包完成", "output": result["stdout"]}


@router.get("/projects/{slug}/deliverables")
async def list_deliverables(slug: str):
    """列出交付物"""
    deliverables_dir = GEOLOOK_DIR / "work" / slug / "deliverables"
    if not deliverables_dir.exists():
        return {"deliverables": []}
    
    deliverables = []
    for f in deliverables_dir.rglob("*.html"):
        if f.is_file():
            deliverables.append({
                "name": f.name,
                "path": str(f.relative_to(deliverables_dir)),
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
    
    return {"deliverables": sorted(deliverables, key=lambda x: x["modified"], reverse=True)}


@router.post("/projects/{slug}/publish")
async def publish_content(slug: str, path: str, platform: str, title: Optional[str] = ""):
    """发布内容到指定平台"""
    args = ["publish", "--slug", slug, "--path", path, "--platform", platform]
    if title:
        args.extend(["--title", title])
    
    result = run_geolook_command(*args, timeout=300)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("stderr", "发布失败"))
    
    return {"message": "发布完成", "output": result["stdout"]}


@router.get("/projects/{slug}/benchmark")
async def get_benchmark(slug: str):
    """
    获取行业大盘对照数据。
    已有 benchmark.json 直接返回；否则尝试现场跑一次 CLI，
    仍失败则返回空态 + 失败原因（不再抛 500 打断前端）。
    """
    pdir = require_project(slug)
    cached = read_json_safe(pdir / "benchmark.json", None)
    if cached:
        cached["exists"] = True
        return cached

    result = run_geolook_command("benchmark", "--slug", slug, timeout=300)
    if result.get("success"):
        fresh = read_json_safe(pdir / "benchmark.json", None)
        if fresh:
            fresh["exists"] = True
            return fresh

    return {
        "exists": False,
        "slug": slug,
        "message": "大盘对照数据尚未生成",
        "reason": clean_error(result, "需要先完成采样（metrics）才能做大盘对照"),
        "output": result.get("stdout", ""),
    }


@router.get("/projects/{slug}/analytics")
async def get_analytics(slug: str):
    """获取分析指标数据（未生成时返回空态）"""
    pdir = require_project(slug)
    analytics = read_json_safe(pdir / "analytics.json", None)
    if analytics is None:
        return {
            "exists": False,
            "slug": slug,
            "metrics": {},
            "trend": [],
            "message": "分析数据不存在，请先完成采样与体检",
        }
    analytics["exists"] = True
    return analytics


@router.get("/projects/{slug}/facts")
async def get_facts(slug: str):
    """获取品牌事实库"""
    facts_file = GEOLOOK_DIR / "work" / slug / "content" / "facts.md"
    if not facts_file.exists():
        return {"facts": "", "exists": False}
    
    return {
        "facts": facts_file.read_text(encoding="utf-8"),
        "exists": True
    }


class FactsUpdate(BaseModel):
    facts: str


@router.put("/projects/{slug}/facts")
async def update_facts(slug: str, payload: FactsUpdate):
    """
    更新品牌事实库（写入 work/<slug>/content/facts.md）。
    用请求体而非查询参数：事实库是多行 Markdown，查询串会撞 URL 长度上限。
    """
    pdir = require_project(slug)
    facts_file = pdir / "content" / "facts.md"
    facts_file.parent.mkdir(parents=True, exist_ok=True)
    facts_file.write_text(payload.facts or "", encoding="utf-8")

    return {"message": "品牌事实库已更新", "path": str(facts_file),
            "size": facts_file.stat().st_size}


@router.post("/projects/{slug}/blueprint")
async def generate_blueprint(slug: str):
    """生成 GEO 建设蓝图（渠道地图的数据来源）"""
    require_project(slug)
    result = run_geolook_command("blueprint", "--slug", slug, timeout=600)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=clean_error(result, "蓝图生成失败"))

    blueprint = read_json_safe(project_dir(slug) / "blueprint.json", None)
    return {
        "message": "蓝图生成完成",
        "output": result.get("stdout", ""),
        "exists": blueprint is not None,
        "channels": (blueprint or {}).get("channels", []),
    }


class CompetitorItem(BaseModel):
    name: str
    site: Optional[str] = ""
    aliases: Optional[List[str]] = []
    notes: Optional[str] = ""


@router.put("/projects/{slug}/competitors")
async def update_competitors(slug: str, competitors: List[CompetitorItem]):
    """
    覆盖写入竞品清单（写入 work/<slug>/geo.json 的 competitors 字段）。
    GeoLook 的 plan/verify 等命令会直接读取该字段，无需额外同步。
    """
    pdir = require_project(slug)
    config_file = pdir / "geo.json"
    config = read_json_safe(config_file, {}) or {}

    config["competitors"] = [c.model_dump() for c in competitors]
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"message": "竞品已更新", "count": len(competitors),
            "competitors": config["competitors"]}


@router.post("/projects/{slug}/competitors")
async def add_competitor(slug: str, competitor: CompetitorItem):
    """追加单个竞品"""
    pdir = require_project(slug)
    config_file = pdir / "geo.json"
    config = read_json_safe(config_file, {}) or {}

    items = config.get("competitors", []) or []
    entry = competitor.model_dump()
    if any((c.get("name") == entry["name"]) for c in items):
        return {"message": "竞品已存在", "count": len(items), "competitors": items}

    items.append(entry)
    config["competitors"] = items
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"message": "竞品已添加", "count": len(items), "competitors": items}


@router.get("/projects/{slug}/questions")
async def get_questions(slug: str):
    """获取问题库"""
    config_file = GEOLOOK_DIR / "work" / slug / "geo.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    config = json.loads(config_file.read_text(encoding="utf-8"))
    return {"questions": config.get("questions", [])}


@router.get("/projects/{slug}/competitors")
async def get_competitors(slug: str):
    """获取竞品列表"""
    config_file = GEOLOOK_DIR / "work" / slug / "geo.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    config = json.loads(config_file.read_text(encoding="utf-8"))
    return {"competitors": config.get("competitors", [])}


@router.get("/projects/{slug}/channels")
async def get_channels(slug: str):
    """
    获取渠道覆盖数据。
    渠道来自 blueprint.json 的 channels；蓝图未生成时返回空态。
    """
    pdir = require_project(slug)
    blueprint = read_json_safe(pdir / "blueprint.json", None)
    if not blueprint:
        return {
            "exists": False,
            "slug": slug,
            "channels": [],
            "platforms": [],
            "coverage": {"covered": 0, "total": 0, "percent": 0},
            "message": "蓝图不存在，请先生成蓝图",
        }

    channels = blueprint.get("channels") or blueprint.get("platforms") or []
    covered = sum(1 for c in channels
                  if isinstance(c, dict) and (c.get("covered") or c.get("status") in ("done", "covered", "已覆盖")))
    return {
        "exists": True,
        "slug": slug,
        "channels": channels,
        "platforms": blueprint.get("platforms", []),
        "coverage": {
            "covered": covered,
            "total": len(channels),
            "percent": round(covered / len(channels) * 100, 1) if channels else 0,
        },
        "generated_at": blueprint.get("generated_at"),
    }


@router.get("/projects/{slug}/gaps")
async def get_gaps(slug: str):
    """
    获取缺口诊断数据。
    缺口来自 audit.json 的 gaps/block_gap；
    若 audit.py 未产出显式 gaps 字段，则按页面薄弱项与站点问题现场投影一份。
    """
    pdir = require_project(slug)
    audit = read_json_safe(pdir / "audit.json", None)
    if not audit:
        return {
            "exists": False,
            "slug": slug,
            "gaps": [],
            "block_gap": [],
            "blockers": [],
            "message": "体检数据不存在，请先执行体检",
        }

    gaps = audit.get("gaps", []) or []
    block_gap = audit.get("block_gap", []) or []

    # 兜底投影：让「缺口诊断」在只有 audit.json 时也能给出可行动信息。
    # 同时补齐前端展示字段（title/description/priority/suggestion），
    # 原始字段（target/score/grade/issues/severity）一并保留，便于二次加工。
    if not gaps:
        for p in audit.get("pages", []) or []:
            score = p.get("score") or 0
            if score >= 65:
                continue
            severity = "P0" if score < 50 else "P1"
            issues = p.get("issues") or p.get("issue_codes") or []
            issues_text = "；".join(str(i) for i in issues) if issues else "页面 GEO 结构化程度不足"
            gaps.append({
                "type": "page",
                "title": f"页面得分 {score:.1f}（{p.get('grade') or '-'}级）：{(p.get('url') or '').split('/')[-1] or p.get('url')}",
                "description": issues_text,
                "priority": severity,
                "suggestion": "按上面列出的检查项逐条修复：补 H1/H2 层级、结构化成段短文、加 JSON-LD 与更新日期",
                "target": p.get("url"),
                "score": score,
                "grade": p.get("grade"),
                "issues": issues,
                "severity": severity,
            })
        for issue in audit.get("site_issues", []) or []:
            text = str(issue)
            severity = text[:2].strip() or "P1"
            block_gap.append({
                "type": "site",
                "title": text[2:].strip()[:60] or text[:60],
                "description": text,
                "priority": severity,
                "suggestion": "站点级问题优先处理：它会影响所有页面的可抓取性与可引性",
                "severity": severity,
                "issue": text,
            })

    # 归一化：无论 gaps 来自 audit.json 还是上面的投影，
    # 都保证前端要用的展示字段存在，避免出现只有编号没有内容的空条目。
    for i, g in enumerate(gaps):
        if not isinstance(g, dict):
            gaps[i] = {"title": str(g), "description": "", "priority": "", "suggestion": ""}
            continue
        if not g.get("title"):
            topic = g.get("topic") or g.get("keyword") or g.get("target") or g.get("type") or ""
            score = g.get("score")
            g["title"] = f"{topic}（得分 {score}）" if score is not None else (topic or f"缺口 {i + 1}")
        if not g.get("description"):
            issues = g.get("issues") or g.get("issue_codes") or []
            if isinstance(issues, list) and issues:
                g["description"] = "；".join(str(x) for x in issues)
            elif g.get("detail") or g.get("note"):
                g["description"] = str(g.get("detail") or g.get("note"))
        if not g.get("priority") and g.get("severity"):
            g["priority"] = g["severity"]
        if not g.get("suggestion"):
            g["suggestion"] = g.get("action") or g.get("fix") or ""

    for i, b in enumerate(block_gap):
        if isinstance(b, dict) and not b.get("title"):
            b["title"] = str(b.get("issue") or b.get("missing") or "")[:60] or f"模块缺口 {i + 1}"
            b.setdefault("description", str(b.get("issue") or ""))
            b.setdefault("priority", str(b.get("severity") or ""))

    return {
        "exists": True,
        "slug": slug,
        "avg_score": audit.get("avg_score"),
        "page_count": audit.get("page_count"),
        "grade_distribution": audit.get("grade_distribution", {}),
        "gaps": gaps,
        "block_gap": block_gap,
        "blockers": [b for b in block_gap if str(b.get("severity", "")).startswith("P0")],
        "layers": audit.get("layers", []),
    }


#: 引擎注册表兜底副本 —— 首选从 GeoLook 源码 sample.py 实时导出，避免与上游漂移
_FALLBACK_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "glm": {"name": "智谱GLM", "market": "cn", "model": "glm-4-flash",
            "model_env": "GLM_MODEL", "key_env": "ZHIPUAI_API_KEY", "search": False},
    "doubao": {"name": "豆包(方舟API)", "market": "cn", "model": "doubao-seed-1-6-250615",
               "model_env": "ARK_MODEL", "key_env": "ARK_API_KEY", "search": True},
    "deepseek": {"name": "DeepSeek", "market": "cn", "model": "deepseek-v4-flash",
                 "model_env": "DEEPSEEK_MODEL", "key_env": "DEEPSEEK_API_KEY", "search": False},
    "kimi": {"name": "Kimi", "market": "cn", "model": "kimi-k2-0905-preview",
             "model_env": "MOONSHOT_MODEL", "key_env": "MOONSHOT_API_KEY", "search": False},
    "minimax": {"name": "MiniMax", "market": "cn", "model": "MiniMax-M2",
                "model_env": "MINIMAX_MODEL", "key_env": "MINIMAX_API_KEY", "search": False},
    "gemini": {"name": "Gemini", "market": "global", "model": "gemini-2.5-flash",
               "model_env": "GEMINI_MODEL", "key_env": "GEMINI_API_KEY", "search": False},
    "openai": {"name": "OpenAI(ChatGPT)", "market": "global", "model": "gpt-4o-mini",
               "model_env": "OPENAI_MODEL", "key_env": "OPENAI_API_KEY", "search": False},
    "claude": {"name": "Claude", "market": "global", "model": "claude-sonnet-5",
               "model_env": "ANTHROPIC_MODEL", "key_env": "ANTHROPIC_API_KEY", "search": False},
    "grok": {"name": "Grok", "market": "global", "model": "grok-3-mini",
             "model_env": "GROK_MODEL", "key_env": "XAI_API_KEY", "search": False},
    "perplexity": {"name": "Perplexity", "market": "global", "model": "sonar",
                   "model_env": "PERPLEXITY_MODEL", "key_env": "PERPLEXITY_API_KEY", "search": True},
}

_MANUAL_ONLY_FALLBACK: Dict[str, Any] = {
    "nano_ai": ["纳米AI搜索（360）", "cn"],
    "baidu": ["百度 AI 搜索", "cn"],
    "doubao_app": ["豆包 App / 网页版", "cn"],
    "chatgpt": ["ChatGPT 网页版（开 Search）", "global"],
    "claude_web": ["Claude 网页版（开 Web Search）", "global"],
    "google_aio": ["Google AI Overviews", "global"],
    "metaso": ["秘塔AI搜索", "cn"],
}

_PROVIDER_CACHE: Dict[str, Any] = {"data": None, "at": 0.0}


def load_provider_registry() -> Dict[str, Any]:
    """
    以 GeoLook 源码为准导出引擎注册表（PROVIDERS / MANUAL_ONLY）。
    带 5 分钟内存缓存；导出失败时退回静态副本，保证接口永不 500。
    """
    now = time.time()
    if _PROVIDER_CACHE["data"] and now - _PROVIDER_CACHE["at"] < 300:
        return _PROVIDER_CACHE["data"]

    data = {"providers": _FALLBACK_PROVIDERS, "manual_only": _MANUAL_ONLY_FALLBACK,
            "source": "fallback"}
    try:
        code = ("import json, sample;"
                "print(json.dumps({'providers': sample.PROVIDERS,"
                " 'manual_only': sample.MANUAL_ONLY}, ensure_ascii=False))")
        r = subprocess.run([PYTHON_ENV, "-c", code], capture_output=True, text=True,
                           timeout=20, cwd=str(GEOLOOK_DIR), encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout.strip():
            parsed = json.loads(r.stdout)
            parsed["source"] = "geolook/sample.py"
            data = parsed
    except Exception:
        pass

    _PROVIDER_CACHE.update({"data": data, "at": now})
    return data


def _read_env_keys() -> Dict[str, str]:
    """
    读取引擎 Key。与 geolib.load_env 同口径：
    geolook/.env 优先，其次进程环境变量（已存在的环境变量不被 .env 覆盖）。
    """
    out: Dict[str, str] = {}
    env_file = GEOLOOK_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip("'\"")
    for k, v in os.environ.items():
        if v and k not in out:
            out[k] = v
    return out


@router.get("/projects/{slug}/engines")
async def get_engines(slug: str):
    """
    获取引擎配置和状态（10 个 API 引擎全保留 + 7 个纯人工采样渠道）。
    无 Key 的引擎标记 fallback=manual_sheet —— 走人工采样表，不影响跑通。
    """
    registry = load_provider_registry()
    providers = registry.get("providers", {}) or {}
    manual_only = registry.get("manual_only", {}) or {}
    keys = _read_env_keys()

    engines = []
    for code, meta in providers.items():
        meta = meta or {}
        key_env = meta.get("key_env", "")
        model_env = meta.get("model_env", "")
        val = keys.get(key_env, "") if key_env else ""
        configured = bool(val)
        item = {
            "code": code,
            "name": meta.get("name", code),
            "market": meta.get("market", "global"),
            "market_label": "中国" if meta.get("market") == "cn" else "国际",
            "model": keys.get(model_env) or meta.get("model", ""),
            "model_default": meta.get("model", ""),
            "model_env": model_env,
            "key_env": key_env,
            "base": meta.get("base", ""),
            "protocol": meta.get("protocol", "openai"),
            "search": bool(meta.get("search")),
            "note": meta.get("note", ""),
            "configured": configured,      # 前端 Settings 页字段名
            "has_key": configured,
            "key_preview": ((val[:6] + "…" + val[-4:]) if len(val) > 12
                            else ("已配置" if configured else "")),
            "status": "ready" if configured else "manual",
            "fallback": None if configured else "manual_sheet",
        }
        engines.append(item)
    engines.sort(key=lambda e: (e["market"] != "cn", e["code"]))

    manual = []
    for code, v in manual_only.items():
        try:
            name, market = v[0], v[1]
        except Exception:
            name, market = str(v), "global"
        manual.append({"code": code, "name": name, "market": market,
                       "market_label": "中国" if market == "cn" else "国际",
                       "status": "manual_only", "configured": False,
                       "fallback": "manual_sheet",
                       "note": "无公开联网问答 API，只能浏览器/人工采样"})

    return {
        "engines": engines,
        "manual_channels": manual,
        "total": len(engines),
        "configured": sum(1 for e in engines if e["has_key"]),
        "manual_only": sum(1 for e in engines if not e["has_key"]),
        "registry_source": registry.get("source"),
        "env_file": str(GEOLOOK_DIR / ".env"),
    }


@router.get("/projects/{slug}/siteaudit")
async def get_site_audit(slug: str):
    """获取站点审计详情（增强版；未体检时返回空态）"""
    pdir = require_project(slug)
    audit = read_json_safe(pdir / "audit.json", None)
    if not audit:
        return {
            "exists": False,
            "slug": slug,
            "avg_score": None,
            "page_count": 0,
            "grade_distribution": {},
            "pages": [],
            "site": {},
            "layers": [],
            "site_issues": [],
            "block_gap": [],
            "message": "体检数据不存在，请先执行体检",
        }

    site = audit.get("site", {}) or {}
    pages = audit.get("pages", []) or []
    grade_dist = audit.get("grade_distribution") or {}
    if not grade_dist and pages:
        grade_dist = {}
        for p in pages:
            g = p.get("grade") or "N/A"
            grade_dist[g] = grade_dist.get(g, 0) + 1

    return {
        "exists": True,
        "slug": slug,
        "audited_at": audit.get("audited_at") or audit.get("date"),
        "avg_score": audit.get("avg_score"),
        "page_count": audit.get("page_count") or len(pages),
        "grade_distribution": grade_dist,
        "pages": pages,
        "weak_pages": [p for p in pages if (p.get("score") or 100) < 65][:20],
        "site": site,
        "layers": audit.get("layers", []),
        "site_issues": audit.get("site_issues", []),
        "block_gap": audit.get("block_gap", []),
        "robots": site.get("robots"),
        "sitemap": site.get("has_sitemap"),
        "ai_bots_blocked": site.get("ai_bots_blocked", []),
    }


@router.get("/projects/{slug}/settings")
async def get_settings(slug: str):
    """获取项目设置"""
    config_file = GEOLOOK_DIR / "work" / slug / "geo.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    config = json.loads(config_file.read_text(encoding="utf-8"))
    return {
        "slug": config.get("slug"),
        "market": config.get("market"),
        "brand": config.get("brand", {}),
        "platforms": config.get("platforms", []),
        "targets": config.get("targets", {})
    }


@router.put("/projects/{slug}/settings")
async def update_settings(slug: str, settings: Dict[str, Any]):
    """更新项目设置"""
    config_file = GEOLOOK_DIR / "work" / slug / "geo.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    config = json.loads(config_file.read_text(encoding="utf-8"))
    
    # 更新配置
    for key, value in settings.items():
        if key in config:
            config[key] = value
    
    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"message": "设置已更新"}


# ═══════════════════════════════════════════════════════════════
# 原始产物层：work/<slug>/ 零改写浏览
# 存储策略 = 原样保留 GeoLook 的 work/<slug>/，不改写、不迁移，
# 这里只提供只读索引与内容读取，方便核对与排查。
# ═══════════════════════════════════════════════════════════════

#: 可直接当文本读取的扩展名
_TEXT_EXT = {".json", ".md", ".txt", ".html", ".htm", ".yml", ".yaml",
             ".csv", ".xml", ".log", ".py", ".js", ".css", ".toml"}

#: 单文件读取上限（防止把大 HTML 报告整份塞进响应）
_TEXT_LIMIT = 400_000


@router.get("/projects/{slug}/work")
async def list_work_files(slug: str):
    """列出 work/<slug>/ 下的全部原始产物文件（只读索引）"""
    pdir = require_project(slug)

    files: List[Dict[str, Any]] = []
    dir_stats: Dict[str, Dict[str, Any]] = {}
    for f in sorted(pdir.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(pdir).as_posix()
        top = rel.split("/")[0] if "/" in rel else "(根)"
        stat = f.stat()
        files.append({
            "path": rel,
            "name": f.name,
            "dir": rel.rsplit("/", 1)[0] if "/" in rel else "",
            "top_dir": top,
            "ext": f.suffix.lstrip(".").lower(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "readable": f.suffix.lower() in _TEXT_EXT,
        })
        d = dir_stats.setdefault(top, {"dir": top, "count": 0, "size": 0})
        d["count"] += 1
        d["size"] += stat.st_size

    return {
        "slug": slug,
        "root": str(pdir),
        "exists": True,
        "file_count": len(files),
        "total_size": sum(f["size"] for f in files),
        "dirs": sorted(dir_stats.values(), key=lambda d: -d["count"]),
        "files": sorted(files, key=lambda f: -f["modified"]),
    }


@router.get("/projects/{slug}/work/file")
async def read_work_file(slug: str, path: str):
    """
    读取 work/<slug>/ 下的单个原始文件。
    仅允许项目目录内的相对路径（防目录穿越）；大文件只返回头部并截断。
    """
    pdir = require_project(slug).resolve()

    target = (pdir / path).resolve()
    if not str(target).startswith(str(pdir)):
        raise HTTPException(status_code=400, detail="路径越界：只允许读取项目目录内的文件")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"文件不存在：{path}")

    size = target.stat().st_size
    ext = target.suffix.lower()
    meta = {
        "slug": slug, "path": path, "size": size,
        "modified": target.stat().st_mtime,
        "ext": ext.lstrip("."),
        "readable": ext in _TEXT_EXT,
    }
    if ext not in _TEXT_EXT:
        return {**meta, "content": None,
                "message": "二进制文件不返回内容，请直接在磁盘查看"}

    text = target.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > _TEXT_LIMIT
    return {
        **meta,
        "truncated": truncated,
        "content": text[:_TEXT_LIMIT] if truncated else text,
    }


# ═══════════════════════════════════════════════════════════════
# 概览聚合：给 Dashboard 增强用（一屏看清全流程状态）
# ═══════════════════════════════════════════════════════════════

@router.get("/projects/{slug}/overview")
async def get_overview(slug: str):
    """项目全局概览：各阶段产物齐备度 + 关键指标 + 引擎可用度"""
    pdir = require_project(slug)

    cfg = read_json_safe(pdir / "geo.json", {}) or {}
    audit = read_json_safe(pdir / "audit.json", {}) or {}
    tasks = (read_json_safe(pdir / "tasks.json", {}) or {}).get("tasks", []) or []
    blueprint = read_json_safe(pdir / "blueprint.json", {}) or {}

    metrics_files = sorted((pdir / "metrics").glob("*.json")) if (pdir / "metrics").exists() else []
    reports = sorted((pdir / "reports").rglob("*.html")) if (pdir / "reports").exists() else []
    assets = sorted((pdir / "assets").rglob("*")) if (pdir / "assets").exists() else []
    assets = [f for f in assets if f.is_file()]
    deliverables = sorted((pdir / "deliverables").rglob("*.html")) if (pdir / "deliverables").exists() else []
    verify_files = sorted((pdir / "verify").glob("*.json")) if (pdir / "verify").exists() else []

    latest_metrics = read_json_safe(metrics_files[-1], {}) if metrics_files else {}

    done = sum(1 for t in tasks if t.get("status") == "done")
    blocked = sum(1 for t in tasks if t.get("status") == "blocked")
    p0 = sum(1 for t in tasks if t.get("priority") == "P0")
    p0_open = sum(1 for t in tasks if t.get("priority") == "P0" and t.get("status") != "done")

    keys = _read_env_keys()
    registry = load_provider_registry()
    providers = registry.get("providers", {}) or {}
    engines_ready = sum(1 for m in providers.values()
                        if m.get("key_env") and keys.get(m.get("key_env", "")))

    verify_payload = build_verify_payload(slug)

    return {
        "exists": True,
        "slug": slug,
        "brand": cfg.get("brand", {}),
        "site": cfg.get("site") or (cfg.get("brand", {}) or {}).get("site"),
        "market": cfg.get("market"),
        "audit": {
            "exists": bool(audit),
            "avg_score": audit.get("avg_score"),
            "page_count": audit.get("page_count"),
            "grade_distribution": audit.get("grade_distribution", {}),
            "site_issue_count": len(audit.get("site_issues", []) or []),
            "weak_page_count": sum(1 for p in (audit.get("pages") or []) if (p.get("score") or 100) < 65),
        },
        "questions": {"count": len(cfg.get("questions", []) or [])},
        "competitors": {"count": len(cfg.get("competitors", []) or [])},
        "metrics": {
            "exists": bool(metrics_files),
            "runs": len(metrics_files),
            "latest_date": latest_metrics.get("date"),
            "records": latest_metrics.get("count") or latest_metrics.get("total"),
        },
        "tasks": {
            "exists": bool(tasks), "total": len(tasks), "done": done, "blocked": blocked,
            "p0": p0, "p0_open": p0_open,
            "percent": round(done / len(tasks) * 100, 1) if tasks else 0,
        },
        "verify": {
            "exists": verify_payload["exists"],
            "verify_time": verify_payload["verify_time"],
            "pass_rate": verify_payload["pass_rate"],
            "passed_tasks": verify_payload["passed_tasks"],
            "total_tasks": verify_payload["total_tasks"],
            "runs": len(verify_files),
        },
        "blueprint": {"exists": bool(blueprint),
                      "channel_count": len(blueprint.get("channels", []) or [])},
        "outputs": {
            "reports": len(reports),
            "assets": len(assets),
            "deliverables": len(deliverables),
            "latest_report": reports[-1].name if reports else None,
        },
        "engines": {
            "total": len(providers),
            "ready": engines_ready,
            "manual": len(providers) - engines_ready,
            "registry_source": registry.get("source"),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 引擎 Key 写入（写 geolook/.env，保留其它行不改写）
# ═══════════════════════════════════════════════════════════════

class EngineKeysUpdate(BaseModel):
    keys: Dict[str, str]


@router.put("/projects/{slug}/engines")
async def update_engine_keys(slug: str, payload: EngineKeysUpdate):
    """
    更新引擎 API Key（写入 geolook/.env）。
    只逐行替换/追加目标 KEY，其它内容原样保留。
    """
    env_file = GEOLOOK_DIR / ".env"
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    updates = {k.strip(): (v or "").strip() for k, v in (payload.keys or {}).items()}

    seen = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.partition("=")[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                seen.add(k)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in seen:
            new_lines.append(f"{k}={v}")

    env_file.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    _PROVIDER_CACHE.update({"data": None, "at": 0.0})

    return {"message": "引擎配置已更新", "updated": sorted(updates.keys()),
            "env_file": str(env_file)}
