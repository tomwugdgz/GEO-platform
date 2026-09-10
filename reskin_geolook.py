"""
把新增的 GeoLook 页面配色统一到应用既有的深色像素主题。

原因：应用全局是深空黑主题（body 文字为浅色），而新页面沿用了浅色卡片配色，
导致标题（继承浅色文字）压在浅底上不可读。这里只在 <style> 块内做等价替换，
不动模板与脚本。

用法：python reskin_geolook.py
"""
from pathlib import Path

VIEWS = Path(__file__).parent / "bmn-frontend" / "src" / "views"
GEO_VIEWS = VIEWS / "geo"

FILES = [
    "GeoLookSiteAudit.vue",
    "GeoLookPlan.vue",
    "GeoLookCompetitors.vue",
    "GeoLookChannels.vue",
    "GeoLookGaps.vue",
    "GeoLookVerify.vue",
    "GeoLookSettings.vue",
]

# 这些页面在子目录下（事实库编辑器等）
SUB_FILES = [
    "KnowledgeEditor.vue",
]

# 文本替换表：浅底 → 深色面板；深色文字 → 浅色文字（应用主题为深色）
REPLACEMENTS = [
    # 背景
    ("background: #fff;", "background: var(--px-bg-card);"),
    ("background: #FFF;", "background: var(--px-bg-card);"),
    ("background: white;", "background: var(--px-bg-card);"),
    ("background: #f5f5f5;", "background: var(--px-bg-elev);"),
    ("background: #FAFAFA;", "background: var(--px-bg-panel);"),
    ("background: #F5F5F7;", "background: var(--px-bg-panel);"),
    ("background: #f9f9f9;", "background: var(--px-bg-panel);"),
    ("background: #E3F2FD;", "background: rgba(0, 240, 255, 0.12);"),
    ("background: #EDE7F6;", "background: rgba(181, 55, 242, 0.14);"),
    ("background: #F3E5F5;", "background: rgba(181, 55, 242, 0.14);"),
    ("background: #FFF3E0;", "background: rgba(255, 107, 0, 0.14);"),
    ("background: #FFEBEE;", "background: rgba(255, 46, 151, 0.14);"),
    ("background: #E8F5E9;", "background: rgba(57, 255, 20, 0.12);"),
    ("background: #F0F0F0;", "background: var(--px-bg-elev);"),
    ("background: #e0e0e0;", "background: rgba(255, 255, 255, 0.08);"),
    ("background: #eee;", "background: var(--px-bg-elev);"),
    ("background: #f0f0f0;", "background: var(--px-bg-elev);"),
    # 文字
    ("color: #333;", "color: var(--px-text-primary);"),
    ("color: #1D1D1F;", "color: var(--px-text-primary);"),
    ("color: #202124;", "color: var(--px-text-primary);"),
    ("color: #666;", "color: var(--px-text-dim);"),
    ("color: #555;", "color: var(--px-text-dim);"),
    ("color: #888;", "color: var(--px-text-muted);"),
    ("color: #777;", "color: var(--px-text-muted);"),
    ("color: #999;", "color: var(--px-text-muted);"),
    ("color: #aaa;", "color: var(--px-text-muted);"),
    # 边框
    ("1px solid #e5e5e5", "1px solid var(--px-border)"),
    ("1px solid #E5E5E5", "1px solid var(--px-border)"),
    ("1px solid #ddd", "1px solid var(--px-border)"),
    ("1px solid #DDD", "1px solid var(--px-border)"),
    ("1px solid #eee", "1px solid var(--px-border)"),
    ("1px solid #EEE", "1px solid var(--px-border)"),
    ("1px solid #e0e0e0", "1px solid var(--px-border)"),
    ("1px dashed #e0e0e0", "1px dashed var(--px-border)"),
    ("border-top: 1px solid #f0f0f0;", "border-top: 1px solid var(--px-border);"),
    ("#e0e0e0", "var(--px-border)"),
    ("#f0f0f0", "var(--px-border)"),
]


def reskin(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    start = text.find("<style")
    if start == -1:
        return 0, 0
    head, style = text[:start], text[start:]

    changed = 0
    for old, new in REPLACEMENTS:
        n = style.count(old)
        if n:
            style = style.replace(old, new)
            changed += n

    path.write_text(head + style, encoding="utf-8")
    return changed, len(style)


def main():
    total = 0
    targets = [(VIEWS / n) for n in FILES] + [(GEO_VIEWS / n) for n in SUB_FILES]
    for p in targets:
        if not p.exists():
            print(f"跳过（不存在）：{p.name}")
            continue
        changed, _ = reskin(p)
        total += changed
        print(f"{p.name:<24} 替换 {changed} 处")
    print(f"\n合计替换 {total} 处")


if __name__ == "__main__":
    main()
