<template>
  <div class="database-info-container">
    <FileDetailModal />

    <!-- 检索配置弹窗 -->
    <SearchConfigModal
      v-model="searchConfigModalVisible"
      :database-id="databaseId"
      @save="handleSearchConfigSave"
    />

    <FileUploadModal
      v-model:visible="addFilesModalVisible"
      :folder-tree="folderTree"
      :current-folder-id="currentFolderId"
      :is-folder-mode="isFolderUploadMode"
      :mode="addFilesMode"
      @success="onFileUploadSuccess"
    />

    <div class="kb-layout">
      <a-tabs
        v-model:activeKey="activeTab"
        tab-position="left"
        class="kb-tabs"
        :tabBarStyle="{ width: '168px' }"
      >
        <template #rightExtra>
          <a-tooltip title="检索配置" placement="right">
            <a-button type="text" class="config-btn" @click="openSearchConfigModal">
              <SettingOutlined />
              <span class="config-text">检索配置</span>
            </a-button>
          </a-tooltip>
        </template>

        <!-- 知识文档 -->
        <a-tab-pane key="docs">
          <template #tab>
            <span class="kb-tab"><FileText :size="16" /><span>知识文档</span></span>
          </template>
          <div class="docs-pane">
            <KnowledgeBaseCard />
            <!-- 待处理文件提示条 -->
            <div class="info-panel" v-if="pendingParseCount > 0 || pendingIndexCount > 0">
              <div class="banner-item" v-if="pendingParseCount > 0" @click="confirmBatchParse">
                <FileText :size="14" />
                <span>{{ pendingParseCount }} 个文件待解析，点击解析</span>
              </div>
              <div class="banner-item" v-if="pendingIndexCount > 0" @click="confirmBatchIndex">
                <Database :size="14" />
                <span>{{ pendingIndexCount }} 个文件待入库，点击入库</span>
              </div>
            </div>
            <FileTable class="docs-table" @show-add-files-modal="showAddFilesModal" />
          </div>
        </a-tab-pane>

        <!-- 检索测试 -->
        <a-tab-pane key="query">
          <template #tab>
            <span class="kb-tab"><Search :size="16" /><span>检索测试</span></span>
          </template>
          <QuerySection ref="querySectionRef" :visible="true" @toggle-visible="() => {}" />
        </a-tab-pane>

        <!-- 知识图谱（仅 LightRAG） -->
        <a-tab-pane key="graph" v-if="isGraphSupported">
          <template #tab>
            <span class="kb-tab"><Network :size="16" /><span>知识图谱</span></span>
          </template>
          <KnowledgeGraphSection
            :visible="true"
            :active="activeTab === 'graph'"
            @toggle-visible="() => {}"
          />
        </a-tab-pane>

        <!-- 知识导图 -->
        <a-tab-pane key="mindmap">
          <template #tab>
            <span class="kb-tab"><MapIcon :size="16" /><span>知识导图</span></span>
          </template>
          <MindMapSection v-if="databaseId" :database-id="databaseId" ref="mindmapSectionRef" />
        </a-tab-pane>

        <!-- RAG评估（仅 Milvus，含评估基准） -->
        <a-tab-pane key="evaluation" v-if="isEvaluationSupported">
          <template #tab>
            <span class="kb-tab"><LineChart :size="16" /><span>RAG评估</span></span>
          </template>
          <div class="evaluation-pane">
            <div class="eval-section eval-benchmarks">
              <div class="eval-section-title">评估基准</div>
              <div class="eval-section-body">
                <EvaluationBenchmarks
                  v-if="databaseId"
                  :database-id="databaseId"
                  @benchmark-selected="() => {}"
                  @refresh="() => {}"
                />
              </div>
            </div>
            <div class="eval-section eval-result">
              <div class="eval-section-title">评估结果</div>
              <div class="eval-section-body">
                <RAGEvaluationTab
                  v-if="databaseId"
                  :database-id="databaseId"
                  @switch-to-benchmarks="() => {}"
                />
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDatabaseStore } from '@/stores/database'
import { useTaskerStore } from '@/stores/tasker'
import { FileText, Database, Search, Network, Map as MapIcon, LineChart } from 'lucide-vue-next'
import { SettingOutlined } from '@ant-design/icons-vue'
import { Modal } from 'ant-design-vue'
import KnowledgeBaseCard from '@/components/KnowledgeBaseCard.vue'
import FileTable from '@/components/FileTable.vue'
import FileDetailModal from '@/components/FileDetailModal.vue'
import FileUploadModal from '@/components/FileUploadModal.vue'
import KnowledgeGraphSection from '@/components/KnowledgeGraphSection.vue'
import QuerySection from '@/components/QuerySection.vue'
import MindMapSection from '@/components/MindMapSection.vue'
import RAGEvaluationTab from '@/components/RAGEvaluationTab.vue'
import EvaluationBenchmarks from '@/components/EvaluationBenchmarks.vue'
import SearchConfigModal from '@/components/SearchConfigModal.vue'

