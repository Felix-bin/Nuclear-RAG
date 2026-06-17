<div align="center">

<h1>核智问答 NucleQA</h1>

<h3>基于 RAG 的核电厂知识库问答系统</h3>

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=ffffff)](docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=ffffff)](pyproject.toml)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat&logo=vuedotjs&logoColor=ffffff)](web)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=ffffff)](server)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

## 项目简介

核电站的运行、维修与应急处置高度依赖运行规程、技术规格书、事故导则、经验反馈、设备手册等海量知识。传统人工检索定位慢、跨文档关联弱，专家经验也难以沉淀为组织资产，影响培训效率与应急响应质量。

**核智问答（NucleQA）** 是一套基于检索增强生成（RAG）与本地大语言模型的核电厂知识库问答系统，将多源文档转化为**可检索、可溯源、可审计**的知识服务，实现自然语言提问、规程依据检索、答案生成与安全合规审查，提升知识获取效率，降低因规程理解偏差带来的安全风险。

系统基于 LangGraph v1 + Vue.js + FastAPI + LightRAG 架构构建，融合 RAG 技术与知识图谱技术，完全通过 Docker Compose 管理，支持热重载开发。

## 核心能力

- **知识采集与治理**：接入运行规程、维修规程、定期试验规程、技术规格书、图纸、运行事件报告与经验反馈，支持文档分类、版本标识、权限分级与敏感信息脱敏。
- **文档解析与知识建模**：通过 OCR、版面分析与 NLP 抽取文本、表格、章节、页码等信息；按规程步骤、设备对象、故障现象等维度分块并生成 Embedding 向量；同时构建“系统-设备-规程-事件”的知识图谱关系。
- **RAG 智能问答**：对自然语言问题进行意图识别、关键词扩展与向量检索，召回相关规程片段与图谱关系，组织上下文交由本地 LLM 生成回答，并给出**原文出处、页码与章节**。
- **安全合规护栏**：对问题与回答进行权限校验、敏感词过滤、规程一致性检查与引用完整性检查；对缺少依据的问题明确提示“知识库未检索到可靠依据”，避免模型臆想。
- **反馈与持续优化**：记录问答日志、命中文档、用户评价与专家修订意见，形成“采集—理解—生成—反馈”的知识闭环，持续优化分块、召回与提示词策略。
- **应用功能**：提供 PC 端问答界面，支持知识库后台管理、对话历史、知识溯源、应急场景模拟训练与审计日志查询。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 智能体编排 | LangGraph v1（多智能体、工具调用、中间件） |
| 知识库 / RAG | Embedding + Rerank 检索，Milvus 向量库 |
| 知识图谱 | LightRAG，G6 可视化 |
| 后端 | FastAPI + OceanBase |
| 前端 | Vue 3 + Vite + Ant Design Vue |
| 部署 | Docker Compose（api / web / milvus / oceanbase / graph 等服务） |

## 快速开始

克隆代码并初始化：

```bash
git clone <本仓库地址> Nuclear-RAG
cd Nuclear-RAG

# Linux/macOS
./scripts/init.sh

# Windows PowerShell
.\scripts\init.ps1
```

使用 Docker 启动（api-dev / web-dev 已配置热重载，本地改代码无需重启容器）：

```bash
docker compose up -d --build
```

启动完成后访问 `http://localhost:5173`。

常用调试命令：

```bash
docker ps                       # 查看服务状态
docker logs api-dev --tail 100  # 查看后端日志
make lint                       # 后端代码检查
make format                     # 后端代码格式化
```

## 界面预览

> 截图待补充。

## 致谢

本项目基于开源平台 [Yuxi-Know](https://github.com/xerrors/Yuxi-Know)（MIT 许可证）二次开发，面向核电厂知识库问答场景进行定制改造，特此致谢。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)。
