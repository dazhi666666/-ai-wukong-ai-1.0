import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.config_service import ConfigService
from app.models.config import LLMProvider, LLMConfig


router = APIRouter(prefix="/api/config", tags=["config"])


class ProviderCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    api_doc_url: Optional[str] = None
    default_base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    supported_features: Optional[List[str]] = []
    is_active: bool = True
    is_aggregator: bool = False


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    api_doc_url: Optional[str] = None
    default_base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    supported_features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_aggregator: Optional[bool] = None


class ConfigCreate(BaseModel):
    provider: str
    model_name: str
    model_display_name: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 180
    retry_times: int = 3
    enabled: bool = True
    enable_memory: str = "full"
    enable_debug: bool = False
    priority: int = 0
    model_category: Optional[str] = None
    description: Optional[str] = None
    input_price_per_1k: float = 0
    output_price_per_1k: float = 0
    currency: str = "CNY"
    is_default: bool = False
    capability_level: int = 2
    suitable_roles: Optional[List[str]] = None
    features: Optional[List[str]] = None
    recommended_depths: Optional[List[str]] = None


def serialize_provider(provider) -> dict:
    result = {
        "id": provider.id,
        "name": provider.name,
        "display_name": provider.display_name,
        "description": provider.description,
        "website": provider.website,
        "api_doc_url": provider.api_doc_url,
        "default_base_url": provider.default_base_url,
        "api_key": provider.api_key if provider.api_key else None,
        "api_secret": provider.api_secret if provider.api_secret else None,
        "is_active": provider.is_active,
        "is_aggregator": provider.is_aggregator,
        "has_api_key": bool(provider.api_key),
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
    }
    
    if provider.supported_features:
        try:
            result["supported_features"] = json.loads(provider.supported_features)
        except:
            result["supported_features"] = []
    else:
        result["supported_features"] = []
    
    return result


def serialize_config(config) -> dict:
    result = {
        "id": config.id,
        "provider": config.provider,
        "model_name": config.model_name,
        "model_display_name": config.model_display_name,
        "api_base": config.api_base,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "timeout": config.timeout,
        "retry_times": config.retry_times,
        "enabled": config.enabled,
        "enable_memory": config.enable_memory,
        "enable_debug": config.enable_debug,
        "priority": config.priority,
        "model_category": config.model_category,
        "description": config.description,
        "input_price_per_1k": config.input_price_per_1k,
        "output_price_per_1k": config.output_price_per_1k,
        "currency": config.currency,
        "is_default": config.is_default,
        "capability_level": config.capability_level,
        "created_at": config.created_at.isoformat() if config.created_at else None,
    }
    
    if config.suitable_roles:
        try:
            result["suitable_roles"] = json.loads(config.suitable_roles)
        except:
            result["suitable_roles"] = ["both"]
    else:
        result["suitable_roles"] = ["both"]
    
    if config.features:
        try:
            result["features"] = json.loads(config.features)
        except:
            result["features"] = ["tool_calling"]
    else:
        result["features"] = ["tool_calling"]
    
    if config.recommended_depths:
        try:
            result["recommended_depths"] = json.loads(config.recommended_depths)
        except:
            result["recommended_depths"] = ["快速", "基础", "标准"]
    else:
        result["recommended_depths"] = ["快速", "基础", "标准"]
    
    return result


@router.get("/providers")
def get_providers(db: Session = Depends(get_db)):
    service = ConfigService(db)
    providers = service.get_all_providers()
    return [serialize_provider(p) for p in providers]


@router.get("/providers/active")
def get_active_providers(db: Session = Depends(get_db)):
    service = ConfigService(db)
    providers = service.get_active_providers()
    return [serialize_provider(p) for p in providers]


@router.post("/providers")
def create_provider(provider: ProviderCreate, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    existing = service.get_provider_by_name(provider.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider.name}' already exists"
        )
    
    result = service.create_provider(provider.model_dump(exclude_none=False))
    return serialize_provider(result)


