import os
import logging
from typing import Optional, Dict, Any, List
from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger("llm_chat.factory")

PROVIDER_CLASSES: Dict[str, type] = {
    "deepseek": ChatDeepSeek,
    "openai": ChatOpenAI,
    "anthropic": ChatAnthropic,
}

PROVIDER_API_KEYS: Dict[str, str] = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "302ai": "AI302_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "baidu": "BAIDU_API_KEY",
    "minimax": "MINIMAX_API_KEY",
    "google": "GOOGLE_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

PROVIDER_DEFAULT_MODELS: Dict[str, str] = {
    "deepseek": "deepseek-chat",
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-20241022",
    "dashscope": "qwen-turbo",
    "302ai": "gpt-4o",
    "zhipu": "glm-4",
    "moonshot": "moonshot-v1-8k",
    "baidu": "ernie-4.0-8k",
    "minimax": "abab6.5s-chat",
    "google": "gemini-1.5-pro",
    "azure": "gpt-4o",
    "openrouter": "openai/gpt-4o",
}

PROVIDER_BASE_URLS: Dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "302ai": "https://api.302.ai/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "moonshot": "https://api.moonshot.cn/v1",
    "baidu": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
    "minimax": "https://api.minimax.chat/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta",
    "openrouter": "https://openrouter.ai/api/v1",
}

PROVIDER_ANTHROPIC_COMPATIBLE: List[str] = ["anthropic", "302ai", "anthropic"]


def get_provider_config_from_db(provider: str) -> Optional[Dict[str, Any]]:
    """从数据库获取 Provider 配置"""
    try:
        from app.database.session import SessionLocal
        from app.models.config import LLMProvider
        
        db = SessionLocal()
        try:
            provider_obj = db.query(LLMProvider).filter(
                LLMProvider.name == provider
            ).first()
            
            if not provider_obj:
                return None
            
            config = {
                "api_key": provider_obj.api_key,
                "api_secret": provider_obj.api_secret,
                "default_base_url": provider_obj.default_base_url,
                "is_active": provider_obj.is_active,
            }
            
            if provider_obj.supported_features:
                import json
                try:
                    config["supported_features"] = json.loads(provider_obj.supported_features)
                except:
                    config["supported_features"] = []
            
            return config
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get provider config from DB: {e}")
        return None


def get_model_config_from_db(provider: str, model_name: str) -> Optional[Dict[str, Any]]:
    """从数据库获取 Model 配置"""
    try:
        from app.database.session import SessionLocal
        from app.models.config import LLMConfig
        
        db = SessionLocal()
        try:
            config_obj = db.query(LLMConfig).filter(
                LLMConfig.provider == provider,
                LLMConfig.model_name == model_name
            ).first()
            
            if not config_obj:
                return None
            
            return {
                "api_base": config_obj.api_base,
                "max_tokens": config_obj.max_tokens,
                "temperature": config_obj.temperature,
                "timeout": config_obj.timeout,
                "retry_times": config_obj.retry_times,
                "enabled": config_obj.enabled,
                "enable_memory": config_obj.enable_memory,
                "enable_debug": config_obj.enable_debug,
                "priority": config_obj.priority,
                "model_category": config_obj.model_category,
                "input_price_per_1k": config_obj.input_price_per_1k,
                "output_price_per_1k": config_obj.output_price_per_1k,
                "currency": config_obj.currency,
                "is_default": config_obj.is_default,
                "capability_level": config_obj.capability_level,
            }
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get model config from DB: {e}")
        return None


def get_all_enabled_models() -> List[Dict[str, Any]]:
    """获取所有启用的模型配置"""
    try:
        from app.database.session import SessionLocal
        from app.models.config import LLMConfig
        
        db = SessionLocal()
        try:
            configs = db.query(LLMConfig).filter(
                LLMConfig.enabled == True
            ).order_by(LLMConfig.priority.desc()).all()
            
            result = []
            for c in configs:
                result.append({
                    "provider": c.provider,
                    "model_name": c.model_name,
                    "model_display_name": c.model_display_name,
                    "temperature": c.temperature,
                    "max_tokens": c.max_tokens,
                    "enable_memory": c.enable_memory,
                    "is_default": c.is_default,
                })
            return result
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get enabled models: {e}")
        return []


