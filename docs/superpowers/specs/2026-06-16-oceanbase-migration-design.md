# 关系型数据库迁移：PostgreSQL → OceanBase 设计文档

- 日期：2026-06-16
- 状态：待评审
- 范围：将应用自身的关系型数据库从 PostgreSQL 替换为 OceanBase（MySQL 协议，端口 2881）

## 1. 背景与目标

当前应用通过 SQLAlchemy async + `asyncpg` 驱动连接 PostgreSQL，由单例 `PostgresManager`（[src/storage/postgres/manager.py](../../../src/storage/postgres/manager.py)）统一管理连接，承载用户、部门、对话历史、知识库元数据、评估结果等全部业务数据。

目标：把这套关系型存储替换为 **OceanBase（MySQL 兼容模式）**，通过 Docker Compose 统一管理，**全新建表、不迁移旧数据**，代码层面**直接改为 MySQL 方言**（不再保留 PG 兼容）。

不在范围内：
- `src/agents/common/toolkits/mysql/`：这是给智能体使用的 MySQL 查询工具，与应用自身存储无关。
- 向量库（Milvus）、图数据库（Neo4j）：不涉及。
- 历史数据迁移。

## 2. 已确认决策

| 决策点 | 选择 |
| --- | --- |
| 部署方式 | 在 docker-compose 中新增 OceanBase 容器，替换 postgres 服务 |
| 数据处理 | 全新开始，不迁移旧数据 |
| 代码策略 | 直接替换为 MySQL 方言，删除 asyncpg |
| 服务/变量命名 | 服务名 `oceanbase`，环境变量 `DATABASE_URL` |
| 补列 SQL | 删除 `ensure_knowledge_schema()`，仅靠 `create_all` 建表 |
| 异步驱动 | `aiomysql`（纯 Python，免编译） |

## 3. 架构改动

### 3.1 连接层

- 驱动：`asyncpg` → `aiomysql`。
- 连接串：`mysql+aiomysql://root:${OB_PASSWORD:-}@oceanbase:2881/nuclearag`（容器内部网络，端口 2881）。
- 数据库名：`nuclearag`。
- 环境变量：`POSTGRES_URL` → `DATABASE_URL`，相关 `POSTGRES_USER/PASSWORD/DB` → `OB_PASSWORD/OB_DATABASE`（见 §4.4）。
- `create_async_engine` 的 `json_serializer/json_deserializer/pool_pre_ping/pool_recycle` 参数对 MySQL 同样适用，保留不变。

### 3.2 数据库容器（docker-compose.yml 与 docker-compose.prod.yml）

- 用 `oceanbase/oceanbase-ce`（4.x）替换 `postgres:16` 服务，服务名与 `container_name` 改为 `oceanbase`。
- 端口映射 `2881:2881`。
- 环境：`MODE=mini`（降低开发资源占用），按镜像约定设置 root 租户口令（`OB_TENANT_PASSWORD`/`OB_PASSWORD`，默认空）。
- **自动建库 `nuclearag`**：通过 OceanBase 容器启动脚本完成。`oceanbase/oceanbase-ce` 镜像支持把初始化 SQL 放入其 boot 脚本目录（如挂载 `CREATE DATABASE nuclearag;` 的 init SQL），具体挂载点以镜像版本约定为准，实现阶段确认。
- 数据卷：`./docker/volumes/oceanbase:/root/ob`（按官方镜像路径为准）。
- healthcheck：OceanBase 启动慢（约 1–2 分钟），用 `mysql`/`obclient` ping 探活，`start_period` 拉长（建议 ≥120s），`retries` 增大。
- 同步更新 api 服务的 `depends_on`（`postgres` → `oceanbase`）与 `NO_PROXY` 列表中的服务名引用。

## 4. 代码改动清单

### 4.1 src/storage/postgres/manager.py

- `KB_DATABASE_URL_ENV = "POSTGRES_URL"` → `"DATABASE_URL"`。
- 删除 `is_postgresql` 属性（无外部调用）。
- 删除 `ensure_knowledge_schema()` 方法（PG 专有语法，全新建表场景下冗余）。
- 日志/注释中的 "PostgreSQL" 措辞按需调整为通用表述。
- **目录与包名 `src/storage/postgres/` 保持不动**（改名会牵动大量 import，违反最小改动原则）。

### 4.2 server/utils/lifespan.py

