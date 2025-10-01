import os
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class DeploymentEnvironment(Enum):
    LOCAL = "local"
    RENDER = "render"
    AWS = "aws"
    GCP = "gcp"
    HEROKU = "heroku"


class ServiceType(Enum):
    CONVERSATION_RELAY = "conversation_relay"
    CONVERSATIONS_MANAGER = "conversations_manager"
    SIGNAL_ANALYTICS = "signal_analytics"
    INTELLIGENCE_WEBHOOK = "intelligence_webhook"


@dataclass
class DatabaseConfig:
    """Database configuration for different environments"""
    type: str  # sqlite, postgresql, redis
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None


@dataclass
class NetworkConfig:
    """Network configuration for inter-service communication"""
    host: str = "localhost"
    port: int = 8080
    protocol: str = "http"
    external_url: Optional[str] = None
    websocket_url: Optional[str] = None


@dataclass
class ServiceConfig:
    """Service-specific configuration"""
    name: str
    network: NetworkConfig
    database: Optional[DatabaseConfig] = None
    enabled: bool = True


class EnvironmentManager:
    """Manages environment-specific configurations for multi-cloud deployments"""
    
    def __init__(self, service_type: ServiceType = ServiceType.CONVERSATION_RELAY):
        load_dotenv()
        self.service_type = service_type
        self.environment = self._detect_environment()
        self.config = self._load_configuration()
    
    def _detect_environment(self) -> DeploymentEnvironment:
        """Auto-detect deployment environment based on environment variables"""
        
        # Check for explicit environment setting
        env_override = os.getenv("DEPLOYMENT_ENVIRONMENT")
        if env_override:
            try:
                return DeploymentEnvironment(env_override.lower())
            except ValueError:
                pass
        
        # Detect based on platform-specific environment variables
        if os.getenv("RENDER"):
            return DeploymentEnvironment.RENDER
        elif os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_REGION"):
            return DeploymentEnvironment.AWS
        elif os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT"):
            return DeploymentEnvironment.GCP
        elif os.getenv("DYNO") or os.getenv("HEROKU_APP_NAME"):
            return DeploymentEnvironment.HEROKU
        else:
            return DeploymentEnvironment.LOCAL
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        
        base_config = {
            "twilio": {
                "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
                "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
                "intelligence_service_sid": os.getenv("TWILIO_INTELLIGENCE_SERVICE_SID"),
                "function_domain": os.getenv("TWILIO_FUNCTION_DOMAIN"),
                "function_url": os.getenv("TWILIO_FUNCTION_URL")
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1"),
                "use_functions": os.getenv("USE_OPENAI_FUNCTIONS", "false").lower() == "true"
            },
            "segment": {
                "space_id": os.getenv("SEGMENT_SPACE_ID"),
                "write_key": os.getenv("SEGMENT_WRITE_KEY"),
                "access_secret": os.getenv("SEGMENT_ACCESS_SECRET")
            }
        }
        
        # Environment-specific configurations
        env_configs = {
            DeploymentEnvironment.LOCAL: self._get_local_config(),
            DeploymentEnvironment.RENDER: self._get_render_config(),
            DeploymentEnvironment.AWS: self._get_aws_config(),
            DeploymentEnvironment.GCP: self._get_gcp_config(),
            DeploymentEnvironment.HEROKU: self._get_heroku_config()
        }
        
        # Merge base config with environment-specific config
        env_config = env_configs.get(self.environment, {})
        return {**base_config, **env_config}
    
    def _get_local_config(self) -> Dict[str, Any]:
        """Local development configuration"""
        return {
            "services": {
                "conversation_relay": ServiceConfig(
                    name="conversation_relay",
                    network=NetworkConfig(host="localhost", port=8080, websocket_url="ws://localhost:8080/websocket")
                ),
                "conversations_manager": ServiceConfig(
                    name="conversations_manager",
                    network=NetworkConfig(host="localhost", port=3001, external_url="http://localhost:3001")
                ),
                "signal_analytics": ServiceConfig(
                    name="signal_analytics",
                    network=NetworkConfig(host="localhost", port=5000)
                ),
                "intelligence_webhook": ServiceConfig(
                    name="intelligence_webhook",
                    network=NetworkConfig(host="localhost", port=4000)
                )
            },
            "client_url": os.getenv("CLIENT_URL", "http://localhost:3000"),
            "debug_mode": os.getenv("DEBUG_MODE", "true").lower() == "true",
            "ngrok": {
                "domain": os.getenv("NGROK_DOMAIN"),
                "auth_token": os.getenv("NGROK_AUTH_TOKEN")
            },
            "data_persistence": {
                "type": "file",
                "base_path": "./data"
            }
        }
    
    def _get_render_config(self) -> Dict[str, Any]:
        """Render.com deployment configuration"""
        return {
            "services": {
                "conversation_relay": ServiceConfig(
                    name="conversation_relay",
                    network=NetworkConfig(
                        host="0.0.0.0",
                        port=int(os.getenv("PORT", "8080")),
                        external_url=f"https://{os.getenv('RENDER_SERVICE_NAME', 'your-app')}.onrender.com",
                        websocket_url=f"wss://{os.getenv('RENDER_SERVICE_NAME', 'your-app')}.onrender.com/websocket"
                    )
                ),
                "conversations_manager": ServiceConfig(
                    name="conversations_manager",
                    network=NetworkConfig(
                        host="0.0.0.0",
                        port=int(os.getenv("PORT", "3001")),
                        external_url=f"https://{os.getenv('RENDER_SERVICE_NAME', 'your-app')}-api.onrender.com"
                    )
                )
            },
            "client_url": f"https://{os.getenv('RENDER_SERVICE_NAME', 'your-app')}.onrender.com",
            "debug_mode": False,
            "database": DatabaseConfig(
                type="postgresql",
                url=os.getenv("DATABASE_URL")
            ),
            "data_persistence": {
                "type": "database",
                "connection_string": os.getenv("DATABASE_URL")
            },
            "redis_url": os.getenv("REDIS_URL")
        }
    
    def _get_aws_config(self) -> Dict[str, Any]:
        """AWS deployment configuration"""
        return {
            "services": {
                "conversation_relay": ServiceConfig(
                    name="conversation_relay",
                    network=NetworkConfig(
                        host="0.0.0.0",
                        port=int(os.getenv("PORT", "8080")),
                        external_url=f"https://{os.getenv('AWS_API_GATEWAY_DOMAIN')}",
                        websocket_url=f"wss://{os.getenv('AWS_WEBSOCKET_DOMAIN')}"
                    )
                )
            },
            "client_url": f"https://{os.getenv('AWS_CLOUDFRONT_DOMAIN')}",
            "debug_mode": False,
            "aws": {
                "region": os.getenv("AWS_REGION"),
                "lambda_function": os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
                "api_gateway_id": os.getenv("AWS_API_GATEWAY_ID"),
                "websocket_api_id": os.getenv("AWS_WEBSOCKET_API_ID")
            },
            "database": DatabaseConfig(
                type="dynamodb",
                host=f"dynamodb.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com"
            ),
            "data_persistence": {
                "type": "s3",
                "bucket": os.getenv("AWS_S3_BUCKET")
            }
        }
    
    def _get_gcp_config(self) -> Dict[str, Any]:
        """Google Cloud Platform deployment configuration"""
        return {
            "services": {
                "conversation_relay": ServiceConfig(
                    name="conversation_relay",
                    network=NetworkConfig(
                        host="0.0.0.0",
                        port=int(os.getenv("PORT", "8080")),
                        external_url=f"https://{os.getenv('GCP_SERVICE_NAME')}-{os.getenv('GCP_PROJECT')}.{os.getenv('GCP_REGION', 'us-central1')}.run.app"
                    )
                )
            },
            "client_url": f"https://{os.getenv('GCP_FRONTEND_SERVICE')}-{os.getenv('GCP_PROJECT')}.{os.getenv('GCP_REGION', 'us-central1')}.run.app",
            "debug_mode": False,
            "gcp": {
                "project_id": os.getenv("GCP_PROJECT"),
                "region": os.getenv("GCP_REGION", "us-central1"),
                "service_name": os.getenv("GCP_SERVICE_NAME")
            },
            "database": DatabaseConfig(
                type="firestore",
                host=f"{os.getenv('GCP_PROJECT')}.firebaseio.com"
            ),
            "data_persistence": {
                "type": "gcs",
                "bucket": os.getenv("GCS_BUCKET")
            }
        }
    
    def _get_heroku_config(self) -> Dict[str, Any]:
        """Heroku deployment configuration"""
        return {
            "services": {
                "conversation_relay": ServiceConfig(
                    name="conversation_relay",
                    network=NetworkConfig(
                        host="0.0.0.0",
                        port=int(os.getenv("PORT", "8080")),
                        external_url=f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com"
                    )
                )
            },
            "client_url": f"https://{os.getenv('HEROKU_APP_NAME')}.herokuapp.com",
            "debug_mode": False,
            "database": DatabaseConfig(
                type="postgresql",
                url=os.getenv("DATABASE_URL")
            ),
            "redis_url": os.getenv("REDIS_URL")
        }
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service"""
        services = self.config.get("services", {})
        service_config = services.get(service_name)
        
        if not service_config:
            raise ValueError(f"Service '{service_name}' not found in configuration")
        
        return service_config
    
    def get_database_config(self) -> Optional[DatabaseConfig]:
        """Get database configuration for current environment"""
        return self.config.get("database")
    
    def get_external_url(self, service_name: str) -> str:
        """Get external URL for a service"""
        service_config = self.get_service_config(service_name)
        return service_config.network.external_url or f"http://localhost:{service_config.network.port}"
    
    def get_websocket_url(self, service_name: str) -> str:
        """Get WebSocket URL for a service"""
        service_config = self.get_service_config(service_name)
        return service_config.network.websocket_url or f"ws://localhost:{service_config.network.port}"
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment != DeploymentEnvironment.LOCAL
    
    def get_cors_origins(self) -> list:
        """Get CORS origins based on environment"""
        if self.environment == DeploymentEnvironment.LOCAL:
            return ["http://localhost:3000", "http://localhost:3001"]
        else:
            client_url = self.config.get("client_url", "")
            return [client_url] if client_url else ["*"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = self.config.copy()
        config_dict["environment"] = self.environment.value
        config_dict["service_type"] = self.service_type.value
        return config_dict


# Global environment manager instance
env_manager = EnvironmentManager()


def get_env_manager(service_type: ServiceType = ServiceType.CONVERSATION_RELAY) -> EnvironmentManager:
    """Get environment manager instance"""
    return EnvironmentManager(service_type)