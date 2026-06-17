<template>
  <a-modal
    v-model:open="visible"
    width="1200px"
    :footer="null"
    :closable="false"
    wrap-class-name="file-detail"
    @after-open-change="afterOpenChange"
    :bodyStyle="{ height: '80vh', padding: '0' }"
  >
    <template #title>
      <div class="modal-title-wrapper">
        <!-- 左侧：文件名和图标 -->
        <div class="file-title">
          <component :is="fileIcon" :style="{ color: fileIconColor, fontSize: '18px' }" />
          <span class="file-name">{{ file?.filename || '文件详情' }}</span>
        </div>

        <div class="header-controls">
          <!-- 字符数与片段数 -->
          <span class="view-info">
            {{ formatTextLength(charCount) }} 字符 · {{ chunkCount }} 个片段
          </span>

          <!-- 下载按钮下拉菜单 -->
          <a-dropdown trigger="click" v-if="file">
            <a-button type="default" class="download-btn">
              <template #icon><Download :size="16" /></template>
              下载
              <ChevronDown :size="16" style="margin-left: 4px" />
            </a-button>
            <template #overlay>
              <a-menu @click="handleDownloadMenuClick">
                <a-menu-item key="original" :disabled="!file.file_id">
                  <template #icon><Download :size="16" /></template>
                  下载原文
                </a-menu-item>
                <a-menu-item
                  key="markdown"
                  :disabled="!((file.lines && file.lines.length > 0) || file.content)"
                >
                  <template #icon><FileText :size="16" /></template>
                  下载 Markdown
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>

          <!-- 自定义关闭按钮 -->
          <button class="custom-close-btn" @click="visible = false">
            <X :size="16" />
          </button>
        </div>
      </div>
    </template>
    <div v-if="loading" class="loading-container">
      <a-spin tip="正在加载文档内容..." />
    </div>
    <div v-else-if="file && hasContent" class="file-detail-content">
      <!-- 左侧：解析出的文档内容 -->
      <div class="doc-pane">
        <div class="pane-title">文档内容</div>
        <div class="pane-body">
          <MdPreview
            v-if="mergedContent"
            :modelValue="mergedContent"
            :theme="theme"
            previewTheme="github"
            class="markdown-content"
          />
          <div v-else class="empty-content">
            <p>暂无文件内容</p>
          </div>
        </div>
      </div>

      <!-- 右侧：Chunk 结果 -->
      <div class="chunk-pane">
        <div class="pane-title">分块结果（{{ chunkCount }}）</div>
        <div class="pane-body">
          <div v-if="mappedChunks.length > 0" class="chunk-list">
            <div v-for="chunk in mappedChunks" :key="chunk.id" class="chunk-card">
              <div class="chunk-card-header">
                <span class="chunk-order">#{{ chunk.chunk_order_index }}</span>
              </div>
              <div class="chunk-card-content">
                {{ chunk.content.replace(/\n+/g, ' ') }}
              </div>
            </div>
          </div>
          <div v-else class="empty-content">
            <p>暂无分块信息</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="file" class="empty-content">
      <p>暂无文件内容</p>
    </div>
  </a-modal>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useDatabaseStore } from '@/stores/database'
import { useThemeStore } from '@/stores/theme'
import { message } from 'ant-design-vue'
import { documentApi } from '@/apis/knowledge_api'
import { mergeChunks } from '@/utils/chunkUtils'
import { getFileIcon, getFileIconColor } from '@/utils/file_utils'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import { Download, ChevronDown, FileText, X } from 'lucide-vue-next'

const store = useDatabaseStore()
const themeStore = useThemeStore()

const visible = computed({
  get: () => store.state.fileDetailModalVisible,
  set: (value) => (store.state.fileDetailModalVisible = value)
})

const file = computed(() => store.selectedFile)
const loading = computed(() => store.state.fileDetailLoading)

// 文件图标
const fileIcon = computed(() => getFileIcon(file.value?.filename))
const fileIconColor = computed(() => getFileIconColor(file.value?.filename))

const downloadingOriginal = ref(false)
const downloadingMarkdown = ref(false)

// 主题设置
const theme = computed(() => (themeStore.isDark ? 'dark' : 'light'))

const hasIndexed = computed(() => ['done', 'indexed'].includes(file.value?.status))
const hasContent = computed(
  () => (file.value?.lines && file.value?.lines.length > 0) || file.value?.content
)

// 统计信息
const mergeResult = computed(() => mergeChunks(file.value?.lines || []))
const mappedChunks = computed(() => mergeResult.value.chunks)
const mergedContent = computed(() => file.value?.content || mergeResult.value.content || '')
const charCount = computed(() => mergedContent.value.length)
const chunkCount = computed(() => mappedChunks.value.length || file.value?.lines?.length || 0)

// 格式化文本长度
function formatTextLength(length) {
  if (!length && length !== 0) return '0 字符'

  if (length < 1000) {
    return `${length}`
  } else {
    return `${(length / 1000).toFixed(1)}k`
  }
}

const afterOpenChange = (open) => {
  if (!open) {
    store.selectedFile = null
  }
}

// 下载菜单点击处理
const handleDownloadMenuClick = ({ key }) => {
  if (key === 'original') {
    handleDownloadOriginal()
  } else if (key === 'markdown') {
    handleDownloadMarkdown()
  }
}

