# -*- coding: utf-8 -*-
"""将生成的代码截图嵌入报告，重写"五、接口技术的使用"章节。"""
import os
import shutil
import re
from PIL import Image

UNPACK = os.path.join(os.path.dirname(__file__), "unpacked")
WORD = os.path.join(UNPACK, "word")
MEDIA = os.path.join(WORD, "media")
SHOTS = os.path.join(os.path.dirname(__file__), "shots")

EMU_W = 5486400  # 图片显示宽度 6 英寸

# 代码截图：(源文件, 目标media名, rId)
code_shots = [
    ("shot_llm_chat.png", "image24.png", "rId29"),
    ("shot_llm_embed.png", "image25.png", "rId30"),
    ("shot_stream_backend.png", "image26.png", "rId31"),
    ("shot_stream_frontend.png", "image27.png", "rId32"),
    ("shot_milvus.png", "image28.png", "rId33"),
    ("shot_neo4j.png", "image29.png", "rId34"),
    ("shot_postgres.png", "image30.png", "rId35"),
    ("shot_minio.png", "image31.png", "rId36"),
    ("shot_mcp.png", "image32.png", "rId37"),
    ("shot_fastapi.png", "image33.png", "rId38"),
]
# 复用已有 UI 截图
reuse = [
    ("image1.png", "rId39"),  # 智能问答界面
    ("image5.png", "rId40"),  # 知识图谱可视化界面
]

# 拷贝代码截图到 media
for src, dst, _ in code_shots:
    shutil.copy(os.path.join(SHOTS, src), os.path.join(MEDIA, dst))

# 计算每个 rId 对应图片显示尺寸
emu = {}
all_imgs = [(r, dst) for src, dst, r in code_shots] + [(r, m) for m, r in reuse]
for rid, name in all_imgs:
    w, h = Image.open(os.path.join(MEDIA, name)).size
    emu[rid] = (EMU_W, int(EMU_W * h / w))


def fig(rid, name):
    cx, cy = emu[rid]
    return f'''    <w:p>
      <w:pPr>
        <w:spacing w:before="160" w:after="0"/>
        <w:jc w:val="center"/>
      </w:pPr>
      <w:r>
        <w:drawing>
          <wp:inline xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <wp:extent cx="{cx}" cy="{cy}"/>
            <wp:docPr id="0" name="{name}"/>
            <wp:cNvGraphicFramePr>
              <a:graphicFrameLocks noChangeAspect="1"/>
            </wp:cNvGraphicFramePr>
            <a:graphic>
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:pic>
                  <pic:nvPicPr>
                    <pic:cNvPr id="0" name="{name}"/>
                    <pic:cNvPicPr/>
                  </pic:nvPicPr>
                  <pic:blipFill>
                    <a:blip r:embed="{rid}"/>
                    <a:stretch><a:fillRect/></a:stretch>
                  </pic:blipFill>
                  <pic:spPr>
                    <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
                    <a:prstGeom prst="rect"/>
                  </pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>
'''


def cap(text):
    return f'''    <w:p>
      <w:pPr>
        <w:spacing w:before="60" w:after="180" w:line="288" w:lineRule="auto"/>
        <w:jc w:val="center"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/><w:b w:val="0"/><w:sz w:val="22"/></w:rPr>
        <w:t>{text}</w:t>
      </w:r>
    </w:p>
'''


def h1(text):
    return f'''    <w:p>
      <w:pPr><w:spacing w:before="200" w:after="80" w:line="288" w:lineRule="auto"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体"/><w:b/><w:sz w:val="32"/></w:rPr><w:t>{text}</w:t></w:r>
    </w:p>
'''


def h2(text):
    return f'''    <w:p>
      <w:pPr><w:spacing w:before="200" w:after="80" w:line="288" w:lineRule="auto"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体"/><w:b/><w:sz w:val="26"/></w:rPr><w:t>{text}</w:t></w:r>
    </w:p>
'''


def p(text):
    return f'''    <w:p>
      <w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:firstLine="480"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体"/><w:sz w:val="24"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>
    </w:p>
'''


parts = []
parts.append(h1("五、接口技术的使用"))
parts.append(p("本节系统梳理项目实际使用的接口技术，并以代码截图与功能截图相结合的方式，说明每类接口的配置方式、调用过程与实现要点。系统涉及的接口技术包括：大模型接口、流式响应接口、向量数据库接口、图数据库接口、关系数据库接口、对象存储接口、MCP 服务接口以及统一 REST API 网关。需要说明的是，系统的实时问答能力通过基于 HTTP 的流式响应（StreamingResponse）实现，而非 WebSocket；同时项目当前未引入 Redis 等独立缓存中间件，会话状态与业务数据统一由 PostgreSQL 与进程内结构承担，因此本节如实围绕项目真实采用的接口技术展开。"))

