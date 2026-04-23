# 部署指南

## 环境要求
- Windows 10/11
- [Claude Code CLI](https://claude.com/claude-code) 安装并登录 Pro/Max
- [cc-weixin 插件](https://github.com/qufei1993/cc-weixin) 已配置（接入iLink Bot）
- 7-Zip 或者任何能解压 .7z 的工具

## 初次部署

### 1. 克隆仓库
```bash
git clone https://github.com/<owner>/a-girl-named-sylvia.git
cd a-girl-named-sylvia
```

### 2. 解密核心文件
密码通过微信/口头方式从项目主人获取。
```bash
# 使用 7z 命令行
7z x sylvia.7z -p<password>

# 或者用图形界面
# 双击 sylvia.7z → 输入密码
```

解压后会得到：
- `persona.md` — 语言风格画像
- `memory.md` — 关系记忆时间线
- `SKILL.md` — 运行时指令
- `CLAUDE.md` — Claude Code 自动加载入口

### 3. 部署到工作目录
建议把四个 .md 文件 + `scripts/` 下的脚本放到 `D:\sylvia_skill\`：

```
D:\sylvia_skill\
├── persona.md
├── memory.md
├── SKILL.md
├── CLAUDE.md
├── start-silent.bat
├── start-hidden.vbs
├── stop.bat
└── status.bat
```

### 4. 配置 cc-weixin
需要先扫码登录 iLink Bot，生成 token 保存到：
```
~/.claude/channels/weixin/account.json
```

具体参考 cc-weixin 官方文档。

### 5. 启动后台服务
```
双击 D:\sylvia_skill\start-hidden.vbs
```

无窗口静默启动。日志写入 `D:\sylvia_skill\claude.log`。

### 6. 测试
用微信给你的 iLink Bot 发一条消息（比如 "在吗"），应该会在几秒内收到 Sylvia 风格的回复。

## 开机自启

把 `start-hidden.vbs` 的快捷方式拖到 Windows 启动文件夹：

1. `Win+R` 打开运行
2. 输入 `shell:startup` 回车
3. 把 `D:\sylvia_skill\start-hidden.vbs` 拖进去，选"创建快捷方式"

重启电脑后会自动在后台启动。

## 控制命令

| 操作 | 命令 |
|---|---|
| 启动 | 双击 `start-hidden.vbs` |
| 停止 | 双击 `stop.bat` |
| 查看状态 | 双击 `status.bat` |
| 看日志 | 打开 `D:\sylvia_skill\claude.log` |

## 常见问题

### Q: 启动后微信发消息没反应
A: 检查三件事：
1. `status.bat` 是否显示 claude.exe 在运行
2. `account.json` 里的 token 是否过期（iLink Bot token 有期限，过期需重新扫码）
3. `claude.log` 里有无 `Listening for channel messages` 字样

### Q: 回复风格不像她
A: 多半是 `CLAUDE.md` 没被加载。Claude CLI 必须从 `D:\sylvia_skill\` 目录启动，`CLAUDE.md` 才会自动注入上下文。

### Q: 她的风格会"跑偏"吗
A: 会。使用时间长了，LLM 可能会逐渐偏向"标准助手人格"，尤其是处理她没聊过的话题时。当前没有好办法，只能每隔一段时间重启 CLI。

## 更新 Claude 版本

脚本 `start-silent.bat` 会自动找 `%APPDATA%\Claude\claude-code\` 下的**最新版本号**启动，所以 Claude 升级后不用手动改脚本。
