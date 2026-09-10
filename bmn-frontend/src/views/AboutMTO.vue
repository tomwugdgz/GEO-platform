<template>
  <div class="mto-about">
    <!-- ═══ Hero ═══ -->
    <section class="mto-hero">
      <div class="mto-hero-badge">MACHINE TRUST OPTIMIZATION</div>
      <h1>MTO · 机器信任优化</h1>
      <p class="mto-hero-sub">
        把品牌主张治理成<strong>机器可验证的证据链</strong>，
        让 AI 智能体在自主交易时能核验并信任你。
      </p>
      <div class="mto-hero-meta">
        <span class="mto-tag">开源共建</span>
        <span class="mto-tag">递进双层：GEO + MTO</span>
        <span class="mto-tag mto-tag-warn">MTO 仍属理论推演阶段</span>
      </div>
    </section>

    <!-- ═══ GEO vs MTO ═══ -->
    <section class="mto-block">
      <h2>▹ GEO 与 MTO 的区别</h2>
      <p class="mto-lead">
        两者是 AI 时代营销逻辑的<strong>不同阶段</strong>，不是替代关系。
      </p>

      <div class="mto-compare">
        <div class="mto-col mto-col-geo">
          <div class="mto-col-head">GEO</div>
          <div class="mto-col-full">Generative Engine Optimization</div>
          <div class="mto-col-cn">生成式引擎优化</div>
          <ul>
            <li>解决「<strong>被 AI 看见</strong>」</li>
            <li>当用户在豆包、DeepSeek 提问时</li>
            <li>让品牌被正确理解、引用、推荐</li>
            <li>终点：进入 AI 的<strong>候选答案池</strong></li>
          </ul>
          <div class="mto-col-foot">让 AI <strong>愿意推荐</strong>你 · 拿到入场资格</div>
          <div class="mto-col-status mto-ok">当下企业正在布局的实操方向</div>
        </div>

        <div class="mto-col mto-col-mto">
          <div class="mto-col-head">MTO</div>
          <div class="mto-col-full">Machine Trust Optimization</div>
          <div class="mto-col-cn">机器信任优化</div>
          <ul>
            <li>解决「<strong>被机器信任</strong>」</li>
            <li>当 AI 智能体普及、机器自主购物时</li>
            <li>让机器验证并信任你的产品证据链</li>
            <li>终点：机器<strong>直接选购</strong></li>
          </ul>
          <div class="mto-col-foot">让机器<strong>敢直接买</strong>你 · 实现自主交易</div>
          <div class="mto-col-status mto-warn">仍处理论推演阶段，尚未全面落地</div>
        </div>
      </div>
    </section>

    <!-- ═══ 递进双层 ═══ -->
    <section class="mto-block">
      <h2>▹ 递进双层架构</h2>
      <p class="mto-lead">
        GEO 是地基，MTO 是在地基上盖的房子。
        <strong>跳过 GEO 做 MTO 不成立，只做 GEO 会停在半路。</strong>
      </p>

      <div class="mto-layers">
        <div class="mto-layer mto-layer-mto">
          <div class="mto-layer-name">MTO 层 · 被机器信任</div>
          <div class="mto-layer-items">证据链可核验 · 信任可量化 · A2A 可调用</div>
          <div class="mto-layer-goal">目标：机器自主交易时选择你</div>
        </div>
        <div class="mto-arrow">▲ 依赖</div>
        <div class="mto-layer mto-layer-geo">
          <div class="mto-layer-name">GEO 层 · 被 AI 看见</div>
          <div class="mto-layer-items">被正确理解 · 被引用 · 被推荐</div>
          <div class="mto-layer-goal">目标：进入 AI 的候选答案池</div>
        </div>
        <div class="mto-arrow">▲ 依赖</div>
        <div class="mto-layer mto-layer-asset">
          <div class="mto-layer-name">资产层 · 品牌知识底座</div>
          <div class="mto-layer-items">品牌事实 · 产品事实 · 结构化内容资产</div>
          <div class="mto-layer-goal">一次治理，两层受益</div>
        </div>
      </div>
    </section>

    <!-- ═══ 四层技术构成 ═══ -->
    <section class="mto-block">
      <h2>▹ MTO 的四层技术构成</h2>
      <div class="mto-grid">
        <div v-for="(p, i) in pillars" :key="i" class="mto-card">
          <div class="mto-card-idx">{{ String(i + 1).padStart(2, '0') }}</div>
          <div class="mto-card-title">{{ p.title }}</div>
          <div class="mto-card-en">{{ p.en }}</div>
          <p class="mto-card-desc">{{ p.desc }}</p>
        </div>
      </div>
    </section>

    <!-- ═══ 本平台差异 ═══ -->
    <section class="mto-block">
      <h2>▹ 本平台多了什么</h2>
      <p class="mto-lead">
        差异不在 GEO 做得更好，而在于<strong>多了两层</strong>。
      </p>
      <div class="mto-diff">
        <div v-for="(d, i) in diffs" :key="i" class="mto-diff-row" :class="{ 'is-extra': d.extra }">
          <span class="mto-diff-name">{{ d.name }}</span>
          <span class="mto-diff-val">{{ d.pure }}</span>
          <span class="mto-diff-val mto-diff-mine">{{ d.mine }}</span>
        </div>
        <div class="mto-diff-head">
          <span class="mto-diff-name"></span>
          <span class="mto-diff-val">纯 GEO 工具</span>
          <span class="mto-diff-val mto-diff-mine">MTO 平台</span>
        </div>
      </div>
      <p class="mto-quote">
        纯 GEO 工具回答「AI 提到我了吗」；<br />
        MTO 平台在回答这个之后，继续回答<strong>「机器凭什么信我」</strong>。
      </p>
    </section>

    <!-- ═══ 成熟度 ═══ -->
    <section class="mto-block">
      <h2>▹ 成熟度分级</h2>
      <p class="mto-lead">主动声明边界，避免概念炒作。</p>
      <div class="mto-maturity">
        <div v-for="(m, i) in maturity" :key="i" class="mto-mat-row">
          <span class="mto-mat-dot" :class="m.dot"></span>
          <span class="mto-mat-name">{{ m.name }}</span>
          <span class="mto-mat-level" :class="m.dot">{{ m.level }}</span>
          <span class="mto-mat-note">{{ m.note }}</span>
        </div>
      </div>
      <div class="mto-alert">
        ⚠ 请勿将本平台的 MTO 能力用于对外商业承诺。现阶段它是一块面向未来的实验田。
      </div>
    </section>

    <!-- ═══ 开源共建 ═══ -->
    <section class="mto-block">
      <h2>▹ 开源共建 MTO</h2>
      <p class="mto-lead">
        MTO 要成立，前提是机器能<strong>跨组织地验证证据</strong>。
        一个封闭系统里的「信任分」没有意义 —— 机器凭什么相信一个它无法审计的黑盒？
      </p>
      <p class="mto-lead">
        所以底层约定必须开放、可审计、可互操作。<strong>这不是姿态，是技术前提。</strong>
      </p>

      <div class="mto-co">
        <div v-for="(c, i) in coBuild" :key="i" class="mto-co-item">
          <div class="mto-co-goal">{{ c.goal }}</div>
          <div class="mto-co-state">{{ c.state }}</div>
          <div class="mto-co-need">{{ c.need }}</div>
        </div>
      </div>

      <div class="mto-ways">
        <div v-for="(w, i) in ways" :key="i" class="mto-way">{{ w }}</div>
      </div>

      <p class="mto-quote">
        我们更欢迎否定意见。<br />
        一个仍在理论推演阶段的框架，<strong>最大的风险不是被批评，而是被附和</strong>。
      </p>
    </section>

    <!-- ═══ 声明 ═══ -->
    <section class="mto-block mto-legal">
      <h2>▹ 声明</h2>
      <p>
        本项目为<strong>个人非商业</strong>学习研究项目，与上游
        <a href="https://github.com/aigclink/geolook" target="_blank" rel="noopener noreferrer">GeoLook</a>
        及其作者无任何隶属、合作、赞助或背书关系。
      </p>
      <p>
        GEO 引擎内核源自开源项目 GeoLook（MIT ·
        Copyright (c) 2026 GeoLook contributors），已完整保留其许可与版权声明。
      </p>
      <p>
        如认为本作品侵犯您的权益，请联系
        <a href="mailto:duckwolf@qq.com">duckwolf@qq.com</a>，
        <strong>核实后立即删除，不作抗辩</strong>。
      </p>
    </section>
  </div>
