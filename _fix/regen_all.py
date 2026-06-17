# -*- coding: utf-8 -*-
"""重新生成全部代码截图（去掉标题栏占位 00000000），并按 图号->rId->实际media文件
的稳健映射覆盖，避免依赖 pack 重编号后的文件名。同时按图片真实尺寸更新显示比例。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import gen_code_shots as g
import fix_ch4 as f4
from PIL import Image

WORK = os.path.join(os.path.dirname(__file__), "work")
DOC = os.path.join(WORK, "word", "document.xml")
RELS = os.path.join(WORK, "word", "_rels", "document.xml.rels")
MEDIA = os.path.join(WORK, "word", "media")
EMU_W = 5486400

# 图号前缀 -> 源截图 PNG（在 g.OUT 下）
CAP2SRC = {
    "图4-1": "ch4_image18.png",   # AgentChatComponent.vue
    "图4-2": "ch4_image19.png",   # knowledge_api.js
    "图4-3": "ch4_image20.png",   # docker-compose.yml
    "图4-4": "ch4_image21.png",   # knowledge_router.py
    "图4-5": "ch4_image22.png",   # chat_stream_service.py
    "图4-6": "ch4_image23.png",   # models_knowledge.py
    "图5-1": "shot_llm_chat.png",
    "图5-2": "shot_llm_embed.png",
    "图5-4": "shot_stream_backend.png",
    "图5-5": "shot_stream_frontend.png",
    "图5-6": "shot_milvus.png",
    "图5-7": "shot_neo4j.png",
    "图5-9": "shot_postgres.png",
    "图5-10": "shot_minio.png",
    "图5-11": "shot_mcp.png",
    "图5-12": "shot_fastapi.png",
}

# 1) 生成全部截图到 g.OUT（标题已去掉占位符）
for title, lang, fn, code in g.SHOTS:
    g.render(title, code, lang, fn)
for rid, media, title, lang, code in f4.SHOTS:
    g.render(title, code, lang, "ch4_" + media)

# 2) 解析 caption -> 对应图片的 rId -> media 文件
xml = open(DOC, encoding="utf-8").read()
rels = open(RELS, encoding="utf-8").read()
relmap = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="media/([^"]+)"', rels))

paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
last_rid = None
plan = []  # (cap_prefix, rid, media_file, src_png)
for p in paras:
    emb = re.findall(r'r:embed="(rId\d+)"', p)
    if emb:
        last_rid = emb[0]
    t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip()
    for cap, src in CAP2SRC.items():
        if t.startswith(cap + " ") or t == cap:
            plan.append((cap, last_rid, relmap[last_rid], src))

assert len(plan) == len(CAP2SRC), f"匹配数不符: {len(plan)} != {len(CAP2SRC)}"

# 3) 覆盖 media 文件并更新 extent
import shutil

for cap, rid, media_file, src in plan:
    src_path = os.path.join(g.OUT, src)
    shutil.copy(src_path, os.path.join(MEDIA, media_file))
    w, h = Image.open(src_path).size
    cy = int(EMU_W * h / w)
    pos = xml.index(f'r:embed="{rid}"')
    start = xml.rfind("<w:drawing>", 0, pos)
    end = xml.index("</w:drawing>", pos)
    block = xml[start:end]
    block = re.sub(r'<wp:extent cx="\d+" cy="\d+"/>',
                   f'<wp:extent cx="{EMU_W}" cy="{cy}"/>', block, count=1)
    block = re.sub(r'<a:ext cx="\d+" cy="\d+"/>',
                   f'<a:ext cx="{EMU_W}" cy="{cy}"/>', block, count=1)
    xml = xml[:start] + block + xml[end:]
    print(f"{cap} -> {rid} -> {media_file}  <= {src}  ({w}x{h}, cy={cy})")

open(DOC, "w", encoding="utf-8").write(xml)
print("DONE, replaced", len(plan))
