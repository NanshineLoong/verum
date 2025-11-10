# pip install openai
import os
from openai import AzureOpenAI

OPENAI_API_KEY = "1a9835533bfe5ad7ccd4683e05b281d7"
MCP_API_TOKEN  = "sk_7b8rLxqLvz6u2XCSmbn2xE1inlG1ctdN7LCecgvjeBY="

client = AzureOpenAI(
    base_url="https://gpt.yunstorm.com/openai",   # 按你的代理API基址
    api_key=OPENAI_API_KEY,
    api_version="2025-04-01-preview"              # 按手册的 Responses API 版本
)

def build_prompt(news_text: str) -> str:
    return f"""
你将收到一份“新闻报告”。请完成并发布一条吸引人的辟谣小红书：
1) 生成一个中文标题（≤30字），要求客观、明确、可读性强，很有吸引力和煽动力。
2) 生成中文文案（≤120字），提炼关键信息，在尊重事实的前提下富有情绪。
3) 生成 3–6 个话题标签（每个以 # 开头，不含空格，贴合受众与平台，比如 #科技热点）。
4) 直接使用已连接的 MCP 服务器中与“小红书发布/创建/上传”相关的工具来发布内容：
   - 将[标题]、[文案]、[话题]映射到工具所需字段（字段名不同时请自行匹配）。
   - 若工具支持图片且新闻中含有可用图片 URL，请一并上传；若没有图片可尝试生成一张相关封面图片并发布笔记。
   - 不要向我追问，直接做出合理决定并执行发布。
5) 不要捏造事实；信息的来源以及时间非常重要，如果有的话在文案结尾简要注明来源名或机构名；避免泄露隐私与受限信息。

6)在发布成功后告诉我图片的来源
【新闻报告原文】
\"\"\"{news_text.strip()}\"\"\"
"""


def publish_xhs_from_news(news_text: str):
    prompt = build_prompt(news_text)

    return client.responses.create(
        model="gpt-4o",   # 或 gpt-4.1 / gpt-4o-mini 等支持 Responses API 的模型
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt}
                ],
            }
        ],
        tool_choice="auto",  # 让模型自动决定并调用 MCP 工具
        tools=[
            {
                "type": "mcp",
                "server_label": "xhs_mcp",
                "server_url": "https://mcp.zouying.work/mcp",
                "require_approval": "never",   # 如要每次确认可改为 "always"
                # 等价于：claude mcp add --header "X-API-Key: <你的API-TOKEN>"
                "headers": {
                    "X-API-Key": MCP_API_TOKEN
                }
            }
        ],
    )

if __name__ == "__main__":
    NEWS_REPORT = """
特斯拉股东批准了一项史无前例的薪酬方案，该方案将首席执行官马斯克与公司的未来十年深度绑定。这笔交易若能完全实现，马斯克价值可能高达近一万亿美元，这不仅是商业史上规模最大的企业高管薪酬计划，更是一场押注特斯拉转型为人工智能与机器人巨头的巨大赌局。

美东时间周四，在特斯拉奥斯汀工厂举行的年度股东大会上，这项薪酬方案以超过75%的支持率获得通过。这一结果标志着马斯克赢得了关键的信任投票，尤其是在该方案此前曾遭遇部分知名投资者、代理顾问公司和活动家的公开反对之后。

此次批准被视为股东对马斯克领导力的关键认可，旨在确保他在特斯拉迈向人工智能和机器人领域的“关键拐点”上保持专注。此前，马斯克在特斯拉之外的活动，包括其政治言论，曾对特斯拉品牌造成了负面影响。如今，这份天价薪酬计划将他的个人利益与特斯拉的未来增长更紧密地捆绑在一起。

马斯克在会上宣布，特斯拉将开启“一本全新的书”，其使命也从“加速世界向可持续能源的过渡”转变为“实现可持续的富足”。他描绘了由Optimus人形机器人、Cybercab自动驾驶汽车以及通过软件升级实现的庞大自动驾驶车队构成的未来蓝图，将公司的赌注从电动汽车毅然转向了人工智能与机器人。

一笔史无前例的“对赌”
这份薪酬方案的规模远超全球任何一家企业的CEO报酬。根据AFL-CIO的CEO薪酬数据库，微软CEO Satya Nadella在2024年的薪酬刚刚超过7900万美元，苹果CEO Tim Cook约为7500万美元，星巴克CEO Brian Niccol的薪酬略低于9600万美元。而马斯克的潜在收益让这些数字相形见绌。与这些高管不同，马斯克在特斯拉不领取传统薪水。
    """

    resp = publish_xhs_from_news(NEWS_REPORT)

    # 打印结果（模型输出和工具调用记录），便于你在控制台查看
    try:
        print(resp.output_text)
    except Exception:
        print(resp.to_json())
