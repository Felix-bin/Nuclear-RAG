# OceanBase 迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将应用关系型数据库从 PostgreSQL（asyncpg）替换为 OceanBase（MySQL 协议，aiomysql），通过 Docker Compose 容器统一管理，全新建表。

**Architecture:** 保留 SQLAlchemy async + 单例 `PostgresManager` 与共享 Base 的 `create_all` 建表机制，仅替换驱动、连接串、数据库容器；删除 PG 专有的补列 SQL 与方言判断；把 MySQL 不支持的部分唯一索引降级为普通索引（唯一性已由应用层 `set_default` 保证）。

**Tech Stack:** Python 3.12+ / SQLAlchemy 2.0 async / aiomysql / OceanBase CE（MySQL 模式）/ Docker Compose

设计依据：[docs/superpowers/specs/2026-06-16-oceanbase-migration-design.md](../specs/2026-06-16-oceanbase-migration-design.md)

---

## 文件清单

| 文件 | 改动 |
| --- | --- |
| `pyproject.toml` | 依赖 `asyncpg` → `aiomysql` |
| `uv.lock` | 重新生成 |
| `src/storage/postgres/manager.py` | 连接串环境变量改名、删除 `is_postgresql`、删除 `ensure_knowledge_schema` |
| `server/utils/lifespan.py` | 移除 `ensure_knowledge_schema()` 调用 |
| `src/storage/postgres/models_business.py` | `AgentConfig` 部分唯一索引降级为普通索引 |
| `docker/oceanbase/init.sql` | 新建：自动建库 SQL |
| `docker-compose.yml` | postgres 服务 → oceanbase；api 的 env/depends_on/NO_PROXY |
| `docker-compose.prod.yml` | 同上（无 api depends_on postgres，仅改 env 与服务块） |

---

## Task 1: 替换 Python 依赖

**Files:**
- Modify: `pyproject.toml:8`
- Modify: `uv.lock`

- [ ] **Step 1: 修改 pyproject.toml 依赖**

把第 8 行的：
```toml
    "asyncpg>=0.30.0",
```
改为：
```toml
    "aiomysql>=0.2.0",
```

- [ ] **Step 2: 重新生成锁文件**

Run: `docker compose exec api uv lock`
（若容器未起，本地有 uv 也可直接 `uv lock`）
Expected: `uv.lock` 更新，`aiomysql` 及其依赖 `PyMySQL` 出现在锁文件中，`asyncpg` 被移除。

- [ ] **Step 3: 验证 aiomysql 可导入**

Run: `docker compose exec api uv run python -c "import aiomysql; print(aiomysql.__version__)"`
Expected: 打印版本号，无 ImportError。

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: 关系型数据库驱动 asyncpg 改为 aiomysql"
```

---

## Task 2: 改造 PostgresManager（连接串/方言/补列）

**Files:**
- Modify: `src/storage/postgres/manager.py`

- [ ] **Step 1: 修改环境变量名**

将第 31 行：
```python
    KB_DATABASE_URL_ENV = "POSTGRES_URL"
```
改为：
```python
    KB_DATABASE_URL_ENV = "DATABASE_URL"
```

- [ ] **Step 2: 删除 `ensure_knowledge_schema` 方法**

删除整段方法（当前第 102-165 行，`async def ensure_knowledge_schema(self):` 到其 `await conn.execute(text(stmt))` 循环结束）。删除后该方法不再存在。

- [ ] **Step 3: 删除 `is_postgresql` 属性**

删除整段（当前第 167-172 行）：
```python
    @property
    def is_postgresql(self) -> bool:
        """检查是否是 PostgreSQL 数据库"""
        if not self._initialized:
            return False
        return self.async_engine.dialect.name == "postgresql"
