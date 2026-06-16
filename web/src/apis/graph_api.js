import { apiGet } from './base'

/**
 * 图数据库API模块
 * 统一图谱接口，供知识库详情页的知识图谱展示使用
 */

// =============================================================================
// === 统一图谱接口 (Unified Graph API) ===
// =============================================================================

export const unifiedApi = {
  /**
   * 获取所有可用的知识图谱列表
   * @returns {Promise} - 图谱列表
   */
  getGraphs: async () => {
    return await apiGet('/api/graph/list', {}, true)
  },

  /**
   * 获取子图数据 (统一接口)
   * @param {Object} params - 查询参数
   * @param {string} params.db_id - 图谱ID
   * @param {string} params.node_label - 节点标签/关键词
   * @param {number} params.max_depth - 最大深度
   * @param {number} params.max_nodes - 最大节点数
   * @returns {Promise} - 子图数据
   */
  getSubgraph: async (params) => {
    const { db_id, node_label = '*', max_depth = 2, max_nodes = 100 } = params

    if (!db_id) {
      throw new Error('db_id is required')
    }

    const queryParams = new URLSearchParams({
      db_id: db_id,
      node_label: node_label,
      max_depth: max_depth.toString(),
      max_nodes: max_nodes.toString()
    })

    return await apiGet(`/api/graph/subgraph?${queryParams.toString()}`, {}, true)
  },

  /**
   * 获取图谱统计信息 (统一接口)
   * @param {string} db_id - 图谱ID
   * @returns {Promise} - 统计信息
   */
  getStats: async (db_id) => {
    if (!db_id) {
      throw new Error('db_id is required')
    }

    const queryParams = new URLSearchParams({
      db_id: db_id
    })

    return await apiGet(`/api/graph/stats?${queryParams.toString()}`, {}, true)
  },

  /**
   * 获取图谱标签列表 (统一接口)
   * @param {string} db_id - 图谱ID
   * @returns {Promise} - 标签列表
   */
  getLabels: async (db_id) => {
    if (!db_id) {
      throw new Error('db_id is required')
    }

    const queryParams = new URLSearchParams({
      db_id: db_id
    })

    return await apiGet(`/api/graph/labels?${queryParams.toString()}`, {}, true)
  }
}
