<template>
  <div v-loading="loading">
    <div class="page-header">
      <el-button text @click="$router.push('/schemes')">
        <el-icon style="margin-right: 4px"><ArrowLeft /></el-icon>返回列表
      </el-button>
    </div>

    <el-card>
      <el-form :model="scheme" label-width="100px">
        <el-form-item label="方案名称">
          <el-input v-model="scheme.name" placeholder="输入方案名称" />
        </el-form-item>
        <el-form-item label="Prompt 头">
          <el-input v-model="scheme.prompt_header" type="textarea" :rows="4" placeholder="放在 system message 开头的指令文本" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <div class="section-header">
          <span class="section-title">标注类</span>
          <el-button type="primary" plain size="small" @click="addClass">+ 添加标注类</el-button>
        </div>
      </template>

      <div v-for="(cls, index) in scheme.classes" :key="cls.id" class="class-item">
        <el-row :gutter="12" align="middle">
          <el-col :span="6">
            <el-input v-model="cls.name" placeholder="类名" />
          </el-col>
          <el-col :span="6">
            <el-select v-model="cls.label_type" placeholder="标注类型" clearable style="width: 100%">
              <el-option label="固定选项 (select)" value="select" />
              <el-option label="自由输出 (无选项)" value="free" />
            </el-select>
          </el-col>
          <el-col :span="12" style="display: flex; gap: 6px; justify-content: flex-end">
            <el-button size="small" v-if="index > 0" @click="moveClass(index, index - 1)">上移</el-button>
            <el-button size="small" v-if="index < scheme.classes.length - 1" @click="moveClass(index, index + 1)">下移</el-button>
            <el-button size="small" type="danger" plain @click="removeClass(index)">删除</el-button>
          </el-col>
        </el-row>
        <el-row :gutter="12" style="margin-top: 8px">
          <el-col :span="24">
            <el-input v-model="cls.description" type="textarea" :rows="2" placeholder="标注类说明（指导大模型如何标注该类）" />
          </el-col>
        </el-row>
        <el-row :gutter="12" style="margin-top: 8px" v-if="cls.label_type === 'select'">
          <el-col :span="24">
            <el-select v-model="cls.options" multiple filterable allow-create default-first-option placeholder="输入选项后回车添加" style="width: 100%" />
          </el-col>
        </el-row>
      </div>

      <el-empty v-if="scheme.classes.length === 0" description="暂无标注类，点击上方添加" :image-size="60" />

      <div style="margin-top: 16px; text-align: right">
        <el-button type="primary" @click="handleSave" :loading="saving">保存方案</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '../api'

const route = useRoute()
const loading = ref(false)
const saving = ref(false)
const scheme = ref({ name: '', prompt_header: '', classes: [] })

async function loadScheme() {
  loading.value = true
  try {
    const { data } = await api.schemes.get(route.params.id)
    scheme.value = data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function addClass() {
  scheme.value.classes.push({
    id: `cls_${Date.now().toString(36)}`,
    name: '',
    description: '',
    label_type: 'free',
    options: [],
  })
}

function removeClass(index) {
  scheme.value.classes.splice(index, 1)
}

function moveClass(from, to) {
  const arr = scheme.value.classes
  const item = arr.splice(from, 1)[0]
  arr.splice(to, 0, item)
}

async function handleSave() {
  saving.value = true
  try {
    await api.schemes.update(scheme.value.id, scheme.value)
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadScheme)
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
}

.class-item {
  border: 1px solid #edf0f5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background: #fafbfc;
  transition: border-color 0.2s;
}

.class-item:hover {
  border-color: #d0d5dd;
}
</style>