# 1 LLM
parts.append(h2("1. 大模型接口（OpenAI 兼容协议）"))
parts.append(p("配置方面，大模型聊天能力封装在 src/models/chat.py 的 OpenAIBase 中，通过 AsyncOpenAI 客户端以 OpenAI 兼容协议接入，连接参数 api_key 与 base_url 来自模型配置与环境变量，从而可灵活对接 OpenAI、本地推理服务或第三方兼容网关。"))
parts.append(p("调用与实现方面，call 方法统一封装同步与流式两种模式：流式调用通过 chat.completions.create(stream=True) 逐 token 返回增量内容，并使用 tenacity 的 @retry 实现指数退避重试，保证模型接口在网络抖动时的稳定性，如图5-1 所示。"))
parts.append(fig("rId29", "image24.png"))
parts.append(cap("图5-1 大模型聊天接口客户端初始化与流式调用代码截图"))
parts.append(p("除聊天接口外，系统还需要向量化接口支撑检索。src/models/embed.py 通过 httpx.AsyncClient 以异步 POST 方式调用 Embedding 服务（兼容 OpenAI 与 Ollama 协议），将文本批量转换为向量，作为后续 Milvus 入库与检索的输入，如图5-2 所示。"))
parts.append(fig("rId30", "image25.png"))
parts.append(cap("图5-2 Embedding 向量化接口异步调用代码截图"))
parts.append(p("从功能效果看，大模型接口最终服务于智能问答页面：用户输入问题后，后端组织模型调用与知识检索，并将答案与引用来源回传前端展示，如图5-3 所示。"))
parts.append(fig("rId39", "image1.png"))
parts.append(cap("图5-3 智能问答界面（大模型接口功能效果）"))

# 2 streaming
parts.append(h2("2. 流式响应接口（HTTP Streaming 实时问答通道）"))
parts.append(p("配置与实现方面，问答接口位于 server/routers/chat_router.py，路由 /api/chat/agent/{agent_id} 通过 FastAPI 的 StreamingResponse 返回一个异步生成器，媒体类型为 application/json，逐块下发以换行符分隔的 JSON（NDJSON）数据，每个数据块包含 request_id、状态与增量内容，如图5-4 所示。"))
parts.append(fig("rId31", "image26.png"))
parts.append(cap("图5-4 后端 StreamingResponse 流式响应构建代码截图"))
parts.append(p("前端在 web/src/composables/useAgentStreamHandler.js 中消费该流：通过 fetch 返回体的 response.body.getReader() 获取可读流，使用 TextDecoder 解码并按换行切分缓冲区，逐行解析 JSON 数据块后增量渲染会话内容，如图5-5 所示。"))
parts.append(fig("rId32", "image27.png"))
parts.append(cap("图5-5 前端 ReadableStream 流式解析代码截图"))
parts.append(p("之所以采用 HTTP 流式而非 WebSocket，是因为问答场景的数据流以“服务端到客户端的单向下行”为主，HTTP 流式可直接复用既有的鉴权中间件、CORS 与访问日志，且能被浏览器原生 fetch 直接消费，无需额外维护长连接的心跳与重连逻辑，在满足实时性的同时降低了实现与运维复杂度。"))

# 3 milvus
parts.append(h2("3. 向量数据库 Milvus 接口"))
parts.append(p("配置方面，src/knowledge/implementations/milvus.py 从环境变量读取 MILVUS_URI 与 MILVUS_TOKEN，并使用 connections.connect 建立带连接别名的连接；随后通过 db.create_database 与 db.using_database 完成数据库的创建与切换。调用方面，系统基于 Collection 完成向量的写入、相似度检索与元数据过滤，如图5-6 所示。"))
parts.append(fig("rId33", "image28.png"))
parts.append(cap("图5-6 Milvus 连接配置与初始化代码截图"))