const route = useRoute()
const store = useDatabaseStore()
const taskerStore = useTaskerStore()

const databaseId = computed(() => store.databaseId)
const database = computed(() => store.database)
// 计算属性：是否支持知识图谱
const isGraphSupported = computed(() => {
  const kbType = database.value.kb_type?.toLowerCase()
  return kbType === 'lightrag'
})

// 计算属性：是否支持评估功能
const isEvaluationSupported = computed(() => {
  const kbType = database.value.kb_type?.toLowerCase()
  return kbType === 'milvus'
})

// 计算待解析文件数量（status: 'uploaded'）
const pendingParseCount = computed(() => {
  const files = store.database.files || {}
  return Object.values(files).filter((f) => !f.is_folder && f.status === 'uploaded').length
})

// 计算待入库文件数量（status: 'parsed' 或 'error_indexing'）
const pendingIndexCount = computed(() => {
  const files = store.database.files || {}
  const isLightRAG = database.value?.kb_type?.toLowerCase() === 'lightrag'
  return Object.values(files).filter((f) => {
    if (f.is_folder) return false
    if (isLightRAG) {
      return f.status === 'parsed'
    }
    return f.status === 'parsed' || f.status === 'error_indexing'
  }).length
})

// 确认批量解析
const confirmBatchParse = () => {
  const fileIds = Object.values(store.database.files || {})
    .filter((f) => f.status === 'uploaded')
    .map((f) => f.file_id)

  if (fileIds.length === 0) {
    return
  }

  Modal.confirm({
    title: '批量解析',
    content: `确定要解析 ${fileIds.length} 个文件吗？`,
    onOk: () => store.parseFiles(fileIds)
  })
}

// 确认批量入库
const confirmBatchIndex = () => {
  const isLightRAG = database.value?.kb_type?.toLowerCase() === 'lightrag'
  const fileIds = Object.values(store.database.files || {})
    .filter((f) => {
      if (f.is_folder) return false
      if (isLightRAG) return f.status === 'parsed'
      return f.status === 'parsed' || f.status === 'error_indexing'
    })
    .map((f) => f.file_id)

  if (fileIds.length === 0) {
    return
  }

  if (isLightRAG) {
    Modal.confirm({
      title: '批量入库',
      content: `确定要入库 ${fileIds.length} 个文件吗？`,
      onOk: () => store.indexFiles(fileIds)
    })
    return
  }

  // 非 LightRAG：触发 FileTable 的入库流程
  // 暂时简单处理，直接调用 store.indexFiles
  Modal.confirm({
    title: '批量入库',
    content: `确定要入库 ${fileIds.length} 个文件吗？`,
    onOk: () => store.indexFiles(fileIds)
  })
}

// Tab 切换逻辑 - 默认展示知识文档
const activeTab = ref('docs')

// 思维导图引用
const mindmapSectionRef = ref(null)

// 查询区域引用
const querySectionRef = ref(null)

