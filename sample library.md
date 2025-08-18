# 示例库

## 基础生产线 (example_basic.json)
```json
{
  "name": "基础生产线",
  "description": "简单串联生产线，包含源、工位和物料终结节点",
  "graph": {
    "nodes": [
      {
        "name": "源节点",
        "type": "源",
        "data": {
          "time": {
            "interval_time": "0:0:5:0"
          }
        }
      },
      {
        "name": "加工工位",
        "type": "工位",
        "data": {
          "time": {
            "processing_time": "0:0:3:0"
          }
        }
      },
      {
        "name": "成品仓库",
        "type": "物料终结",
        "data": {}
      }
    ],
    "edges": [
      {"from": "源节点", "to": "加工工位"},
      {"from": "加工工位", "to": "成品仓库"}
    ]
  }
}

{
  "name": "带故障的生产线",
  "description": "包含故障设置的复杂生产线",
  "graph": {
    "nodes": [
      {
        "name": "原料源",
        "type": "源",
        "data": {
          "time": {
            "interval_time": "0:0:10:0",
            "start_time": "0:0:0:0",
            "stop_time": "8:0:0:0"
          }
        }
      },
      {
        "name": "主加工站",
        "type": "工位",
        "data": {
          "time": {
            "processing_time": {
              "distribution_pattern": "normal",
              "parameters": {"mean": 200, "sigma": 30}
            }
          },
          "failure": {
            "interval_time": {
              "distribution_pattern": "negexp",
              "parameters": {"mean": 3600}
            },
            "duration_time": "0:10:0:0"
          }
        }
      },
      {
        "name": "成品区",
        "type": "物料终结",
        "data": {}
      }
    ],
    "edges": [
      {"from": "原料源", "to": "主加工站"},
      {"from": "主加工站", "to": "成品区"}
    ]
  }
}

{
  "name": "带传送器的生产线",
  "description": "包含传送器节点的生产线",
  "graph": {
    "nodes": [
      {
        "name": "原料供应",
        "type": "源",
        "data": {
          "time": {
            "interval_time": "0:0:15:0"
          }
        }
      },
      {
        "name": "装配工位",
        "type": "工位",
        "data": {
          "time": {
            "processing_time": "0:0:8:0"
          }
        }
      },
      {
        "name": "传送带",
        "type": "传送器",
        "data": {
          "capacity": 5,
          "length": 10,
          "speed": 0.5
        }
      },
      {
        "name": "包装区",
        "type": "物料终结",
        "data": {}
      }
    ],
    "edges": [
      {"from": "原料供应", "to": "装配工位"},
      {"from": "装配工位", "to": "传送带"},
      {"from": "传送带", "to": "包装区"}
    ]
  }
}

{
  "name": "质量控制生产线",
  "description": "包含质量检测和分流的生产线",
  "graph": {
    "nodes": [
      {
        "name": "原材料",
        "type": "源",
        "data": {
          "time": {
            "interval_time": "0:0:7:0"
          }
        }
      },
      {
        "name": "成型工位",
        "type": "工位",
        "data": {
          "time": {
            "processing_time": "0:0:5:0"
          }
        }
      },
      {
        "name": "质检站",
        "type": "工位",
        "data": {
          "time": {
            "processing_time": "0:0:2:0"
          },
          "production_status": {
            "qualified": 0.85,
            "unqualified": 0.15
          }
        }
      },
      {
        "name": "合格品库",
        "type": "物料终结",
        "data": {}
      },
      {
        "name": "返修区",
        "type": "物料终结",
        "data": {}
      }
    ],
    "edges": [
      {"from": "原材料", "to": "成型工位"},
      {"from": "成型工位", "to": "质检站"},
      {"from": "质检站", "to": "合格品库"},
      {"from": "质检站", "to": "返修区"}
    ]
  }
}