# 4 neo4j
parts.append(h2("4. 图数据库 Neo4j / LightRAG 接口"))
parts.append(p("配置方面，src/knowledge/adapters/base.py 从环境变量读取 NEO4J_URI、NEO4J_USERNAME 与 NEO4J_PASSWORD，通过 Bolt 协议创建驱动并以一次 RETURN 1 查询校验连通性；调用方面，系统借助 driver.session() 上下文执行 Cypher 查询，并由 LightRAG 协同 Milvus 完成知识图谱的构建与检索，如图5-7 所示。"))
parts.append(fig("rId34", "image29.png"))
parts.append(cap("图5-7 Neo4j 驱动连接配置代码截图"))
parts.append(p("从功能效果看，图数据库接口最终支撑知识图谱可视化：用户可在知识库详情页查看图谱节点与关系，辅助跨文档关联分析，如图5-8 所示。"))
parts.append(fig("rId40", "image5.png"))
parts.append(cap("图5-8 知识图谱可视化界面（图数据库接口功能效果）"))

# 5 postgres
parts.append(h2("5. 关系数据库 PostgreSQL 接口"))
parts.append(p("配置方面，src/storage/postgres/manager.py 以单例方式管理数据库连接：从环境变量 POSTGRES_URL 读取连接串，通过 create_async_engine 创建异步引擎，并设置 pool_pre_ping 取连接前心跳检测与 pool_recycle 连接回收时间；随后由 async_sessionmaker 构建异步会话工厂，统一承载用户、权限、对话历史、反馈与审计等业务数据的读写，如图5-9 所示。"))
parts.append(fig("rId35", "image30.png"))
parts.append(cap("图5-9 PostgreSQL 异步引擎与会话工厂配置代码截图"))

# 6 minio
parts.append(h2("6. 对象存储 MinIO（S3 接口）"))
parts.append(p("配置方面，src/storage/minio/client.py 从环境变量读取 MINIO_URI、MINIO_ACCESS_KEY 与 MINIO_SECRET_KEY，并以懒加载方式创建 S3 兼容的 MinIO 客户端；调用方面，系统通过该客户端完成存储桶的检查、原始文档与图片资源的上传与下载，为知识库文档与生成图片提供对象存储支撑，如图5-10 所示。"))
parts.append(fig("rId36", "image31.png"))
parts.append(cap("图5-10 MinIO 客户端配置与懒加载代码截图"))

# 7 mcp
parts.append(h2("7. MCP 服务接口（Model Context Protocol）"))
parts.append(p("系统通过 MCP 协议扩展智能体的外部工具能力。src/services/mcp_service.py 在启动时从 PostgreSQL 的 MCPServer 表加载所有启用的 MCP 服务配置，并以异步锁保护全局缓存；MCP 服务支持 sse、streamable_http 与 stdio 多种传输方式，配置项的增删改查由 server/routers/mcp_router.py 提供 REST 接口，如图5-11 所示。"))
parts.append(fig("rId37", "image32.png"))
parts.append(cap("图5-11 MCP 服务配置加载代码截图"))

# 8 fastapi gateway
parts.append(h2("8. REST API 网关（FastAPI 与中间件）"))
parts.append(p("上述各类接口最终统一收敛到 FastAPI 网关。server/main.py 创建带 lifespan 生命周期的应用，以 /api 前缀注册全部路由，并配置 CORS 跨域；同时通过中间件栈串联访问日志、登录限流与统一鉴权，最后由 uvicorn 以 ASGI 方式启动服务，如图5-12 所示。"))
parts.append(fig("rId38", "image33.png"))
parts.append(cap("图5-12 FastAPI 应用与中间件注册代码截图"))

new_section = "".join(parts)

# 读取 document.xml，替换原章节
doc_path = os.path.join(WORD, "document.xml")
xml = open(doc_path, encoding="utf-8").read()
start = xml.find('<w:p w14:paraId="124A3017">')
six = xml.find("六、结论")
end = xml.rfind("<w:p ", 0, six)
assert start != -1 and end != -1 and start < end, (start, end)
old = xml[start:end]
xml = xml[:start] + new_section + xml[end:]
open(doc_path, "w", encoding="utf-8").write(xml)
print("section replaced, old len", len(old), "new len", len(new_section))

# 追加 relationships
rels_path = os.path.join(WORD, "_rels", "document.xml.rels")
rels = open(rels_path, encoding="utf-8").read()
add = []
for src, dst, rid in code_shots:
    add.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{dst}"/>')
for name, rid in reuse:
    add.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>')
rels = rels.replace("</Relationships>", "".join(add) + "</Relationships>")
open(rels_path, "w", encoding="utf-8").write(rels)
print("rels added", len(add))
