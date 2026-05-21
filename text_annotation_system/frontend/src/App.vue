<template>
  <el-container style="min-height: 100vh; background: var(--app-bg)">
    <el-header class="app-header">
      <div class="app-logo" @click="$router.push('/')">
        <el-icon :size="22" style="color: var(--app-primary)"><Document /></el-icon>
        <span class="app-logo-text">文本批量标注系统</span>
      </div>
      <el-menu
        :default-active="$route.path"
        mode="horizontal"
        :ellipsis="false"
        class="app-nav"
        router
      >
        <el-menu-item index="/schemes">
          <el-icon><Files /></el-icon>
          <span>标注方案</span>
        </el-menu-item>
        <el-menu-item index="/annotate">
          <el-icon><EditPen /></el-icon>
          <span>执行标注</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><Monitor /></el-icon>
          <span>任务监控</span>
        </el-menu-item>
        <el-menu-item index="/config">
          <el-icon><Setting /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
        <div class="nav-spacer" />
        <el-popconfirm
          title="确定关闭系统？关闭后需重新启动。"
          @confirm="shutdownSystem"
          confirm-button-text="确定关闭"
          cancel-button-text="取消"
        >
          <template #reference>
            <el-menu-item class="nav-shutdown">
              <el-icon><SwitchButton /></el-icon>
              <span>关闭系统</span>
            </el-menu-item>
          </template>
        </el-popconfirm>
      </el-menu>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { Document, Files, EditPen, Monitor, Setting, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from './api'

async function shutdownSystem() {
  try {
    await api.system.shutdown()
    ElMessage.success('系统已关闭')
    document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;color:#666"><div style="text-align:center"><h2 style="margin-bottom:8px">系统已关闭</h2><p style="color:#999">可以关闭此页面了</p></div></div>'
  } catch (e) {
    ElMessage.error('关闭失败')
  }
}
</script>

<style scoped>
.app-header {
  background: var(--app-header-bg);
  border-bottom: 1px solid var(--app-header-border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  margin-right: 32px;
  white-space: nowrap;
}

.app-logo-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--app-header-text);
  letter-spacing: 0.5px;
}

.app-nav {
  border: none !important;
  background: transparent !important;
  height: 56px;
}

.app-nav .el-menu-item {
  height: 56px;
  line-height: 56px;
  color: var(--app-text-secondary) !important;
  font-size: 14px;
  font-weight: 500;
  border-bottom: 2px solid transparent !important;
  padding: 0 16px;
  transition: all 0.2s;
}

.app-nav .el-menu-item:hover {
  color: var(--app-primary) !important;
  background: transparent !important;
}

.app-nav .el-menu-item.is-active {
  color: var(--app-primary) !important;
  border-bottom-color: var(--app-primary) !important;
  background: transparent !important;
}

.app-nav .el-menu-item .el-icon {
  font-size: 18px;
  margin-right: 4px;
}

.app-main {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.nav-spacer {
  flex: 1;
}

.nav-shutdown {
  color: var(--app-text-secondary) !important;
}

.nav-shutdown:hover {
  color: var(--app-danger) !important;
}
</style>
