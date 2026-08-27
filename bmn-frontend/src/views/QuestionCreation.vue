<template>
  <div class="cyber-page">
    <h1 class="cyber-title">❓ 问题创作</h1>
    <p class="cyber-subtitle">基于蒸馏关键词，批量生成AI搜索问答对</p>

    <!-- 生成面板 -->
    <div class="cyber-card cyber-mb-24">
      <div class="cyber-flex-between cyber-mb-16">
        <h3>生成问答</h3>
        <div class="cyber-flex">
          <select v-model="selectedKeywordId" class="cyber-selector">
            <option value="">选择蒸馏词</option>
            <option v-for="kw in keywords" :key="kw.id" :value="kw.id">
              {{ kw.training_keyword }}
            </option>
          </select>
          <input 
            v-model="questionCount" 
            type="number" 
            class="cyber-input" 
            style="width: 100px;"
            min="1"
            max="20"
            placeholder="数量"
          />
        </div>
      </div>
      
      <div class="cyber-grid-2">
        <div>
          <label class="cyber-text-secondary cyber-mb-8">问题类型</label>
          <select v-model="questionType" class="cyber-input">
            <option value="how">怎么做（How-to）</option>
            <option value="what">是什么（What）</option>
            <option value="why">为什么（Why）</option>
            <option value="compare">对比评测（Compare）</option>
            <option value="recommend">推荐（Recommend）</option>
          </select>
        </div>
        <div>
          <label class="cyber-text-secondary cyber-mb-8">回答风格</label>
          <select v-model="answerStyle" class="cyber-input">
            <option value="professional">专业严谨</option>
            <option value="friendly">友好亲切</option>
            <option value="concise">简洁直接</option>
            <option value="detailed">详细全面</option>
          </select>
        </div>
      </div>
      
      <div class="cyber-flex cyber-mt-16">
        <button class="cyber-btn" @click="generateQA" :disabled="generating">
          {{ generating ? '生成中...' : 'AI生成问答' }}
        </button>
        <button class="cyber-btn cyber-btn-secondary" @click="clearAll">
          清空全部
        </button>
      </div>
    </div>

    <!-- 问答列表 -->
    <div class="cyber-card">
      <div class="cyber-flex-between cyber-mb-16">
        <h3>问答库 ({{ qaList.length }})</h3>
        <div class="cyber-flex">
          <input 
            v-model="searchText" 
            type="text" 
            class="cyber-input" 
            style="width: 200px;"
            placeholder="搜索问答..."
          />
          <button class="cyber-btn cyber-btn-secondary" @click="exportQA">
            导出
          </button>
        </div>
      </div>

      <div v-if="filteredQA.length > 0" class="qa-list">
        <div 
          v-for="(qa, idx) in filteredQA" 
          :key="idx" 
          class="qa-item"
        >
          <div class="qa-header">
            <div class="qa-question">
              <span class="qa-icon">Q</span>
              <input 
                v-model="qa.question" 
                class="qa-input"
                placeholder="输入问题..."
              />
            </div>
            <div class="qa-actions">
              <button class="cyber-icon-btn" @click="copyQA(qa)" title="复制">
                📋
              </button>
              <button class="cyber-icon-btn cyber-icon-btn-danger" @click="deleteQA(idx)" title="删除">
                🗑️
              </button>
            </div>
          </div>
          <div class="qa-answer">
            <span class="qa-icon qa-icon-a">A</span>
            <textarea 
              v-model="qa.answer" 
              class="qa-textarea"
              rows="4"
              placeholder="输入回答..."
            ></textarea>
          </div>
          <div class="qa-meta">
            <span class="cyber-tag">{{ qa.type }}</span>
            <span class="cyber-text-muted">{{ qa.wordCount }} 字</span>
            <span class="cyber-text-muted">{{ qa.createdAt }}</span>
          </div>
        </div>
      </div>

      <div v-else class="cyber-empty">
        <div class="cyber-empty-icon">💭</div>
        <div>暂无问答，点击上方按钮生成</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/business'

const keywords = ref([])
const selectedKeywordId = ref('')
const questionCount = ref(5)
const questionType = ref('how')
const answerStyle = ref('professional')
const generating = ref(false)
const searchText = ref('')
const qaList = ref([])

const filteredQA = computed(() => {
  if (!searchText.value) return qaList.value
  const keyword = searchText.value.toLowerCase()
  return qaList.value.filter(qa => 
    qa.question.toLowerCase().includes(keyword) ||
    qa.answer.toLowerCase().includes(keyword)
  )
})

const loadKeywords = async () => {
  try {
    const res = await api.getKeywords({ tenant_id: localStorage.getItem('tenant_id') })
    keywords.value = res.data || []
  } catch (e) { console.warn(e) }
}

const generateQA = async () => {
  if (!selectedKeywordId.value) {
    alert('请先选择蒸馏词')
    return
  }
  
  generating.value = true
  
  // 模拟AI生成
  setTimeout(() => {
    const keyword = keywords.value.find(k => k.id === selectedKeywordId.value)
    const count = parseInt(questionCount.value) || 5
    
    const newQA = []
    const typeMap = {
      how: '怎么做',
      what: '是什么',
      why: '为什么',
      compare: '对比',
      recommend: '推荐'
    }
    
    for (let i = 0; i < count; i++) {
      newQA.push({
        question: `${typeMap[questionType.value]}${keyword?.training_keyword || '这个话题'}（${i + 1}）`,
        answer: `这是关于${keyword?.training_keyword || '该话题'}的专业回答。根据${answerStyle.value}风格，这里提供了详细的解答内容...`,
        type: typeMap[questionType.value],
        wordCount: 150 + Math.floor(Math.random() * 100),
        createdAt: new Date().toLocaleString('zh-CN')
      })
    }
    
    qaList.value = [...newQA, ...qaList.value]
    generating.value = false
  }, 1500)
}

const copyQA = (qa) => {
  const text = `Q: ${qa.question}\nA: ${qa.answer}`
  navigator.clipboard.writeText(text)
  alert('已复制到剪贴板')
}

const deleteQA = (idx) => {
  if (confirm('确认删除这条问答？')) {
    qaList.value.splice(idx, 1)
  }
}

const clearAll = () => {
  if (confirm('确认清空所有问答？')) {
    qaList.value = []
  }
}

const exportQA = () => {
  const data = qaList.value.map(qa => ({
    问题: qa.question,
    回答: qa.answer,
    类型: qa.type,
    字数: qa.wordCount,
    创建时间: qa.createdAt
  }))
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `qa_export_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadKeywords()
})
</script>

<style scoped>
.qa-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.qa-item {
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  padding: 16px;
}

.qa-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.qa-question,
.qa-answer {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.qa-icon {
  width: 28px;
  height: 28px;
  background: var(--cyber-neon-green);
  color: var(--cyber-bg-primary);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.qa-icon-a {
  background: var(--cyber-neon-cyan);
}

.qa-input,
.qa-textarea {
  flex: 1;
  background: var(--cyber-bg-card);
  border: 1px solid var(--cyber-border);
  color: var(--cyber-text-primary);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
}

.qa-input:focus,
.qa-textarea:focus {
  outline: none;
  border-color: var(--cyber-neon-green);
}

.qa-actions {
  display: flex;
  gap: 8px;
}

.qa-meta {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--cyber-border);
}
</style>
