<template>
  <div style="max-width: 600px">
    <div class="page-header">
      <h2 class="page-title">系统配置</h2>
    </div>

    <el-card>
      <template #header>API 配置</template>
      <el-alert
        v-if="configured"
        title="密钥已配置"
        type="success"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-form :model="form" label-width="120px">
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="输入 API Key" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="模型列表">
          <div style="width: 100%">
            <div v-for="(m, index) in form.models" :key="index" style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center">
              <el-input v-model="form.models[index]" placeholder="模型名称，如 gpt-4o-mini" style="flex: 1" />
              <el-button type="danger" size="small" plain @click="removeModel(index)" :disabled="form.models.length <= 1">删除</el-button>
            </div>
            <el-button type="primary" plain size="small" @click="addModel">+ 添加模型</el-button>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px" v-if="configured">
      <template #header>测试连接</template>
      <el-form label-width="120px">
        <el-form-item label="选择模型">
          <el-select v-model="testModel" placeholder="选择要测试的模型" style="width: 100%">
            <el-option v-for="m in form.models" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="handleTest" :loading="testing">测试连接</el-button>
        </el-form-item>
      </el-form>
      <el-alert
        v-if="testResult"
        :title="testResult.success ? '连接成功' : '连接失败'"
        :type="testResult.success ? 'success' : 'error'"
        :description="testResult.message"
        show-icon
        :closable="false"
        style="margin-top: 12px"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const configured = ref(false)
const saving = ref(false)
const testing = ref(false)
const testModel = ref('')
const testResult = ref(null)
const form = ref({
  api_key: '',
  base_url: '',
  models: [''],
})

async function loadStatus() {
  try {
    const { data } = await api.config.status()
    configured.value = data.configured
    if (data.configured && data.models && data.models.length > 0) {
      form.value.models = [...data.models]
      if (!testModel.value && data.models.length > 0) {
        testModel.value = data.models[0]
      }
    }
  } catch (e) { /* ignore */ }
}

function addModel() {
  form.value.models.push('')
}

function removeModel(index) {
  form.value.models.splice(index, 1)
}

async function handleSave() {
  const validModels = form.value.models.filter(m => m.trim())
  if (!form.value.api_key.trim() || !form.value.base_url.trim() || validModels.length === 0) {
    ElMessage.warning('API Key、Base URL 和至少一个模型为必填项')
    return
  }
  saving.value = true
  try {
    await api.config.set({
      api_key: form.value.api_key,
      base_url: form.value.base_url,
      models: validModels,
    })
    configured.value = true
    form.value.models = validModels
    if (!testModel.value && validModels.length > 0) {
      testModel.value = validModels[0]
    }
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  if (!testModel.value) {
    ElMessage.warning('请选择要测试的模型')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const { data } = await api.config.test({ model: testModel.value })
    testResult.value = { success: true, message: `模型 ${data.model} 响应: ${data.answer}` }
  } catch (e) {
    testResult.value = { success: false, message: e.response?.data?.detail || '连接失败' }
  } finally {
    testing.value = false
  }
}

onMounted(loadStatus)
</script>
