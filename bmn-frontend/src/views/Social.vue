<template>
  <div class="social-page">
    <h2>自媒体账号管理</h2>
    <p class="description">
      管理已授权的自媒体平台账号，支持内容自动分发到多个平台。
    </p>

    <el-button type="primary" @click="showAddDialog = true">
      <el-icon><Plus /></el-icon> 添加账号
    </el-button>

    <el-table :data="accounts" style="width: 100%; margin-top: 20px">
      <el-table-column prop="platform" label="平台" width="120">
        <template #default="{ row }">
          <el-tag>{{ getPlatformName(row.platform) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="account_name" label="账号名称" />
      <el-table-column prop="account_id" label="账号ID" width="200" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '已激活' : '未激活' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="添加时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'inactive'"
            type="success"
            size="small"
            @click="activateAccount(row)"
          >
            激活
          </el-button>
          <el-button type="danger" size="small" @click="deleteAccount(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加账号对话框 -->
    <el-dialog v-model="showAddDialog" title="添加自媒体账号" width="500px">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="平台">
          <el-select v-model="addForm.platform" placeholder="选择平台">
            <el-option
              v-for="p in platforms"
              :key="p.value"
              :label="p.label"
              :value="p.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账号名称">
          <el-input v-model="addForm.account_name" placeholder="例如：我的小红书账号" />
        </el-form-item>
        <el-form-item label="账号ID">
          <el-input v-model="addForm.account_id" placeholder="平台的账号ID或用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 激活账号对话框 -->
    <el-dialog v-model="showActivateDialog" title="激活账号" width="600px">
      <div class="activate-guide">
        <h4>激活步骤：</h4>
        <ol>
          <li>点击下方按钮下载 GEO 助手客户端</li>
          <li>安装并运行 GEO 助手</li>
          <li>在 GEO 助手中输入授权码：<strong>{{ currentAccount.auth_code }}</strong></li>
          <li>完成授权后，账号将自动激活</li>
        </ol>
        <el-button type="primary" @click="downloadGEOHelper">
          <el-icon><Download /></el-icon> 下载 GEO 助手
        </el-button>
      </div>
      <template #footer>
        <el-button @click="showActivateDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import { getSocialAccounts, createSocialAccount, deleteSocialAccount, activateSocialAccount } from '@/api/business'

const accounts = ref([])
const showAddDialog = ref(false)
const showActivateDialog = ref(false)
const currentAccount = ref(null)

const platforms = [
  { value: 'wechat', label: '微信公众号' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'douyin', label: '抖音' },
  { value: 'zhihu', label: '知乎' },
  { value: 'weibo', label: '微博' },
  { value: 'toutiao', label: '今日头条' },
  { value: 'bilibili', label: '哔哩哔哩' },
  { value: 'jianshu', label: '简书' },
  { value: 'csdn', label: 'CSDN' },
  { value: '163', label: '网易号' },
  { value: 'sohu', label: '搜狐号' },
  { value: 'baijiahao', label: '百家号' }
]

const addForm = ref({
  platform: '',
  account_name: '',
  account_id: ''
})

const getPlatformName = (value) => {
  const p = platforms.find(p => p.value === value)
  return p ? p.label : value
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

const loadAccounts = async () => {
  try {
    const res = await getSocialAccounts()
    accounts.value = res.data
  } catch (e) {
    console.error('加载账号列表失败', e)
  }
}

const submitAdd = async () => {
  if (!addForm.value.platform || !addForm.value.account_name || !addForm.value.account_id) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await createSocialAccount(addForm.value)
    ElMessage.success('账号添加成功')
    showAddDialog.value = false
    addForm.value = { platform: '', account_name: '', account_id: '' }
    await loadAccounts()
  } catch (e) {
    ElMessage.error('添加失败：' + (e.response?.data?.detail || e.message))
  }
}

const activateAccount = (account) => {
  currentAccount.value = account
  showActivateDialog.value = true
}

const downloadGEOHelper = () => {
  ElMessage.info('GEO 助手下载功能开发中，请联系管理员获取')
}

const deleteAccount = async (account) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除账号 "${account.account_name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteSocialAccount(account.id)
    ElMessage.success('删除成功')
    await loadAccounts()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.social-page {
  padding: 20px;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.activate-guide {
  line-height: 1.8;
}

.activate-guide ol {
  margin: 15px 0;
  padding-left: 20px;
}

.activate-guide li {
  margin: 10px 0;
}

.activate-guide strong {
  color: #409eff;
  font-size: 16px;
}
</style>
