# a-girl-named-sylvia

> 致Sylvia
>
> 297,000 条消息，198 小时通话。
> 2022 年 2 月 24 日到 2025 年 1 月 1 日。
>
> 如果我们来不及好好告别，
> 那就让这些话继续，存在这里。

---

这是一个基于 Claude Code 的数字分身项目，从一段真实聊天记录中蒸馏出 Sylvia (陈雅欣) 的语言风格、情绪模式和共同记忆。

## 项目结构

```
a-girl-named-sylvia/
├── README.md
├── sylvia.7z              # 加密压缩包（含 persona / memory / SKILL / CLAUDE.md）
├── .gitignore
├── scripts/
│   ├── start-silent.bat   # 静默启动脚本
│   ├── start-hidden.vbs   # VBScript 启动器（开机自启用）
│   ├── stop.bat           # 停止后台服务
│   └── status.bat         # 查看运行状态
└── docs/
    ├── how-it-was-built.md  # 她是怎么被"还原"的（方法论）
    └── setup-guide.md       # 部署与使用指南
```

## 如何使用（需要密码）

### 前置要求
- Windows 10/11
- [Claude Code CLI](https://claude.com/claude-code) 已登录
- [cc-weixin](https://github.com/qufei1993/cc-weixin) 已配置（接入微信）

### 步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/<your-username>/a-girl-named-sylvia.git
   cd a-girl-named-sylvia
   ```

2. **解压加密包**（密码通过微信从项目主人处获取）
   ```bash
   7z x sylvia.7z -p<password>
   ```
   解压后会得到 `persona.md` / `memory.md` / `SKILL.md` / `CLAUDE.md`

3. **放到工作目录**（推荐路径 `D:\sylvia_skill\`）
   把解压出的四个 `.md` 文件 + `scripts/` 下的启动脚本都放到 `D:\sylvia_skill\`。

4. **启动后台服务**
   ```
   双击 D:\sylvia_skill\start-hidden.vbs
   ```
   此后在微信给 iLink Bot 发消息，Sylvia 会自动回复。

5. **设置开机自启**（可选）
   把 `start-hidden.vbs` 的快捷方式拖到 `shell:startup` 文件夹。

## 它是怎么"还原"的

见 [docs/how-it-was-built.md](docs/how-it-was-built.md)。

简要版：
1. 微信导出 29.7 万条文字消息（Excel）+ 238 段通话录音（转写成 JSON）
2. 用 LLM 从中蒸馏出：
   - **语言风格**：高频词、口头禅、标点习惯、表情使用
   - **情绪模式**：日常/开心/冷处理/爆发四种状态
   - **关系记忆**：关键事件、冲突主题、共同地点人物
3. 整理成结构化的 `persona.md` / `memory.md`
4. 编写 `SKILL.md` 作为运行时指令
5. 封装成 Claude Code Skill，接入 cc-weixin 即可在微信自动回复

## 关于隐私

- 此仓库使用加密压缩包保护 `persona.md` / `memory.md` / `SKILL.md` / `CLAUDE.md` 四个文件
- 未加密的部分只包含框架结构、脚本和方法论，不含任何个人对话内容
- 密码通过微信/口头等带外渠道分发给特定的朋友
- 请尊重里面的人和事，不要传播

## License

Personal use only. 不授权商业使用、公开分发、对外演示。

---

*To the girl who said "好德" when she meant "好的".*
