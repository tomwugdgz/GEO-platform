<template>
  <div class="px-fade-in">
    <div class="px-page-title">
      <div class="px-page-title-icon">⊞</div>
      <h1>全流程总览</h1>
      <span class="sub">SOP WORKFLOW // 8 STEPS</span>
    </div>

    <!-- 工作流时间线 -->
    <div class="px-timeline">
      <div v-for="(step, idx) in steps" :key="step.id" class="px-timeline-item" :class="'px-step-' + step.status">
        <div class="px-tl-connector" v-if="idx > 0"></div>
        <div class="px-tl-node">
          <div class="px-tl-icon">{{ step.icon }}</div>
          <div class="px-tl-num">{{ String(step.id).padStart(2, '0') }}</div>
        </div>
        <div class="px-tl-content">
          <div class="px-tl-header">
            <div class="px-tl-title">{{ step.name }}</div>
            <span :class="'px-tag px-tag-' + step.tagType">{{ step.tag }}</span>
          </div>
          <div class="px-tl-desc">{{ step.desc }}</div>
          <div class="px-tl-meta">
            <span class="px-tl-time" v-if="step.time">⏱ {{ step.time }}</span>
            <span class="px-tl-count" v-if="step.count">◈ {{ step.count }}</span>
          </div>
          <div class="px-tl-progress" v-if="step.progress !== undefined">
            <div class="px-progress" style="height:4px">
              <div class="px-progress-bar" :style="{ width: step.progress + '%' }"></div>
            </div>
            <span class="px-tl-pct">{{ step.progress }}%</span>
          </div>
          <div class="px-tl-actions" v-if="step.actions">
            <button v-for="act in step.actions" :key="act" class="px-btn px-btn-ghost">{{ act }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const steps = ref([
  {
    id: 1, name: '提供资料', icon: '⊡', status: 'done', tag: '已完成', tagType: 'success',
    desc: '品牌基础信息录入：公司名称、行业、核心产品、目标客群',
    time: '2min', count: '12项字段', progress: 100
  },
  {
    id: 2, name: '蒸馏主词', icon: '◇', status: 'done', tag: '已完成', tagType: 'success',
    desc: 'AI 扩展关联问题：训练主词 → 目标转化词 → 蒸馏问题列表',
    time: '5min', count: '8个问题', progress: 100
  },
  {
    id: 3, name: '自媒体授权', icon: '⊕', status: 'active', tag: '进行中', tagType: '',
    desc: '连接自媒体平台：微信公众号、知乎、小红书、头条号等12个渠道',
    time: '10min', count: '8/12已连接', progress: 67,
    actions: ['去授权']
  },
  {
    id: 4, name: '写作任务', icon: '⎔', status: 'pending', tag: '待启动', tagType: 'warn',
    desc: 'AI 批量生成 SEO 优化内容：基于蒸馏词创作问答对',
    actions: ['配置任务']
  },
  {
    id: 5, name: '分发任务', icon: '⇗', status: 'pending', tag: '待启动', tagType: 'warn',
    desc: '多平台发布配置：选择渠道、定时发布、内容适配',
    actions: ['创建分发']
  },
  {
    id: 6, name: '本地客户端发布', icon: '▣', status: 'pending', tag: '待启动', tagType: 'warn',
    desc: '通过本地客户端执行实际发布动作',
    actions: ['查看客户端']
  },
  {
    id: 7, name: '系统自动训练', icon: '◉', status: 'pending', tag: '待启动', tagType: 'warn',
    desc: 'AI 模型持续优化：监测出镜率、调整策略',
    actions: ['启动训练']
  },
  {
    id: 8, name: '数据报表', icon: '▤', status: 'pending', tag: '待启动', tagType: 'warn',
    desc: '实时监测各 AI 平台出镜率、引用率、推荐率',
    actions: ['查看报表']
  }
])
</script>

<style scoped>
.px-timeline {
  position: relative;
  padding-left: 40px;
}

.px-timeline-item {
  position: relative;
  padding-bottom: 32px;
}

.px-tl-connector {
  position: absolute;
  left: 20px;
  top: -32px;
  width: 2px;
  height: 32px;
  background: linear-gradient(180deg, rgba(0, 240, 255, 0.3), rgba(0, 240, 255, 0.1));
}

.px-tl-node {
  position: absolute;
  left: -40px;
  top: 0;
  width: 40px;
  height: 40px;
  background: var(--px-bg-card);
  border: 2px solid var(--px-border);
  display: flex;
  align-items: center;
  justify-content: center;
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
}

.px-step-done .px-tl-node {
  border-color: var(--px-neon-green);
  box-shadow: 0 0 12px rgba(57, 255, 20, 0.3);
}

.px-step-active .px-tl-node {
  border-color: var(--px-neon-cyan);
  box-shadow: 0 0 16px rgba(0, 240, 255, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.px-tl-icon {
  font-size: 18px;
  color: var(--px-neon-cyan);
}

.px-step-done .px-tl-icon {
  color: var(--px-neon-green);
}

.px-tl-num {
  position: absolute;
  bottom: -2px;
  right: 2px;
  font-family: 'VT323', monospace;
  font-size: 10px;
  color: var(--px-text-muted);
}

.px-tl-content {
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  padding: 16px;
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}

.px-step-active .px-tl-content {
  border-color: var(--px-border-bright);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.1);
}

.px-tl-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.px-tl-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--px-text-primary);
  letter-spacing: 1px;
}

.px-tl-desc {
  font-size: 11px;
  color: var(--px-text-dim);
  line-height: 1.6;
  margin-bottom: 12px;
}

.px-tl-meta {
  display: flex;
  gap: 16px;
  font-size: 10px;
  color: var(--px-text-muted);
  margin-bottom: 8px;
}

.px-tl-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.px-tl-pct {
  font-family: 'VT323', monospace;
  font-size: 14px;
  color: var(--px-neon-cyan);
}

.px-tl-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