</template>

<script setup>
// 「关于 MTO」为纯静态说明页，不依赖后端接口。
// 概念全文见仓库 docs/MTO平台定义说明.md
const pillars = [
  {
    title: '证据链',
    en: 'Evidence Chain',
    desc: '机器不信任主张，只信任证据。「适合敏感肌」本身没有意义，有意义的是它能沿一条可追溯的链路走到原始凭据：成分表、检测报告、认证编号、临床数据。',
  },
  {
    title: '机器可读性',
    en: 'Machine Readability',
    desc: '证据存在不等于机器能读到。需要结构化数据、稳定的数据接口、机器可读的知识文件，以及明确的数据许可 —— 机器得知道「我能不能用」。',
  },
  {
    title: '信任量化',
    en: 'Trust Quantification',
    desc: '机器需要一个可比较的量。把无形的信任拆成证据完整度、可信度、主张一致性、可验证性、时效性等可计算指标。这是与 GEO 最大的分野。',
  },
  {
    title: '协议与执行',
    en: 'A2A & Execution',
    desc: '前三层让机器愿意信任你，这一层让机器能够与你完成交易：A2A 机器间协议、机器身份与授权、标准化交易接口、可审计决策日志。',
  },
]

const diffs = [
  { name: 'AI 可见性诊断', pure: '✅', mine: '✅ 内置' },
  { name: '工单化闭环与验收', pure: '✅', mine: '✅' },
  { name: 'AI 智能体编排', pure: '❌', mine: '✅ 多智能体协同', extra: true },
  { name: 'A2A 机器间协议', pure: '❌', mine: '✅ 核验能力可被调用', extra: true },
  { name: '证据链建模与信任量化', pure: '❌', mine: '✅ MTO 核心', extra: true },
  { name: '机器调用审计', pure: '❌', mine: '✅ 记录机器为何选你', extra: true },
]