const resetGraphStats = () => {
  store.graphStats = {
    total_nodes: 0,
    total_edges: 0,
    displayed_nodes: 0,
    displayed_edges: 0,
    is_truncated: false
  }
}

// 切换知识库或类型变化时，回到知识文档；当前 tab 不再支持时也回退
watch(
  () => [databaseId.value, isGraphSupported.value, isEvaluationSupported.value],
  ([newDbId, supported, evaluationSupported], oldValue = []) => {
    const [oldDbId, previouslySupported] = oldValue

    if (!newDbId) {
      return
    }

    if (newDbId !== oldDbId) {
      resetGraphStats()
      activeTab.value = 'docs'
      return
    }

    if (!supported && previouslySupported) {
      resetGraphStats()
    }

    if (!supported && activeTab.value === 'graph') {
      activeTab.value = 'docs'
    }

    if (!evaluationSupported && activeTab.value === 'evaluation') {
      activeTab.value = 'docs'
    }
  },
  { immediate: true }
)

// 检索配置弹窗
const searchConfigModalVisible = ref(false)

const handleSearchConfigSave = () => {
  store.getDatabaseInfo()
}

// 打开检索配置弹窗
const openSearchConfigModal = () => {
  searchConfigModalVisible.value = true
}

// 添加文件弹窗
const addFilesModalVisible = ref(false)
const currentFolderId = ref(null)
const isFolderUploadMode = ref(false)
const addFilesMode = ref('file')

// 标记是否是初次加载
const isInitialLoad = ref(true)

// 显示添加文件弹窗
const showAddFilesModal = (options = {}) => {
  const { isFolder = false, mode = 'file' } = options
  isFolderUploadMode.value = isFolder
  addFilesMode.value = mode
  addFilesModalVisible.value = true
  currentFolderId.value = null // 重置
}

// 传递给 FileUploadModal 的文件夹树
const folderTree = computed(() => {
  // 复用 FileTable 中构建文件树的逻辑，或者从 store 中获取
  // 简单起见，这里假设 store.database.files 是扁平列表，我们在 FileTable 中已经有了构建好的树
  // 但 FileTable 是子组件，最好将树的构建逻辑放到 store 或 composable 中，或者在这里重新构建
  // 既然 FileTable 中已经实现了 buildFileTree，我们可以考虑将其提取出来
  // 为了快速实现，我们这里简单实现一个仅用于选择的树构建
  const files = store.database.files || {}
  const fileList = Object.values(files)

  // 构建树的简化版逻辑 (只关心文件夹)
  const nodeMap = new Map()
  const roots = []

  // 1. 初始化节点
  fileList.forEach((file) => {
    if (file.is_folder) {
      const item = { ...file, title: file.filename, value: file.file_id, children: [] }
      nodeMap.set(file.file_id, item)
    }
  })

  // 2. 构建层级
  fileList.forEach((file) => {
    if (file.is_folder && file.parent_id && nodeMap.has(file.parent_id)) {
      const parent = nodeMap.get(file.parent_id)
      const child = nodeMap.get(file.file_id)
      if (parent && child) {
        parent.children.push(child)
      }
    } else if (file.is_folder && !file.parent_id) {
      // 只有显式根文件夹才放入 roots
      // 对于隐式路径生成的文件夹，目前简化处理暂不支持在上传时选择（因为它们没有物理ID）
      // 除非我们复用 FileTable 的复杂逻辑。
      // 如果用户只用新建文件夹功能创建文件夹，那么逻辑是够用的。
      if (nodeMap.has(file.file_id)) {
        roots.push(nodeMap.get(file.file_id))
      }
    }
  })

  return roots
})

// 文件上传成功回调
const onFileUploadSuccess = () => {
  taskerStore.loadTasks()
}

// 重置文件选中状态
const resetFileSelectionState = () => {
  store.selectedRowKeys = []
  store.selectedFile = null
  store.state.fileDetailModalVisible = false
}

