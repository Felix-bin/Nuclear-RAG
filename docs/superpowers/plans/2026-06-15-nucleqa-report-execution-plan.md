# NucleQA 课程设计报告执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于现有项目与课程模板，产出一份内容完整、结构美观、图文可信、可直接提交的《应用软件架构课程设计报告》DOCX。

**Architecture:** 先固定素材目录和证据清单，再分别完成架构图生成、真实截图采集、正文撰写、DOCX 填充与版式校验。所有论述均以仓库真实实现为依据，AI 仅用于生成抽象架构图，不替代功能和代码证据。

**Tech Stack:** PowerShell, `uv`, Python (`python-docx`, `zipfile`/XML), Word DOCX, PackyAPI `gpt-image-2`, LibreOffice/Poppler（如可用）

---

## 文件结构

- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\应用软件架构课程设计报告模板.docx`
  - 原始课程模板，将被读取并复制为最终交付文档
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx`
  - 最终提交版报告
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\`
  - 报告插图、截图、代码截图输出目录
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\`
  - `gpt-image-2` 生成的技术图、业务图、部署图、数据流图
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\`
  - 功能页面截图、代码截图、配置截图
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\`
  - 中间文件、渲染页、临时脚本输出
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-evidence.md`
  - 报告证据清单，记录每一节使用的来源文件与截图对象
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md`
  - 报告逐节正文草稿
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\diagram-prompts.md`
  - 架构图生成提示词与图示要素清单
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\docx_fill_report.md`
  - DOCX 填充过程记录，便于核对遗漏项
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\rendered-pages\`
  - 渲染后的报告页面图片

### Task 1: 建立输出目录与模板副本

**Files:**
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx`

- [ ] **Step 1: 创建报告工作目录**

Run:

```powershell
New-Item -ItemType Directory -Force `
  'C:\Users\HP\Desktop\Nuclear-RAG\output\doc' `
  'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets' `
  'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams' `
  'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots' `
  'C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs'
```

Expected: PowerShell 返回 5 个目录对象，`Mode` 含 `d----`。

- [ ] **Step 2: 复制模板为最终工作文档**

Run:

```powershell
Copy-Item `
  'C:\Users\HP\Desktop\Nuclear-RAG\应用软件架构课程设计报告模板.docx' `
  'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx' `
  -Force
```

Expected: 无报错；目标文件存在，大小大于 100 KB。

- [ ] **Step 3: 验证模板副本已就位**

Run:

```powershell
Get-Item 'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx' |
  Select-Object FullName, Length, LastWriteTime
```

Expected: 输出目标路径、非零文件大小和最新修改时间。

### Task 2: 生成报告证据清单与章节大纲

**Files:**
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-evidence.md`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\README.md`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\docs\latest\intro\project-overview.md`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\docs\latest\intro\knowledge-base.md`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\docs\latest\intro\quick-start.md`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\pyproject.toml`

- [ ] **Step 1: 盘点可用证据来源**

Run:

```powershell
rg -n "LangGraph|Milvus|Neo4j|MinIO|FastAPI|Vue|知识库|图谱|问答|权限|反馈|任务" `
  README.md docs\latest\intro\project-overview.md docs\latest\intro\knowledge-base.md `
  docs\latest\intro\quick-start.md pyproject.toml
```

Expected: 输出多条命中，覆盖技术栈、知识库、图谱、问答与权限等关键词。

- [ ] **Step 2: 写入证据清单**

Write `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-evidence.md` with:

```markdown
# 报告证据清单

## 功能实现展示
- 智能问答与引用溯源：README.md，web/src/components/AgentChatComponent.vue，server/routers/chat_router.py
- 知识库创建与文档入库：docs/latest/intro/knowledge-base.md，server/routers/knowledge_router.py，web/src/apis/knowledge_api.js
- 图谱可视化：docs/latest/intro/knowledge-base.md，web/src/components/GraphCanvas.vue，server/routers/graph_router.py
- 历史/反馈/任务：src/services/feedback_service.py，src/services/task_service.py，web/src/components/TaskCenterDrawer.vue
- 权限管理：server/routers/auth_router.py，server/utils/auth_middleware.py，web/src/components/DepartmentManagementComponent.vue

## 技术架构图
- README.md
- docs/latest/intro/project-overview.md
- pyproject.toml
- docker-compose.yml

## 业务架构图
- docs/latest/intro/knowledge-base.md
- server/routers/*.py
- src/services/*.py

## 核心架构设计
- 功能点 A：知识库文档上传-解析-入库
- 功能点 B：RAG 问答-检索-生成-溯源
```

