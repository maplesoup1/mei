# PocketTrack Pro - 智慧零花钱管理

基于 Python + CustomTkinter 的桌面记账应用，支持收支记录、分类统计、图表分析和 CSV 导出。

## 环境要求

- Python 3.8+
- tkinter（Python 标准库，macOS/Windows 通常自带；Linux 需安装 `python3-tk`）

## 第三方依赖

| 包名 | 用途 |
|------|------|
| customtkinter | 现代化 UI 框架 |
| matplotlib | 图表绘制（饼图、柱状图） |
| numpy | 图表数据处理 |

## 安装与运行

```bash
# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install customtkinter matplotlib numpy

# 运行
python Allowancemanagement.py
```

## 打包为可执行文件

项目已包含 `Allowancemanagement.spec`，可使用 PyInstaller 打包：

```bash
pip install pyinstaller
pyinstaller Allowancemanagement.spec
```

打包产物位于 `dist/` 目录。
