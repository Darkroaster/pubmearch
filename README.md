# PubMed Analysis MCP Server

> **苦逼医学生自己的MCP server**：这是一个刚刚开发的项目，功能仍在完善中，欢迎各位提出建议和改进！
> 
> **Note**: This is a newly developed project with features still being refined. Suggestions and improvements are welcome!

一个专业的PubMed医学文献分析MCP服务器，帮助科研人员快速洞察医学研究动态。

A professional MCP server for analyzing PubMed medical literature to help researchers quickly gain insights into medical research dynamics.

## 功能特点 / Features

- **文献检索 / Literature Retrieval**: 支持PubMed高级检索语法，可设置日期范围和结果数量。/ Supports PubMed advanced search syntax with date filtering.

- **热点分析 / Hotspot Analysis**: 统计关键词频率，识别热门研究方向，汇总相关文献。/ Analyzes keyword frequencies to identify popular research areas.

- **趋势追踪 / Trend Tracking**: 追踪关键词随时间的频率变化，揭示研究趋势演变。/ Tracks keyword changes over time to reveal evolving research trends.

- **发文统计 / Publication Count**: 提供灵活的时间周期设置，分析文献数量变化。/ Analyzes publication volume changes with customizable time periods.

- **全面报告 / Comprehensive Reports**: 一键生成包含热点、趋势和统计的分析报告。/ Generates complete reports with customizable parameters.

## MCP工具 / MCP Tools

### 1. search_pubmed
搜索PubMed并保存结果。/ Search PubMed and save results.

主要参数 / Key parameters:
- `email`: 您的电子邮件（必填）/ Your email (required)
- `advanced_search`: PubMed搜索查询（必填，与高级检索语法相同）/ PubMed search query (required, same as advanced search syntax)
- `max_results`: 最大结果数（默认：1000）/ Maximum results (default: 1000)

### 2. list_result_files
列出可用的结果文件。/ List available result files.

### 3. analyze_research_hotspots
分析研究热点。/ Analyze research hotspots.

主要参数 / Key parameters:
- `filename`: 结果文件名（必填）/ Result filename (required)
- `top_n`: 分析的关键词数量（默认：20）/ Number of keywords (default: 20)

### 4. analyze_research_trends
分析研究趋势。/ Analyze research trends.

### 5. analyze_publication_count
分析发文数量。/ Analyze publication counts.

### 6. generate_comprehensive_analysis
生成全面分析报告。/ Generate comprehensive analysis.

## Cursor使用示例 / Example for Cursor

```bash
# 安装依赖
pip install -r requirements.txt
# 或使用uv
uv pip install -r requirements.txt
```

### Write mcp.json
因为我习惯用uv虚拟环境，因此这里直接使用python的路径运行python文件。
```json
// Add the following configuration in mcp.json (for Windows)
"PubMed": {
        "command": "cmd",
        "args": [
          "/c",
          "path/to/python.exe",
          "path/to/server.py"
        ]
    }
// For example, my mcp.json file looks like this
{
    "mcpServers": {
      "fetch":{
        "command": "cmd",
        "args": [
          "/c",
          "uvx",
          "mcp-server-fetch"
        ]
      },
      "PubMed": {
        "command": "cmd",
        "args": [
          "/c",
          "path/to/python.exe",
          "path/to/server.py"
        ]
      }
    }
  }
```

### LLM prompt (Agent mode)

/your_mcp_name (note: it is PubMed here) Help me analyze the research hotspots on prostate cancer immunotherapy in the past three months. Set top_n to 50 and max_results to 5000. My email adress is ...
/your_mcp_name（注：比如我的mcp.json里面是PubMed）帮我分析一下近三个月前列腺癌免疫治疗的研究热点。top_n设置为50，max_results设置为5000。我的电子邮箱是...


## 注意事项 / Notes

- 请遵循NCBI的API使用政策。/ Follow NCBI usage policies.
- 结果文件保存在`results`目录，日志位于`pubmed_server.log`。/ Results saved in `results` directory, logs in `pubmed_server.log`.
- 项目处于开发阶段，欢迎通过Issue或Pull Request贡献改进。/ Project in development, contributions welcome via Issues or Pull Requests.