- [ ] **Step 3: 写入报告章节大纲**

Write `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md` with:

```markdown
# 报告正文大纲

1. 功能实现展示
   - 1.1 智能问答与引用溯源
   - 1.2 知识库创建、文档上传与解析入库
   - 1.3 知识图谱/LightRAG 图谱可视化
   - 1.4 对话历史、反馈与任务管理
   - 1.5 部门、用户与知识库权限控制
2. 技术角度的技术架构图
   - 2.1 总体技术架构
   - 2.2 部署与运行时组件
3. 业务角度的业务架构图
   - 3.1 用户问答业务流
   - 3.2 知识生命周期业务流
4. 核心架构设计
   - 4.1 前端表示层
   - 4.2 后端架构与接口层
   - 4.3 业务服务层
   - 4.4 数据操作与存储层
5. 接口技术的使用
   - 5.1 大模型/聊天接口接入
   - 5.2 向量检索或图数据库接口接入
6. 结论
7. 参考文献
```

- [ ] **Step 4: 验证清单与大纲已生成**

Run:

```powershell
Get-Content 'C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-evidence.md'
Get-Content 'C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md'
```

Expected: 两个文件内容完整显示，无空白占位项。

### Task 3: 编写架构图提示词并生成 AI 图示

**Files:**
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\diagram-prompts.md`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\*.png`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\docker-compose.yml`

- [ ] **Step 1: 写入图示要素与提示词**

Write `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\diagram-prompts.md` with:

```markdown
# 图示提示词

## 图 1 总体技术架构图
科研学术风格软件架构图，白底，蓝灰配色，横向布局，展示 Nuclear-RAG / NucleQA 系统的总体技术架构。左侧为用户与浏览器，中间为 Vue 3 + Vite 前端层，后接 FastAPI 后端服务层，后端内部标注 LangGraph 智能体编排、知识库管理、文档解析、问答服务、权限与审计模块；右侧为 PostgreSQL、Milvus、Neo4j、MinIO、本地或远程 LLM 服务；底部标注 Docker Compose 运行环境。使用整洁箭头和模块框，不要插画风，不要 3D，不要海报风，适合课程报告插图。

## 图 2 部署与运行时组件图
科研学术风格部署图，白底，简洁配色，展示 Docker Compose 下的 web-dev、api-dev、postgres、milvus、neo4j、minio 等容器及其通信关系，带端口和职责标签，强调前后端分离、存储分层、RAG 运行链路。

## 图 3 用户问答业务架构图
科研学术风格业务架构图，白底，结构清晰，展示用户提问、前端交互、问答接口、检索增强、知识图谱增强、答案生成、引用溯源、反馈闭环之间的业务流程；模块名称使用中文，箭头标注请求、检索、生成、引用、反馈。

## 图 4 知识生命周期业务架构图
科研学术风格业务处理图，白底，蓝灰配色，展示文档上传、对象存储、OCR/解析、文本分块、Embedding、Milvus 入库、LightRAG/Neo4j 图谱构建、知识库管理、后续问答调用之间的全生命周期流程。
```

- [ ] **Step 2: 生成总体技术架构图**

Run:

```powershell
uv run C:\Users\HP\.codex\skills\gpt-image-2\scripts\generate_image.py `
  --prompt "科研学术风格软件架构图，白底，蓝灰配色，横向布局，展示 Nuclear-RAG / NucleQA 系统的总体技术架构。左侧为用户与浏览器，中间为 Vue 3 + Vite 前端层，后接 FastAPI 后端服务层，后端内部标注 LangGraph 智能体编排、知识库管理、文档解析、问答服务、权限与审计模块；右侧为 PostgreSQL、Milvus、Neo4j、MinIO、本地或远程 LLM 服务；底部标注 Docker Compose 运行环境。使用整洁箭头和模块框，不要插画风，不要 3D，不要海报风，适合课程报告插图。" `
  --filename "C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\2026-06-15-technical-architecture.png" `
  --size 2k-landscape --quality high
```

Expected: 命令输出 `MEDIA:` 行，目标 PNG 文件生成。

- [ ] **Step 3: 生成其余三张架构图**

Run the same script three more times with filenames:

```text
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\2026-06-15-deployment-architecture.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\2026-06-15-business-qa-flow.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams\2026-06-15-business-knowledge-flow.png
```

Expected: 4 张 PNG 均存在，文件大小均大于 200 KB。

- [ ] **Step 4: 验证架构图文件已生成**

Run:

