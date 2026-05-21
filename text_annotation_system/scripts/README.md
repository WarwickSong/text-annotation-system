# 封装说明

## 概述

本项目使用 PyInstaller 将 Python 后端与 Vue 前端打包为独立的桌面应用程序。由于 PyInstaller 是平台绑定的，因此必须在目标平台上分别执行封装。

---

## 封装机环境要求

### 通用（Windows & macOS）

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| Node.js | LTS（≥18） | 构建前端页面 |
| npm | ≥9 | 安装前端依赖 |
| Python | ≥3.10 | 运行 PyInstaller 打包 |
| pip | — | 安装 [requirements.txt](../requirements.txt) 中的依赖 |
| PyInstaller | ≥6.0 | 将 Python 应用打包为独立可执行文件（已包含在 requirements.txt 中） |

### macOS 额外要求

- macOS 上首次构建时可能需要允许终端访问"下载"等目录，否则 `npm install` 可能失败。
- 构建完成后产物为 `dist/TextAnnotationSystem.app`（macOS Bundle）。

---

## 源码目录结构要求

封装前须确保以下目录结构（`async_batch_inference` 必须与 `text_annotation_system` 并列）：

```
<parent>/
├── async_batch_inference/          # 核心推理库（必须！与项目并列放置）
│   ├── __init__.py
│   ├── config.py
│   ├── handle.py
│   ├── inference.py
│   └── prompt_manager.py
└── text_annotation_system/         # 项目目录
    ├── main.py
    ├── text_annotation_system.spec
    ├── frontend/
    ├── scripts/
    ├── api/
    ├── core/
    └── ...
```

构建脚本和 `.spec` 均通过 `../async_batch_inference`（即项目目录的兄弟目录）确定位核心库。如果不存在，打包时会立即报错终止，不会静默跳过。

从 Windows 迁移到 Mac 封装时，需要把整个 `<parent>/` 目录一并复制，保持上述并列关系不变。

---

## 封装步骤

### Windows

在项目根目录下以 **PowerShell（管理员）** 执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

脚本会自动：
1. 停止正在运行的旧版本进程
2. `npm install && npm run build` 构建前端
3. `pip install -r requirements.txt` 安装 Python 依赖
4. `python -m PyInstaller --clean --noconfirm text_annotation_system.spec` 打包
5. 在 `dist/TextAnnotationSystem/` 下创建 `data_dir.txt` 和 `data/` 目录
6. 将输出压缩为 `dist/TextAnnotationSystem-windows.zip`

### macOS

在项目根目录下执行：

```bash
chmod +x scripts/build_macos.sh
bash scripts/build_macos.sh
```

脚本会自动：
1. `npm install && npm run build` 构建前端
2. `pip install -r requirements.txt` 安装 Python 依赖
3. `python3 -m PyInstaller --clean text_annotation_system.spec` 打包
4. 在 `dist/TextAnnotationSystem/` 下创建 `data_dir.txt` 和 `data/` 目录

---

## 产物结构

```
dist/
├── TextAnnotationSystem/               # 应用程序目录
│   ├── TextAnnotationSystem.exe        # Windows 可执行文件
│   ├── data_dir.txt                    # 数据目录指针（内容为 "data"）
│   ├── data/                           # 用户数据目录（运行时生成）
│   │   ├── schemes/
│   │   ├── tasks/
│   │   ├── uploads/
│   │   └── outputs/
│   └── _internal/                      # Python 运行时 & 依赖库 & async_batch_inference
│       ├── python3.dll
│       ├── base_library.zip
│       ├── async_batch_inference/
│       ├── uvicorn/ fastapi/ pandas/ ...
│       └── *.pyd / *.dll               # C 扩展和动态库
└── TextAnnotationSystem-windows.zip    # 压缩发布包（仅 Windows）
```

macOS 下会额外生成 `TextAnnotationSystem.app` Bundle。

---

## 分发

| 平台 | 交付物 | 用户操作 |
|------|--------|----------|
| Windows | `TextAnnotationSystem-windows.zip` | 解压后双击 `TextAnnotationSystem.exe` |
| macOS | `TextAnnotationSystem.app` 或 `TextAnnotationSystem/` 文件夹 | 双击 `TextAnnotationSystem.app` |

用户端**无需安装** Python、Node.js 或任何依赖，应用完全自包含。

---

## 关键技术细节

### 路径解析（frozen 模式）

`main.py` 中通过 `sys.frozen` 判断运行模式：

- **源码运行**：所有路径基于 `__file__`（项目源码目录）
- **frozen 运行**（PyInstaller 打包后）：
  - 资源目录 → `sys._MEIPASS`（PyInstaller 解压后的临时目录）
  - 应用目录 → `sys.executable` 所在目录（即 exe 所在文件夹）
  - 数据目录 → `data_dir.txt` 指向的路径（默认为 exe 同级的 `data/`）

### PyInstaller 配置

详见 [text_annotation_system.spec](../text_annotation_system.spec)：

- `static/` → 前端构建产物，作为 data 打包
- `async_batch_inference/` → 核心推理库，作为 data 打包，路径固定为 `../async_batch_inference`（项目目录的兄弟目录），不存在时立即报错，防止遗漏
- `hiddenimports` → 显式声明 uvicorn/pandas/openai 等隐式导入，防止遗漏
- `console=False` → 不显示控制台窗口（Windows）

### data_dir.txt 的作用

`data/` 目录不在 `_internal` 中，而是放在 exe 同级，这样：
- 用户数据（方案、上传文件、标注结果）不会混入系统文件
- 应用可以读写数据目录而不受打包目录权限限制
- 支持通过环境变量 `TAS_DATA_DIR` 自定义数据目录路径
