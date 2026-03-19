"""
Serviço de configuração usando YAML
"""
from pathlib import Path
from typing import Any, Dict
import yaml

from utils.logger import LoggerMixin
from utils.constants import CONFIG_PATH, DEFAULT_CONFIG, DATA_DIR


class ConfigService(LoggerMixin):
    """Gerencia configurações da aplicação"""
    
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Carrega configurações do arquivo"""
        # Criar diretório se não existir
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                self.logger.info(f"Configurações carregadas de {self.config_path}")
            except Exception as e:
                self.logger.error(f"Erro ao carregar configurações: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self.logger.info("Arquivo de configuração não encontrado, usando padrões")
            self._config = DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self):
        """Salva configurações no arquivo"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            self.logger.debug("Configurações salvas")
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor por chave (suporta nested: 'general.theme')
        
        Args:
            key: Chave da configuração
            default: Valor padrão se não encontrar
        
        Returns:
            Valor da configuração
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any, save: bool = True):
        """
        Define valor por chave
        
        Args:
            key: Chave da configuração
            value: Novo valor
            save: Se deve salvar imediatamente
        """
        keys = key.split('.')
        config = self._config
        
        # Navegar até o último nível
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Definir valor
        config[keys[-1]] = value
        
        if save:
            self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Retorna todas as configurações"""
        return self._config.copy()
    
    def reset_to_defaults(self):
        """Restaura configurações padrão"""
        self._config = DEFAULT_CONFIG.copy()
        self.save()
        self.logger.info("Configurações restauradas para padrão")