class LLMFactory:
    _instance: Optional[BaseChatModel] = None
    _current_provider: Optional[str] = None
    _current_model: Optional[str] = None
    _current_params: Optional[Dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        provider: str = "deepseek",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseChatModel:
        provider = provider.lower()
        
        if model is None:
            model = PROVIDER_DEFAULT_MODELS.get(provider, "gpt-4o")

        db_provider_config = get_provider_config_from_db(provider)
        
        if api_key is None:
            if db_provider_config and db_provider_config.get("api_key"):
                api_key = db_provider_config["api_key"]
            else:
                api_key_env = PROVIDER_API_KEYS.get(provider)
                if api_key_env:
                    api_key = os.getenv(api_key_env)
                if not api_key:
                    raise ValueError(f"API key not configured for provider: {provider}")

        if base_url is None:
            if db_provider_config and db_provider_config.get("default_base_url"):
                base_url = db_provider_config["default_base_url"]
            else:
                base_url = PROVIDER_BASE_URLS.get(provider)

        db_model_config = get_model_config_from_db(provider, model)
        if db_model_config:
            if db_model_config.get("temperature") is not None:
                temperature = db_model_config["temperature"]
            if db_model_config.get("max_tokens") is not None:
                max_tokens = db_model_config["max_tokens"]
            if db_model_config.get("api_base"):
                base_url = db_model_config["api_base"]

        chat_class = PROVIDER_CLASSES.get(provider)
        if not chat_class:
            if provider == "dashscope":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "302ai":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "zhipu":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "moonshot":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "baidu":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "minimax":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                chat_class = ChatGoogleGenerativeAI
            elif provider == "azure":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            elif provider == "openrouter":
                from langchain_community.chat_models import ChatOpenAI
                chat_class = ChatOpenAI
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        llm_params = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }

        if base_url and provider not in PROVIDER_ANTHROPIC_COMPATIBLE:
            llm_params["base_url"] = base_url.rstrip('/')
        
        if provider in PROVIDER_ANTHROPIC_COMPATIBLE or provider == "anthropic":
            llm_params["anthropic_api_key"] = api_key
            if provider == "302ai":
                llm_params["anthropic_api_key"] = api_key
                llm_params["base_url"] = "https://api.302.ai/v1"

        if provider == "google":
            llm_params["google_api_key"] = api_key

        llm_params.update(kwargs)

        logger.info(f"Creating LLM: provider={provider}, model={model}, temperature={temperature}, max_tokens={max_tokens}")

        try:
            return chat_class(**llm_params)
        except Exception as e:
            logger.error(f"Failed to create LLM: {e}")
            raise

    @classmethod
    def get_cached(
        cls,
        provider: str = "deepseek",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        force_new: bool = False,
        **kwargs
    ) -> BaseChatModel:
        if model is None:
            model = PROVIDER_DEFAULT_MODELS.get(provider, "gpt-4o")

        current_params = {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if force_new or cls._instance is None or cls._current_provider != provider or cls._current_model != model:
            cls._instance = cls.create(
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                **kwargs
            )
            cls._current_provider = provider
            cls._current_model = model
            cls._current_params = current_params

        return cls._instance

    @classmethod
    def clear_cache(cls):
        cls._instance = None
        cls._current_provider = None
        cls._current_model = None
        cls._current_params = None


def get_llm(
    provider: str = "deepseek",
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    force_new: bool = False,
    **kwargs
) -> BaseChatModel:
    return LLMFactory.get_cached(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        force_new=force_new,
        **kwargs
    )