const maturity = [
  { name: 'GEO 层能力', level: '可用', dot: 'g', note: '站点审计、答案采样、缺口诊断、工单闭环、验收均可实际运行' },
  { name: 'AI 智能体层', level: '可用但依赖配置', dot: 'y', note: '需自行配置各模型 API Key，未配置的引擎降级为人工采样' },
  { name: 'A2A 协议层', level: '接口就绪，生态未成熟', dot: 'y', note: '协议已实现，但外部尚无规模化支持 A2A 交易的商业生态' },
  { name: 'MTO 方法论', level: '理论推演阶段', dot: 'r', note: '机器自主交易尚未大规模发生，本框架是推演与工程化尝试' },
  { name: '信任量化指标', level: '实验性', dot: 'r', note: '未经过真实交易场景验证，不构成任何决策依据' },
]

const coBuild = [
  { goal: '证据链的数据模型', state: '初版设计', need: '不同行业的证据类型与溯源需求' },
  { goal: '信任量化指标', state: '实验性', need: '真实的验证场景与反例，用来证伪' },
  { goal: 'A2A 核验接口', state: '接口就绪', need: '真实的机器调用方接入测试' },
  { goal: '机器可读知识文件约定', state: '已实践', need: '更多实现方参与，形成事实标准' },
  { goal: '行业证据模板', state: '待补充', need: '快消 / 美妆 / 3C / 医疗健康等领域知识' },
]

const ways = [
  '🐛 提 Issue 挑战框架 —— 尤其欢迎「这个指标算不出来」的具体反例',
  '🔧 提 PR 补充行业证据模型 —— 一条真实证据链胜过十页理论',
  '📄 参与规范讨论 —— 证据链格式、信任指标口径、A2A 接口约定',
  '🔬 做证伪实验 —— 试着让机器完成一次真实核验，把失败的地方告诉我们',
]
</script>

