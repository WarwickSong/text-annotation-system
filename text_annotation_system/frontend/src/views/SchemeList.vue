<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">标注方案</h2>
      <div class="page-actions">
        <el-upload :show-file-list="false" :before-upload="handleImport" accept=".json">
          <el-button plain size="small">
            <el-icon style="margin-right: 4px"><Upload /></el-icon>导入方案
          </el-button>
        </el-upload>
        <el-button type="primary" size="small" @click="handleCreate">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>新建方案
        </el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="8" v-for="item in schemes" :key="item.id">
        <el-card class="scheme-card" shadow="hover" @click="$router.push(`/schemes/${item.id}`)">
          <div class="scheme-card-body">
            <h3 class="scheme-name">{{ item.name }}</h3>
            <p class="scheme-time">{{ formatTime(item.updated_at) }}</p>
          </div>
          <div class="scheme-card-actions" @click.stop>
            <el-button link type="primary" size="small" @click="$router.push(`/schemes/${item.id}`)">编辑</el-button>
            <el-button link type="success" size="small" @click="handleExport(item.id)">导出</el-button>
            <el-popconfirm title="确定删除该方案？" @confirm="handleDelete(item.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && schemes.length === 0" description="暂无标注方案，点击上方新建" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'
import api from '../api'

const schemes = ref([])
const loading = ref(false)

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function loadSchemes() {
  loading.value = true
  try {
    const { data } = await api.schemes.list()
    schemes.value = data
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  try {
    const { data } = await api.schemes.create({ name: '新方案', prompt_header: '', classes: [] })
    ElMessage.success('创建成功')
    loadSchemes()
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

async function handleDelete(id) {
  try {
    await api.schemes.delete(id)
    ElMessage.success('删除成功')
    loadSchemes()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function handleExport(id) {
  try {
    const { data } = await api.schemes.exportScheme(id)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${id}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

async function handleImport(file) {
  try {
    await api.schemes.importScheme(file)
    ElMessage.success('导入成功')
    loadSchemes()
  } catch (e) {
    ElMessage.error('导入失败')
  }
  return false
}

onMounted(loadSchemes)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--app-text);
  margin: 0;
}

.page-actions {
  display: flex;
  gap: 8px;
}

.scheme-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.scheme-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--app-card-shadow-hover) !important;
}

.scheme-card-body {
  padding-bottom: 8px;
}

.scheme-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
  margin: 0 0 6px 0;
}

.scheme-time {
  font-size: 12px;
  color: var(--app-text-secondary);
  margin: 0;
}

.scheme-card-actions {
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
  display: flex;
  gap: 4px;
}
</style>
