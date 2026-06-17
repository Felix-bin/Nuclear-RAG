# -*- coding: utf-8 -*-
"""根据项目真实代码生成"代码截图"，风格与报告中已有截图(图4-x)保持一致：
白底卡片 + slate 描边 + blue-50 标题栏 + 等宽字体 + 行号。"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "shots")
os.makedirs(OUT, exist_ok=True)

# ---- 风格常量（采样自报告现有截图）----
BG = (255, 255, 255)
BORDER = (203, 213, 225)        # slate-300
TITLE_BG = (239, 246, 255)      # blue-50
TITLE_FG = (30, 58, 138)        # blue-900
CODE_FG = (15, 23, 42)          # slate-900
COMMENT_FG = (135, 139, 148)    # 灰色注释
GUTTER_FG = (148, 163, 184)     # slate-400 行号
GUTTER_LINE = (226, 232, 240)   # slate-200 分隔线

FONT_REG = "C:/Windows/Fonts/consola.ttf"
FONT_BOLD = "C:/Windows/Fonts/consolab.ttf"
SIZE = 30
LH = 44                         # 行高
PAD_X = 26
PAD_TOP = 18
PAD_BOT = 18
TITLE_H = 60

FONT_CJK = "C:/Windows/Fonts/msyh.ttc"   # 微软雅黑，用于中文注释回退

font = ImageFont.truetype(FONT_REG, SIZE)
font_b = ImageFont.truetype(FONT_BOLD, SIZE)
font_t = ImageFont.truetype(FONT_BOLD, 26)
font_cjk = ImageFont.truetype(FONT_CJK, SIZE - 2)
font_t_cjk = ImageFont.truetype(FONT_CJK, 24)

# 字符宽度（等宽）
_tmp = Image.new("RGB", (10, 10))
_d = ImageDraw.Draw(_tmp)
CW = _d.textlength("M", font=font)


def _is_cjk(ch):
    return ord(ch) > 0x2E00


def draw_mixed(d, xy, text, fill, ascii_font, cjk_font):
    """逐字符绘制，非 ASCII 字符使用中文字体回退，返回总宽度。"""
    x, y = xy
    start = x
    for ch in text:
        f = cjk_font if _is_cjk(ch) else ascii_font
        # 中文基线略低，微调使其与等宽字体对齐
        oy = 3 if _is_cjk(ch) else 0
        d.text((x, y + oy), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f)
    return x - start


def measure_mixed(text, ascii_font, cjk_font):
    return sum(_d.textlength(c, font=(cjk_font if _is_cjk(c) else ascii_font)) for c in text)


def split_comment(line, lang):
    """返回 (code_part, comment_part)。仅做简单整行/行尾注释切分。"""
    s = line.lstrip()
    indent = line[: len(line) - len(s)]
    if lang in ("py", "yaml"):
        if s.startswith("#"):
            return "", line
        m = re.search(r"(\s+#\s.*)$", line)
        if m:
            return line[: m.start()], line[m.start():]
    if lang == "js":
        if s.startswith("//"):
            return "", line
        m = re.search(r"(\s+//\s.*)$", line)
        if m and "://" not in line[max(0, m.start() - 1): m.start() + 3]:
            return line[: m.start()], line[m.start():]
    return line, ""


def render(title, code, lang, filename):
    lines = code.rstrip("\n").split("\n")
    n = len(lines)
    gutter_digits = len(str(n))
    gutter_w = int(CW * (gutter_digits + 1)) + 24
    code_w = int(max((measure_mixed(l, font, font_cjk) for l in lines), default=200)) + 36
    W = gutter_w + code_w + PAD_X
    H = TITLE_H + PAD_TOP + n * LH + PAD_BOT

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # 卡片描边
    d.rectangle([0, 0, W - 1, H - 1], outline=BORDER, width=1)
    # 标题栏
    d.rectangle([1, 1, W - 2, TITLE_H], fill=TITLE_BG)
    d.line([1, TITLE_H, W - 2, TITLE_H], fill=BORDER, width=1)
    draw_mixed(d, (PAD_X, (TITLE_H - 26) // 2 + 1), f"code-{title}",
               TITLE_FG, font_t, font_t_cjk)
    # 行号分隔线
    gx = gutter_w
    d.line([gx, TITLE_H + 1, gx, H - 2], fill=GUTTER_LINE, width=1)

    y = TITLE_H + PAD_TOP
    for i, line in enumerate(lines, 1):
        num = str(i)
        nx = gutter_w - 14 - d.textlength(num, font=font)
        d.text((nx, y), num, font=font, fill=GUTTER_FG)
        code_part, comment_part = split_comment(line, lang)
        x = gx + 18
        if code_part:
            x += draw_mixed(d, (x, y), code_part, CODE_FG, font, font_cjk)
        if comment_part:
            draw_mixed(d, (x, y), comment_part, COMMENT_FG, font, font_cjk)
        y += LH

    img.save(os.path.join(OUT, filename))
    print("saved", filename, img.size)


SHOTS = []

SHOTS.append(("src/models/chat.py", "py", "shot_llm_chat.png", r'''class OpenAIBase:
    def __init__(self, api_key, base_url, model_name, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        # 使用 OpenAI 兼容协议初始化异步客户端
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=1, max=10),
           reraise=True)
    async def call(self, message, stream=False):
        messages = [{"role": "user", "content": message}] \
            if isinstance(message, str) else message
        if stream:
            return self._stream_response(messages)
        return await self._get_response(messages)

    async def _stream_response(self, messages):
        response = await self.client.chat.completions.create(
            model=self.model_name, messages=messages, stream=True,
        )
        async for chunk in response:          # 逐 token 流式返回增量
            if len(chunk.choices) > 0:
                yield chunk.choices[0].delta'''))

SHOTS.append(("src/models/embed.py", "py", "shot_llm_embed.png", r'''async def aencode(self, message: list[str] | str) -> list[list[float]]:
    if isinstance(message, str):
        message = [message]
    payload = {"model": self.model, "input": message}
    # 通过 httpx 异步调用 Embedding 服务（OpenAI / Ollama 兼容）
    async with httpx.AsyncClient() as client:
        response = await client.post(self.base_url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["embeddings"]'''))

SHOTS.append(("server/routers/chat_router.py", "py", "shot_stream_backend.png", r'''@chat.post("/agent/{agent_id}")
async def chat_agent(
    agent_id: str,
    query: str = Body(...),
    config: dict = Body({}),
    meta: dict = Body({}),
    image_content: str | None = Body(None),
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """使用特定智能体进行对话（需要登录）"""
    if not meta.get("request_id"):
        meta["request_id"] = str(uuid.uuid4())
    # 以 HTTP 流式响应逐块下发问答内容（NDJSON）
    return StreamingResponse(
        stream_agent_chat(
            agent_id=agent_id, query=query, config=config, meta=meta,
            image_content=image_content, current_user=current_user, db=db,
        ),
        media_type="application/json",
    )'''))

SHOTS.append(("web/src/composables/useAgentStreamHandler.js", "js", "shot_stream_frontend.png", r'''const processStreamResponse = async (response, onChunk) => {
  const reader = response.body.getReader()   // 获取可读流读取器
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')          // 按行切分 NDJSON
    buffer = lines.pop() || ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      const chunk = JSON.parse(trimmed)        // 解析单个数据块
      if (onChunk && onChunk(chunk)) return    // 增量渲染并按需中断
    }
  }
}'''))

SHOTS.append(("src/knowledge/implementations/milvus.py", "py", "shot_milvus.png", r'''# Milvus 连接配置（读取环境变量）
self.milvus_token = os.getenv("MILVUS_TOKEN") or ""
self.milvus_uri = os.getenv("MILVUS_URI") or "http://localhost:19530"
self.milvus_db = "yuxi_know"
self.connection_alias = f"milvus_{hashstr(work_dir, 6)}"

def _init_connection(self):
    """初始化 Milvus 连接"""
    # 建立到 Milvus 向量数据库的连接
    connections.connect(alias=self.connection_alias,
                        uri=self.milvus_uri, token=self.milvus_token)
    # 创建数据库（若不存在）并切换
    if self.milvus_db not in db.list_database():
        db.create_database(self.milvus_db)
    db.using_database(self.milvus_db)
    logger.info(f"Connected to Milvus at {self.milvus_uri}")'''))

SHOTS.append(("src/knowledge/adapters/base.py", "py", "shot_neo4j.png", r'''def _connect(self):
    """建立 Neo4j 连接"""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "0123456789")

    # 使用 Bolt 协议创建驱动并校验连通性
    self.driver = GD.driver(uri, auth=(username, password))
    with self.driver.session() as session:
        session.run("RETURN 1")
    self.status = "open"
    logger.info("Successfully connected to Neo4j")'''))

SHOTS.append(("src/storage/postgres/manager.py", "py", "shot_postgres.png", r'''def initialize(self):
    """初始化数据库连接"""
    db_url = os.getenv(self.KB_DATABASE_URL_ENV)   # POSTGRES_URL
    # 创建异步 SQLAlchemy 引擎
    self.async_engine = create_async_engine(
        db_url,
        json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
        json_deserializer=json.loads,
        pool_pre_ping=True,      # 取连接前心跳检测
        pool_recycle=1800,       # 连接回收时间（秒）
    )
    # 创建异步会话工厂
    self.AsyncSession = async_sessionmaker(
        bind=self.async_engine, class_=AsyncSession,
        expire_on_commit=False,
    )
    self._initialized = True'''))

SHOTS.append(("src/storage/minio/client.py", "py", "shot_minio.png", r'''def __init__(self):
    """初始化 MinIO 客户端配置"""
    self.endpoint = os.getenv("MINIO_URI") or "http://milvus-minio:9000"
    self.access_key = os.getenv("MINIO_ACCESS_KEY") or "minioadmin"
    self.secret_key = os.getenv("MINIO_SECRET_KEY") or "minioadmin"
    self._client = None

@property
def client(self) -> Minio:
    """获取 S3 兼容的 MinIO 客户端实例（懒加载）"""
    if self._client is None:
        endpoint = self.endpoint.split("://")[-1]
        self._client = Minio(endpoint=endpoint,
                            access_key=self.access_key,
                            secret_key=self.secret_key, secure=False)
    return self._client'''))

SHOTS.append(("src/services/mcp_service.py", "py", "shot_mcp.png", r'''async def load_mcp_servers_from_db() -> None:
    """从数据库加载所有启用的 MCP 服务配置到缓存"""
    global MCP_SERVERS
    from src.storage.postgres.manager import pg_manager
    async with pg_manager.get_async_session_context() as session:
        result = await session.execute(
            select(MCPServer).filter(MCPServer.enabled == 1))
        servers = result.scalars().all()
        async with _mcp_lock:                 # 异步锁保护共享缓存
            MCP_SERVERS.clear()
            for server in servers:
                MCP_SERVERS[server.name] = server.to_mcp_config()
    logger.info(f"Loaded {len(MCP_SERVERS)} MCP servers")'''))

SHOTS.append(("server/main.py", "py", "shot_fastapi.png", r'''app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/api")   # 统一以 /api 前缀注册路由

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
# 中间件栈：访问日志 / 登录限流 / 统一鉴权
app.add_middleware(AccessLogMiddleware)
app.add_middleware(LoginRateLimitMiddleware)
app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050, reload=True)'''))

if __name__ == "__main__":
    for title, lang, fn, code in SHOTS:
        render(title, code, lang, fn)
    print("ALL DONE ->", OUT)