<style scoped>
.mto-about {
  padding: 24px 28px 48px;
  max-width: 1180px;
}

/* ═══ Hero ═══ */
.mto-hero {
  padding: 28px 26px;
  margin-bottom: 24px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-left: 4px solid var(--px-neon-orange);
}

.mto-hero-badge {
  display: inline-block;
  padding: 3px 10px;
  margin-bottom: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--px-neon-orange);
  border: 1px solid rgba(255, 107, 0, 0.45);
}

.mto-hero h1 {
  margin: 0 0 12px;
  font-size: 28px;
  color: var(--px-text-primary);
}

.mto-hero-sub {
  margin: 0 0 16px;
  font-size: 15px;
  line-height: 1.7;
  color: var(--px-text-dim);
  max-width: 720px;
}

.mto-hero-sub strong {
  color: var(--px-neon-cyan);
}

.mto-hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mto-tag {
  padding: 4px 10px;
  font-size: 11px;
  color: var(--px-text-dim);
  background: var(--px-bg-deep);
  border: 1px solid var(--px-border);
}

.mto-tag-warn {
  color: var(--px-neon-yellow);
  border-color: rgba(255, 242, 0, 0.4);
}

/* ═══ Block ═══ */
.mto-block {
  margin-bottom: 26px;
  padding: 22px 24px 24px;
  background: var(--px-bg-panel);
  border: 1px solid var(--px-border);
}

.mto-block h2 {
  margin: 0 0 14px;
  font-size: 17px;
  color: var(--px-text-primary);
  letter-spacing: 1px;
}

.mto-lead {
  margin: 0 0 16px;
  font-size: 13px;
  line-height: 1.75;
  color: var(--px-text-dim);
  max-width: 820px;
}

.mto-lead strong {
  color: var(--px-text-primary);
}

/* ═══ 对比 ═══ */
.mto-compare {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.mto-col {
  padding: 18px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
}

.mto-col-geo {
  border-top: 3px solid var(--px-neon-cyan);
}

.mto-col-mto {
  border-top: 3px solid var(--px-neon-orange);
}

.mto-col-head {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--px-text-primary);
}

.mto-col-full {
  margin-top: 2px;
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--px-text-muted);
}

.mto-col-cn {
  margin: 6px 0 12px;
  font-size: 13px;
  color: var(--px-text-dim);
}

.mto-col ul {
  margin: 0 0 14px;
  padding-left: 18px;
}

.mto-col li {
  margin-bottom: 6px;
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--px-text-dim);
}

.mto-col li strong {
  color: var(--px-text-primary);
}

.mto-col-foot {
  padding-top: 12px;
  border-top: 1px dashed var(--px-border);
  font-size: 13px;
  color: var(--px-text-primary);
}

.mto-col-foot strong {
  color: var(--px-neon-yellow);
}

.mto-col-status {
  margin-top: 10px;
  padding: 5px 9px;
  font-size: 11px;
  line-height: 1.5;
}

.mto-ok {
  color: var(--px-neon-green);
  background: rgba(57, 255, 20, 0.08);
  border: 1px solid rgba(57, 255, 20, 0.25);
}

.mto-warn {
  color: var(--px-neon-yellow);
  background: rgba(255, 242, 0, 0.07);
  border: 1px solid rgba(255, 242, 0, 0.25);
}

/* ═══ 层级图 ═══ */
.mto-layers {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.mto-layer {
  padding: 16px 18px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
}

.mto-layer-mto {
  border-left: 4px solid var(--px-neon-orange);
}

.mto-layer-geo {
  border-left: 4px solid var(--px-neon-cyan);
}

.mto-layer-asset {
  border-left: 4px solid var(--px-neon-purple);
}

.mto-layer-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--px-text-primary);
}

.mto-layer-items {
  margin-top: 6px;
  font-size: 12px;
  color: var(--px-text-dim);
}

.mto-layer-goal {
  margin-top: 4px;
  font-size: 11px;
  color: var(--px-text-muted);
}