```

- [ ] **Step 4: 清理无用 import 与措辞**

确认删除 `ensure_knowledge_schema` 后 `from sqlalchemy import text` 是否仍被使用：在文件内搜索 `text(`。
- 若 `execute()` 等其他方法未用到 `text`，删除第 7 行 `from sqlalchemy import text`。
- 否则保留。

将第 47-48 行错误日志中的 "PostgreSQL 连接字符串" 改为通用表述：
```python
                "请在 docker-compose.yml 或 .env 中配置数据库连接字符串"
```

- [ ] **Step 5: 验证文件可导入**

Run: `docker compose exec api uv run python -c "from src.storage.postgres.manager import pg_manager; print('ok')"`
Expected: 打印 `ok`，无 AttributeError/ImportError。

- [ ] **Step 6: Commit**

```bash
git add src/storage/postgres/manager.py
git commit -m "refactor: manager 改用 DATABASE_URL，移除 PG 专有补列与方言判断"
```

---

## Task 3: 移除 lifespan 中的补列调用

**Files:**
- Modify: `server/utils/lifespan.py:19`

- [ ] **Step 1: 删除 ensure_knowledge_schema 调用**

将第 16-21 行：
```python
    try:
        pg_manager.initialize()
        await pg_manager.create_business_tables()
        await pg_manager.ensure_knowledge_schema()
    except Exception as e:
        logger.error(f"Failed to initialize database during startup: {e}")
```
改为：
```python
    try:
        pg_manager.initialize()
        await pg_manager.create_business_tables()
    except Exception as e:
        logger.error(f"Failed to initialize database during startup: {e}")
```

- [ ] **Step 2: 验证导入**

Run: `docker compose exec api uv run python -c "import server.utils.lifespan; print('ok')"`
Expected: 打印 `ok`。

- [ ] **Step 3: Commit**

```bash
git add server/utils/lifespan.py
git commit -m "refactor: 启动流程移除 PG 专有补列调用"
```

---

## Task 4: AgentConfig 部分唯一索引降级

**Files:**
- Modify: `src/storage/postgres/models_business.py:144-153`

**背景：** MySQL/OceanBase 不支持带 WHERE 的部分唯一索引；`postgresql_where` 在 MySQL 方言下被忽略，`unique=True` 会退化为对 `(department_id, agent_id)` 的普通唯一索引，禁止同一部门同一 agent 多份配置。唯一性已由 `AgentConfigRepository.set_default()` 在应用层保证，故降级为普通非唯一索引。

- [ ] **Step 1: 修改索引定义**

将第 144-153 行：
```python
    __table_args__ = (
        UniqueConstraint("department_id", "agent_id", "name", name="uq_agent_configs_department_agent_name"),
        Index(
            "uq_agent_configs_department_agent_default",
            "department_id",
            "agent_id",
            unique=True,
            postgresql_where=is_default.is_(True),
        ),
    )
```
改为：
```python
    __table_args__ = (
        UniqueConstraint("department_id", "agent_id", "name", name="uq_agent_configs_department_agent_name"),
        Index(
            "ix_agent_configs_department_agent",
            "department_id",
            "agent_id",
        ),
    )
```

- [ ] **Step 2: 验证导入与元数据**

Run:
```bash
docker compose exec api uv run python -c "from src.storage.postgres.models_business import AgentConfig; print([i.name for i in AgentConfig.__table__.indexes])"
```
Expected: 输出包含 `ix_agent_configs_department_agent`，不再含 `uq_agent_configs_department_agent_default`。

- [ ] **Step 3: Commit**

```bash
git add src/storage/postgres/models_business.py
git commit -m "fix: AgentConfig 部分唯一索引降级为普通索引（MySQL 兼容）"
```

---

## Task 5: OceanBase 初始化 SQL

**Files:**
- Create: `docker/oceanbase/init.sql`

- [ ] **Step 1: 新建建库 SQL**

创建 `docker/oceanbase/init.sql`，内容：
```sql
CREATE DATABASE IF NOT EXISTS nuclearag DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

- [ ] **Step 2: Commit**

```bash
git add docker/oceanbase/init.sql
git commit -m "chore: OceanBase 初始化建库 SQL"
```

---

## Task 6: docker-compose.yml 替换数据库服务

**Files:**
- Modify: `docker-compose.yml`（api env 第 28 行、depends_on 第 52-58 行、NO_PROXY 第 41-42 行、postgres 服务块第 183-202 行）

- [ ] **Step 1: 替换 api 的数据库连接环境变量**

将第 28 行：
```yaml
      - POSTGRES_URL=${POSTGRES_URL:-postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-yuxi_know}}
```
改为：
```yaml
      - DATABASE_URL=${DATABASE_URL:-mysql+aiomysql://root:${OB_PASSWORD:-}@oceanbase:2881/${OB_DATABASE:-nuclearag}}
```

- [ ] **Step 2: 更新 NO_PROXY 列表**

第 41-42 行把 `graph` 等同级位置加入 `oceanbase`（保持原有项），将两行中的服务名列表追加 `,oceanbase`。例如：
```yaml
      - NO_PROXY=localhost,127.0.0.1,milvus,graph,oceanbase,milvus-minio,milvus-etcd-dev,etcd,minio,mineru,paddlex,api.siliconflow.cn
      - no_proxy=localhost,127.0.0.1,milvus,graph,oceanbase,milvus-minio,milvus-etcd-dev,etcd,minio,mineru,paddlex,api.siliconflow.cn
```

- [ ] **Step 3: 更新 api 的 depends_on**

将第 52-54 行：
```yaml
    depends_on:
      postgres:
        condition: service_healthy
```
改为：
```yaml
    depends_on:
      oceanbase:
        condition: service_healthy
```

- [ ] **Step 4: 替换 postgres 服务块为 oceanbase**

将第 183-202 行整个 `postgres:` 服务块替换为：
```yaml
  oceanbase:
    image: oceanbase/oceanbase-ce:4.3.5-lts
    container_name: oceanbase
    ports:
      - "2881:2881"
    environment:
      - MODE=mini
      - OB_TENANT_PASSWORD=${OB_PASSWORD:-}
      - TZ=${TZ:-Asia/Shanghai}
    volumes:
      - ./docker/volumes/oceanbase:/root/ob
      - ./docker/oceanbase/init.sql:/root/boot/init.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "obclient -h127.0.0.1 -P2881 -uroot -e 'SELECT 1' || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 30
      start_period: 180s
    networks:
      - app-network
    restart: unless-stopped
```

> 注意：`init.sql` 挂载点 `/root/boot/init.d/` 是 oceanbase-ce 镜像约定的启动后执行目录。执行本步骤时先 `docker compose up -d oceanbase`，再用 Step 6 验证；若该版本镜像目录约定不同（查 `docker logs oceanbase` 与镜像文档），调整挂载点或改为容器内手动 `CREATE DATABASE`。

- [ ] **Step 5: 启动数据库容器**

Run: `docker compose up -d oceanbase`
然后等待健康：`docker inspect --format '{{.State.Health.Status}}' oceanbase`（轮询直到 `healthy`，约 1-2 分钟）。
Expected: 最终输出 `healthy`。

- [ ] **Step 6: 验证库已自动创建**

Run: `docker compose exec oceanbase obclient -h127.0.0.1 -P2881 -uroot -e "SHOW DATABASES" `
Expected: 输出中包含 `nuclearag`。若不包含，按 Step 4 注意事项调整挂载点后重建容器。

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: docker-compose 用 OceanBase 替换 PostgreSQL"
```

---

## Task 7: docker-compose.prod.yml 同步替换

**Files:**
- Modify: `docker-compose.prod.yml`（api env 第 19 行、postgres 服务块第 155-174 行）

- [ ] **Step 1: 替换 api 数据库连接环境变量**

将第 19 行：
```yaml
      - POSTGRES_URL=${POSTGRES_URL:-postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-yuxi_know}}
