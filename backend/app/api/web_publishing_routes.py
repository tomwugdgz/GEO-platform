"""
GEO 网站与内容发布优化 API
基于 geo-web-publishing-main 规范，提供页面分析和优化建议
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
import subprocess
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

router = APIRouter(prefix="/web-publishing", tags=["网站优化"])

# GeoLook 引擎路径（复用）
GEOLOOK_DIR = Path(__file__).resolve().parent.parent.parent / "geolook"
PYTHON_ENV = r"C:\Users\wolf2\.workbuddy\binaries\python\envs\geolook\Scripts\python.exe"

# 网站规范文件路径
SITE_SPEC_PATH = Path(__file__).resolve().parent.parent.parent.parent / "download" / "geo-web-publishing-main" / "geo-web-publishing-main" / "references" / "site-spec.md"


class PageAnalysisRequest(BaseModel):
    url: str
    check_type: Optional[str] = "full"  # full | metadata | content | technical


class PageIssue(BaseModel):
    category: str
    severity: str  # critical | warning | info | suggestion
    title: str
    description: str
    recommendation: str
    affected_elements: Optional[List[str]] = None


class PageAnalysisResult(BaseModel):
    url: str
    status_code: int
    title: Optional[str]
    description: Optional[str]
    canonical: Optional[str]
    language: Optional[str]
    issues: List[PageIssue]
    score: float
    recommendations: List[str]


def analyze_metadata(soup: BeautifulSoup, url: str) -> List[PageIssue]:
    """分析页面元数据"""
    issues = []
    
    # 检查 title
    title = soup.find('title')
    if not title or not title.get_text().strip():
        issues.append(PageIssue(
            category="元数据",
            severity="critical",
            title="缺少页面标题",
            description="页面没有设置 <title> 标签，影响搜索收录和用户体验",
            recommendation="添加描述性的 <title> 标签，准确概括页面内容"
        ))
    elif len(title.get_text()) > 60:
        issues.append(PageIssue(
            category="元数据",
            severity="warning",
            title="页面标题过长",
            description=f"标题长度 {len(title.get_text())} 字符，超过推荐的 60 字符",
            recommendation="精简标题，保持在 60 字符以内"
        ))
    
    # 检查 meta description
    description = soup.find('meta', attrs={'name': 'description'})
    if not description or not description.get('content'):
        issues.append(PageIssue(
            category="元数据",
            severity="warning",
            title="缺少页面描述",
            description="没有设置 meta description，影响搜索结果展示",
            recommendation="添加 meta description，概括页面内容，控制在 150-160 字符"
        ))
    elif len(description.get('content', '')) > 160:
        issues.append(PageIssue(
            category="元数据",
            severity="info",
            title="页面描述较长",
            description=f"描述长度 {len(description.get('content', ''))} 字符，可能被截断",
            recommendation="精简描述，保持在 160 字符以内"
        ))
    
    # 检查 canonical
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if not canonical:
        issues.append(PageIssue(
            category="元数据",
            severity="suggestion",
            title="建议添加 canonical 标签",
            description="未设置 canonical 标签，可能导致重复内容问题",
            recommendation="添加 <link rel=\"canonical\"> 指向本页的正式 URL"
        ))
    else:
        canonical_url = canonical.get('href', '')
        if not canonical_url.startswith('http'):
            issues.append(PageIssue(
                category="元数据",
                severity="warning",
                title="canonical 使用相对 URL",
                description=f"canonical 使用了相对路径: {canonical_url}",
                recommendation="使用绝对 URL 作为 canonical"
            ))
    
    # 检查语言
    html = soup.find('html')
    if not html or not html.get('lang'):
        issues.append(PageIssue(
            category="元数据",
            severity="warning",
            title="缺少语言声明",
            description="HTML 标签没有 lang 属性，影响多语言识别",
            recommendation="添加 <html lang=\"zh-CN\"> 或对应语言"
        ))
    
    return issues


def analyze_content_structure(soup: BeautifulSoup) -> List[PageIssue]:
    """分析内容结构"""
    issues = []
    
    # 检查 H1
    h1s = soup.find_all('h1')
    if not h1s:
        issues.append(PageIssue(
            category="内容结构",
            severity="warning",
            title="缺少 H1 标题",
            description="页面没有使用 H1 标签，影响内容层次",
            recommendation="添加一个 H1 标签，清楚描述页面主题"
        ))
    elif len(h1s) > 1:
        issues.append(PageIssue(
            category="内容结构",
            severity="info",
            title="多个 H1 标题",
            description=f"页面有 {len(h1s)} 个 H1 标签，建议保持单一主标题",
            recommendation="保留一个主 H1，其他改为 H2 或更低级别"
        ))
    
    # 检查 H2 层次
    h2s = soup.find_all('h2')
    if len(h2s) < 2:
        issues.append(PageIssue(
            category="内容结构",
            severity="suggestion",
            title="内容层次较少",
            description=f"页面只有 {len(h2s)} 个 H2 标题，内容可能不够结构化",
            recommendation="使用 H2 划分内容段落，提升可读性"
        ))
    
    # 检查主内容区
    main = soup.find('main') or soup.find('article')
    if not main:
        issues.append(PageIssue(
            category="内容结构",
            severity="warning",
            title="缺少语义化主内容区",
            description="未使用 <main> 或 <article> 标签包裹主要内容",
            recommendation="使用语义化标签包裹主内容，提升可访问性"
        ))
    
    # 检查导航
    nav = soup.find('nav')
    if not nav:
        issues.append(PageIssue(
            category="内容结构",
            severity="suggestion",
            title="缺少导航标签",
            description="未使用 <nav> 标签，影响导航识别",
            recommendation="使用 <nav> 标签包裹导航链接"
        ))
    
    return issues


def analyze_technical(soup: BeautifulSoup, response: requests.Response) -> List[PageIssue]:
    """分析技术问题"""
    issues = []
    
    # 检查 HTTPS
    url = response.url
    if url.startswith('http://'):
        issues.append(PageIssue(
            category="技术",
            severity="critical",
            title="未使用 HTTPS",
            description="页面通过 HTTP 访问，存在安全风险",
            recommendation="配置 HTTPS，提升安全性和搜索信任度"
        ))
    
    # 检查 robots meta
    robots_meta = soup.find('meta', attrs={'name': 'robots'})
    if robots_meta:
        content = robots_meta.get('content', '').lower()
        if 'noindex' in content:
            issues.append(PageIssue(
                category="技术",
                severity="critical",
                title="页面被标记为 noindex",
                description="meta robots 包含 noindex，搜索引擎不会索引此页",
                recommendation="移除 noindex 或确认这是有意为之"
            ))
    
    # 检查 X-Robots-Tag
    x_robots = response.headers.get('X-Robots-Tag', '')
    if 'noindex' in x_robots.lower():
        issues.append(PageIssue(
            category="技术",
            severity="critical",
            title="HTTP 响应头标记为 noindex",
            description=f"X-Robots-Tag: {x_robots}，搜索引擎不会索引此页",
            recommendation="移除 X-Robots-Tag 中的 noindex 或确认这是有意为之"
        ))
    
    # 检查 viewport
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if not viewport:
        issues.append(PageIssue(
            category="技术",
            severity="warning",
            title="缺少 viewport 设置",
            description="未设置 viewport meta，移动端可能显示异常",
            recommendation="添加 <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        ))
    
    # 检查图片 alt
    images = soup.find_all('img')
    images_without_alt = [img for img in images if not img.get('alt')]
    if images_without_alt:
        issues.append(PageIssue(
            category="技术",
            severity="warning",
            title="图片缺少 alt 属性",
            description=f"{len(images_without_alt)} 张图片没有 alt 属性，影响可访问性和 SEO",
            recommendation="为所有图片添加描述性的 alt 属性",
            affected_elements=[str(img)[:100] for img in images_without_alt[:3]]
        ))
    
    return issues


def analyze_links(soup: BeautifulSoup) -> List[PageIssue]:
    """分析链接质量"""
    issues = []
    
    links = soup.find_all('a')
    internal_links = []
    external_links = []
    
    for link in links:
        href = link.get('href', '')
        if href.startswith('http'):
            external_links.append(link)
        elif href.startswith('/') or (href and not href.startswith('http')):
            internal_links.append(link)
    
    if len(internal_links) < 3:
        issues.append(PageIssue(
            category="链接",
            severity="suggestion",
            title="内部链接较少",
            description=f"页面只有 {len(internal_links)} 个内部链接",
            recommendation="增加相关内容的内部链接，提升网站结构"
        ))
    
    # 检查空链接
    empty_links = [link for link in links if not link.get('href') or link.get('href') == '#']
    if empty_links:
        issues.append(PageIssue(
            category="链接",
            severity="info",
            title="存在空链接",
            description=f"{len(empty_links)} 个链接没有有效 href",
            recommendation="为链接添加有效的目标地址"
        ))
    
    return issues


def calculate_score(issues: List[PageIssue]) -> float:
    """根据问题计算页面得分"""
    score = 100.0
    
    severity_weights = {
        'critical': -20,
        'warning': -10,
        'info': -3,
        'suggestion': -1
    }
    
    for issue in issues:
        score += severity_weights.get(issue.severity, 0)
    
    return max(0, min(100, score))


def generate_recommendations(issues: List[PageIssue]) -> List[str]:
    """生成优化建议列表"""
    recommendations = []
    
    # 按优先级排序
    priority_order = {'critical': 0, 'warning': 1, 'info': 2, 'suggestion': 3}
    sorted_issues = sorted(issues, key=lambda x: priority_order.get(x.severity, 4))
    
    for issue in sorted_issues[:10]:  # 最多 10 条建议
        recommendations.append(f"[{issue.severity.upper()}] {issue.title}: {issue.recommendation}")
    
    return recommendations


@router.post("/analyze", response_model=PageAnalysisResult)
async def analyze_page(request: PageAnalysisRequest):
    """分析页面并生成优化建议"""
    url = request.url
    
    try:
        # 抓取页面
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"页面返回状态码 {response.status_code}")
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 收集所有问题
        all_issues = []
        
        if request.check_type in ['full', 'metadata']:
            all_issues.extend(analyze_metadata(soup, url))
        
        if request.check_type in ['full', 'content']:
            all_issues.extend(analyze_content_structure(soup))
        
        if request.check_type in ['full', 'technical']:
            all_issues.extend(analyze_technical(soup, response))
            all_issues.extend(analyze_links(soup))
        
        # 计算得分和建议
        score = calculate_score(all_issues)
        recommendations = generate_recommendations(all_issues)
        
        # 提取基本信息
        title = soup.find('title').get_text() if soup.find('title') else None
        description = soup.find('meta', attrs={'name': 'description'})
        description = description.get('content') if description else None
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        canonical = canonical.get('href') if canonical else None
        html = soup.find('html')
        language = html.get('lang') if html else None
        
        return PageAnalysisResult(
            url=url,
            status_code=response.status_code,
            title=title,
            description=description,
            canonical=canonical,
            language=language,
            issues=all_issues,
            score=score,
            recommendations=recommendations
        )
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="页面加载超时")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"无法访问页面: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/spec")
async def get_site_spec():
    """获取网站规范内容"""
    if not SITE_SPEC_PATH.exists():
        raise HTTPException(status_code=404, detail="规范文件不存在")
    
    content = SITE_SPEC_PATH.read_text(encoding='utf-8')
    return {
        "spec": content,
        "path": str(SITE_SPEC_PATH)
    }


@router.get("/checklist")
async def get_optimization_checklist():
    """获取优化检查清单"""
    return {
        "categories": [
            {
                "name": "元数据",
                "items": [
                    "页面标题（<title>）",
                    "Meta 描述",
                    "Canonical 标签",
                    "语言声明（lang）",
                    "Viewport 设置"
                ]
            },
            {
                "name": "内容结构",
                "items": [
                    "H1 主标题",
                    "H2 内容分段",
                    "语义化标签（main/article/nav）",
                    "内容层次清晰"
                ]
            },
            {
                "name": "技术",
                "items": [
                    "HTTPS",
                    "robots 指令",
                    "图片 alt 属性",
                    "链接有效性"
                ]
            },
            {
                "name": "链接",
                "items": [
                    "内部链接数量",
                    "外部链接质量",
                    "链接文案描述性"
                ]
            }
        ]
    }