@router.put("/providers/{name}")
def update_provider(name: str, provider: ProviderUpdate, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    existing = service.get_provider_by_name(name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{name}' not found"
        )
    
    update_data = provider.model_dump(exclude_none=True)
    result = service.update_provider(name, update_data)
    return serialize_provider(result)


@router.delete("/providers/{name}")
def delete_provider(name: str, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    existing = service.get_provider_by_name(name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{name}' not found"
        )
    
    success = service.delete_provider(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete provider"
        )
    
    return {"message": f"Provider '{name}' deleted successfully"}


@router.patch("/providers/{name}/toggle")
def toggle_provider(name: str, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    result = service.toggle_provider(name)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{name}' not found"
        )
    
    return serialize_provider(result)


@router.post("/providers/init-presets")
def init_preset_providers(db: Session = Depends(get_db)):
    service = ConfigService(db)
    count = service.init_preset_providers()
    return {"message": f"Initialized {count} preset providers"}


@router.get("/models")
def get_models(db: Session = Depends(get_db)):
    service = ConfigService(db)
    configs = service.get_all_configs()
    return [serialize_config(c) for c in configs]


@router.get("/models/enabled")
def get_enabled_models(db: Session = Depends(get_db)):
    service = ConfigService(db)
    configs = service.get_enabled_configs()
    return [serialize_config(c) for c in configs]


@router.get("/models/default")
def get_default_model(db: Session = Depends(get_db)):
    service = ConfigService(db)
    config = service.get_default_config()
    if not config:
        return None
    return serialize_config(config)


@router.post("/models")
def create_or_update_model(config: ConfigCreate, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    if config.is_default:
        db.query(LLMConfig).update({"is_default": False})
        db.commit()
    
    result = service.create_or_update_config(config.model_dump(exclude_none=False))
    return serialize_config(result)


@router.delete("/models/{provider}/{model_name}")
def delete_model(provider: str, model_name: str, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    success = service.delete_config(provider, model_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config for model '{model_name}' under provider '{provider}' not found"
        )
    
    return {"message": f"Model config deleted successfully"}


@router.post("/models/{config_id}/set-default")
def set_default_model(config_id: int, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    result = service.set_default_config(config_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config with id {config_id} not found"
        )
    
    return serialize_config(result)


@router.patch("/models/{config_id}/toggle")
def toggle_model(config_id: int, db: Session = Depends(get_db)):
    service = ConfigService(db)
    
    result = service.toggle_config(config_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config with id {config_id} not found"
        )
    
    return serialize_config(result)


class ModelCatalogRequest(BaseModel):
    provider: str
    provider_name: str
    models: List[dict]


@router.get("/model-catalog")
def get_model_catalog(db: Session = Depends(get_db)):
    from app.services.config_service import ModelCatalogService
    service = ModelCatalogService(db)
    catalogs = service.get_all_catalogs()
    return catalogs


@router.get("/model-catalog/{provider}")
def get_provider_model_catalog(provider: str, db: Session = Depends(get_db)):
    from app.services.config_service import ModelCatalogService
    service = ModelCatalogService(db)
    catalog = service.get_catalog_by_provider(provider)
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model catalog for provider '{provider}' not found"
        )
    return catalog


@router.post("/model-catalog")
def save_model_catalog(catalog: ModelCatalogRequest, db: Session = Depends(get_db)):
    from app.services.config_service import ModelCatalogService
    service = ModelCatalogService(db)
    success = service.save_catalog(catalog.provider, catalog.provider_name, catalog.models)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save model catalog"
        )
    return {"message": "Model catalog saved successfully"}


@router.delete("/model-catalog/{provider}")
def delete_model_catalog(provider: str, db: Session = Depends(get_db)):
    from app.services.config_service import ModelCatalogService
    service = ModelCatalogService(db)
    success = service.delete_catalog(provider)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model catalog for provider '{provider}' not found"
        )
    return {"message": "Model catalog deleted successfully"}


@router.post("/model-catalog/init")
def init_model_catalog(db: Session = Depends(get_db)):
    from app.services.config_service import ModelCatalogService
    service = ModelCatalogService(db)
    count = service.init_default_catalogs()
    return {"message": f"Initialized {count} model catalogs"}