watch(
  () => route.params.database_id,
  async (newId, oldId) => {
    // 切换知识库时，标记为初次加载
    isInitialLoad.value = true

    store.databaseId = newId
    resetFileSelectionState()
    resetGraphStats()
    store.stopAutoRefresh()
    await store.getDatabaseInfo(newId, false) // Explicitly load query params on initial load
    store.startAutoRefresh()
  },
  { immediate: true }
)

// 监听文件列表变化，自动更新思维导图和生成示例问题
const previousFileCount = ref(0)

watch(
  () => database.value?.files,
  (newFiles, oldFiles) => {
    if (!newFiles) return

    const newFileCount = Object.keys(newFiles).length
    const oldFileCount = previousFileCount.value

    // 首次加载时，只更新计数，不触发任何操作
    if (isInitialLoad.value) {
      previousFileCount.value = newFileCount
      isInitialLoad.value = false
      return
    }

    // 如果文件数量发生变化（增加或减少），只重新生成问题，不自动生成思维导图
    if (newFileCount !== oldFileCount) {
      const changeType = newFileCount > oldFileCount ? '增加' : '减少'
      console.log(`文件数量从 ${oldFileCount} ${changeType}到 ${newFileCount}，准备重新生成问题`)

      // 只要有文件，就重新生成问题（无论之前是否有问题）
      if (newFileCount > 0) {
        setTimeout(async () => {
          console.log('文件数量变化，检查是否需要生成问题，querySectionRef:', querySectionRef.value)
          if (querySectionRef.value) {
            // 检查是否开启了自动生成问题
            if (database.value.additional_params?.auto_generate_questions) {
              console.log('开始重新生成问题...')
              await querySectionRef.value.generateSampleQuestions(true)
            } else {
              console.log('自动生成问题已关闭，跳过生成')
            }
          } else {
            console.warn('querySectionRef 未准备好，稍后重试')
            // 如果组件还没准备好，再等一会儿
            setTimeout(async () => {
              if (querySectionRef.value) {
                if (database.value.additional_params?.auto_generate_questions) {
                  console.log('延迟后开始生成问题...')
                  await querySectionRef.value.generateSampleQuestions(true)
                } else {
                  console.log('自动生成问题已关闭，跳过生成')
                }
              }
            }, 2000)
          }
        }, 3000) // 等待3秒让后端处理完成
      } else {
        // 如果文件数量变为0，清空问题列表
        console.log('文件数量为0，清空问题列表')
        setTimeout(() => {
          if (querySectionRef.value) {
            // 清空问题列表
            querySectionRef.value.clearQuestions()
          }
        }, 1000)
      }
    }

    previousFileCount.value = newFileCount
  },
  { deep: true }
)

// 组件挂载时启动示例轮播
onMounted(() => {
  store.databaseId = route.params.database_id
  resetFileSelectionState()
  store.getDatabaseInfo()
  store.startAutoRefresh()
})

// 组件卸载时停止示例轮播
onUnmounted(() => {
  store.stopAutoRefresh()
})
</script>

<style lang="less" scoped>
.db-main-container {
  display: flex;
  width: 100%;
}

.ant-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.auto-refresh-control {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 6px;

  span {
    color: var(--gray-700);
    font-weight: 500;
    font-size: 14px;
  }

  .ant-switch {
    &.ant-switch-checked {
      background-color: var(--main-color);
    }
  }
}

/* 左侧 Tab 布局 */
.kb-layout {
  height: 100vh;
  background-color: var(--gray-0);
  overflow: hidden;
}