```powershell
Get-ChildItem 'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\diagrams' |
  Select-Object Name, Length
```

Expected: 输出 4 个 PNG 文件，均有非零大小。

### Task 4: 采集真实功能截图与代码证据

**Files:**
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\*.png`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\web\src\components\AgentChatComponent.vue`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\server\routers\chat_router.py`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\server\routers\knowledge_router.py`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\web\src\components\GraphCanvas.vue`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\src\services\feedback_service.py`

- [ ] **Step 1: 列出核心代码文件以便截图**

Run:

```powershell
rg --files `
  web/src/components/AgentChatComponent.vue `
  server/routers/chat_router.py `
  server/routers/knowledge_router.py `
  web/src/components/GraphCanvas.vue `
  src/services/feedback_service.py `
  src/services/task_service.py `
  server/utils/auth_middleware.py
```

Expected: 输出上述文件的实际路径。

- [ ] **Step 2: 启动项目或确认已有服务可供截图**

Run:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected: 若 `web-dev`、`api-dev` 等已运行则直接复用；若未运行，则后续执行 `docker compose up -d`。

- [ ] **Step 3: 采集真实页面截图**

Use in-app Browser or Playwright to capture:

```text
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\feature-chat.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\feature-knowledge-base.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\feature-graph.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\feature-task-feedback.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\feature-auth-department.png
```

Expected: 5 张页面截图清晰可读，能体现各功能界面与核心控件。

- [ ] **Step 4: 采集代码与配置截图**

Capture code screenshots for:

```text
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\code-chat-router.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\code-knowledge-router.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\code-feedback-service.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\code-agent-chat-component.png
C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots\code-storage-config.png
```

Expected: 每张图包含足够上下文，可读出函数名、接口路径或组件职责。

- [ ] **Step 5: 验证截图资产完整**

Run:

```powershell
Get-ChildItem 'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\screenshots' |
  Select-Object Name, Length
```

Expected: 至少 10 张 PNG 文件存在。

### Task 5: 撰写报告正文草稿

**Files:**
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-evidence.md`

- [ ] **Step 1: 写出功能实现展示正文**

Replace `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md` section 1 with complete prose covering:

```markdown
## 一、功能实现展示

### 1. 智能问答与引用溯源
系统面向核电知识问答场景提供自然语言交互界面。用户输入问题后，前端将请求发送至后端问答接口，系统结合知识库内容、图谱关联和模型能力生成回答，并在界面中显示引用来源、章节或文档依据。该功能体现了系统“可回答”和“可追溯”两项核心能力，避免仅给出不可验证的生成式结果。
```

Then continue with all five planned features in the same formal style.

- [ ] **Step 2: 写出技术架构与业务架构分析正文**

Append complete prose for sections 2 and 3 including:

```markdown
## 二、技术角度的技术架构图
本系统采用典型的前后端分离与多存储协同架构。表示层由 Vue 3 与 Vite 构建，负责问答交互、知识库管理、图谱展示和系统配置；服务层由 FastAPI 提供 REST 接口，并通过 LangGraph 组织复杂问答流程；数据层同时使用 PostgreSQL、Milvus、Neo4j 与 MinIO，分别承担结构化数据、向量检索、图谱关系与原始文件存储职责。
```

Expected: 章节 2 和 3 的正文均为完整段落，不是图片标题列表。

- [ ] **Step 3: 写出核心架构设计与接口技术正文**

Append complete prose for sections 4, 5, 6, 7 including:

```markdown
## 四、核心架构设计
本节选择“知识库文档上传-解析-入库”和“RAG 问答-检索-生成-溯源”两个功能点进行说明，以体现系统在表示层、服务层、业务层和数据层之间的协同设计。
```

Expected: section 4 covers front-end, router/API, service, and data/storage by mapping them to the two chosen features.

- [ ] **Step 4: 验证正文草稿覆盖所有章节**

Run:

```powershell
Get-Content 'C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\report-outline.md'
```

Expected: 文稿包含 1-7 节完整内容，无“待补充”“按要求填写”等字样。

### Task 6: 将正文与图片填入 DOCX

**Files:**
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx`
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\docx_fill_report.md`

- [ ] **Step 1: 记录 DOCX 填充策略**

Write `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\docx_fill_report.md` with:

```markdown
# DOCX 填充记录

- 保留封面和任务书表格
- 从“一、功能实现展示(30分)”开始替换占位段落
- 每个功能点插入对应页面截图
- 技术架构与业务架构章节分别插入 2 张图，并补图题
- 核心架构设计按前端、接口、业务层、数据层顺序插入代码截图与文字
- 接口技术使用选择 2 项真实接口能力展开
```

