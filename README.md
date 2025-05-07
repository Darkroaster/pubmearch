# PubMed Analysis MCP Server

> **适用于PubMed的MCP server**：这是一个刚刚开发的项目，功能仍在完善中，欢迎各位提出建议和改进！
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
一般而言不需要显性设置，与大模型沟通即可。/ Generally, no need to set explicitly, communicate with large models.
- `advanced_search`: PubMed搜索查询（必填，与高级检索语法相同）/ PubMed search query (required, same as advanced search syntax)
- `start_date`: 开始日期（格式：YYYY/MM/DD）/ Start date (format: YYYY/MM/DD)
- `end_date`: 结束日期（格式：YYYY/MM/DD）/ End date (format: YYYY/MM/DD)
- `max_results`: 最大结果数（默认：1000）/ Maximum results (default: 1000)

### 2. list_result_files
列出可用的结果文件。/ List available result files.

### 3. analyze_research_keywords
分析研究热点以及研究趋势。/ Analyze research hotspots and research trends.
主要参数 / Key parameters:
- `top_n`: 分析的关键词数量（默认：20）/ Number of keywords (default: 20)

### 4. analyze_publication_count
分析发文数量。/ Analyze publication counts.

### 5. generate_comprehensive_analysis
生成全面分析报告。/ Generate comprehensive analysis.

## Trae使用示例 / Example for Trae
*Between us... when I use the same model, Cursor makes me feel like I'm the one not making sense. Trae, on the other hand, just gets me. Seriously great IDE!*

### 安装依赖 / Install Dependencies
推荐使用uv虚拟环境。/ Recommend using uv virtual environment.  
uv：[访问uv repo](https://github.com/astral-sh/uv) 

```bash
# pyproject.toml 目录下：
uv pip install -e .
```

### Write mcp.json
Merge the following configuration in mcp.json (for Windows):
```json
{
  "mcpServers": {
    "pubmearch": {
      "command": "cmd",
      "args": [
        "/c",
        "uv",
        "run",
        "--directory",
        "path/to/project/root/directory",  // The folder where the pubmearch folder is located
        "-m",
        "pubmearch.server"
      ],
      "env": {
        "NCBI_USER_EMAIL": "youremailaddress@email.com",
        "NCBI_USER_API_KEY": "your_api_key"
      }
    }
  }
}
```

### PubMed API key获取 / Get PubMed API key
1. 登录PubMed网站。/ Log in to PubMed.
2. 点击右上角的头像，选择“ Account Settings”。/ Click on your profile picture and select " Account Settings".
3. 向下滚动到“API Keys”部分，点击“Create API Key”。/ Scroll down to the "API Keys" section and click "Create API Key".

### LLM prompt (Agent mode)
**推荐使用高级检索语法**。/ **Use advanced search syntax**. 
- Help me analyze the research hotspots on prostate cancer immunotherapy in the past three months. The advanced search query is ((prostat*[Title/Abstract]) AND (cancer[Title/Abstract])) AND (immu*[Title/Abstract]).  
- 帮我分析一下近三个月前列腺癌免疫治疗的研究热点，检索词为((prostat*[Title/Abstract]) AND (cancer[Title/Abstract])) AND (immu*[Title/Abstract]).


## 注意事项 / Notes

- 请遵循NCBI的API使用政策。/ Follow NCBI usage policies. 
- 结果文件保存在`pubmearch/results`目录，日志位于`pubmed_server.log`。/ Results saved in `pubmearch/results` directory, logs in `pubmed_server.log`.
- 本人平时学业繁忙，项目可能会有延迟。/ I am busy with my studies, the project may be delayed.

## 贡献 / Contributions

欢迎通过Issue或Pull Request贡献改进。/ Contributions are welcome via Issues or Pull Requests.

## 许可证 / License

[MIT](https://github.com/Darkroaster/pubmearch/blob/main/LICENSE)
