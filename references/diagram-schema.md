# 可复用的依赖图接口

`scripts/render_dependency_graph.py` 使用Python标准库，将已核对的图结构转成SVG。示例：

```sh
python scripts/render_dependency_graph.py graph.json --output method.svg
```

输入可以是图对象，也可以是含 `diagram.graph` 的整篇讲义对象。图对象字段：

```json
{
  "nodes": [
    {"id":"image", "label":"共同输入", "row":0, "col":0.5, "kind":"input"},
    {"id":"detail", "label":"细节支路", "row":1, "col":0, "kind":"process"},
    {"id":"context", "label":"范围支路", "row":1, "col":1, "kind":"process"},
    {"id":"out", "label":"汇合后的输出", "row":2, "col":0.5, "kind":"output"}
  ],
  "edges": [
    {"from":"image", "to":"detail"},
    {"from":"image", "to":"context"},
    {"from":"detail", "to":"out"},
    {"from":"context", "to":"out"}
  ]
}
```

`row`、`col`只决定布局，不推断边。两列用0、1，共同节点可居中在0.5；三列用0、1、2。`kind`区分外部输入、中间处理与输出。每个标签尽量短，最多33个字符，每行最多11个字符以容纳中文。长依赖可加 `"route":"left"` 或 `"right"`，让箭头从边缘绕开中间节点。

该脚本适合小型、分层的教学示意。它验证端点存在、节点不占同一格，但不能自动避免所有交叉、识别错误的依赖或证明论文机制。生成后要实际看图；复杂循环可按时间展开、分成两张小图，或采用更合适的布局工具，不把复杂架构强塞成单线。

SVG自带文字标签与辅助说明，嵌入网页时加“辅助示意”图注以及原文依据。区分训练/推理、监督/数据/更新箭头；本脚本默认边仅表示一般依赖，若混合不同边类型，应扩展图例或分图说明。