- [ ] **Step 2: 使用 python-docx 将正文和图片写入目标 DOCX**

Run a Python script via `uv` that:

```python
from docx import Document
from docx.shared import Inches

doc = Document(r"C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx")
# 定位占位段落，从第一章开始逐段替换
# 读取 tmp/docs/report-outline.md 中的正文
# 在对应章节位置插入图片：
# technical-architecture.png
# deployment-architecture.png
# business-qa-flow.png
# business-knowledge-flow.png
# feature-chat.png 等
# 保存回目标 DOCX
doc.save(r"C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx")
```

Expected: 脚本执行成功，目标 DOCX 修改时间更新。

- [ ] **Step 3: 验证模板占位语已被清理**

Run:

```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem
$path='C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx'
$zip=[System.IO.Compression.ZipFile]::OpenRead($path)
$entry=$zip.GetEntry('word/document.xml')
$sr=New-Object System.IO.StreamReader($entry.Open())
$xmlText=$sr.ReadToEnd()
$sr.Close()
$zip.Dispose()
$xmlText | Select-String '在此处按要求填写|功能截图和介绍|采用的主要架构技术描述'
```

Expected: 无命中，或仅保留作为标题要求而非空白占位。

### Task 7: 渲染并检查版式

**Files:**
- Create: `C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\rendered-pages\`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx`

- [ ] **Step 1: 检查渲染工具是否可用**

Run:

```powershell
Get-Command soffice,pdftoppm -ErrorAction SilentlyContinue
```

Expected: 若两者都存在，继续使用渲染链路；若缺失，记录风险并至少做文本结构验证。

- [ ] **Step 2: 将 DOCX 渲染为 PDF 并输出页面图片**

Run:

```powershell
soffice -env:UserInstallation=file:///C:/Users/HP/Desktop/Nuclear-RAG/tmp/docs/lo_profile `
  --headless --convert-to pdf `
  --outdir C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs `
  C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx

pdftoppm -png `
  C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\NucleQA-应用软件架构课程设计报告.pdf `
  C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\rendered-pages\page
```

Expected: 生成 PDF 和多页 PNG。

- [ ] **Step 3: 检查分页与图文布局**

Inspect rendered pages for:

```text
- 标题是否断裂
- 图片是否溢出页边距
- 图题是否紧邻图片
- 表格与正文是否重叠
- 代码截图是否清晰
```

Expected: 若发现问题，返回 Task 6 微调后重新渲染。

- [ ] **Step 4: 验证渲染结果存在**

Run:

```powershell
Get-ChildItem 'C:\Users\HP\Desktop\Nuclear-RAG\tmp\docs\rendered-pages' |
  Select-Object Name, Length
```

Expected: 至少输出 5 页以上 PNG。

### Task 8: 最终核查与交付

**Files:**
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx`
- Modify: `C:\Users\HP\Desktop\Nuclear-RAG\output\doc\assets\`

- [ ] **Step 1: 核对交付清单**

Run:

```powershell
Get-ChildItem 'C:\Users\HP\Desktop\Nuclear-RAG\output\doc' -Recurse |
  Select-Object FullName
```

Expected: 至少包含最终 DOCX、图示目录、截图目录。

- [ ] **Step 2: 核对评分点覆盖**

Check manually against this checklist:

```markdown
- [ ] 4-6 个功能点已展示
- [ ] 至少 1 个业务实体关联场景已覆盖
- [ ] 技术架构图已给出
- [ ] 业务架构图已给出
- [ ] 2 个核心功能点的前端/接口/业务/数据层分析已给出
- [ ] 2 项接口技术使用已给出
- [ ] 结论与参考文献已补齐
```

Expected: 7 项全部勾选通过。

- [ ] **Step 3: 记录最终验证结果**

Run:

```powershell
Get-Item 'C:\Users\HP\Desktop\Nuclear-RAG\output\doc\NucleQA-应用软件架构课程设计报告.docx' |
  Select-Object FullName, Length, LastWriteTime
```

Expected: 输出最终文件路径与最新时间，可作为交付依据。

## 自检

- 规格覆盖：设计稿中的章节、图示、功能点、核心功能分析、接口技术使用、版式验证均已映射到任务。
- 占位检查：本计划未使用 “TBD” 或 “后续补充” 之类占位词。
- 一致性检查：所有输出路径统一落在 `output/doc` 与 `tmp/docs` 下，执行顺序由取证到生成再到填充和验证，前后命名一致。