// 下载原文
const handleDownloadOriginal = async () => {
  if (!file.value || !file.value.file_id) {
    message.error('文件信息不完整')
    return
  }

  const dbId = store.databaseId
  if (!dbId) {
    message.error('无法获取数据库ID，请刷新页面后重试')
    return
  }

  downloadingOriginal.value = true
  try {
    const response = await documentApi.downloadDocument(dbId, file.value.file_id)

    // 获取文件名
    const contentDisposition = response.headers.get('content-disposition')
    let filename = file.value.filename
    if (contentDisposition) {
      // 首先尝试匹配RFC 2231格式 filename*=UTF-8''...
      const rfc2231Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/)
      if (rfc2231Match) {
        try {
          filename = decodeURIComponent(rfc2231Match[1])
        } catch (error) {
          console.warn('Failed to decode RFC2231 filename:', rfc2231Match[1], error)
        }
      } else {
        // 回退到标准格式 filename="..."
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '')
          // 解码URL编码的文件名
          try {
            filename = decodeURIComponent(filename)
          } catch (error) {
            console.warn('Failed to decode filename:', filename, error)
          }
        }
      }
    }

    // 创建blob并下载
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error) {
    console.error('下载文件时出错:', error)
    message.error(error.message || '下载文件失败')
  } finally {
    downloadingOriginal.value = false
  }
}

// 下载 Markdown
const handleDownloadMarkdown = () => {
  const content = mergedContent.value

  if (!content) {
    message.error('没有可下载的 Markdown 内容')
    return
  }

  downloadingMarkdown.value = true
  try {
    // 生成文件名（如果原文件没有 .md 扩展名，则添加）
    let filename = file.value.filename || 'document.md'
    if (!filename.toLowerCase().endsWith('.md')) {
      // 移除原扩展名，添加 .md
      const lastDotIndex = filename.lastIndexOf('.')
      if (lastDotIndex > 0) {
        filename = filename.substring(0, lastDotIndex) + '.md'
      } else {
        filename = filename + '.md'
      }
    }

    // 创建 blob 并下载
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error) {
    console.error('下载 Markdown 时出错:', error)
    message.error(error.message || '下载 Markdown 失败')
  } finally {
    downloadingMarkdown.value = false
  }
}
</script>

<style scoped>
.file-detail-content {
  height: 100%;
  display: flex;
  overflow: hidden;
}

/* 左右分栏 */
.doc-pane,
.chunk-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
}

.doc-pane {
  flex: 1 1 60%;
  border-right: 1px solid var(--gray-200);
}

.chunk-pane {
  flex: 1 1 40%;
  background: var(--gray-25);
}

.pane-title {
  flex-shrink: 0;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
  border-bottom: 1px solid var(--gray-150);
}

.pane-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
}

.markdown-content {
  min-height: 100%;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.empty-content {
  text-align: center;
  padding: 40px 0;
  color: var(--gray-400);
  width: 100%;
}

/* Chunks 面板样式 */
.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chunk-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s ease;
}

.chunk-card:hover {
  border-color: var(--main-color);
  box-shadow: 0 2px 8px rgba(1, 97, 121, 0.1);
}

.chunk-card-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.chunk-order {
  font-weight: 600;
  color: var(--main-color);
  font-size: 12px;
}

.chunk-card-content {
  font-size: 12px;
  color: var(--gray-600);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

<style lang="less">
.file-detail {
  .ant-modal {
    top: 20px;
  }

  .ant-modal-header {
    .ant-modal-title {
      width: 100%;
    }
  }
}

.modal-title-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

/* 文件标题样式 */
.file-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--gray-900);
}

.title-info {
  font-size: 13px;
  color: var(--gray-600);
  font-weight: 500;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

/* 下载按钮样式 */
.download-btn {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  height: 28px;
  font-size: 13px;
  line-height: 1;
  border-radius: 6px;
  gap: 4px;

  svg {
    vertical-align: middle;
  }
}

/* 自定义关闭按钮 */
.custom-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--gray-500);
  transition: all 0.2s;

  &:hover {
    background: var(--gray-100);
    color: var(--gray-700);
  }
}

.view-info {
  font-size: 12px;
  color: var(--gray-500);
  white-space: nowrap;
}

/* 下拉菜单样式 */
.ant-dropdown-menu {
  border-radius: 8px;
  padding: 4px;
}

.ant-dropdown-menu-item {
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 8px 12px;

  svg {
    margin-right: 8px;
  }
}
/* MdPreview 覆盖样式 - 非 scoped */
.doc-pane {
  .md-editor-preview-wrapper {
    padding: 0;
  }

  .md-editor-preview {
    font-size: 14px;
    line-height: 1.75;
    color: var(--gray-1000);

    h1 {
      font-size: 1.2rem;
      margin: 16px 0 12px;
      font-weight: 600;
    }

    h2 {
      font-size: 1.2rem;
      margin: 16px 0 12px;
      font-weight: 600;
    }

    h3 {
      font-size: 1.1rem;
      margin: 14px 0 10px;
      font-weight: 600;
    }

    h4 {
      font-size: 1rem;
      margin: 14px 0 10px;
      font-weight: 600;
    }

    h5 {
      font-size: 1rem;
      margin: 12px 0 8px;
      font-weight: 600;
    }

    h6 {
      font-size: 1rem;
      margin: 12px 0 8px;
      font-weight: 600;
    }
  }
}
</style>