- 移除对 `ensure_knowledge_schema()` 的调用（[lifespan.py:19](../../../server/utils/lifespan.py#L19)）。
- 保留 `pg_manager.initialize()` 与 `create_business_tables()`（后者经共享 Base 的 `create_all` 建出全部表）。

### 4.3 src/storage/postgres/models_business.py

- `AgentConfig.__table_args__` 中的部分唯一索引 `Index(..., unique=True, postgresql_where=is_default.is_(True))`：
  - 问题：MySQL/OceanBase 不支持带 WHERE 的部分唯一索引；`postgresql_where` 被忽略后会退化为对 `(department_id, agent_id)` 的**普通唯一索引**，从而禁止"同一部门同一 agent 拥有多份配置"。
  - 处理：去掉 `unique=True` 与 `postgresql_where`，降级为普通复合索引（保留用于 `get_default` 查询加速）。
  - 安全性：`AgentConfigRepository.set_default()`（[agent_config_repository.py:29](../../../src/repositories/agent_config_repository.py#L29)）已在应用层保证"每个 (dept, agent) 只有一个 default"，DB 层唯一约束本就是冗余保险，去除不影响正确性。

### 4.4 docker-compose.yml / docker-compose.prod.yml

- 数据库服务块整体替换（见 §3.2）。
- api 服务环境变量：`POSTGRES_URL=...` → `DATABASE_URL=mysql+aiomysql://root:${OB_PASSWORD:-}@oceanbase:2881/${OB_DATABASE:-nuclearag}`。
- `depends_on` 与 `NO_PROXY` 同步更新。

### 4.5 pyproject.toml / uv.lock

- 依赖 `asyncpg>=0.30.0` → `aiomysql>=0.2.0`。
- `uv lock` 重新生成锁文件。

## 5. 不改动的部分（明确排除）

- `JSON_VALUE = JSON().with_variant(JSONB, "postgresql")`（[models_knowledge.py:21](../../../src/storage/postgres/models_knowledge.py#L21)）：非 PG 方言自动退回普通 `JSON`，无需改。
- 各 repository / service 的 SQLAlchemy ORM 查询：方言无关，无需改。
- `server/utils/migrate.py`：旧 SQLite 迁移器，启动流程未调用（死代码），按"不擅自删除无关死代码"原则保留。
- `server/routers/dashboard_router.py` 中的 naive datetime 处理：MySQL 同样要求 naive datetime，保留。
- `src/agents/common/toolkits/mysql/`：智能体工具，与本次无关。

## 6. JSON 字段兼容性说明

- 所有模型已使用 SQLAlchemy 通用 `JSON` 类型（business）或 `JSON_VALUE` 变体（knowledge）。OceanBase MySQL 模式支持 `JSON` 列类型，`create_all` 可正确建表。
- ORM 读写 JSON 字段（如 `extra_metadata`、`config_json`、`payload`）在 MySQL 方言下由 SQLAlchemy 序列化为 JSON 列，行为与 PG 一致。

## 7. 验证标准

1. `docker compose up -d` 后，OceanBase 容器healthcheck 通过，api 容器成功启动无数据库错误日志。
2. 应用首次启动自动建出全部表（用户、部门、对话、知识库、评估、MCP、任务等）。
3. 用 `YUXI_SUPER_ADMIN_NAME/PASSWORD` 登录成功（验证用户表读写）。
4. 创建知识库、发起一次对话（验证知识库元数据 + 对话历史 + JSON 字段读写）。
5. 同一部门同一 agent 下创建 ≥2 份 AgentConfig 并切换 default（验证 §4.3 索引降级后的正确性）。
6. `make lint` 通过。

## 8. 风险与注意

- **OceanBase 启动时延**：bootstrap 较慢，healthcheck 与 `depends_on: service_healthy` 的 `start_period` 必须给足，否则 api 会因依赖未就绪反复重启。
- **建库与口令**：`nuclearag` 库由 OceanBase 容器启动脚本自动创建（实现阶段确认镜像的 init SQL 挂载机制）。root 默认空口令，如镜像要求设置租户口令则通过 `OB_PASSWORD` 注入并同步到连接串。应用走容器内部网络（服务名 `oceanbase:2881`），宿主机连接信息仅供本地调试参考。
- **资源占用**：OceanBase 即便 mini 模式也比 postgres:16 占用更多内存，开发机需留意。
