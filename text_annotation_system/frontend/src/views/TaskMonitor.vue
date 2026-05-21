<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">任务监控</h2>
      <el-button @click="loadTasks" type="primary" plain size="small">
        <el-icon style="margin-right: 4px"><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <el-card>
      <el-table :data="taskList" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="file_name" label="文件名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="scheme_name" label="方案" width="120" />
        <el-table-column prop="model" label="模型" width="130" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="dark">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="row.progress_percent"
                :stroke-width="6"
                :status="row.status === 'completed' ? 'success' : row.status === 'terminated' ? 'exception' : ''"
              />
              <span class="progress-text">{{ row.completed_rows }} / {{ row.total_rows }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="用时" width="90" align="center">
          <template #default="{ row }">
            <span style="font-variant-numeric: tabular-nums">{{ row.duration || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="150">
          <template #default="{ row }">
            <span style="color: var(--app-text-secondary); font-size: 12px">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="结束时间" width="150">
          <template #default="{ row }">
            <span style="color: var(--app-text-secondary); font-size: 12px">{{ row.finished_at ? formatTime(row.finished_at) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" size="small" @click="downloadResult(row.id)" v-if="row.status === 'completed' || row.status === 'terminated'">下载</el-button>
            <el-popconfirm title="确定终止该任务？" @confirm="terminateTask(row.id)" v-if="row.status === 'running'">
              <template #reference>
                <el-button link type="danger" size="small">终止</el-button>
              </template>
            </el-popconfirm>
            <el-popconfirm title="确定删除该任务记录？删除后不可恢复。" @confirm="deleteTask(row.id)" v-if="row.status !== 'running'">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import api from '../api'

const loading = ref(false)
const taskList = ref([])
let wsConnections = {}

function formatTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function statusType(status) {
  const map = { running: '', completed: 'success', terminated: 'danger' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { running: '运行中', completed: '已完成', terminated: '已终止' }
  return map[status] || status
}

async function loadTasks() {
  loading.value = true
  try {
    const { data } = await api.tasks.list()
    taskList.value = data
    setupWebSockets()
  } finally {
    loading.value = false
  }
}

function setupWebSockets() {
  for (const task of taskList.value) {
    if (task.status === 'running' && !wsConnections[task.id]) {
      const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${wsProto}//${location.host}/api/tasks/ws/${task.id}/progress`)
      ws.onmessage = (event) => {
        const update = JSON.parse(event.data)
        const idx = taskList.value.findIndex(t => t.id === update.id)
        if (idx >= 0) {
          taskList.value[idx] = { ...taskList.value[idx], ...update }
        }
        if (update.status !== 'running') {
          ws.close()
          delete wsConnections[update.id]
        }
      }
      wsConnections[task.id] = ws
    }
  }
}

async function downloadResult(taskId) {
  try {
    const { data } = await api.tasks.download(taskId)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    const task = taskList.value.find(t => t.id === taskId)
    a.download = task ? task.file_name : 'result.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

async function terminateTask(taskId) {
  try {
    await api.tasks.terminate(taskId)
    ElMessage.success('已终止')
    loadTasks()
  } catch (e) {
    ElMessage.error('终止失败')
  }
}

async function deleteTask(taskId) {
  try {
    await api.tasks.delete(taskId)
    ElMessage.success('已删除')
    loadTasks()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(loadTasks)
onUnmounted(() => {
  for (const ws of Object.values(wsConnections)) {
    ws.close()
  }
  wsConnections = {}
})
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

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.progress-text {
  font-size: 11px;
  color: var(--app-text-secondary);
}
</style>