```
改为：
```yaml
      - DATABASE_URL=${DATABASE_URL:-mysql+aiomysql://root:${OB_PASSWORD:-}@oceanbase:2881/${OB_DATABASE:-nuclearag}}
```

- [ ] **Step 2: 替换 postgres 服务块**

将第 155-174 行整个 `postgres:` 服务块替换为（与 Task 6 Step 4 相同的 oceanbase 块）：
```yaml
  oceanbase:
    image: oceanbase/oceanbase-ce:4.3.5-lts
    container_name: oceanbase
    ports:
      - "2881:2881"
    environment:
      - MODE=mini
      - OB_TENANT_PASSWORD=${OB_PASSWORD:-}
      - TZ=${TZ:-Asia/Shanghai}
    volumes:
      - ./docker/volumes/oceanbase:/root/ob
      - ./docker/oceanbase/init.sql:/root/boot/init.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "obclient -h127.0.0.1 -P2881 -uroot -e 'SELECT 1' || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 30
      start_period: 180s
    networks:
      - app-network
    restart: unless-stopped
```

- [ ] **Step 3: Commit**

```bash
git add docker-compose.prod.yml
git commit -m "feat: prod compose 用 OceanBase 替换 PostgreSQL"
```

---

## Task 8: 端到端验证

**Files:** 无（仅运行验证）

- [ ] **Step 1: 重建并启动全栈**

Run: `docker compose up -d --build`
等待 api 健康：`docker inspect --format '{{.State.Health.Status}}' api-dev`（轮询至 `healthy`）。
Expected: api-dev 最终 `healthy`。

- [ ] **Step 2: 检查启动日志无数据库错误**

Run: `docker logs api-dev --tail 100`
Expected: 出现 "PostgreSQL manager initialized" 类日志，无 "Failed to initialize database during startup"，无连接/方言报错。

- [ ] **Step 3: 验证表已建出**

Run: `docker compose exec oceanbase obclient -h127.0.0.1 -P2881 -uroot -Dnuclearag -e "SHOW TABLES"`
Expected: 列出 `users`、`departments`、`conversations`、`messages`、`knowledge_bases`、`knowledge_files`、`agent_configs`、`mcp_servers`、`tasks` 等表。

- [ ] **Step 4: 验证登录（用户表读写）**

Run（用 .env 中的 YUXI_SUPER_ADMIN_NAME/PASSWORD 替换占位）:
```bash
curl -s -X POST http://localhost:5050/api/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=$YUXI_SUPER_ADMIN_NAME&password=$YUXI_SUPER_ADMIN_PASSWORD"
```
Expected: 返回包含 `access_token` 的 JSON。

- [ ] **Step 5: 验证 AgentConfig 多份配置（§4.3 索引降级正确性）**

在 api 容器内执行脚本，验证同一 (department_id, agent_id) 可插入多份配置且不报唯一约束冲突：
```bash
docker compose exec api uv run python - <<'PY'
import asyncio
from src.storage.postgres.manager import pg_manager
from src.storage.postgres.models_business import Department
from src.repositories.agent_config_repository import AgentConfigRepository

async def main():
    pg_manager.initialize()
    async with pg_manager.get_async_session_context() as s:
        # 临时部门，满足 AgentConfig.department_id 外键
        dept = Department(name="_ob_test_dept")
        s.add(dept)
        await s.commit()
        await s.refresh(dept)

        repo = AgentConfigRepository(s)
        await repo.create(department_id=dept.id, agent_id="t_ob", name="cfg-A", is_default=True)
        b = await repo.create(department_id=dept.id, agent_id="t_ob", name="cfg-B", is_default=False)
        await repo.set_default(config=b)
        items = await repo.list_by_department_agent(department_id=dept.id, agent_id="t_ob")
        print("count=", len(items), "defaults=", sum(1 for i in items if i.is_default))

        # 清理：先删配置（无级联），再删部门
        for i in items:
            await s.delete(i)
        await s.delete(dept)
        await s.commit()

asyncio.run(main())
PY
```
Expected: 打印 `count= 2 defaults= 1`（两份配置共存，且恰好一份为默认）。

- [ ] **Step 6: 运行 lint**

Run: `make lint`
Expected: 通过，无新增错误。

- [ ] **Step 7: 最终提交（如有验证脚本残留改动则清理；通常无需提交）**

确认工作区无意外改动：`git status`

---

## 文档更新检查

- [ ] 检查 `docs/latest` 中提及 PostgreSQL 连接配置的文档（如 `docs/latest/intro/quick-start.md`、`docs/latest/advanced/misc.md`），将 PostgreSQL/POSTGRES_URL 描述更新为 OceanBase/DATABASE_URL。
- [ ] 检查 `README.md` 中数据库相关说明并同步更新。
- 仅在确实存在相关描述时更新，避免无关改动。
