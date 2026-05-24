# 渊索寓言 (The Abyss Fables)

> AI 驱动的深度文字冒险游戏 | DeepSeek 赋能的互动叙事体验

## 简介

**渊索寓言** 是一款基于 AI 大语言模型的文字冒险游戏。你可以创建属于自己的故事世界，设定世界观、主角、风格与道德边界，然后由 DeepSeek AI 驱动故事的发展。每一步都由你做出选择，AI 根据你的意志推进剧情，创造独一无二的叙事体验。

## ✨ 核心特性

- **AI 叙事引擎** —— 基于 DeepSeek API，实时生成富有文学性的故事内容
- **种子编辑器** —— 从零创建故事：设定类型、风格、语调、世界观、主角等一切细节
- **多类型交互** —— 多选、单选、简答、自由意志四种题型，让选择不再单调
- **上帝模式** —— 突破故事限制，直接向 AI 发出至高意志指令
- **状态系统** —— HP/MP、物品清单、同行角色、敌对角色，完整的 RPG 数值模型
- **记忆链系统** —— AI 自动记录重要事件，长篇故事不丢上下文
- **种子加密** —— 支持对故事种子加密分享（AES）
- **存档系统** —— 随时保存/读取游戏进度
- **主题定制** —— 多种 UI 配色方案，可调节字体与字号
- **流式输出** —— 故事内容实时逐字输出，沉浸式阅读体验

## 运行环境

- **操作系统**：Windows 10/11（主要支持），Linux/macOS 理论兼容
- **Python**：3.10+
- **API**：DeepSeek API Key（需自行申请：[platform.deepseek.com](https://platform.deepseek.com)）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/the-abyss-fables.git
cd the-abyss-fables
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

将 `config_data/config.json.example` 复制为 `config_data/config.json`，填入你的 DeepSeek API Key：

```json
{
  "api": {
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-your-api-key-here",
    "model": "deepseek-chat"
  }
}
```

> ⚠️ **请勿将含真实 API Key 的 config.json 上传到公开仓库！** 该文件已在 `.gitignore` 中排除。

### 4. 启动游戏

**Windows 用户**：双击 `启动游戏.bat`

**其他系统**：
```bash
python main.py
```

## 项目结构

```
game-txt/
├── main.py              # 程序入口
├── requirements.txt     # Python 依赖
├── 启动游戏.bat          # Windows 启动脚本
├── config/              # 配置模块（默认值、主题、字体、IO）
├── config_data/         # 用户配置目录（运行时生成）
├── core/                # 核心逻辑（AI客户端、游戏引擎、存档管理、种子加密）
├── models/              # 数据模型（角色、物品、状态、记忆）
├── prompts/             # AI 提示词工程
├── ui/                  # 图形界面（主窗口、菜单、面板、设置）
├── utils/               # 工具模块（日志）
├── logs/                # 日志目录
├── saves/               # 存档目录
└── 素材/                # 素材资源（图标、背景图）
```

## 开发与贡献

本项目由 [Trae IDE](https://trae.ai) 辅助开发。

欢迎提交 Issue 和 Pull Request！在提交 PR 前，请确保：

- 代码风格与现有代码保持一致
- 不引入新的硬编码配置或敏感信息
- 测试基本功能正常

## 技术栈

| 技术 | 用途 | 协议 |
|------|------|------|
| Python | 编程语言 | PSF |
| PyQt5 | 图形界面框架 | GPL v3 |
| DeepSeek | AI 大语言模型 | — |
| openai | API 客户端库 | MIT |
| loguru | 结构化日志 | MIT |
| cryptography | 种子加密 | Apache 2.0 |
| pydantic | 数据校验 | MIT |
| tiktoken | Token 预估 | MIT |
| qasync | Qt 异步事件循环 | BSD |

## 协议

本项目使用 [GNU General Public License v3.0](LICENSE) 开源。

---

**开发者**：Monkey3072

*感谢所有开源项目及其贡献者。*