.mto-arrow {
  padding: 4px 0 4px 22px;
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--px-text-muted);
}

/* ═══ 四层卡片 ═══ */
.mto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.mto-card {
  padding: 16px 16px 18px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-top: 2px solid var(--px-neon-purple);
}

.mto-card-idx {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--px-neon-purple);
  letter-spacing: 2px;
}

.mto-card-title {
  margin-top: 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--px-text-primary);
}

.mto-card-en {
  margin-top: 2px;
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--px-text-muted);
}

.mto-card-desc {
  margin: 10px 0 0;
  font-size: 12px;
  line-height: 1.75;
  color: var(--px-text-dim);
}

/* ═══ 差异表 ═══ */
.mto-diff {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--px-border);
  border: 1px solid var(--px-border);
}

.mto-diff-row,
.mto-diff-head {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 1fr;
  gap: 1px;
  background: var(--px-bg-card);
  padding: 11px 14px;
  align-items: center;
}

.mto-diff-head {
  background: var(--px-bg-deep);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--px-text-muted);
}

.mto-diff-row.is-extra {
  background: rgba(255, 107, 0, 0.06);
}

.mto-diff-name {
  font-size: 12.5px;
  color: var(--px-text-primary);
}

.mto-diff-val {
  font-size: 12px;
  color: var(--px-text-muted);
}

.mto-diff-mine {
  color: var(--px-neon-green);
}

.mto-quote {
  margin: 18px 0 0;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.85;
  color: var(--px-text-dim);
  background: var(--px-bg-deep);
  border-left: 3px solid var(--px-neon-cyan);
}

.mto-quote strong {
  color: var(--px-neon-cyan);
}

/* ═══ 成熟度 ═══ */
.mto-maturity {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--px-border);
  border: 1px solid var(--px-border);
}

.mto-mat-row {
  display: grid;
  grid-template-columns: 16px 1.1fr 1.2fr 2.2fr;
  gap: 12px;
  align-items: center;
  padding: 11px 14px;
  background: var(--px-bg-card);
}

.mto-mat-dot {
  width: 8px;
  height: 8px;
}

.mto-mat-dot.g {
  background: var(--px-neon-green);
}

.mto-mat-dot.y {
  background: var(--px-neon-yellow);
}

.mto-mat-dot.r {
  background: var(--px-neon-pink);
}

.mto-mat-name {
  font-size: 12.5px;
  color: var(--px-text-primary);
}

.mto-mat-level {
  font-size: 11.5px;
}

.mto-mat-level.g {
  color: var(--px-neon-green);
}

.mto-mat-level.y {
  color: var(--px-neon-yellow);
}

.mto-mat-level.r {
  color: var(--px-neon-pink);
}

.mto-mat-note {
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--px-text-muted);
}

.mto-alert {
  margin-top: 14px;
  padding: 12px 14px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--px-neon-yellow);
  background: rgba(255, 242, 0, 0.06);
  border: 1px solid rgba(255, 242, 0, 0.28);
}

/* ═══ 共建 ═══ */
.mto-co {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.mto-co-item {
  padding: 14px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-left: 3px solid var(--px-neon-green);
}

.mto-co-goal {
  font-size: 13px;
  font-weight: 700;
  color: var(--px-text-primary);
}

.mto-co-state {
  margin-top: 6px;
  font-size: 11px;
  color: var(--px-neon-yellow);
}

.mto-co-need {
  margin-top: 6px;
  font-size: 11.5px;
  line-height: 1.65;
  color: var(--px-text-dim);
}

.mto-ways {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.mto-way {
  padding: 10px 14px;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--px-text-dim);
  background: var(--px-bg-deep);
  border: 1px solid var(--px-border);
}

/* ═══ 声明 ═══ */
.mto-legal {
  border-left: 3px solid var(--px-text-muted);
}

.mto-legal p {
  margin: 0 0 10px;
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--px-text-dim);
}

.mto-legal p:last-child {
  margin-bottom: 0;
}

.mto-legal strong {
  color: var(--px-text-primary);
}

.mto-legal a {
  color: var(--px-neon-cyan);
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
