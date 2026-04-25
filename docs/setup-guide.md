# 部署指南

## 环境要求

- Windows 10/11
- Python 3.11（**重要**：3.13 + torch 在 Windows 上有 ABI 兼容问题，会卡死。Linux/Mac 任意版本都可）
- [Claude Code CLI](https://claude.com/claude-code) 已登录 Pro/Max
- [cc-weixin 插件](https://github.com/qufei1993/cc-weixin) 已配置（接入 iLink Bot）
- 7-Zip 解压工具
- 至少 8GB RAM（FAISS 索引 + 模型加载）

## 初次部署

### 1. 克隆仓库

```bash
git clone https://github.com/dapao29/a-girl-named-sylvia.git
cd a-girl-named-sylvia
```

### 2. 解压加密包

密码通过私下渠道获取。

```bash
7z x sylvia.7z -p<password>
```

得到 7 个文件：`persona.md` / `memory.md` / `SKILL.md` / `CLAUDE.md` / `persona/v1_base.md` / `persona/v2_refined.md` / `memory/long_term.json`

### 3. 部署到工作目录

把仓库放到 `D:\sylvia_skill\`（脚本里硬编码了这个路径，改的话要全局替换）。

最终目录结构：

```
D:\sylvia_skill\
├── persona.md           # 解压来
├── memory.md            # 解压来
├── SKILL.md             # 解压来
├── CLAUDE.md            # 解压来 + 后续运行时会有更新
├── persona/             # 解压来 + 迭代产出
│   ├── v1_base.md
│   ├── v2_refined.md
│   └── samples/         # 极端样本（吵架/冷处理/亲昵）
├── memory/
│   ├── long_term.json   # 解压来
│   ├── mid_term.json    # 运行时生成
│   └── short_term.json  # 运行时生成
├── rag/
│   ├── parse_corpus.py
│   ├── build_index.py
│   ├── retrieve.py
│   ├── corpus/          # 你自己导出的微信对话 + 通话转写
│   └── vector_db/       # FAISS 索引（约 230MB）
├── iterate/
├── scoring/
├── hooks/
├── bin/
└── scripts/             # 启动 / 守护 / 停止
```

### 4. 安装 Python 依赖

```bash
python -m pip install pandas openpyxl sentence-transformers faiss-cpu pyzipper
```

### 5. 准备你自己的对话数据

这套框架的精髓在于"用你自己的对话训练"。你需要准备：

- **微信对话 Excel**：用 [WeFlow](https://github.com/eric2788/MiraiCP) 等工具导出
- **通话录音转写 JSON**（可选）：Whisper / FunASR 转写

修改 `rag/parse_corpus.py` 顶部的路径：
```python
EXCEL_PATH = r"F:\path\to\你的对话.xlsx"
CALL_JSON_DIR = r"D:\path\to\转写JSON"
```

### 6. 解析 + 建索引（一次性）

```bash
cd D:\sylvia_skill\rag
python parse_corpus.py all   # 输出 corpus/{wx,call}_corpus.jsonl
python build_index.py         # 嵌入 + FAISS 索引（CPU 上 116K 条约 16-25 分钟）
```

### 7. 配置 cc-weixin

扫码登录 iLink Bot，token 保存到 `~/.claude/channels/weixin/account.json`。具体见 cc-weixin 官方文档。

### 8. 启动后台服务

```
双击 D:\sylvia_skill\scripts\start-hidden.vbs
```

无窗口静默启动，日志在 `D:\sylvia_skill\claude.log`。

### 9. 测试

用微信给你的 iLink Bot 发"在干啥"，应该会收到 2-3 条独立的微信消息（碎片化连发）。

## 守护进程

`scripts/guardian.ps1` 每 15 分钟检查：
- Sylvia 主进程是否存活（不存在则重启）
- bun 子进程（cc-weixin MCP）是否存活
- 启动宽限期 90 秒（避免误判）
- 清理孤儿 bun

注册为 Windows 计划任务：

```powershell
schtasks /Create /TN "SylviaGuardian" /SC MINUTE /MO 15 /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\sylvia_skill\scripts\guardian.ps1" /F
```

## 用户消息接入流程

```
你在微信发消息
   ↓
cc-weixin 收到 → 推给 Claude CLI
   ↓
UserPromptSubmit hook 触发：
   inject_rag_context.py
   ├─ 拼凑当前消息 + 最近 4 轮上下文
   ├─ 调 retrieve.py 拿 top-5 历史相似对话
   └─ 写到 memory/short_term.json
   ↓
Sylvia (Claude with CLAUDE.md persona) 生成回复：
   ├─ 加载 long_term.json（核心记忆）
   ├─ 加载 mid_term.json（最近话题）
   ├─ 加载 short_term.json（含 RAG 命中）
   └─ 按 v2 触发词 + 五段式规则回复
   ↓
分多条 reply 工具调用（v3 规则：不合并多行）
   ↓
你在微信收到 2-5 条独立消息
```

## 评分反馈

- 你觉得回得像 → 微信发 `/5` 或 `/good`
- 不像 → `/1` 或 `/bad`
- 看累积 → `/stats`

记到 `scoring/{gold,negative}.jsonl`，后续可作 few-shot 注入或迭代权重。

## 常见问题

### Q: Python 3.13 + torch 卡死
A: 已知问题，降级到 3.11，所有 torch 版本都能秒开。

### Q: BGE-M3 vs bge-small-zh
A: BGE-M3 (2GB, 1024 维) 精度高但 CPU 跑 116K 条要 2-3 小时；bge-small-zh-v1.5 (100MB, 512 维) CPU 上 16 分钟，对 RAG 召回任务完全够用。我们用了后者。

### Q: 风格"漂移"了怎么办
A: 看 `iterate/persona_iterate.py stats` 的最新统计，对比 v1/v2，如果消息长度上升、口头禅占比下降就是漂移。重启 Sylvia + 在 CLAUDE.md 里再强调规则。

## 关于隐私

- `corpus/`、`samples/`、`vector_db/` 都不要 commit（已在 .gitignore）
- 你和她真实对话的衍生物全部本地保留，不上传
- 加密包只放最终模板和方法论
