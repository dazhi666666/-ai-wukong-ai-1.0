#!/usr/bin/env python3
"""
统一日志管理器
提供项目级别的日志配置和管理功能
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager
import json
import traceback


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        for field in ['conversation_id', 'provider', 'model', 'tool_name', 'agent_name', 'duration', 'status', 'error']:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        return json.dumps(log_entry, ensure_ascii=False)


class LoggingManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _load_default_config(self) -> Dict[str, Any]:
        config = self._load_config_file()
        if config:
            return config
        log_level = os.getenv('LLM_LOG_LEVEL', 'INFO').upper()
        log_dir = os.getenv('LLM_LOG_DIR', './logs')
        return {
            'level': log_level,
            'format': {
                'console': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
                'file': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            },
            'handlers': {
                'console': {'enabled': True, 'colored': True, 'level': log_level},
                'file': {'enabled': True, 'level': 'DEBUG', 'max_size': '10MB', 'backup_count': 5, 'directory': log_dir},
                'error': {'enabled': True, 'level': 'WARNING', 'max_size': '10MB', 'backup_count': 5, 'directory': log_dir, 'filename': 'error.log'},
                'structured': {'enabled': os.getenv('LLM_LOG_STRUCTURED', 'false').lower() == 'true', 'level': 'INFO', 'directory': log_dir},
            },
            'loggers': {
                'llm_chat': {'level': log_level}, 'app': {'level': log_level}, 'services': {'level': log_level},
                'routers': {'level': log_level}, 'uvicorn': {'level': 'WARNING'}, 'fastapi': {'level': 'WARNING'}
            },
            'docker': {'enabled': os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true', 'stdout_only': True}
        }

    def _load_config_file(self) -> Optional[Dict[str, Any]]:
        config_paths = [
            'config/logging.json',
            './logging.json',
            Path(__file__).parent.parent.parent / 'config' / 'logging.json'
        ]
        for config_path in config_paths:
            if config_path and Path(config_path).exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get('logging', {})
                except Exception:
                    continue
        return None

    def _setup_logging(self):
        if self.config['handlers']['file']['enabled']:
            log_dir = Path(self.config['handlers']['file']['directory'])
            log_dir.mkdir(parents=True, exist_ok=True)
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['level']))
        root_logger.handlers.clear()
        self._add_console_handler(root_logger)
        if not self.config['docker']['enabled'] or not self.config['docker']['stdout_only']:
            self._add_file_handler(root_logger)
            self._add_error_handler(root_logger)
            if self.config['handlers'].get('structured', {}).get('enabled', False):
                self._add_structured_handler(root_logger)
        self._configure_specific_loggers()
    
    def _add_console_handler(self, logger: logging.Logger):
        if not self.config['handlers']['console']['enabled']:
            return
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config['handlers']['console']['level']))
        if self.config['handlers']['console']['colored'] and sys.stdout.isatty():
            formatter = ColoredFormatter(self.config['format']['console'])
        else:
            formatter = logging.Formatter(self.config['format']['console'])
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger):
        if not self.config['handlers']['file']['enabled']:
            return
        log_dir = Path(self.config['handlers']['file']['directory'])
        log_file = log_dir / 'llm_chat.log'
        max_size = self._parse_size(self.config['handlers']['file']['max_size'])
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_size, backupCount=self.config['handlers']['file']['backup_count'], encoding='utf-8')
        file_handler.setLevel(getattr(logging, self.config['handlers']['file']['level']))
        file_handler.setFormatter(logging.Formatter(self.config['format']['file']))
        logger.addHandler(file_handler)
    
    def _add_error_handler(self, logger: logging.Logger):
        error_config = self.config['handlers'].get('error', {})
        if not error_config.get('enabled', True):
            return
        log_dir = Path(error_config.get('directory', self.config['handlers']['file']['directory']))
        error_log_file = log_dir / error_config.get('filename', 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(error_log_file, maxBytes=self._parse_size(error_config.get('max_size', '10MB')), backupCount=error_config.get('backup_count', 5), encoding='utf-8')
        error_handler.setLevel(getattr(logging, error_config.get('level', 'WARNING')))
        error_handler.setFormatter(logging.Formatter(self.config['format']['file']))
        logger.addHandler(error_handler)

    def _add_structured_handler(self, logger: logging.Logger):
        structured_config = self.config['handlers'].get('structured', {})
        log_dir = Path(structured_config.get('directory', self.config['handlers']['file']['directory']))
        structured_handler = logging.handlers.RotatingFileHandler(log_dir / 'llm_chat_structured.log', maxBytes=self._parse_size('10MB'), backupCount=3, encoding='utf-8')
        structured_handler.setLevel(getattr(logging, structured_config.get('level', 'INFO')))
        structured_handler.setFormatter(StructuredFormatter())
        logger.addHandler(structured_handler)
    
    def _configure_specific_loggers(self):
        for logger_name, logger_config in self.config['loggers'].items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, logger_config['level']))
    
    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.upper()
        if size_str.endswith('KB'): return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'): return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'): return int(size_str[:-2]) * 1024 * 1024 * 1024
        return int(size_str)
    
    def get_logger(self, name: str) -> logging.Logger:
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]

    @contextmanager
    def timer(self, logger: logging.Logger, operation: str, **kwargs):
        start_time = datetime.now()
        logger.info(f"[START] {operation}", extra=kwargs)
        try:
            yield
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[END] {operation} | duration={duration:.3f}s", extra={'duration': duration, **kwargs})
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"[ERROR] {operation} | duration={duration:.3f}s | error={str(e)}", extra={'duration': duration, 'error': str(e), **kwargs}, exc_info=True)
            raise

    def log_chat_start(self, logger: logging.Logger, conversation_id: str, model: str, provider: str):
        logger.info(f"🚀 Chat started: {conversation_id} | model={model} | provider={provider}", extra={'conversation_id': conversation_id, 'model': model, 'provider': provider, 'event_type': 'chat_start'})
    
    def log_chat_complete(self, logger: logging.Logger, conversation_id: str, duration: float, message_count: int):
        logger.info(f"✅ Chat completed: {conversation_id} | duration={duration:.2f}s | messages={message_count}", extra={'conversation_id': conversation_id, 'duration': duration, 'message_count': message_count, 'event_type': 'chat_complete'})
    
    def log_tool_execution(self, logger: logging.Logger, tool_name: str, provider: str, success: bool, duration: float, error: str = None):
        if success:
            logger.info(f"🔧 Tool executed: {tool_name} | provider={provider} | duration={duration:.3f}s", extra={'tool_name': tool_name, 'provider': provider, 'duration': duration, 'status': 'success', 'event_type': 'tool_execution'})
        else:
            logger.error(f"❌ Tool failed: {tool_name} | provider={provider} | error={error}", extra={'tool_name': tool_name, 'provider': provider, 'status': 'error', 'error': error, 'event_type': 'tool_execution'}, exc_info=bool(error))
    
    def log_agent_execution(self, logger: logging.Logger, agent_name: str, conversation_id: str, success: bool, duration: float, steps: int = 0, error: str = None):
        if success:
            logger.info(f"🤖 Agent executed: {agent_name} | conversation={conversation_id} | steps={steps} | duration={duration:.3f}s", extra={'agent_name': agent_name, 'conversation_id': conversation_id, 'steps': steps, 'duration': duration, 'status': 'success', 'event_type': 'agent_execution'})
        else:
            logger.error(f"❌ Agent failed: {agent_name} | conversation={conversation_id} | error={error}", extra={'agent_name': agent_name, 'conversation_id': conversation_id, 'status': 'error', 'error': error, 'event_type': 'agent_execution'}, exc_info=bool(error))

    def log_llm_call(self, logger: logging.Logger, provider: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0, duration: float = 0, cost: float = 0):
        total_tokens = prompt_tokens + completion_tokens
        logger.info(f"💬 LLM call: {provider}/{model} | prompt={prompt_tokens} | completion={completion_tokens} | total={total_tokens} | duration={duration:.3f}s | cost=${cost:.6f}", extra={'provider': provider, 'model': model, 'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': total_tokens, 'duration': duration, 'cost': cost, 'event_type': 'llm_call'})
    
    def log_error_with_context(self, logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
        context = context or {}
        logger.error(f"💥 Error: {type(error).__name__}: {str(error)}", extra={'error_type': type(error).__name__, 'error_message': str(error), 'context': context, 'event_type': 'error'}, exc_info=True)


_logger_manager: Optional[LoggingManager] = None

def get_logger_manager() -> LoggingManager:
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggingManager()
    return _logger_manager

def get_logger(name: str) -> logging.Logger:
    return get_logger_manager().get_logger(name)

def setup_logging(config: Optional[Dict[str, Any]] = None):
    global _logger_manager
    _logger_manager = LoggingManager(config)
    return _logger_manager