.kb-tabs {
  height: 100%;
  overflow: hidden;

  :deep(.ant-tabs-content),
  :deep(.ant-tabs-content-holder) {
    height: 100%;
    overflow: hidden;
  }

  :deep(.ant-tabs-tabpane) {
    height: 100%;
    overflow: hidden;
  }

  /* 左侧导航栏 */
  :deep(.ant-tabs-nav) {
    margin: 0;
    padding: 10px 8px;
    background: var(--gray-25);
    border-right: 1px solid var(--gray-150);
  }

  :deep(.ant-tabs-nav-list) {
    gap: 2px;
  }

  :deep(.ant-tabs-tab) {
    margin: 0 !important;
    padding: 9px 12px;
    border-radius: 8px;
    transition:
      background 0.15s,
      color 0.15s;

    + .ant-tabs-tab {
      margin: 0 !important;
    }

    .kb-tab {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      color: var(--gray-700);
      line-height: 1;

      svg {
        color: var(--gray-500);
        flex-shrink: 0;
      }
    }

    &:hover .kb-tab,
    &:hover .kb-tab svg {
      color: var(--gray-900);
    }
  }

  :deep(.ant-tabs-tab-active) {
    background: var(--main-50);

    .kb-tab,
    .kb-tab svg {
      color: var(--main-color);
      font-weight: 500;
    }
  }

  /* 隐藏默认的滑动指示条，用背景块表达选中态 */
  :deep(.ant-tabs-ink-bar) {
    display: none;
  }

  /* 检索配置：固定在导航栏底部 */
  :deep(.ant-tabs-nav-operations) {
    display: none;
  }

  :deep(.ant-tabs-extra-content) {
    margin-top: auto;
    padding-top: 8px;
    border-top: 1px solid var(--gray-150);
  }
}

/* 知识文档页 */
.docs-pane {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px;
  overflow: hidden;

  .docs-table {
    flex: 1;
    min-height: 0;
  }
}

.info-panel {
  background: var(--gray-10);
  border-radius: 12px;
  border: 1px solid var(--gray-200);
  display: flex;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 8px;
  flex-shrink: 0;

  .banner-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--color-info-50);
    border-left: 3px solid var(--color-info-500);
    border-radius: 2px;
    font-size: 13px;
    color: var(--color-info-700);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: var(--color-info-100);
    }

    svg {
      color: var(--color-info-500);
    }
  }
}

/* RAG评估页：上下分区同屏 */
.evaluation-pane {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .eval-section {
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }

  .eval-benchmarks {
    flex: 0 0 40%;
    border-bottom: 1px solid var(--gray-200);
  }

  .eval-result {
    flex: 1;
  }

  .eval-section-title {
    flex-shrink: 0;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--gray-700);
    background: var(--gray-25);
    border-bottom: 1px solid var(--gray-150);
  }

  .eval-section-body {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
}

.config-btn {
  width: 100%;
  color: var(--gray-600);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  padding: 9px 12px;
  height: auto;
  border-radius: 8px;
  transition: all 0.15s;

  &:hover {
    color: var(--main-color);
    background-color: var(--gray-100);
  }

  .config-text {
    font-size: 14px;
  }
}

/* Table row selection styling */
:deep(.ant-table-tbody > tr.ant-table-row-selected > td) {
  background-color: var(--main-5);
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: var(--main-5);
}
</style>

<style lang="less">
/* 全局样式作为备用方案 */
.ant-popover .query-params-compact {
  width: 220px;
}

.ant-popover .query-params-compact .params-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80px;
}

.ant-popover .query-params-compact .params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

.ant-popover .query-params-compact .param-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
}

.ant-popover .query-params-compact .param-item label {
  font-weight: 500;
  color: var(--gray-700);
  margin-right: 8px;
}

/* Improve panel transitions */
.panel-section {
  display: flex;
  flex-direction: column;
  border-radius: 4px;
  transition: all 0.3s;
  min-height: 0;

  &.collapsed {
    height: 36px;
    flex: none;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 1px solid var(--gray-150);
    background-color: var(--gray-25);

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .section-title {
      font-size: 14px;
      font-weight: 500;
      color: var(--gray-700);
      margin: 0;
    }

    .panel-actions {
      display: flex;
      gap: 0px;
    }
  }

  .content {
    flex: 1;
    min-height: 0;
  }
}

.query-section,
.graph-section {
  .panel-section();

  .content {
    padding: 8px;
    flex: 1;
    overflow: hidden;
  }
}
</style>
