# -*- coding: utf-8 -*-
"""重新生成"核心架构"章节(图4-1~图4-6)的代码截图：
原截图过长(最高 5258px)，导致 Word 跨页排版不美观。
此处改为紧凑的代表性片段，风格与图5-x 一致，并替换文档中对应图片与显示尺寸。"""
import os
import re
import sys
import shutil

sys.path.insert(0, os.path.dirname(__file__))
import gen_code_shots as g  # 复用渲染与样式
from PIL import Image

WORK = os.path.join(os.path.dirname(__file__), "work")
MEDIA = os.path.join(WORK, "word", "media")
EMU_W = 5486400  # 显示宽度 6 英寸

# (rId, media文件, 标题, 语言, 代码)
SHOTS = [
    ("rId23", "image18.png", "web/src/components/AgentChatComponent.vue", "js", r'''const sendMessage = async ({ agentId, threadId, text, signal, imageData }) => {
  if (!agentId || !threadId || !text) {
    return Promise.reject(new Error('Missing agent, thread, or message text'))
  }
  // 新对话以首条消息内容作为标题
  if ((threadMessages.value[threadId] || []).length === 0) {
    const autoTitle = text.replace(/\s+/g, ' ').trim().slice(0, 255)
    if (autoTitle) void updateThread(threadId, autoTitle).catch(() => {})
  }
  const requestData = {
    query: text,
    config: { thread_id: threadId,
      ...(selectedAgentConfigId.value
        ? { agent_config_id: selectedAgentConfigId.value } : {}) },
  }
  // 携带图片实现多模态输入
  if (imageData && imageData.imageContent) {
    requestData.image_content = imageData.imageContent
  }
  // 调用流式问答接口
  return await agentApi.sendAgentMessage(
    agentId, requestData, signal ? { signal } : undefined)
}'''),

    ("rId24", "image19.png", "web/src/apis/knowledge_api.js", "js", r'''// 知识库管理 API 模块
export const databaseApi = {
  getDatabases: async () => {
    return apiAdminGet('/api/knowledge/databases')
  },
  createDatabase: async (databaseData) => {
    return apiAdminPost('/api/knowledge/databases', databaseData)
  },
  getDatabaseInfo: async (dbId) => {
    return apiAdminGet(`/api/knowledge/databases/${dbId}`)
  },
  updateDatabase: async (dbId, updateData) => {
    return apiAdminPut(`/api/knowledge/databases/${dbId}`, updateData)
  },
  deleteDatabase: async (dbId) => {
    return apiAdminDelete(`/api/knowledge/databases/${dbId}`)
  },
}'''),

    ("rId25", "image20.png", "docker-compose.yml", "yaml", r'''services:
  api:                              # 后端 FastAPI 服务
    build:
      context: .
      dockerfile: docker/api.Dockerfile
    container_name: api-dev
    ports:
      - "5050:5050"
    environment:
      - POSTGRES_URL=postgresql+asyncpg://postgres:***@postgres:5432/yuxi_know
      - NEO4J_URI=bolt://graph:7687
      - MILVUS_URI=http://milvus:19530
      - MINIO_URI=http://milvus-minio:9000
    command: uv run uvicorn server.main:app --host 0.0.0.0 --port 5050
    depends_on:                     # 声明服务依赖与启动顺序
      postgres:
        condition: service_healthy
      milvus:
        condition: service_healthy
      minio:
        condition: service_healthy'''),

    ("rId26", "image21.png", "server/routers/knowledge_router.py", "py", r'''knowledge = APIRouter(prefix="/knowledge", tags=["knowledge"])

@knowledge.get("/databases")
async def get_databases(current_user: User = Depends(get_admin_user)):
    """获取所有知识库（根据用户权限过滤）"""
    user_info = {"role": current_user.role,
                 "department_id": current_user.department_id}
    return await knowledge_base.get_databases_by_user(user_info)

@knowledge.post("/databases")
async def create_database(
    database_name: str = Body(...),
    description: str = Body(...),
    embed_model_name: str = Body(...),
    kb_type: str = Body("lightrag"),
    current_user: User = Depends(get_admin_user),
):
    """创建知识库"""
    # 创建并返回新建的知识库信息
    return await knowledge_base.create_database(...)'''),

    ("rId27", "image22.png", "src/services/chat_stream_service.py", "py", r'''async def stream_agent_chat(*, agent_id, query, config, meta, **kw):

    def make_chunk(content=None, **kwargs):
        # 每个数据块为一行 JSON（NDJSON）
        return json.dumps(
            {"request_id": meta.get("request_id"),
             "response": content, **kwargs},
            ensure_ascii=False).encode("utf-8") + b"\n"

    yield make_chunk(status="init", meta=meta, msg=init_msg)
    # 逐条消费 LangGraph 流式消息并下发增量
    async for msg, metadata in agent.stream_messages(messages, ...):
        if isinstance(msg, AIMessageChunk):
            yield make_chunk(content=msg.content, msg=msg.model_dump(),
                             metadata=metadata, status="loading")
        else:
            yield make_chunk(msg=msg.model_dump(),
                             metadata=metadata, status="loading")'''),

    ("rId28", "image23.png", "src/storage/postgres/models_knowledge.py", "py", r'''class KnowledgeBase(Base):
    """知识库实体模型"""
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    db_id = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    kb_type = Column(String(32), nullable=False, index=True)
    embed_info = Column(JSON_VALUE)
    created_at = Column(DateTime(timezone=True), default=utc_now_naive)


class KnowledgeBaseRepository:
    async def get_all(self) -> list[KnowledgeBase]:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(KnowledgeBase))
            return list(result.scalars().all())

    async def get_by_id(self, db_id: str) -> KnowledgeBase | None:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.db_id == db_id))
            return result.scalar_one_or_none()'''),
]

if __name__ == "__main__":
    # 1) 生成紧凑截图（输出到 g.OUT），再覆盖到 work/media
    new_cy = {}
    for rid, media, title, lang, code in SHOTS:
        g.render(title, code, lang, "ch4_" + media)
        src = os.path.join(g.OUT, "ch4_" + media)
        shutil.copy(src, os.path.join(MEDIA, media))
        w, h = Image.open(src).size
        new_cy[rid] = int(EMU_W * h / w)

    # 2) 更新 document.xml 中对应 drawing 的显示尺寸
    doc = os.path.join(WORK, "word", "document.xml")
    xml = open(doc, encoding="utf-8").read()
    for rid, cy in new_cy.items():
        pos = xml.index(f'r:embed="{rid}"')
        start = xml.rfind("<w:drawing>", 0, pos)
        end = xml.index("</w:drawing>", pos)
        block = xml[start:end]
        block = re.sub(r'<wp:extent cx="\d+" cy="\d+"/>',
                       f'<wp:extent cx="{EMU_W}" cy="{cy}"/>', block, count=1)
        block = re.sub(r'<a:ext cx="\d+" cy="\d+"/>',
                       f'<a:ext cx="{EMU_W}" cy="{cy}"/>', block, count=1)
        xml = xml[:start] + block + xml[end:]
    open(doc, "w", encoding="utf-8").write(xml)
    print("updated extents:", {k: v for k, v in new_cy.items()})
