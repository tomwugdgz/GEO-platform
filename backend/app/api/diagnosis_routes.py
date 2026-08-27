"""
品牌 GEO 诊断 API - 苍何诊断师工作流
实现 4 阶段流水线：基础调研 → 收录+可见性 → 舆情分析 → 评分建议
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import asyncio
import random
from datetime import datetime

router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

class DiagnosisRequest(BaseModel):
    brandName: str
    productType: str
    website: Optional[str] = None
    platforms: List[int] = [1,2,3,4,5,6,7,8]

class DiagnosisStage(BaseModel):
    stage: int
    name: str
    status: str  # pending, running, completed
    progress: int  # 0-100

class DiagnosisTask(BaseModel):
    taskId: str
    brandName: str
    productType: str
    website: Optional[str]
    platforms: List[int]
    stages: List[DiagnosisStage]
    currentStage: int
    result: Optional[Dict[str, Any]] = None

# 任务存储（实际应使用 Redis）
diagnosis_tasks: Dict[str, DiagnosisTask] = {}

# 平台数据
PLATFORM_DATA = {
    1: {"name": "DeepSeek", "icon": "D", "bias": "偏技术参数对比，提及技术领先品牌"},
    2: {"name": "豆包", "icon": "豆", "bias": "偏生活场景选购，提及大众口碑品牌"},
    3: {"name": "元宝", "icon": "元", "bias": "偏全面推荐，百科式回答"},
    4: {"name": "通义千问", "icon": "通", "bias": "偏结构化对比，列出多个选项"},
    5: {"name": "文心一言", "icon": "文", "bias": "偏中文生态，百度百科优先"},
    6: {"name": "纳米搜索", "icon": "纳", "bias": "偏简洁推荐，快速回答"},
    7: {"name": "Kimi", "icon": "K", "bias": "偏长文深度分析，引用多来源"},
    8: {"name": "智谱清言", "icon": "智", "bias": "偏学术/技术分析"},
}

# ═══════════════════════════════════════════════════════════════
# 4 阶段流水线
# ═══════════════════════════════════════════════════════════════

async def stage1_basic_research(task: DiagnosisTask) -> Dict[str, Any]:
    """
    阶段 1：基础调研
    - 用户画像 + 搜索场景
    - 基建评估（官网 + 自媒体 + 权威媒体）
    - 竞品分析
    """
    task.stages[0].status = "running"
    task.stages[0].progress = 0
    
    await asyncio.sleep(0.5)  # 模拟处理时间
    
    result = {
        "userProfile": {
            "brand": task.brandName,
            "category": task.productType,
            "profileDimensions": [
                {"key": "age_range", "label": "年龄分布", "value": random.randint(60, 85)},
                {"key": "interest", "label": "兴趣偏好", "value": random.randint(65, 90)},
                {"key": "purchase_power", "label": "购买力", "value": random.randint(50, 80)},
                {"key": "tech_savvy", "label": "技术敏感度", "value": random.randint(55, 85)},
            ],
            "groups": [
                {
                    "highlight": f"{task.brandName}核心产品优势",
                    "userProfile": "25-40岁，注重品质与性价比",
                    "scenario": f"用户搜索'{task.productType}推荐'时AI倾向推荐",
                    "questions": [
                        f"{task.productType}哪个牌子好",
                        f"{task.brandName}怎么样",
                        f"{task.productType}品牌排行榜",
                        f"值得买的{task.productType}推荐",
                        f"{task.brandName}口碑如何",
                    ]
                }
            ]
        },
        "infraEval": {
            "officialSite": {
                "exists": task.website is not None,
                "url": task.website,
                "score": random.randint(60, 85) if task.website else 0,
                "summary": "官网存在，响应速度良好，SEO基础待优化" if task.website else "未检测到官网",
            },
            "selfMedia": {
                "totalCount": random.randint(8, 20),
                "platformBreakdown": {
                    "知乎": random.randint(2, 6),
                    "小红书": random.randint(1, 5),
                    "B站": random.randint(1, 4),
                    "微信公众号": random.randint(2, 5),
                },
                "items": [
                    {
                        "platform": "知乎",
                        "title": f"如何评价{task.brandName}的{task.productType}",
                        "url": f"https://zhihu.com/question/example",
                        "source": "virtual"
                    }
                ]
            },
            "authoritativeMedia": {
                "totalCount": random.randint(2, 8),
                "platformBreakdown": {
                    "36氪": random.randint(0, 2),
                    "虎嗅": random.randint(0, 2),
                    "IT之家": random.randint(0, 2),
                },
                "items": []
            }
        },
        "competitors": {
            "competitors": [
                {
                    "name": f"竞品{chr(65+i)}",
                    "level": "头部" if i < 2 else "腰部",
                    "category": task.productType,
                    "geoScore": random.randint(60, 90),
                    "marketShare": random.randint(10, 25),
                    "threatLevel": "high" if i < 2 else "medium",
                    "strengths": ["品牌知名度高", "渠道覆盖广"],
                    "weaknesses": ["价格偏高", "创新不足"],
                    "productFeatures": ["核心功能A", "差异化服务B"],
                    "description": f"行业领先品牌，市场份额约{random.randint(15, 25)}%",
                    "website": None
                }
                for i in range(4)
            ],
            "brandStrengths": [f"{task.brandName}在特定细分市场有优势", "产品性价比高"],
            "brandWeaknesses": ["品牌知名度待提升", "权威媒体覆盖不足"],
            "marketPosition": "腰部品牌，快速增长中"
        }
    }
    
    task.stages[0].status = "completed"
    task.stages[0].progress = 100
    return result


async def stage2_inclusion_visibility(task: DiagnosisTask, stage1_result: Dict) -> Dict[str, Any]:
    """
    阶段 2：收录 + 可见性
    - 8 平台虚拟收录查询（品牌提及率）
    - GEO 效果统计
    """
    task.stages[1].status = "running"
    task.stages[1].progress = 0
    
    await asyncio.sleep(0.5)
    
    # 根据平台偏好生成提及率（±8% 波动）
    base_rate = random.randint(45, 75)
    platforms = []
    
    for pid in task.platforms:
        if pid not in PLATFORM_DATA:
            continue
        pdata = PLATFORM_DATA[pid]
        # 平台偏好波动 ±8%
        rate = max(5, min(95, base_rate + random.randint(-8, 8)))
        platforms.append({
            "name": pdata["name"],
            "icon": pdata["icon"],
            "rate": rate,
            "color": ["#00f0ff", "#39ff14", "#b537f2", "#fff200", "#ff6b00", "#ff2e97", "#3b82f6", "#8b5cf6"][pid-1] if pid <= 8 else "#00f0ff"
        })
    
    result = {
        "aiSearch": {
            "totalQueries": len(task.platforms) * 10,
            "mentionRate": sum(p["rate"] for p in platforms) / len(platforms) if platforms else 0,
            "platforms": platforms
        },
        "geoEffect": {
            "exposureScore": random.randint(55, 80),
            "citationRate": random.randint(40, 70),
            "recommendationRate": random.randint(35, 65),
            "summary": f"品牌在 {len(platforms)} 个AI平台的平均提及率为 {sum(p['rate'] for p in platforms) / len(platforms):.1f}%"
        }
    }
    
    task.stages[1].status = "completed"
    task.stages[1].progress = 100
    return result


async def stage3_sentiment_analysis(task: DiagnosisTask, stage1_result: Dict) -> Dict[str, Any]:
    """
    阶段 3：舆情分析
    - 负面舆情词识别
    - 情感分析
    - 舆情健康度评估
    """
    task.stages[2].status = "running"
    task.stages[2].progress = 0
    
    await asyncio.sleep(0.5)
    
    positive = random.randint(120, 200)
    neutral = random.randint(180, 280)
    negative = random.randint(10, 30)
    complaints = random.randint(3, 12)
    total = positive + neutral + negative + complaints
    
    health_score = int((positive + neutral * 0.5) / total * 100)
    
    result = {
        "health": health_score,
        "breakdown": [
            {"label": "正面提及", "count": positive, "color": "#39ff14"},
            {"label": "中性提及", "count": neutral, "color": "#00f0ff"},
            {"label": "负面提及", "count": negative, "color": "#ff2e97"},
            {"label": "投诉相关", "count": complaints, "color": "#ff6b00"},
        ],
        "negativeKeywords": ["售后服务差", "价格偏高", "响应慢"][:random.randint(1, 3)],
        "riskLevel": "low" if health_score >= 80 else "medium" if health_score >= 60 else "high",
        "summary": f"舆情整体健康，正面提及占比 {positive/total*100:.1f}%，需关注 {negative} 条负面内容"
    }
    
    task.stages[2].status = "completed"
    task.stages[2].progress = 100
    return result


async def stage4_scoring_suggestions(task: DiagnosisTask, stage_results: Dict) -> Dict[str, Any]:
    """
    阶段 4：评分建议
    - AIVO 四维评分（等权重 25%）
    - 综合优化建议
    """
    task.stages[3].status = "running"
    task.stages[3].progress = 0
    
    await asyncio.sleep(0.5)
    
    # AIVO 四维评分
    ai_visibility = int(stage_results["stage2"]["aiSearch"]["mentionRate"])
    infrastructure = min(100, stage1_result["infraEval"]["officialSite"]["score"] + 
                        stage1_result["infraEval"]["selfMedia"]["totalCount"] * 2)
    advantage = random.randint(55, 80)
    sentiment = stage_results["stage3"]["health"]
    
    total_score = int((ai_visibility + infrastructure + advantage + sentiment) / 4)
    
    # 生成建议
    suggestions = []
    
    if stage1_result["infraEval"]["officialSite"]["score"] < 70:
        suggestions.append({
            "title": "优化官网SEO基础",
            "desc": "官网建设评分偏低，需优化TDK标签、页面加载速度、移动端适配",
            "priority": "high",
            "impact": f"基建完善度 +{70 - stage1_result['infraEval']['officialSite']['score']}"
        })
    
    if stage1_result["infraEval"]["selfMedia"]["totalCount"] < 15:
        suggestions.append({
            "title": "扩充自媒体矩阵覆盖",
            "desc": f"当前仅 {stage1_result['infraEval']['selfMedia']['totalCount']} 篇自媒体报道，建议增加知乎/小红书/B站内容",
            "priority": "high",
            "impact": "基建完善度 +15"
        })
    
    if ai_visibility < 60:
        suggestions.append({
            "title": "提升AI平台可见性",
            "desc": f"AI搜索平均提及率仅 {ai_visibility}%，需批量铺设问答内容争夺推荐位",
            "priority": "high",
            "impact": "AI可见性 +20"
        })
    
    if advantage < 70:
        suggestions.append({
            "title": "强化竞争优势",
            "desc": "与竞品相比，品牌差异化优势不明显，需突出核心卖点",
            "priority": "medium",
            "impact": "竞争优势 +12"
        })
    
    if sentiment < 80:
        suggestions.append({
            "title": "处理负面舆情",
            "desc": f"舆情健康度 {sentiment}，存在负面提及需及时响应",
            "priority": "medium",
            "impact": "舆情健康度 +10"
        })
    
    suggestions.append({
        "title": "建立竞品对比内容",
        "desc": "AI平台在对比类问题中倾向推荐竞品，需创建对比类内容",
        "priority": "low",
        "impact": "竞争优势 +8"
    })
    
    result = {
        "aivo": {
            "aiVisibility": ai_visibility,
            "infrastructure": min(100, infrastructure),
            "advantage": advantage,
            "sentiment": sentiment,
        },
        "totalScore": total_score,
        "grade": "优秀" if total_score >= 90 else "良好" if total_score >= 75 else "一般" if total_score >= 60 else "较差",
        "suggestions": suggestions[:6]
    }
    
    task.stages[3].status = "completed"
    task.stages[3].progress = 100
    return result


# ═══════════════════════════════════════════════════════════════
# API 路由
# ═══════════════════════════════════════════════════════════════

@router.post("/start")
async def start_diagnosis(request: DiagnosisRequest, background_tasks: BackgroundTasks):
    """
    启动品牌 GEO 诊断任务
    """
    task_id = str(uuid.uuid4())
    
    # 创建任务
    task = DiagnosisTask(
        taskId=task_id,
        brandName=request.brandName,
        productType=request.productType,
        website=request.website,
        platforms=request.platforms,
        stages=[
            DiagnosisStage(stage=1, name="基础调研", status="pending", progress=0),
            DiagnosisStage(stage=2, name="收录+可见性", status="pending", progress=0),
            DiagnosisStage(stage=3, name="舆情分析", status="pending", progress=0),
            DiagnosisStage(stage=4, name="评分建议", status="pending", progress=0),
        ],
        currentStage=0,
        result=None
    )
    
    diagnosis_tasks[task_id] = task
    
    # 后台执行 4 阶段流水线
    background_tasks.add_task(run_diagnosis_pipeline, task_id)
    
    return {"taskId": task_id, "message": "诊断任务已启动"}


async def run_diagnosis_pipeline(task_id: str):
    """
    执行 4 阶段诊断流水线
    """
    task = diagnosis_tasks[task_id]
    
    try:
        # 阶段 1：基础调研
        task.currentStage = 0
        stage1_result = await stage1_basic_research(task)
        
        # 阶段 2+3：并行执行（收录可见性 + 舆情分析）
        task.currentStage = 1
        stage2_task = asyncio.create_task(stage2_inclusion_visibility(task, stage1_result))
        task.currentStage = 2
        stage3_task = asyncio.create_task(stage3_sentiment_analysis(task, stage1_result))
        
        stage2_result, stage3_result = await asyncio.gather(stage2_task, stage3_task)
        
        # 阶段 4：评分建议
        task.currentStage = 3
        stage4_result = await stage4_scoring_suggestions(task, {
            "stage2": stage2_result,
            "stage3": stage3_result
        })
        
        # 合并最终结果
        task.result = {
            "totalScore": stage4_result["totalScore"],
            "grade": stage4_result["grade"],
            "aivo": stage4_result["aivo"],
            "platforms": stage2_result["aiSearch"]["platforms"],
            "infrastructure": [
                {
                    "icon": "⊡",
                    "label": "官网建设",
                    "detail": stage1_result["infraEval"]["officialSite"]["summary"],
                    "score": stage1_result["infraEval"]["officialSite"]["score"]
                },
                {
                    "icon": "⊕",
                    "label": "自媒体矩阵",
                    "detail": f"已覆盖 {len(stage1_result['infraEval']['selfMedia']['platformBreakdown'])} 平台",
                    "score": min(100, stage1_result["infraEval"]["selfMedia"]["totalCount"] * 5)
                },
                {
                    "icon": "▤",
                    "label": "权威媒体收录",
                    "detail": f"{stage1_result['infraEval']['authoritativeMedia']['totalCount']} 篇权威报道",
                    "score": min(100, stage1_result["infraEval"]["authoritativeMedia"]["totalCount"] * 10)
                },
            ],
            "sentiment": {
                "health": stage3_result["health"],
                "breakdown": stage3_result["breakdown"]
            },
            "competitors": [
                {
                    "name": task.brandName,
                    "geoScore": stage4_result["totalScore"],
                    "marketShare": 8,
                    "threatLevel": "-",
                    "aiMention": int(stage2_result["aiSearch"]["mentionRate"]),
                    "position": "本品牌",
                    "isBrand": True
                }
            ] + [
                {
                    "name": c["name"],
                    "geoScore": c["geoScore"],
                    "marketShare": c["marketShare"],
                    "threatLevel": c["threatLevel"],
                    "aiMention": random.randint(40, 80),
                    "position": c["description"],
                    "isBrand": False
                }
                for c in stage1_result["competitors"]["competitors"]
            ],
            "suggestions": stage4_result["suggestions"]
        }
        
    except Exception as e:
        print(f"Diagnosis pipeline error: {e}")
        task.result = {"error": str(e)}


@router.get("/status/{task_id}")
async def get_diagnosis_status(task_id: str):
    """
    获取诊断任务状态
    """
    if task_id not in diagnosis_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = diagnosis_tasks[task_id]
    
    return {
        "taskId": task.taskId,
        "brandName": task.brandName,
        "currentStage": task.currentStage,
        "stages": [
            {
                "stage": s.stage,
                "name": s.name,
                "status": s.status,
                "progress": s.progress
            }
            for s in task.stages
        ],
        "result": task.result,
        "completed": all(s.status == "completed" for s in task.stages)
    }


@router.get("/result/{task_id}")
async def get_diagnosis_result(task_id: str):
    """
    获取诊断结果
    """
    if task_id not in diagnosis_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = diagnosis_tasks[task_id]
    
    if not task.result:
        raise HTTPException(status_code=400, detail="诊断尚未完成")
    
    return task.result


@router.get("/platforms")
async def get_platforms():
    """
    获取支持的 AI 平台列表
    """
    return [
        {"code": code, "name": data["name"], "icon": data["icon"], "bias": data["bias"]}
        for code, data in PLATFORM_DATA.items()
    ]
