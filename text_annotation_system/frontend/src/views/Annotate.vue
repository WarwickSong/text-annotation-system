<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">执行标注</h2>
    </div>

    <el-card>
      <el-steps :active="step" align-center style="margin-bottom: 24px" finish-status="success">
        <el-step title="上传文件" />
        <el-step title="配置参数" />
        <el-step title="执行标注" />
      </el-steps>

      <div v-if="step === 0">
        <el-upload
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          accept=".csv,.xlsx,.xls"
          :limit="1"
          class="upload-area"
        >
          <el-icon style="font-size: 40px; color: #c0c4cc"><UploadFilled /></el-icon>
          <div style="margin-top: 8px; color: #606266">拖拽文件到此处，或<em style="color: var(--app-primary)">点击上传</em></div>
          <template #tip>
            <div style="color: var(--app-text-secondary); font-size: 12px; margin-top: 4px">支持 .csv / .xlsx / .xls 文件</div>
          </template>
        </el-upload>
      </div>

      <div v-if="step === 1">
        <el-form label-width="120px">
          <el-form-item label="文件预览">
            <el-table :data="preview" stripe max-height="240" size="small" border />
          </el-form-item>
          <el-form-item label="目标列">
            <el-select v-model="selectedColumn" placeholder="选择要标注的列" style="width: 240px">
              <el-option v-for="col in columns" :key="col" :label="col" :value="col" />
            </el-select>
          </el-form-item>
          <el-form-item label="标注方案">
            <el-select v-model="selectedScheme" placeholder="选择标注方案" style="width: 240px">
              <el-option v-for="s in schemeList" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="执行模型">
            <el-select v-model="selectedModel" placeholder="选择执行模型" style="width: 240px">
              <el-option v-for="m in modelList" :key="m" :label="m" :value="m" />
            </el-select>
          </el-form-item>
          <el-form-item label="并发数量">
            <el-input-number v-model="concurrency" :min="1" :max="100" :step="1" />
          </el-form-item>
          <el-form-item label="批次大小">
            <el-input-number v-model="batchSize" :min="5" :max="100" :step="5" />
          </el-form-item>
        </el-form>
      </div>

      <div v-if="step === 2">
        <el-result
          v-if="taskCreated"
          icon="success"
          title="标注任务已创建"
          sub-title="任务已在后台执行中，可在任务监控页查看进度"
        >
          <template #extra>
            <el-button type="primary" @click="$router.push('/tasks')">前往任务监控</el-button>
          </template>
        </el-result>
      </div>

      <div class="step-actions">
        <el-button v-if="step > 0 && step < 2" @click="step--">上一步</el-button>
        <el-button v-if="step === 0 && uploadFile" type="primary" @click="goStep2">下一步</el-button>
        <el-button v-if="step === 1 && selectedColumn && selectedScheme && selectedModel" type="primary" @click="handleStart" :loading="starting">开始标注</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const step = ref(0)
const uploadFile = ref(null)
const uploadResult = ref(null)
const preview = ref([])
const columns = ref([])
const selectedColumn = ref('')
const schemeList = ref([])
const selectedScheme = ref('')
const modelList = ref([])
const selectedModel = ref('')
const concurrency = ref(3)
const batchSize = ref(20)
const starting = ref(false)
const taskCreated = ref(false)

async function handleFileChange(file) {
  uploadFile.value = file.raw
  try {
    const { data } = await api.files.upload(file.raw)
    uploadResult.value = data
    preview.value = data.preview
    columns.value = data.columns
    ElMessage.success('文件上传成功')
  } catch (e) {
    ElMessage.error('文件上传失败')
    uploadFile.value = null
  }
}

async function goStep2() {
  step.value = 1
  try {
    const [schemesRes, configRes] = await Promise.all([
      api.schemes.list(),
      api.config.status(),
    ])
    schemeList.value = schemesRes.data
    if (configRes.data.models && configRes.data.models.length > 0) {
      modelList.value = configRes.data.models
      selectedModel.value = configRes.data.models[0]
    }
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

async function handleStart() {
  starting.value = true
  try {
    await api.tasks.create({
      file_id: uploadResult.value.file_id,
      column: selectedColumn.value,
      scheme_id: selectedScheme.value,
      file_name: uploadResult.value.file_name,
      model: selectedModel.value,
        batch_size: batchSize.value,
        max_concurrency: concurrency.value,
    })
    taskCreated.value = true
    step.value = 2
    ElMessage.success('标注任务已创建')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建任务失败')
  } finally {
    starting.value = false
  }
}
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

.upload-area {
  margin: 20px auto;
  max-width: 460px;
}

.step-actions {
  margin-top: 24px;
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
