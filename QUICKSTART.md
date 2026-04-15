# Quick Start - Paper Trend Tracking

## 5 分钟快速开始

### 1. 安装依赖

```bash
cd paper-trend-tracking

# 使用 conda（推荐）
conda env create -f environment.yml
conda activate paper-trends
python -m spacy download en_core_web_sm

# 或使用 pip
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. 配置（可选）

编辑 `config.yaml` 自定义搜索主题：

```yaml
collection:
  tracked_queries:
    - "machine learning drug discovery"
    - "deep learning protein structure"
    - "AI clinical trials"
  max_papers_per_query: 100  # 先测试少量数据
```

### 3. 运行 Pipeline

```bash
python run_pipeline.py
```

**输出：**
- `data/papers.db` - SQLite 数据库
- `output/visualizations/` - HTML 图表
- `logs/pipeline.log` - 运行日志

### 4. 启动 Dashboard

```bash
python run_dashboard.py
```

**访问：** http://localhost:8050

## 测试安装

```bash
# 测试 API 连接
python test_apis.py

# 预期输出：
# ✅ PubMed: Working
# ✅ arXiv: Working
```

## 预期结果

**第一次运行（测试数据）：**
```
📚 Collecting papers...
✅ Collection complete: 50-100 papers

🔗 Building network...
✅ Built 1-2 snapshots

📈 Analyzing trends...
🔥 Top trending keywords:
  1. machine learning (growth: 2.5)
  2. deep learning (growth: 1.8)
  ...

✅ PIPELINE COMPLETE!
```

**Dashboard 界面：**
- 左侧：时间窗口和指标选择器
- 中间：Trending keywords 柱状图
- 下方：关键词网络图
- 底部：数据表格

## 常见问题

### Dashboard 无法启动

```bash
# 检查是否安装了 dash
pip install dash plotly

# 或使用 conda
conda install -c conda-forge dash plotly
```

### 没有数据

1. 确保已运行 pipeline：
   ```bash
   python run_pipeline.py
   ```

2. 检查数据库：
   ```bash
   ls -lh data/papers.db
   ```

3. 查看日志：
   ```bash
   tail logs/pipeline.log
   ```

### API 错误

**PubMed 错误：**
- 检查网络连接
- 稍后重试（速率限制）

**arXiv 错误：**
- 查询词太宽泛，尝试更具体的词
- 减少 `max_papers_per_query`

## 下一步

1. **自定义查询** - 编辑 `config.yaml` 添加你的研究领域
2. **增加数据量** - 设置 `max_papers_per_query: 500`
3. **定时运行** - 设置 cron job 每日更新
4. **导出结果** - Dashboard 表格支持导出 CSV

## 获取帮助

- 完整文档：`USAGE.md`
- GitHub Issues: https://github.com/hiuhiu2026/paper-trend-tracking/issues
