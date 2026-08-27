<template>
  <div class="gallery-page">
    <div class="page-header">
      <h2>图库管理</h2>
      <p class="desc">管理品牌图片素材，支持分类上传和组织</p>
    </div>

    <!-- 分类管理 -->
    <div class="category-section">
      <div class="section-header">
        <h3>图库分类</h3>
        <el-button type="primary" @click="showCategoryDialog = true">
          <el-icon><Plus /></el-icon>
          新建分类
        </el-button>
      </div>
      <el-tabs v-model="activeCategory" type="card" @tab-click="handleCategoryChange">
        <el-tab-pane
          v-for="cat in categories"
          :key="cat.id"
          :label="`${cat.name} (${cat.image_count || 0})`"
          :name="cat.id"
        >
          <template #label>
            <span>{{ cat.name }} ({{ cat.image_count || 0 }})</span>
            <el-icon class="delete-btn" @click.stop="deleteCategory(cat.id)"><Delete /></el-icon>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 图片上传 -->
    <div class="upload-section" v-if="activeCategory">
      <el-upload
        :action="`/api/v2/geo/gallery/images?tenant_id=${tenantId}&category_id=${activeCategory}`"
        :headers="uploadHeaders"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        multiple
        accept="image/*"
      >
        <el-button type="success">
          <el-icon><Upload /></el-icon>
          上传图片
        </el-button>
      </el-upload>
    </div>

    <!-- 图片列表 -->
    <div class="image-grid" v-loading="loadingImages">
      <div
        v-for="img in currentImages"
        :key="img.id"
        class="image-card"
      >
        <el-image
          :src="`http://localhost:5006${img.file_url}`"
          fit="cover"
          class="preview"
        >
          <template #error>
            <div class="image-error">
              <el-icon><Picture /></el-icon>
              <span>加载失败</span>
            </div>
          </template>
        </el-image>
        <div class="image-info">
          <div class="image-name">{{ img.file_name }}</div>
          <div class="image-meta">
            <span>{{ formatSize(img.file_size) }}</span>
            <el-button
              type="danger"
              size="small"
              @click="deleteImage(img.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="currentImages.length === 0" description="暂无图片" />
    </div>

    <!-- 新建分类对话框 -->
    <el-dialog v-model="showCategoryDialog" title="新建图库分类" width="500px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="createCategory" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Delete, Picture } from '@element-plus/icons-vue'
import { getCategories as fetchCategories, createCategory as postCategory, deleteCategory as removeCategory, uploadImage, getImages as fetchImages, deleteImage as removeImage } from '@/api/business'

const tenantId = computed(() => localStorage.getItem('tenant_id'))
const brandId = computed(() => localStorage.getItem('brand_id'))

const categories = ref([])
const activeCategory = ref('')
const currentImages = ref([])
const loadingImages = ref(false)
const showCategoryDialog = ref(false)
const creating = ref(false)
const categoryForm = ref({ name: '', description: '' })

const uploadHeaders = computed(() => ({
  'X-Tenant-ID': tenantId.value
}))

// 加载分类列表
const loadCategories = async () => {
  try {
    const res = await fetchCategories(tenantId.value, brandId.value)
    categories.value = res.data
    if (categories.value.length > 0 && !activeCategory.value) {
      activeCategory.value = categories.value[0].id
    }
  } catch (err) {
    ElMessage.error('加载分类失败')
  }
}

// 加载当前分类的图片
const loadImages = async () => {
  if (!activeCategory.value) return
  loadingImages.value = true
  try {
    const res = await fetchImages({ tenant_id: tenantId.value, category_id: activeCategory.value })
    currentImages.value = res.data
  } catch (err) {
    ElMessage.error('加载图片失败')
  } finally {
    loadingImages.value = false
  }
}

// 创建分类
const createCategory = async () => {
  if (!categoryForm.value.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  creating.value = true
  try {
    await postCategory({
      tenant_id: tenantId.value,
      brand_id: brandId.value,
      name: categoryForm.value.name,
      description: categoryForm.value.description
    })
    ElMessage.success('分类创建成功')
    showCategoryDialog.value = false
    categoryForm.value = { name: '', description: '' }
    await loadCategories()
  } catch (err) {
    ElMessage.error('创建分类失败')
  } finally {
    creating.value = false
  }
}

// 删除分类
const deleteCategory = async (id) => {
  try {
    await ElMessageBox.confirm('删除分类将同时删除该分类下的所有图片，确认继续？', '警告', {
      type: 'warning'
    })
    await removeCategory(id, tenantId.value)
    ElMessage.success('分类已删除')
    if (activeCategory.value === id) {
      activeCategory.value = categories.value[0]?.id || ''
    }
    await loadCategories()
    await loadImages()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// 删除图片
const deleteImage = async (id) => {
  try {
    await ElMessageBox.confirm('确认删除该图片？', '警告', { type: 'warning' })
    await removeImage(id, tenantId.value)
    ElMessage.success('图片已删除')
    await loadImages()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

// 上传前验证
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
  }
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
  }
  return isImage && isLt5M
}

// 上传成功
const handleUploadSuccess = () => {
  ElMessage.success('上传成功')
  loadImages()
  loadCategories() // 更新计数
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

// 切换分类
const handleCategoryChange = () => {
  loadImages()
}

onMounted(() => {
  loadCategories()
  loadImages()
})
</script>

<style scoped>
.gallery-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
}

.desc {
  color: #909399;
  margin: 0;
}

.category-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
}

.delete-btn {
  margin-left: 8px;
  cursor: pointer;
  color: #f56c6c;
}

.upload-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.image-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.image-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview {
  width: 100%;
  height: 160px;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 160px;
  background: #f5f7fa;
  color: #909399;
}

.image-error .el-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.image-info {
  padding: 12px;
}

.image-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 8px;
}

.image-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}
</style>
