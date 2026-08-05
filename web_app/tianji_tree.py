# -*- coding: utf-8 -*-
"""天纪目录树（由 tools/gen_tianji_tree.py 依据 列表.txt 生成）。

每个叶子节点带 src(数据源) 与 idx(在 _DATA[src] 中的序号)，
前端点击叶子调用 /api/tianji/item?sub=<src>&i=<idx> 取详情。
"""
TIANJI_TREE = [
  {
    "t": "斗数",
    "children": [
      {
        "t": "基础理论",
        "children": [
          {
            "t": "甲级星",
            "children": [
              {
                "t": "紫微",
                "src": "lilun",
                "idx": 66
              },
              {
                "t": "天机",
                "src": "lilun",
                "idx": 67
              },
              {
                "t": "太阳",
                "src": "lilun",
                "idx": 68
              },
              {
                "t": "武曲",
                "src": "lilun",
                "idx": 69
              },
              {
                "t": "天同",
                "src": "lilun",
                "idx": 70
              },
              {
                "t": "廉贞",
                "src": "lilun",
                "idx": 71
              },
              {
                "t": "天府",
                "src": "lilun",
                "idx": 72
              },
              {
                "t": "贪狼",
                "src": "lilun",
                "idx": 73
              },
              {
                "t": "巨门",
                "src": "lilun",
                "idx": 74
              },
              {
                "t": "天相",
                "src": "lilun",
                "idx": 75
              },
              {
                "t": "天梁",
                "src": "lilun",
                "idx": 76
              },
              {
                "t": "七杀",
                "src": "lilun",
                "idx": 77
              },
              {
                "t": "破军",
                "src": "lilun",
                "idx": 78
              },
              {
                "t": "禄存",
                "src": "lilun",
                "idx": 79
              },
              {
                "t": "天马",
                "src": "lilun",
                "idx": 80
              },
              {
                "t": "文昌",
                "src": "lilun",
                "idx": 81
              },
              {
                "t": "文曲",
                "src": "lilun",
                "idx": 82
              },
              {
                "t": "天魁",
                "src": "lilun",
                "idx": 83
              },
              {
                "t": "天钺",
                "src": "lilun",
                "idx": 84
              },
              {
                "t": "左辅",
                "src": "lilun",
                "idx": 85
              },
              {
                "t": "右弼",
                "src": "lilun",
                "idx": 86
              },
              {
                "t": "擎羊",
                "src": "lilun",
                "idx": 87
              },
              {
                "t": "陀罗",
                "src": "lilun",
                "idx": 88
              },
              {
                "t": "火星",
                "src": "lilun",
                "idx": 89
              },
              {
                "t": "铃星",
                "src": "lilun",
                "idx": 90
              },
              {
                "t": "天空",
                "src": "lilun",
                "idx": 91
              },
              {
                "t": "地劫",
                "src": "lilun",
                "idx": 92
              }
            ],
            "_sec": "基础理论",
            "_grp": "甲级星"
          },
          {
            "t": "乙级星及神煞",
            "children": [
              {
                "t": "三台",
                "src": "lilun",
                "idx": 93
              },
              {
                "t": "八座",
                "src": "lilun",
                "idx": 94
              },
              {
                "t": "台辅",
                "src": "lilun",
                "idx": 95
              },
              {
                "t": "封诰",
                "src": "lilun",
                "idx": 96
              },
              {
                "t": "恩光",
                "src": "lilun",
                "idx": 97
              },
              {
                "t": "天贵",
                "src": "lilun",
                "idx": 98
              },
              {
                "t": "龙池",
                "src": "lilun",
                "idx": 99
              },
              {
                "t": "凤阁",
                "src": "lilun",
                "idx": 100
              },
              {
                "t": "天哭",
                "src": "lilun",
                "idx": 101
              },
              {
                "t": "天虚",
                "src": "lilun",
                "idx": 102
              },
              {
                "t": "孤辰",
                "src": "lilun",
                "idx": 103
              },
              {
                "t": "寡宿",
                "src": "lilun",
                "idx": 104
              },
              {
                "t": "红鸾",
                "src": "lilun",
                "idx": 105
              },
              {
                "t": "天喜",
                "src": "lilun",
                "idx": 106
              },
              {
                "t": "长生",
                "src": "lilun",
                "idx": 107
              },
              {
                "t": "沐浴",
                "src": "lilun",
                "idx": 108
              },
              {
                "t": "冠带",
                "src": "lilun",
                "idx": 109
              },
              {
                "t": "临官",
                "src": "lilun",
                "idx": 110
              },
              {
                "t": "帝旺",
                "src": "lilun",
                "idx": 111
              },
              {
                "t": "衰",
                "src": "lilun",
                "idx": 249
              },
              {
                "t": "病",
                "src": "lilun",
                "idx": 113
              },
              {
                "t": "死",
                "src": "lilun",
                "idx": 250
              },
              {
                "t": "墓",
                "src": "lilun",
                "idx": 115
              },
              {
                "t": "绝",
                "src": "lilun",
                "idx": 116
              },
              {
                "t": "胎",
                "src": "lilun",
                "idx": 117
              },
              {
                "t": "养",
                "src": "lilun",
                "idx": 251
              },
              {
                "t": "博士",
                "src": "lilun",
                "idx": 252
              },
              {
                "t": "力士",
                "src": "lilun",
                "idx": 120
              },
              {
                "t": "青龙",
                "src": "lilun",
                "idx": 121
              },
              {
                "t": "小耗",
                "src": "lilun",
                "idx": 136
              },
              {
                "t": "将军",
                "src": "lilun",
                "idx": 123
              },
              {
                "t": "奏书",
                "src": "lilun",
                "idx": 253
              },
              {
                "t": "飞廉",
                "src": "lilun",
                "idx": 254
              },
              {
                "t": "喜神",
                "src": "lilun",
                "idx": 255
              },
              {
                "t": "病符",
                "src": "lilun",
                "idx": 142
              },
              {
                "t": "大耗",
                "src": "lilun",
                "idx": 261
              },
              {
                "t": "伏兵",
                "src": "lilun",
                "idx": 129
              },
              {
                "t": "官符",
                "src": "lilun",
                "idx": 260
              },
              {
                "t": "岁建",
                "src": "lilun",
                "idx": 131
              },
              {
                "t": "晦气",
                "src": "lilun",
                "idx": 132
              },
              {
                "t": "丧门",
                "src": "lilun",
                "idx": 258
              },
              {
                "t": "贯索",
                "src": "lilun",
                "idx": 259
              },
              {
                "t": "龙德",
                "src": "lilun",
                "idx": 138
              },
              {
                "t": "白虎",
                "src": "lilun",
                "idx": 262
              },
              {
                "t": "天德",
                "src": "lilun",
                "idx": 263
              },
              {
                "t": "吊客",
                "src": "lilun",
                "idx": 264
              },
              {
                "t": "将星",
                "src": "lilun",
                "idx": 265
              },
              {
                "t": "攀鞍",
                "src": "lilun",
                "idx": 266
              },
              {
                "t": "岁驿",
                "src": "lilun",
                "idx": 267
              },
              {
                "t": "息神",
                "src": "lilun",
                "idx": 146
              },
              {
                "t": "华盖",
                "src": "lilun",
                "idx": 268
              },
              {
                "t": "劫煞",
                "src": "lilun",
                "idx": 148
              },
              {
                "t": "灾煞",
                "src": "lilun",
                "idx": 149
              },
              {
                "t": "天煞",
                "src": "lilun",
                "idx": 269
              },
              {
                "t": "指背",
                "src": "lilun",
                "idx": 151
              },
              {
                "t": "咸池",
                "src": "lilun",
                "idx": 201
              },
              {
                "t": "月煞",
                "src": "lilun",
                "idx": 270
              },
              {
                "t": "亡神",
                "src": "lilun",
                "idx": 154
              },
              {
                "t": "天姚",
                "src": "lilun",
                "idx": 200
              },
              {
                "t": "天刑",
                "src": "lilun",
                "idx": 202
              },
              {
                "t": "阴煞",
                "src": "lilun",
                "idx": 203
              },
              {
                "t": "天伤",
                "src": "lilun",
                "idx": 204
              },
              {
                "t": "天使",
                "src": "lilun",
                "idx": 205
              },
              {
                "t": "破碎",
                "src": "lilun",
                "idx": 206
              },
              {
                "t": "蜚廉",
                "src": "lilun",
                "idx": 207
              },
              {
                "t": "解神",
                "src": "lilun",
                "idx": 210
              },
              {
                "t": "天月",
                "src": "lilun",
                "idx": 211
              },
              {
                "t": "天巫",
                "src": "lilun",
                "idx": 212
              },
              {
                "t": "天官",
                "src": "lilun",
                "idx": 213
              },
              {
                "t": "天福",
                "src": "lilun",
                "idx": 214
              },
              {
                "t": "天寿",
                "src": "lilun",
                "idx": 215
              },
              {
                "t": "天才",
                "src": "lilun",
                "idx": 216
              },
              {
                "t": "旬空",
                "src": "lilun",
                "idx": 217
              },
              {
                "t": "截空",
                "src": "lilun",
                "idx": 218
              }
            ],
            "_sec": "基础理论",
            "_grp": "乙级星及神煞"
          },
          {
            "t": "基础概念",
            "children": [
              {
                "t": "星宿",
                "src": "lilun",
                "idx": 155
              },
              {
                "t": "正星、辅星",
                "src": "lilun",
                "idx": 156
              },
              {
                "t": "副星、杂曜",
                "src": "lilun",
                "idx": 157
              },
              {
                "t": "吉星",
                "src": "lilun",
                "idx": 158
              },
              {
                "t": "煞星",
                "src": "lilun",
                "idx": 159
              },
              {
                "t": "四化星",
                "src": "lilun",
                "idx": 160
              },
              {
                "t": "流星",
                "src": "lilun",
                "idx": 161
              },
              {
                "t": "星曜的简称",
                "src": "lilun",
                "idx": 162
              },
              {
                "t": "星情",
                "src": "lilun",
                "idx": 163
              },
              {
                "t": "宫垣",
                "src": "lilun",
                "idx": 164
              },
              {
                "t": "本宫",
                "src": "lilun",
                "idx": 165
              },
              {
                "t": "对宫",
                "src": "lilun",
                "idx": 166
              },
              {
                "t": "三合宫",
                "src": "lilun",
                "idx": 167
              },
              {
                "t": "三方四正",
                "src": "lilun",
                "idx": 168
              },
              {
                "t": "坐、锯、守",
                "src": "lilun",
                "idx": 169
              },
              {
                "t": "朝与冲",
                "src": "lilun",
                "idx": 170
              },
              {
                "t": "会与照",
                "src": "lilun",
                "idx": 171
              },
              {
                "t": "遇、加、逢、同或同度",
                "src": "lilun",
                "idx": 172
              },
              {
                "t": "辅与夹",
                "src": "lilun",
                "idx": 173
              },
              {
                "t": "扶拱",
                "src": "lilun",
                "idx": 174
              },
              {
                "t": "大限",
                "src": "lilun",
                "idx": 175
              },
              {
                "t": "流年",
                "src": "lilun",
                "idx": 176
              },
              {
                "t": "天罗地网",
                "src": "lilun",
                "idx": 177
              },
              {
                "t": "四恶曜",
                "src": "lilun",
                "idx": 178
              },
              {
                "t": "杀破狼",
                "src": "lilun",
                "idx": 179
              },
              {
                "t": "庙",
                "src": "lilun",
                "idx": 180
              },
              {
                "t": "旺",
                "src": "lilun",
                "idx": 181
              },
              {
                "t": "得地",
                "src": "lilun",
                "idx": 182
              },
              {
                "t": "利益",
                "src": "lilun",
                "idx": 183
              },
              {
                "t": "平和",
                "src": "lilun",
                "idx": 184
              },
              {
                "t": "陷落",
                "src": "lilun",
                "idx": 185
              },
              {
                "t": "闲宫",
                "src": "lilun",
                "idx": 186
              },
              {
                "t": "四马之地",
                "src": "lilun",
                "idx": 187
              },
              {
                "t": "四库之地",
                "src": "lilun",
                "idx": 188
              },
              {
                "t": "四败之地",
                "src": "lilun",
                "idx": 189
              },
              {
                "t": "男女阴阳",
                "src": "lilun",
                "idx": 190
              },
              {
                "t": "格局",
                "src": "lilun",
                "idx": 191
              },
              {
                "t": "局象",
                "src": "lilun",
                "idx": 192
              },
              {
                "t": "星的阴阳",
                "src": "lilun",
                "idx": 193
              },
              {
                "t": "地支六合",
                "src": "lilun",
                "idx": 194
              },
              {
                "t": "对星",
                "src": "lilun",
                "idx": 195
              },
              {
                "t": "体和用",
                "src": "lilun",
                "idx": 196
              },
              {
                "t": "顺行与逆行",
                "src": "lilun",
                "idx": 197
              },
              {
                "t": "空星",
                "src": "lilun",
                "idx": 198
              },
              {
                "t": "限年",
                "src": "lilun",
                "idx": 219
              },
              {
                "t": "强宫、弱宫",
                "src": "lilun",
                "idx": 220
              }
            ],
            "_sec": "基础理论",
            "_grp": "基础概念"
          },
          {
            "t": "十二宫",
            "children": [
              {
                "t": "兄弟宫",
                "src": "lilun",
                "idx": 221
              },
              {
                "t": "夫妻宫",
                "src": "lilun",
                "idx": 222
              },
              {
                "t": "子女宫",
                "src": "lilun",
                "idx": 223
              },
              {
                "t": "财帛宫",
                "src": "lilun",
                "idx": 224
              },
              {
                "t": "疾厄宫",
                "src": "lilun",
                "idx": 225
              },
              {
                "t": "迁移宫",
                "src": "lilun",
                "idx": 226
              },
              {
                "t": "交友宫",
                "src": "lilun",
                "idx": 227
              },
              {
                "t": "事业宫",
                "src": "lilun",
                "idx": 228
              },
              {
                "t": "田宅宫",
                "src": "lilun",
                "idx": 229
              },
              {
                "t": "福德宫",
                "src": "lilun",
                "idx": 230
              },
              {
                "t": "父母宫",
                "src": "lilun",
                "idx": 231
              },
              {
                "t": "身宫",
                "src": "lilun",
                "idx": 232
              }
            ],
            "_sec": "基础理论",
            "_grp": "十二宫"
          },
          {
            "t": "八字·十神",
            "children": [
              {
                "t": "比肩",
                "src": "lilun",
                "idx": 1
              },
              {
                "t": "劫财",
                "src": "lilun",
                "idx": 13
              },
              {
                "t": "偏财",
                "src": "lilun",
                "idx": 16
              },
              {
                "t": "偏官",
                "src": "lilun",
                "idx": 17
              },
              {
                "t": "偏印",
                "src": "lilun",
                "idx": 18
              },
              {
                "t": "伤官",
                "src": "lilun",
                "idx": 20
              },
              {
                "t": "食神",
                "src": "lilun",
                "idx": 22
              },
              {
                "t": "正财",
                "src": "lilun",
                "idx": 30
              },
              {
                "t": "正官",
                "src": "lilun",
                "idx": 31
              },
              {
                "t": "正印",
                "src": "lilun",
                "idx": 32
              },
              {
                "t": "大运流年十神吉凶",
                "src": "lilun",
                "idx": 40
              },
              {
                "t": "一、正财、偏财吉凶信息之像",
                "src": "lilun",
                "idx": 41
              },
              {
                "t": "二、正官、七杀吉凶信息之象",
                "src": "lilun",
                "idx": 42
              },
              {
                "t": "三、正印、偏印吉凶信息之象",
                "src": "lilun",
                "idx": 43
              },
              {
                "t": "四、比肩、劫财吉凶信息之象",
                "src": "lilun",
                "idx": 44
              },
              {
                "t": "五、食神、伤官吉凶信息之象",
                "src": "lilun",
                "idx": 45
              }
            ],
            "_sec": "基础理论",
            "_grp": "八字·十神"
          },
          {
            "t": "八字·六亲",
            "children": [
              {
                "t": "八字同六亲异六亲",
                "src": "lilun",
                "idx": 37
              },
              {
                "t": "如何区分六亲性别",
                "src": "lilun",
                "idx": 58
              },
              {
                "t": "吉凶应在那个六亲",
                "src": "lilun",
                "idx": 47
              },
              {
                "t": "看兄弟排行的方法",
                "src": "lilun",
                "idx": 59
              },
              {
                "t": "六亲",
                "src": "lilun",
                "idx": 247
              }
            ],
            "_sec": "基础理论",
            "_grp": "八字·六亲"
          },
          {
            "t": "八字·格局与基础",
            "children": [
              {
                "t": "百神论",
                "src": "lilun",
                "idx": 0
              },
              {
                "t": "大运流年作用关系补充内容",
                "src": "lilun",
                "idx": 2
              },
              {
                "t": "地支作用",
                "src": "lilun",
                "idx": 3
              },
              {
                "t": "反断论",
                "src": "lilun",
                "idx": 4
              },
              {
                "t": "先天风水",
                "src": "lilun",
                "idx": 5
              },
              {
                "t": "环境论",
                "src": "lilun",
                "idx": 10
              },
              {
                "t": "空亡论",
                "src": "lilun",
                "idx": 14
              },
              {
                "t": "命局、大运、流年三者作用关系",
                "src": "lilun",
                "idx": 15
              },
              {
                "t": "人造八字",
                "src": "lilun",
                "idx": 19
              },
              {
                "t": "四墓库",
                "src": "lilun",
                "idx": 23
              },
              {
                "t": "天干作用",
                "src": "lilun",
                "idx": 24
              },
              {
                "t": "虚实论",
                "src": "lilun",
                "idx": 26
              },
              {
                "t": "地支空亡论001",
                "src": "lilun",
                "idx": 34
              },
              {
                "t": "左右环境论002",
                "src": "lilun",
                "idx": 35
              },
              {
                "t": "命运年关系003",
                "src": "lilun",
                "idx": 36
              },
              {
                "t": "八字单双算法",
                "src": "lilun",
                "idx": 51
              },
              {
                "t": "八字后天风水",
                "src": "lilun",
                "idx": 52
              },
              {
                "t": "八字工作调动",
                "src": "lilun",
                "idx": 56
              },
              {
                "t": "八字断特殊事",
                "src": "lilun",
                "idx": 57
              },
              {
                "t": "八字牢狱信息",
                "src": "lilun",
                "idx": 61
              },
              {
                "t": "八字先天风水",
                "src": "lilun",
                "idx": 63
              }
            ],
            "_sec": "基础理论",
            "_grp": "八字·格局与基础"
          }
        ]
      },
      {
        "t": "断法细则",
        "children": [
          {
            "t": "事业",
            "children": [
              {
                "t": "工作二",
                "src": "lilun",
                "idx": 6
              },
              {
                "t": "工作三",
                "src": "lilun",
                "idx": 7
              },
              {
                "t": "工作四",
                "src": "lilun",
                "idx": 8
              },
              {
                "t": "工作一",
                "src": "lilun",
                "idx": 9
              },
              {
                "t": "工作",
                "src": "lilun",
                "idx": 62
              },
              {
                "t": "事业",
                "src": "lilun",
                "idx": 243
              }
            ],
            "_sec": "断法细则",
            "_grp": "事业"
          },
          {
            "t": "感情",
            "children": [
              {
                "t": "婚姻感情二",
                "src": "lilun",
                "idx": 11
              },
              {
                "t": "婚姻感情一",
                "src": "lilun",
                "idx": 12
              },
              {
                "t": "合婚",
                "src": "lilun",
                "idx": 39
              },
              {
                "t": "婚姻",
                "src": "lilun",
                "idx": 248
              },
              {
                "t": "命理断婚外情",
                "src": "lilun",
                "idx": 64
              }
            ],
            "_sec": "断法细则",
            "_grp": "感情"
          },
          {
            "t": "疾病",
            "children": [
              {
                "t": "人体与疾病",
                "src": "lilun",
                "idx": 21
              }
            ],
            "_sec": "断法细则",
            "_grp": "疾病"
          },
          {
            "t": "相貌",
            "children": [
              {
                "t": "相貌与身高",
                "src": "lilun",
                "idx": 25
              },
              {
                "t": "长相",
                "src": "lilun",
                "idx": 55
              }
            ],
            "_sec": "断法细则",
            "_grp": "相貌"
          },
          {
            "t": "考试",
            "children": [
              {
                "t": "学业二",
                "src": "lilun",
                "idx": 27
              },
              {
                "t": "学业一",
                "src": "lilun",
                "idx": 28
              },
              {
                "t": "学业",
                "src": "lilun",
                "idx": 48
              }
            ],
            "_sec": "断法细则",
            "_grp": "考试"
          },
          {
            "t": "择吉",
            "children": [
              {
                "t": "择日",
                "src": "lilun",
                "idx": 29
              },
              {
                "t": "命理怎样择日",
                "src": "lilun",
                "idx": 60
              }
            ],
            "_sec": "断法细则",
            "_grp": "择吉"
          },
          {
            "t": "财运",
            "children": [
              {
                "t": "财运",
                "src": "lilun",
                "idx": 244
              },
              {
                "t": "官运",
                "src": "lilun",
                "idx": 50
              }
            ],
            "_sec": "断法细则",
            "_grp": "财运"
          },
          {
            "t": "风水",
            "children": [
              {
                "t": "住房条件看法",
                "src": "lilun",
                "idx": 65
              }
            ],
            "_sec": "断法细则",
            "_grp": "风水"
          },
          {
            "t": "灾祸",
            "children": [
              {
                "t": "灾厄预测",
                "src": "lilun",
                "idx": 233
              },
              {
                "t": "车祸预测",
                "src": "lilun",
                "idx": 234
              },
              {
                "t": "坠跌预测",
                "src": "lilun",
                "idx": 235
              },
              {
                "t": "水祸",
                "src": "lilun",
                "idx": 236
              },
              {
                "t": "动物伤害",
                "src": "lilun",
                "idx": 237
              },
              {
                "t": "药物中毒灾祸",
                "src": "lilun",
                "idx": 238
              },
              {
                "t": "自杀",
                "src": "lilun",
                "idx": 239
              },
              {
                "t": "火灾暴炸祸害",
                "src": "lilun",
                "idx": 240
              },
              {
                "t": "刑讼与牢狱之灾",
                "src": "lilun",
                "idx": 241
              },
              {
                "t": "失窃破财",
                "src": "lilun",
                "idx": 242
              },
              {
                "t": "灾祸",
                "src": "lilun",
                "idx": 245
              },
              {
                "t": "官司",
                "src": "lilun",
                "idx": 246
              }
            ],
            "_sec": "断法细则",
            "_grp": "灾祸"
          },
          {
            "t": "其他",
            "children": [
              {
                "t": "性格",
                "src": "lilun",
                "idx": 54
              }
            ],
            "_sec": "断法细则",
            "_grp": "其他"
          }
        ]
      },
      {
        "t": "天纪卦象查询",
        "children": [
          {
            "t": "六十四卦",
            "children": [
              {
                "t": "乾为天",
                "src": "gua",
                "idx": 0
              },
              {
                "t": "坤为地",
                "src": "gua",
                "idx": 1
              },
              {
                "t": "水雷屯",
                "src": "gua",
                "idx": 2
              },
              {
                "t": "山水蒙",
                "src": "gua",
                "idx": 3
              },
              {
                "t": "水天需",
                "src": "gua",
                "idx": 4
              },
              {
                "t": "天水讼",
                "src": "gua",
                "idx": 5
              },
              {
                "t": "地水师",
                "src": "gua",
                "idx": 6
              },
              {
                "t": "水地比",
                "src": "gua",
                "idx": 7
              },
              {
                "t": "风天小畜",
                "src": "gua",
                "idx": 8
              },
              {
                "t": "天泽履",
                "src": "gua",
                "idx": 9
              },
              {
                "t": "地天泰",
                "src": "gua",
                "idx": 10
              },
              {
                "t": "天地否",
                "src": "gua",
                "idx": 11
              },
              {
                "t": "天火同人",
                "src": "gua",
                "idx": 12
              },
              {
                "t": "火天大有",
                "src": "gua",
                "idx": 13
              },
              {
                "t": "地山谦",
                "src": "gua",
                "idx": 14
              },
              {
                "t": "雷地豫",
                "src": "gua",
                "idx": 15
              },
              {
                "t": "泽雷随",
                "src": "gua",
                "idx": 16
              },
              {
                "t": "山风蛊",
                "src": "gua",
                "idx": 17
              },
              {
                "t": "地泽临",
                "src": "gua",
                "idx": 18
              },
              {
                "t": "风地观",
                "src": "gua",
                "idx": 19
              },
              {
                "t": "火雷噬嗑",
                "src": "gua",
                "idx": 20
              },
              {
                "t": "山火贲",
                "src": "gua",
                "idx": 21
              },
              {
                "t": "山地剥",
                "src": "gua",
                "idx": 22
              },
              {
                "t": "地雷复",
                "src": "gua",
                "idx": 23
              },
              {
                "t": "天雷无妄",
                "src": "gua",
                "idx": 24
              },
              {
                "t": "山天大畜",
                "src": "gua",
                "idx": 25
              },
              {
                "t": "山雷颐",
                "src": "gua",
                "idx": 26
              },
              {
                "t": "泽风大过",
                "src": "gua",
                "idx": 27
              },
              {
                "t": "坎为水",
                "src": "gua",
                "idx": 28
              },
              {
                "t": "离为火",
                "src": "gua",
                "idx": 29
              },
              {
                "t": "泽山咸",
                "src": "gua",
                "idx": 30
              },
              {
                "t": "雷风恒",
                "src": "gua",
                "idx": 31
              },
              {
                "t": "天山遯",
                "src": "gua",
                "idx": 32
              },
              {
                "t": "雷天大壮",
                "src": "gua",
                "idx": 33
              },
              {
                "t": "火地晋",
                "src": "gua",
                "idx": 34
              },
              {
                "t": "地火明夷",
                "src": "gua",
                "idx": 35
              },
              {
                "t": "风火家人",
                "src": "gua",
                "idx": 36
              },
              {
                "t": "火泽睽",
                "src": "gua",
                "idx": 37
              },
              {
                "t": "水山蹇",
                "src": "gua",
                "idx": 38
              },
              {
                "t": "雷水解",
                "src": "gua",
                "idx": 39
              },
              {
                "t": "山泽损",
                "src": "gua",
                "idx": 40
              },
              {
                "t": "风雷益",
                "src": "gua",
                "idx": 41
              },
              {
                "t": "泽天夬",
                "src": "gua",
                "idx": 42
              },
              {
                "t": "天风姤",
                "src": "gua",
                "idx": 43
              },
              {
                "t": "泽地萃",
                "src": "gua",
                "idx": 44
              },
              {
                "t": "地风升",
                "src": "gua",
                "idx": 45
              },
              {
                "t": "泽水困",
                "src": "gua",
                "idx": 46
              },
              {
                "t": "水风井",
                "src": "gua",
                "idx": 47
              },
              {
                "t": "泽火革",
                "src": "gua",
                "idx": 48
              },
              {
                "t": "火风鼎",
                "src": "gua",
                "idx": 49
              },
              {
                "t": "震为雷",
                "src": "gua",
                "idx": 50
              },
              {
                "t": "艮为山",
                "src": "gua",
                "idx": 51
              },
              {
                "t": "风山渐",
                "src": "gua",
                "idx": 52
              },
              {
                "t": "雷泽归妹",
                "src": "gua",
                "idx": 53
              },
              {
                "t": "雷火丰",
                "src": "gua",
                "idx": 54
              },
              {
                "t": "火山旅",
                "src": "gua",
                "idx": 55
              },
              {
                "t": "巽为风",
                "src": "gua",
                "idx": 56
              },
              {
                "t": "兑为泽",
                "src": "gua",
                "idx": 57
              },
              {
                "t": "风水涣",
                "src": "gua",
                "idx": 58
              },
              {
                "t": "水泽节",
                "src": "gua",
                "idx": 59
              },
              {
                "t": "风泽中孚",
                "src": "gua",
                "idx": 60
              },
              {
                "t": "雷山小过",
                "src": "gua",
                "idx": 61
              },
              {
                "t": "水火既济",
                "src": "gua",
                "idx": 62
              },
              {
                "t": "火水未济",
                "src": "gua",
                "idx": 63
              }
            ],
            "_sec": "天纪卦象查询",
            "_grp": "六十四卦"
          },
          {
            "t": "人间道",
            "children": [
              {
                "t": "乾为天",
                "src": "rendao",
                "idx": 0
              },
              {
                "t": "坤为地",
                "src": "rendao",
                "idx": 1
              },
              {
                "t": "水雷屯",
                "src": "rendao",
                "idx": 2
              },
              {
                "t": "山水蒙",
                "src": "rendao",
                "idx": 3
              },
              {
                "t": "水天需",
                "src": "rendao",
                "idx": 4
              },
              {
                "t": "天水讼",
                "src": "rendao",
                "idx": 5
              },
              {
                "t": "地水师",
                "src": "rendao",
                "idx": 6
              },
              {
                "t": "水地比",
                "src": "rendao",
                "idx": 7
              },
              {
                "t": "风天小畜",
                "src": "rendao",
                "idx": 8
              },
              {
                "t": "天泽履",
                "src": "rendao",
                "idx": 9
              },
              {
                "t": "地天泰",
                "src": "rendao",
                "idx": 10
              },
              {
                "t": "天地否",
                "src": "rendao",
                "idx": 11
              },
              {
                "t": "天火同人",
                "src": "rendao",
                "idx": 12
              },
              {
                "t": "火天大有",
                "src": "rendao",
                "idx": 13
              },
              {
                "t": "地山谦",
                "src": "rendao",
                "idx": 14
              },
              {
                "t": "雷地豫",
                "src": "rendao",
                "idx": 15
              },
              {
                "t": "泽雷随",
                "src": "rendao",
                "idx": 16
              },
              {
                "t": "山风蛊",
                "src": "rendao",
                "idx": 17
              },
              {
                "t": "地泽临",
                "src": "rendao",
                "idx": 18
              },
              {
                "t": "风地观",
                "src": "rendao",
                "idx": 19
              },
              {
                "t": "火雷噬嗑",
                "src": "rendao",
                "idx": 20
              },
              {
                "t": "山火贲",
                "src": "rendao",
                "idx": 21
              },
              {
                "t": "山地剥",
                "src": "rendao",
                "idx": 22
              },
              {
                "t": "地雷复",
                "src": "rendao",
                "idx": 23
              },
              {
                "t": "天雷无妄",
                "src": "rendao",
                "idx": 24
              },
              {
                "t": "山天大畜",
                "src": "rendao",
                "idx": 25
              },
              {
                "t": "山雷颐",
                "src": "rendao",
                "idx": 26
              },
              {
                "t": "泽风大过",
                "src": "rendao",
                "idx": 27
              },
              {
                "t": "坎为水",
                "src": "rendao",
                "idx": 28
              },
              {
                "t": "离为火",
                "src": "rendao",
                "idx": 29
              },
              {
                "t": "泽山咸",
                "src": "rendao",
                "idx": 30
              },
              {
                "t": "雷风恒",
                "src": "rendao",
                "idx": 31
              },
              {
                "t": "天山遯",
                "src": "rendao",
                "idx": 32
              },
              {
                "t": "雷天大壮",
                "src": "rendao",
                "idx": 33
              },
              {
                "t": "火地晋",
                "src": "rendao",
                "idx": 34
              },
              {
                "t": "地火明夷",
                "src": "rendao",
                "idx": 35
              },
              {
                "t": "风火家人",
                "src": "rendao",
                "idx": 36
              },
              {
                "t": "火泽睽",
                "src": "rendao",
                "idx": 37
              },
              {
                "t": "水山蹇",
                "src": "rendao",
                "idx": 38
              },
              {
                "t": "雷水解",
                "src": "rendao",
                "idx": 39
              },
              {
                "t": "山泽损",
                "src": "rendao",
                "idx": 40
              },
              {
                "t": "风雷益",
                "src": "rendao",
                "idx": 41
              },
              {
                "t": "泽天夬",
                "src": "rendao",
                "idx": 42
              },
              {
                "t": "天风姤",
                "src": "rendao",
                "idx": 43
              },
              {
                "t": "泽地萃",
                "src": "rendao",
                "idx": 44
              },
              {
                "t": "地风升",
                "src": "rendao",
                "idx": 45
              },
              {
                "t": "泽水困",
                "src": "rendao",
                "idx": 46
              },
              {
                "t": "水风井",
                "src": "rendao",
                "idx": 47
              },
              {
                "t": "泽火革",
                "src": "rendao",
                "idx": 48
              },
              {
                "t": "火风鼎",
                "src": "rendao",
                "idx": 49
              },
              {
                "t": "震为雷",
                "src": "rendao",
                "idx": 50
              },
              {
                "t": "艮为山",
                "src": "rendao",
                "idx": 51
              },
              {
                "t": "风山渐",
                "src": "rendao",
                "idx": 52
              },
              {
                "t": "雷泽归妹",
                "src": "rendao",
                "idx": 53
              },
              {
                "t": "雷火丰",
                "src": "rendao",
                "idx": 54
              },
              {
                "t": "火山旅",
                "src": "rendao",
                "idx": 55
              },
              {
                "t": "巽为风",
                "src": "rendao",
                "idx": 56
              },
              {
                "t": "兑为泽",
                "src": "rendao",
                "idx": 57
              },
              {
                "t": "风水涣",
                "src": "rendao",
                "idx": 58
              },
              {
                "t": "水泽节",
                "src": "rendao",
                "idx": 59
              },
              {
                "t": "风泽中孚",
                "src": "rendao",
                "idx": 60
              },
              {
                "t": "雷山小过",
                "src": "rendao",
                "idx": 61
              },
              {
                "t": "水火既济",
                "src": "rendao",
                "idx": 62
              },
              {
                "t": "火水未济",
                "src": "rendao",
                "idx": 63
              }
            ],
            "_sec": "天纪卦象查询",
            "_grp": "人间道"
          },
          {
            "t": "地脉道"
          }
        ]
      },
      {
        "t": "子女",
        "src": "lilun",
        "idx": 33
      },
      {
        "t": "时辰效验",
        "children": [
          {
            "t": "验证方法"
          },
          {
            "t": "验证时辰法",
            "src": "lilun",
            "idx": 38
          }
        ]
      },
      {
        "t": "案例查询",
        "children": [
          {
            "t": "大师案例",
            "children": [
              {
                "t": "倪师001",
                "src": "mingli",
                "idx": 10
              },
              {
                "t": "倪师002",
                "src": "mingli",
                "idx": 5
              },
              {
                "t": "倪师003",
                "src": "mingli",
                "idx": 6
              },
              {
                "t": "倪师004",
                "src": "mingli",
                "idx": 7
              },
              {
                "t": "倪师005",
                "src": "mingli",
                "idx": 8
              },
              {
                "t": "倪师05",
                "src": "mingli",
                "idx": 9
              }
            ],
            "_sec": "案例查询",
            "_grp": "大师案例"
          },
          {
            "t": "收集案例",
            "children": [
              {
                "t": "案例十",
                "src": "mingli",
                "idx": 64
              },
              {
                "t": "案十五",
                "src": "mingli",
                "idx": 2
              },
              {
                "t": "案例二",
                "src": "mingli",
                "idx": 56
              },
              {
                "t": "案例四",
                "src": "mingli",
                "idx": 58
              },
              {
                "t": "案例六",
                "src": "mingli",
                "idx": 60
              },
              {
                "t": "案例七",
                "src": "mingli",
                "idx": 61
              },
              {
                "t": "案例八",
                "src": "mingli",
                "idx": 62
              },
              {
                "t": "案例九",
                "src": "mingli",
                "idx": 98
              },
              {
                "t": "案例三",
                "src": "mingli",
                "idx": 57
              },
              {
                "t": "案五十",
                "src": "mingli",
                "idx": 47
              },
              {
                "t": "例四六",
                "src": "mingli",
                "idx": 48
              },
              {
                "t": "例四四",
                "src": "mingli",
                "idx": 49
              },
              {
                "t": "例四五",
                "src": "mingli",
                "idx": 50
              },
              {
                "t": "例六十",
                "src": "mingli",
                "idx": 51
              },
              {
                "t": "例一百",
                "src": "mingli",
                "idx": 52
              },
              {
                "t": "例九八",
                "src": "mingli",
                "idx": 53
              },
              {
                "t": "例九七",
                "src": "mingli",
                "idx": 54
              },
              {
                "t": "案例一",
                "src": "mingli",
                "idx": 55
              },
              {
                "t": "案例五",
                "src": "mingli",
                "idx": 59
              },
              {
                "t": "例十一",
                "src": "mingli",
                "idx": 65
              },
              {
                "t": "案十二",
                "src": "mingli",
                "idx": 66
              },
              {
                "t": "案十三",
                "src": "mingli",
                "idx": 67
              },
              {
                "t": "案十四",
                "src": "mingli",
                "idx": 68
              },
              {
                "t": "例十五",
                "src": "mingli",
                "idx": 69
              },
              {
                "t": "例十六",
                "src": "mingli",
                "idx": 70
              },
              {
                "t": "例十七",
                "src": "mingli",
                "idx": 71
              },
              {
                "t": "例十八",
                "src": "mingli",
                "idx": 72
              },
              {
                "t": "例十九",
                "src": "mingli",
                "idx": 73
              },
              {
                "t": "例二十",
                "src": "mingli",
                "idx": 74
              },
              {
                "t": "例二一",
                "src": "mingli",
                "idx": 75
              },
              {
                "t": "例二二",
                "src": "mingli",
                "idx": 76
              },
              {
                "t": "例二三",
                "src": "mingli",
                "idx": 77
              },
              {
                "t": "例二四",
                "src": "mingli",
                "idx": 78
              },
              {
                "t": "例二五",
                "src": "mingli",
                "idx": 79
              },
              {
                "t": "例二六",
                "src": "mingli",
                "idx": 80
              },
              {
                "t": "例二七",
                "src": "mingli",
                "idx": 81
              },
              {
                "t": "例二八",
                "src": "mingli",
                "idx": 82
              },
              {
                "t": "例二九",
                "src": "mingli",
                "idx": 83
              },
              {
                "t": "例三十",
                "src": "mingli",
                "idx": 84
              },
              {
                "t": "例三一",
                "src": "mingli",
                "idx": 85
              },
              {
                "t": "例三二",
                "src": "mingli",
                "idx": 86
              },
              {
                "t": "例三三",
                "src": "mingli",
                "idx": 87
              },
              {
                "t": "例三四",
                "src": "mingli",
                "idx": 88
              },
              {
                "t": "例三五",
                "src": "mingli",
                "idx": 89
              },
              {
                "t": "例三六",
                "src": "mingli",
                "idx": 90
              },
              {
                "t": "例三七",
                "src": "mingli",
                "idx": 91
              },
              {
                "t": "例三八",
                "src": "mingli",
                "idx": 92
              },
              {
                "t": "例三九",
                "src": "mingli",
                "idx": 93
              },
              {
                "t": "例四十",
                "src": "mingli",
                "idx": 94
              },
              {
                "t": "例四一",
                "src": "mingli",
                "idx": 95
              },
              {
                "t": "例四二",
                "src": "mingli",
                "idx": 96
              },
              {
                "t": "例四三",
                "src": "mingli",
                "idx": 97
              },
              {
                "t": "例五十",
                "src": "mingli",
                "idx": 99
              }
            ],
            "_sec": "案例查询",
            "_grp": "收集案例"
          },
          {
            "t": "自断案例",
            "children": [
              {
                "t": "张柏芝",
                "src": "mingli",
                "idx": 1
              },
              {
                "t": "CC",
                "src": "mingli",
                "idx": 3
              },
              {
                "t": "民国58年",
                "src": "mingli",
                "idx": 13
              },
              {
                "t": "民国40年",
                "src": "mingli",
                "idx": 14
              },
              {
                "t": "民国46年",
                "src": "mingli",
                "idx": 27
              },
              {
                "t": "民国50年",
                "src": "mingli",
                "idx": 16
              },
              {
                "t": "民国38年",
                "src": "mingli",
                "idx": 36
              },
              {
                "t": "民国51年",
                "src": "mingli",
                "idx": 18
              },
              {
                "t": "民国47年",
                "src": "mingli",
                "idx": 19
              },
              {
                "t": "民国37年",
                "src": "mingli",
                "idx": 20
              },
              {
                "t": "民国41年",
                "src": "mingli",
                "idx": 32
              },
              {
                "t": "民国34年",
                "src": "mingli",
                "idx": 24
              },
              {
                "t": "民国55年",
                "src": "mingli",
                "idx": 25
              },
              {
                "t": "民国33年",
                "src": "mingli",
                "idx": 26
              },
              {
                "t": "民国30年",
                "src": "mingli",
                "idx": 28
              },
              {
                "t": "1111",
                "src": "mingli",
                "idx": 29
              },
              {
                "t": "民国28年",
                "src": "mingli",
                "idx": 33
              },
              {
                "t": "民国49年",
                "src": "mingli",
                "idx": 34
              },
              {
                "t": "民国18年",
                "src": "mingli",
                "idx": 35
              },
              {
                "t": "民国31年",
                "src": "mingli",
                "idx": 37
              },
              {
                "t": "风水一",
                "src": "mingli",
                "idx": 39
              },
              {
                "t": "阴宅五",
                "src": "mingli",
                "idx": 41
              },
              {
                "t": "中华易123",
                "src": "mingli",
                "idx": 100
              },
              {
                "t": "HJ",
                "src": "mingli",
                "idx": 101
              },
              {
                "t": "RTT",
                "src": "mingli",
                "idx": 102
              },
              {
                "t": "陈彦中",
                "src": "mingli",
                "idx": 103
              },
              {
                "t": "ymq",
                "src": "mingli",
                "idx": 104
              },
              {
                "t": "芳草护法",
                "src": "mingli",
                "idx": 105
              },
              {
                "t": "黄振华",
                "src": "mingli",
                "idx": 106
              }
            ],
            "_sec": "案例查询",
            "_grp": "自断案例"
          }
        ]
      }
    ]
  }
]
