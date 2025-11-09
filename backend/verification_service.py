"""
独立的新闻真假判别服务
可以被深度思考和浅度思考两种模式调用
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 添加路径以便导入
deepsearch_demo_path = os.path.join(os.path.dirname(__file__), 'deepsearchagent_demo')
sys.path.insert(0, deepsearch_demo_path)

from src.llms import BaseLLM
from src.nodes.verification_node import NewsVerificationNode
from src.utils.config import Config
from loguru import logger


class VerificationService:
    """新闻真假判别服务"""
    
    def __init__(self, llm_client: Optional[BaseLLM] = None, config: Optional[Config] = None):
        """
        初始化判别服务
        
        Args:
            llm_client: LLM客户端，必须提供
            config: 配置对象，用于输出目录等配置
        """
        if not llm_client:
            raise ValueError("必须提供 llm_client 参数")
        
        self.llm_client = llm_client
        
        # 配置对象（主要用于输出目录）
        if config:
            self.config = config
        else:
            # 创建默认配置（不验证，因为我们已经有了LLM客户端）
            from src.utils.config import Config
            self.config = Config(output_dir="reports")
        
        # 初始化判别节点
        self.verification_node = NewsVerificationNode(self.llm_client)
        
        logger.info("新闻真假判别服务已初始化")
    
    def verify_news(self, query: str, final_report: str, save_result: bool = False, 
                   output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        执行新闻真假判别
        
        Args:
            query: 原始查询/新闻内容
            final_report: 完整的研究报告
            save_result: 是否保存判别结果到文件
            output_dir: 输出目录，如果不提供则使用配置中的目录
            
        Returns:
            包含判别结果的字典
        """
        try:
            logger.info("开始进行新闻真假判别...")
            
            # 准备输入数据
            verification_input = {
                "query": query,
                "final_report": final_report
            }
            
            # 调用判别节点
            verification_result = self.verification_node.run(verification_input)
            
            verdict = verification_result.get("verdict", "无法确定")
            summary = verification_result.get("summary", "无法生成判别摘要")
            
            logger.info(f"判别结果: {verdict}")
            
            # 构建返回结果
            result = {
                "verdict": verdict,
                "summary": summary,
                "query": query,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存结果到文件（如果需要）
            if save_result:
                self._save_verification_result(result, output_dir)
            
            return result
            
        except Exception as e:
            logger.error(f"新闻真假判别失败: {str(e)}")
            # 返回错误结果
            return {
                "verdict": "无法确定",
                "summary": f"判别过程中发生错误: {str(e)}",
                "query": query,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
    
    def _save_verification_result(self, result: Dict[str, Any], output_dir: Optional[str] = None):
        """
        保存判别结果到文件
        
        Args:
            result: 判别结果字典
            output_dir: 输出目录
        """
        try:
            output_dir = output_dir or self.config.output_dir
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_safe = "".join(c for c in result["query"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            query_safe = query_safe.replace(' ', '_')[:30]
            
            # 保存为 JSON 格式
            json_filename = f"verification_result_{query_safe}_{timestamp}.json"
            json_filepath = os.path.join(output_dir, json_filename)
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"判别结果已保存到: {json_filepath}")
            
            # 同时保存为 Markdown 格式
            md_filename = f"verification_result_{query_safe}_{timestamp}.md"
            md_filepath = os.path.join(output_dir, md_filename)
            
            # 根据判别结果选择emoji
            emoji_map = {
                "真": "✅",
                "假": "❌",
                "部分真实": "⚠️",
                "无法确定": "❓"
            }
            emoji = emoji_map.get(result["verdict"], "❓")
            
            md_content = f"""# {emoji} 新闻真假判别结果

## 查询内容

{result['query']}

## 判别结果

**{result['verdict']}**

## 判别摘要

{result['summary']}

## 判别时间

{result['timestamp']}

---
*此文件由新闻真假判别服务自动生成*
"""
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"判别结果（Markdown格式）已保存到: {md_filepath}")
            
        except Exception as e:
            logger.error(f"保存判别结果时发生错误: {str(e)}")


def create_verification_service(api_key: Optional[str] = None, 
                                provider: str = "deepseek",
                                model_name: Optional[str] = None,
                                output_dir: Optional[str] = None) -> VerificationService:
    """
    创建判别服务实例的便捷函数
    
    Args:
        api_key: API密钥
        provider: LLM提供商 (deepseek/openai)
        model_name: 模型名称
        output_dir: 输出目录
        
    Returns:
        VerificationService实例
    """
    from src.llms import DeepSeekLLM, OpenAILLM
    from src.utils.config import Config
    
    if provider == "deepseek":
        llm_client = DeepSeekLLM(
            api_key=api_key,
            model_name=model_name or "deepseek-chat"
        )
    elif provider == "openai":
        llm_client = OpenAILLM(
            api_key=api_key,
            model_name=model_name or "gpt-4"
        )
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")
    
    # 创建配置对象（不需要验证，因为我们已经有了LLM客户端）
    config = Config(
        deepseek_api_key=api_key if provider == "deepseek" else None,
        openai_api_key=api_key if provider == "openai" else None,
        tavily_api_key=None,  # 判罚服务不需要搜索API
        default_llm_provider=provider,
        deepseek_model=model_name or "deepseek-chat",
        openai_model=model_name or "gpt-4",
        output_dir=output_dir or "reports"
    )
    
    return VerificationService(llm_client=llm_client, config=config)

