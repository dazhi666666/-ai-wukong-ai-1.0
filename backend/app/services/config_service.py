import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.config import LLMProvider, LLMConfig, ModelCatalogEntry


PRESET_PROVIDERS = [
    {
        "name": "dashscope",
        "display_name": "阿里云百炼",
        "description": "阿里云百炼大模型服务平台，提供通义千问等模型",
        "website": "https://bailian.console.aliyun.com",
        "api_doc_url": "https://help.aliyun.com/zh/dashscope/",
        "default_base_url": "https://dashscope.aliyuncs.com/api/v1",
        "supported_features": ["chat", "completion", "embedding", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "302ai",
        "display_name": "302.AI",
        "description": "302.AI是企业级AI聚合平台，提供多种主流大模型的统一接口",
        "website": "https://302.ai",
        "api_doc_url": "https://doc.302.ai",
        "default_base_url": "https://api.302.ai/v1",
        "supported_features": ["chat", "completion", "embedding", "image", "vision", "function_calling", "streaming"],
        "is_aggregator": True,
    },
    {
        "name": "deepseek",
        "display_name": "DeepSeek",
        "description": "DeepSeek提供高性能的AI推理服务",
        "website": "https://www.deepseek.com",
        "api_doc_url": "https://platform.deepseek.com/api-docs",
        "default_base_url": "https://api.deepseek.com",
        "supported_features": ["chat", "completion", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "openai",
        "display_name": "OpenAI",
        "description": "OpenAI是人工智能领域的领先公司，提供GPT系列模型",
        "website": "https://openai.com",
        "api_doc_url": "https://platform.openai.com/docs",
        "default_base_url": "https://api.openai.com/v1",
        "supported_features": ["chat", "completion", "embedding", "image", "vision", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "anthropic",
        "display_name": "Anthropic",
        "description": "Anthropic专注于AI安全研究，提供Claude系列模型",
        "website": "https://anthropic.com",
        "api_doc_url": "https://docs.anthropic.com",
        "default_base_url": "https://api.anthropic.com",
        "supported_features": ["chat", "completion", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "google",
        "display_name": "Google AI",
        "description": "Google的人工智能平台，提供Gemini系列模型",
        "website": "https://ai.google.dev",
        "api_doc_url": "https://ai.google.dev/docs",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "supported_features": ["chat", "completion", "embedding", "vision", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "azure",
        "display_name": "Azure OpenAI",
        "description": "Microsoft Azure平台上的OpenAI服务",
        "website": "https://azure.microsoft.com/en-us/products/ai-services/openai-service",
        "api_doc_url": "https://learn.microsoft.com/en-us/azure/ai-services/openai/",
        "default_base_url": "https://your-resource.openai.azure.com",
        "supported_features": ["chat", "completion", "embedding", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "zhipu",
        "display_name": "智谱AI",
        "description": "智谱AI提供GLM系列中文大模型",
        "website": "https://zhipuai.cn",
        "api_doc_url": "https://open.bigmodel.cn/doc",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "supported_features": ["chat", "completion", "embedding", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "baidu",
        "display_name": "百度智能云",
        "description": "百度提供的文心一言等AI服务",
        "website": "https://cloud.baidu.com",
        "api_doc_url": "https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html",
        "default_base_url": "https://aip.baidubce.com",
        "supported_features": ["chat", "completion", "embedding", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "moonshot",
        "display_name": "月之暗面 (Moonshot)",
        "description": "月之暗面提供Kimi系列大模型服务",
        "website": "https://www.moonshot.cn",
        "api_doc_url": "https://platform.moonshot.cn/docs",
        "default_base_url": "https://api.moonshot.cn/v1",
        "supported_features": ["chat", "completion", "function_calling", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "minimax",
        "display_name": "MiniMax",
        "description": "MiniMax提供文本生成服务",
        "website": "https://www.minimax.io",
        "api_doc_url": "https://platform.minimax.io/docs",
        "default_base_url": "https://api.minimax.chat/v1",
        "supported_features": ["chat", "completion", "embedding", "streaming"],
        "is_aggregator": False,
    },
    {
        "name": "openrouter",
        "display_name": "OpenRouter",
        "description": "OpenRouter是AI模型的统一聚合平台",
        "website": "https://openrouter.ai",
        "api_doc_url": "https://openrouter.ai/docs",
        "default_base_url": "https://openrouter.ai/api/v1",
        "supported_features": ["chat", "completion", "embedding", "image", "vision", "function_calling", "streaming"],
        "is_aggregator": True,
    },
]


class ConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_providers(self) -> List[LLMProvider]:
        return self.db.query(LLMProvider).order_by(LLMProvider.id).all()

    def get_provider_by_name(self, name: str) -> Optional[LLMProvider]:
        return self.db.query(LLMProvider).filter(LLMProvider.name == name).first()

    def get_active_providers(self) -> List[LLMProvider]:
        return self.db.query(LLMProvider).filter(LLMProvider.is_active == True).order_by(LLMProvider.id).all()

    def create_provider(self, provider_data: dict) -> LLMProvider:
        if isinstance(provider_data.get("supported_features"), list):
            provider_data["supported_features"] = json.dumps(provider_data["supported_features"])
        
        provider = LLMProvider(**provider_data)
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def update_provider(self, name: str, provider_data: dict) -> Optional[LLMProvider]:
        provider = self.get_provider_by_name(name)
        if not provider:
            return None
        
        if "supported_features" in provider_data:
            if isinstance(provider_data["supported_features"], list):
                provider_data["supported_features"] = json.dumps(provider_data["supported_features"])
        
        for key, value in provider_data.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def delete_provider(self, name: str) -> bool:
        provider = self.get_provider_by_name(name)
        if not provider:
            return False
        
        self.db.delete(provider)
        self.db.commit()
        return True

    def toggle_provider(self, name: str) -> Optional[LLMProvider]:
        provider = self.get_provider_by_name(name)
        if not provider:
            return None
        
        provider.is_active = not provider.is_active
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def init_preset_providers(self) -> int:
        count = 0
        for preset in PRESET_PROVIDERS:
            existing = self.get_provider_by_name(preset["name"])
            if not existing:
                self.create_provider(preset)
                count += 1
        return count

    def get_all_configs(self) -> List[LLMConfig]:
        return self.db.query(LLMConfig).order_by(LLMConfig.priority.desc()).all()

    def get_config_by_id(self, config_id: int) -> Optional[LLMConfig]:
        return self.db.query(LLMConfig).filter(LLMConfig.id == config_id).first()

    def get_config_by_provider_model(self, provider: str, model_name: str) -> Optional[LLMConfig]:
        return self.db.query(LLMConfig).filter(
            LLMConfig.provider == provider,
            LLMConfig.model_name == model_name
        ).first()

    def get_enabled_configs(self) -> List[LLMConfig]:
        return self.db.query(LLMConfig).filter(LLMConfig.enabled == True).order_by(LLMConfig.priority.desc()).all()

    def get_default_config(self) -> Optional[LLMConfig]:
        return self.db.query(LLMConfig).filter(LLMConfig.is_default == True).first()

    def create_or_update_config(self, config_data: dict) -> LLMConfig:
        provider = config_data.get("provider")
        model_name = config_data.get("model_name")
        
        if isinstance(config_data.get("suitable_roles"), list):
            config_data["suitable_roles"] = json.dumps(config_data["suitable_roles"])
        if isinstance(config_data.get("features"), list):
            config_data["features"] = json.dumps(config_data["features"])
        if isinstance(config_data.get("recommended_depths"), list):
            config_data["recommended_depths"] = json.dumps(config_data["recommended_depths"])

        existing = self.get_config_by_provider_model(provider, model_name)
        
        if existing:
            for key, value in config_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            config = LLMConfig(**config_data)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config

    def delete_config(self, provider: str, model_name: str) -> bool:
        config = self.get_config_by_provider_model(provider, model_name)
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        return True

    def set_default_config(self, config_id: int) -> Optional[LLMConfig]:
        self.db.query(LLMConfig).update({"is_default": False})
        
        config = self.get_config_by_id(config_id)
        if not config:
            return None
        
        config.is_default = True
        self.db.commit()
        self.db.refresh(config)
        return config

    def toggle_config(self, config_id: int) -> Optional[LLMConfig]:
        config = self.get_config_by_id(config_id)
        if not config:
            return None
        
        config.enabled = not config.enabled
        self.db.commit()
        self.db.refresh(config)
        return config


PRESET_MODEL_CATALOG = {
    "deepseek": [
        {"name": "deepseek-chat", "display_name": "DeepSeek Chat", "description": "通用对话模型，适合日常任务", "context_length": 64000, "max_tokens": 4096, "input_price_per_1k": 0.000, "output_price_per_1k": 0.000, "currency": "CNY", "capabilities": ["chat", "function_calling"]},
        {"name": "deepseek-reasoner", "display_name": "DeepSeek R1 (推理模型)", "description": "深度推理模型，适合复杂问题分析", "context_length": 64000, "max_tokens": 4096, "input_price_per_1k": 0.000, "output_price_per_1k": 0.000, "currency": "CNY", "capabilities": ["chat", "reasoning"]},
        {"name": "deepseek-coder", "display_name": "DeepSeek Coder", "description": "编程专用模型", "context_length": 64000, "max_tokens": 4096, "input_price_per_1k": 0.000, "output_price_per_1k": 0.000, "currency": "CNY", "capabilities": ["code"]},
    ],
    "openai": [
        {"name": "gpt-4o", "display_name": "GPT-4o", "description": "OpenAI最新旗舰模型，多模态", "context_length": 128000, "max_tokens": 16384, "input_price_per_1k": 2.5, "output_price_per_1k": 10.0, "currency": "USD", "capabilities": ["chat", "vision", "function_calling"]},
        {"name": "gpt-4-turbo", "display_name": "GPT-4 Turbo", "description": "高性能GPT-4版本", "context_length": 128000, "max_tokens": 4096, "input_price_per_1k": 10.0, "output_price_per_1k": 30.0, "currency": "USD", "capabilities": ["chat", "vision", "function_calling"]},
        {"name": "gpt-4", "display_name": "GPT-4", "description": "OpenAI经典旗舰模型", "context_length": 8192, "max_tokens": 4096, "input_price_per_1k": 30.0, "output_price_per_1k": 60.0, "currency": "USD", "capabilities": ["chat", "function_calling"]},
        {"name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo", "description": "性价比最高的对话模型", "context_length": 16385, "max_tokens": 4096, "input_price_per_1k": 0.0005, "output_price_per_1k": 0.0015, "currency": "USD", "capabilities": ["chat", "function_calling"]},
    ],
    "anthropic": [
        {"name": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet", "description": "Anthropic最新旗舰模型", "context_length": 200000, "max_tokens": 8192, "input_price_per_1k": 3.0, "output_price_per_1k": 15.0, "currency": "USD", "capabilities": ["chat", "vision", "function_calling"]},
        {"name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus", "description": "Anthropic最高性能模型", "context_length": 200000, "max_tokens": 4096, "input_price_per_1k": 15.0, "output_price_per_1k": 75.0, "currency": "USD", "capabilities": ["chat", "vision"]},
        {"name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku", "description": "Anthropic快速响应模型", "context_length": 200000, "max_tokens": 4096, "input_price_per_1k": 0.00025, "output_price_per_1k": 0.00125, "currency": "USD", "capabilities": ["chat", "vision"]},
    ],
    "google": [
        {"name": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "description": "Google最新旗舰多模态模型", "context_length": 2000000, "max_tokens": 8192, "input_price_per_1k": 1.25, "output_price_per_1k": 5.0, "currency": "USD", "capabilities": ["chat", "vision", "long_context"]},
        {"name": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "description": "Google快速多模态模型", "context_length": 1000000, "max_tokens": 8192, "input_price_per_1k": 0.075, "output_price_per_1k": 0.3, "currency": "USD", "capabilities": ["chat", "vision", "long_context"]},
        {"name": "gemini-1.0-pro", "display_name": "Gemini 1.0 Pro", "description": "Google上一代旗舰模型", "context_length": 32768, "max_tokens": 4096, "input_price_per_1k": 0.5, "output_price_per_1k": 1.5, "currency": "USD", "capabilities": ["chat", "vision"]},
    ],
    "dashscope": [
        {"name": "qwen-turbo", "display_name": "Qwen Turbo", "description": "阿里通义千问快速版", "context_length": 10000, "max_tokens": 6000, "input_price_per_1k": 0.002, "output_price_per_1k": 0.006, "currency": "CNY", "capabilities": ["chat", "function_calling"]},
        {"name": "qwen-plus", "display_name": "Qwen Plus", "description": "阿里通义千问增强版", "context_length": 30000, "max_tokens": 6000, "input_price_per_1k": 0.02, "output_price_per_1k": 0.06, "currency": "CNY", "capabilities": ["chat", "function_calling"]},
        {"name": "qwen-max", "display_name": "Qwen Max", "description": "阿里通义千问旗舰版", "context_length": 30000, "max_tokens": 6000, "input_price_per_1k": 0.2, "output_price_per_1k": 0.6, "currency": "CNY", "capabilities": ["chat", "function_calling"]},
        {"name": "qwen-coder-turbo", "display_name": "Qwen Coder Turbo", "description": "阿里通义编程模型", "context_length": 10000, "max_tokens": 6000, "input_price_per_1k": 0.004, "output_price_per_1k": 0.012, "currency": "CNY", "capabilities": ["code"]},
    ],
    "zhipu": [
        {"name": "glm-4", "display_name": "GLM-4", "description": "智谱最新旗舰模型", "context_length": 128000, "max_tokens": 4096, "input_price_per_1k": 0.1, "output_price_per_1k": 0.1, "currency": "CNY", "capabilities": ["chat", "function_calling"]},
        {"name": "glm-4-plus", "display_name": "GLM-4 Plus", "description": "智谱增强版模型", "context_length": 128000, "max_tokens": 4096, "input_price_per_1k": 0.1, "output_price_per_1k": 0.1, "currency": "CNY", "capabilities": ["chat", "function_calling"]},
        {"name": "glm-3-turbo", "display_name": "GLM-3 Turbo", "description": "智谱性价比模型", "context_length": 128000, "max_tokens": 4096, "input_price_per_1k": 0.001, "output_price_per_1k": 0.001, "currency": "CNY", "capabilities": ["chat"]},
    ],
    "moonshot": [
        {"name": "moonshot-v1-8k", "display_name": "Kimi k8", "description": "月之暗面8K上下文版本", "context_length": 8000, "max_tokens": 4096, "input_price_per_1k": 0.015, "output_price_per_1k": 0.015, "currency": "CNY", "capabilities": ["chat", "long_context"]},
        {"name": "moonshot-v1-32k", "display_name": "Kimi k32", "description": "月之暗面32K上下文版本", "context_length": 32000, "max_tokens": 4096, "input_price_per_1k": 0.03, "output_price_per_1k": 0.03, "currency": "CNY", "capabilities": ["chat", "long_context"]},
        {"name": "moonshot-v1-128k", "display_name": "Kimi k128", "description": "月之暗面128K超长上下文", "context_length": 128000, "max_tokens": 4096, "input_price_per_1k": 0.06, "output_price_per_1k": 0.06, "currency": "CNY", "capabilities": ["chat", "long_context"]},
    ],
    "baidu": [
        {"name": "ernie-4.0-8k", "display_name": "文心一言4.0", "description": "百度最新旗舰模型", "context_length": 8000, "max_tokens": 4000, "input_price_per_1k": 0.12, "output_price_per_1k": 0.12, "currency": "CNY", "capabilities": ["chat"]},
        {"name": "ernie-3.5-8k", "display_name": "文心一言3.5", "description": "百度性价比模型", "context_length": 8000, "max_tokens": 4000, "input_price_per_1k": 0.012, "output_price_per_1k": 0.012, "currency": "CNY", "capabilities": ["chat"]},
    ],
    "azure": [
        {"name": "gpt-4o", "display_name": "Azure GPT-4o", "description": "Azure上的GPT-4o", "context_length": 128000, "max_tokens": 16384, "input_price_per_1k": 2.5, "output_price_per_1k": 10.0, "currency": "USD", "capabilities": ["chat", "vision", "function_calling"]},
        {"name": "gpt-4", "display_name": "Azure GPT-4", "description": "Azure上的GPT-4", "context_length": 8192, "max_tokens": 4096, "input_price_per_1k": 30.0, "output_price_per_1k": 60.0, "currency": "USD", "capabilities": ["chat", "function_calling"]},
        {"name": "gpt-35-turbo", "display_name": "Azure GPT-3.5 Turbo", "description": "Azure上的GPT-3.5", "context_length": 16385, "max_tokens": 4096, "input_price_per_1k": 0.0005, "output_price_per_1k": 0.0015, "currency": "USD", "capabilities": ["chat", "function_calling"]},
    ],
    "302ai": [
        {"name": "openai/gpt-4o", "display_name": "302-GPT-4o", "description": "通过302.AI调用GPT-4o", "context_length": 128000, "max_tokens": 16384, "input_price_per_1k": 2.0, "output_price_per_1k": 8.0, "currency": "CNY", "capabilities": ["chat", "vision", "function_calling"], "original_provider": "openai", "original_model": "gpt-4o"},
        {"name": "anthropic/claude-3.5-sonnet", "display_name": "302-Claude 3.5", "description": "通过302.AI调用Claude 3.5", "context_length": 200000, "max_tokens": 8192, "input_price_per_1k": 2.5, "output_price_per_1k": 12.5, "currency": "CNY", "capabilities": ["chat", "vision", "function_calling"], "original_provider": "anthropic", "original_model": "claude-3.5-sonnet-20241022"},
        {"name": "google/gemini-1.5-pro", "display_name": "302-Gemini Pro", "description": "通过302.AI调用Gemini 1.5 Pro", "context_length": 2000000, "max_tokens": 8192, "input_price_per_1k": 1.0, "output_price_per_1k": 4.0, "currency": "CNY", "capabilities": ["chat", "vision", "long_context"], "original_provider": "google", "original_model": "gemini-1.5-pro"},
    ],
    "openrouter": [
        {"name": "openai/gpt-4o", "display_name": "OR-GPT-4o", "description": "通过OpenRouter调用GPT-4o", "context_length": 128000, "max_tokens": 16384, "input_price_per_1k": 2.5, "output_price_per_1k": 10.0, "currency": "USD", "capabilities": ["chat", "vision", "function_calling"], "original_provider": "openai", "original_model": "gpt-4o"},
        {"name": "anthropic/claude-3.5-sonnet", "display_name": "OR-Claude 3.5", "description": "通过OpenRouter调用Claude 3.5", "context_length": 200000, "max_tokens": 8192, "input_price_per_1k": 3.0, "output_price_per_1k": 15.0, "currency": "USD", "capabilities": ["chat", "vision", "function_calling"], "original_provider": "anthropic", "original_model": "claude-3.5-sonnet-20241022"},
    ],
}


class ModelCatalogService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_catalogs(self) -> List[dict]:
        catalogs = []
        providers = self.db.query(LLMProvider).all()
        for provider in providers:
            models = self.db.query(ModelCatalogEntry).filter(
                ModelCatalogEntry.provider == provider.name
            ).all()
            if models:
                catalogs.append({
                    "provider": provider.name,
                    "provider_name": provider.display_name,
                    "models": [self._serialize_model(m) for m in models]
                })
        return catalogs

    def get_catalog_by_provider(self, provider: str) -> Optional[dict]:
        provider_obj = self.db.query(LLMProvider).filter(LLMProvider.name == provider).first()
        if not provider_obj:
            return None
        
        models = self.db.query(ModelCatalogEntry).filter(
            ModelCatalogEntry.provider == provider
        ).all()
        
        return {
            "provider": provider_obj.name,
            "provider_name": provider_obj.display_name,
            "models": [self._serialize_model(m) for m in models]
        }

    def save_catalog(self, provider: str, provider_name: str, models: List[dict]) -> bool:
        existing_models = self.db.query(ModelCatalogEntry).filter(
            ModelCatalogEntry.provider == provider
        ).all()
        
        for m in existing_models:
            self.db.delete(m)
        
        for model_data in models:
            model = ModelCatalogEntry(
                provider=provider,
                name=model_data.get("name"),
                display_name=model_data.get("display_name"),
                description=model_data.get("description"),
                context_length=model_data.get("context_length"),
                max_tokens=model_data.get("max_tokens"),
                input_price_per_1k=model_data.get("input_price_per_1k", 0),
                output_price_per_1k=model_data.get("output_price_per_1k", 0),
                currency=model_data.get("currency", "CNY"),
                is_deprecated=model_data.get("is_deprecated", False),
                capabilities=json.dumps(model_data.get("capabilities", [])),
                original_provider=model_data.get("original_provider"),
                original_model=model_data.get("original_model"),
            )
            self.db.add(model)
        
        self.db.commit()
        return True

    def delete_catalog(self, provider: str) -> bool:
        models = self.db.query(ModelCatalogEntry).filter(
            ModelCatalogEntry.provider == provider
        ).all()
        
        if not models:
            return False
        
        for m in models:
            self.db.delete(m)
        
        self.db.commit()
        return True

    def init_default_catalogs(self) -> int:
        count = 0
        for provider_name, models in PRESET_MODEL_CATALOG.items():
            existing = self.db.query(ModelCatalogEntry).filter(
                ModelCatalogEntry.provider == provider_name
            ).first()
            
            if not existing:
                provider = self.db.query(LLMProvider).filter(LLMProvider.name == provider_name).first()
                if provider:
                    self.save_catalog(provider_name, provider.display_name, models)
                    count += 1
        return count

    def _serialize_model(self, model: ModelCatalogEntry) -> dict:
        capabilities = []
        if model.capabilities:
            try:
                capabilities = json.loads(model.capabilities)
            except:
                capabilities = []
        
        return {
            "name": model.name,
            "display_name": model.display_name,
            "description": model.description,
            "context_length": model.context_length,
            "max_tokens": model.max_tokens,
            "input_price_per_1k": model.input_price_per_1k,
            "output_price_per_1k": model.output_price_per_1k,
            "currency": model.currency,
            "is_deprecated": model.is_deprecated,
            "capabilities": capabilities,
            "original_provider": model.original_provider,
            "original_model": model.original_model,
        }
