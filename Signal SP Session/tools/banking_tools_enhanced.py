# banking_tools_enhanced.py
# Enhanced banking tools with OpenAI Functions support
# Maintains backward compatibility with existing banking_tools.py

import requests
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
import re
from dataclasses import dataclass

# Import original tools to maintain compatibility
from .banking_tools import BankingTools as OriginalBankingTools

logger = logging.getLogger(__name__)

@dataclass
class FunctionResult:
    """Result of a function execution"""
    success: bool
    content: str
    tool_call_id: str = ""
    metadata: Dict[str, Any] = None

class EnhancedBankingTools(OriginalBankingTools):
    """Enhanced banking tools with OpenAI Functions support"""
    
    def __init__(self, base_url: str = "https://owl-bank-finserv-demo-1-1-8657.twil.io"):
        super().__init__(base_url)
        self.function_registry = {}
        self._register_functions()
    
    def _register_functions(self):
        """Register all available banking functions"""
        # Account balance function
        self.function_registry["get_account_balance"] = {
            "function": self._execute_get_account_balance,
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_account_balance",
                    "description": "Get current account balance, credit card debt, and loyalty points when customer explicitly asks for balance or account information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_type": {
                                "type": "string",
                                "enum": ["checking", "savings", "credit", "all"],
                                "description": "Type of account information to retrieve",
                                "default": "all"
                            },
                            "include_details": {
                                "type": "boolean",
                                "description": "Whether to include detailed breakdown of balance, credit debt, and loyalty points",
                                "default": True
                            }
                        }
                    }
                }
            }
        }
        
        # Account access help function
        self.function_registry["help_with_account_access"] = {
            "function": self._execute_help_with_account_access,
            "schema": {
                "type": "function",
                "function": {
                    "name": "help_with_account_access",
                    "description": "Provide help when customer cannot access their account, having login issues, or needs technical support",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_type": {
                                "type": "string",
                                "enum": ["login_failed", "password_reset", "locked_account", "app_access", "general_access"],
                                "description": "Type of access issue the customer is experiencing"
                            },
                            "language": {
                                "type": "string",
                                "enum": ["pt-BR", "en-US", "es-US"],
                                "description": "Language for the response",
                                "default": "pt-BR"
                            }
                        },
                        "required": ["issue_type"]
                    }
                }
            }
        }
        
        # Transfer money function
        self.function_registry["initiate_transfer"] = {
            "function": self._execute_initiate_transfer,
            "schema": {
                "type": "function",
                "function": {
                    "name": "initiate_transfer",
                    "description": "Help with money transfers, PIX, or sending money to other accounts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transfer_type": {
                                "type": "string",
                                "enum": ["pix", "ted", "doc", "internal_transfer"],
                                "description": "Type of transfer requested"
                            },
                            "language": {
                                "type": "string",
                                "enum": ["pt-BR", "en-US", "es-US"],
                                "description": "Language for the response",
                                "default": "pt-BR"
                            }
                        },
                        "required": ["transfer_type"]
                    }
                }
            }
        }
    
    def get_function_schemas(self) -> List[Dict]:
        """Get all function schemas for OpenAI API"""
        return [func_data["schema"] for func_data in self.function_registry.values()]
    
    def execute_function(self, function_name: str, arguments: str, tool_call_id: str = "") -> FunctionResult:
        """Execute a function by name with JSON arguments"""
        try:
            if function_name not in self.function_registry:
                return FunctionResult(
                    success=False,
                    content=f"Function {function_name} not found",
                    tool_call_id=tool_call_id
                )
            
            # Parse arguments
            try:
                args = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError as e:
                return FunctionResult(
                    success=False,
                    content=f"Invalid JSON arguments: {e}",
                    tool_call_id=tool_call_id
                )
            
            # Execute function
            func = self.function_registry[function_name]["function"]
            # Add customer_phone for banking functions if not already present
            if function_name in ['get_account_balance'] and 'customer_phone' not in args:
                # This will be set by the LLM client
                pass
            result = func(**args)
            
            return FunctionResult(
                success=True,
                content=result["content"],
                tool_call_id=tool_call_id,
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"[BANK] Error executing function {function_name}: {e}")
            return FunctionResult(
                success=False,
                content=f"Error executing function: {str(e)}",
                tool_call_id=tool_call_id
            )
    
    def _execute_get_account_balance(self, account_type: str = "all", include_details: bool = True, language: str = "pt-BR", customer_phone: str = None) -> Dict[str, Any]:
        """Execute account balance retrieval"""
        # Use the customer phone provided or fall back to demo user
        if not customer_phone:
            customer_phone = "owl.anunes@gmail.com"  # Demo fallback
        
        # The parent class get_banking_data method now uses POST like PWA
        banking_data = self.get_banking_data(customer_phone)
        
        if not banking_data.get("success"):
            if language == "pt-BR":
                content = "Desculpe, não consegui acessar os dados da sua conta no momento."
            elif language == "es-US":
                content = "Lo siento, no pude acceder a los datos de tu cuenta en este momento."
            else:
                content = "Sorry, I couldn't access your account information at the moment."
        else:
            content = self.format_balance_response(banking_data, language)
        
        return {
            "content": content,
            "metadata": {
                "action": "balance_check",
                "account_type": account_type,
                "language": language,
                "banking_data": banking_data.get("data", {}) if banking_data.get("success") else None
            }
        }
    
    def _execute_help_with_account_access(self, issue_type: str, language: str = "pt-BR") -> Dict[str, Any]:
        """Execute account access help"""
        responses = {
            "pt-BR": {
                "login_failed": "Entendo que você está com dificuldades para fazer login. Vou te ajudar com isso. Primeiro, vamos verificar se você está usando as credenciais corretas. Você lembra do seu email de cadastro?",
                "password_reset": "Sem problemas! Posso ajudar você a redefinir sua senha. Vou enviar um link de redefinição para o email cadastrado na sua conta. Confirma se o email owl.anunes@gmail.com está correto?",
                "locked_account": "Vejo que sua conta pode estar bloqueada. Isso geralmente acontece após algumas tentativas de login incorretas. Vou desbloquear para você. Por favor, aguarde um momento.",
                "app_access": "Problemas com o aplicativo podem ser frustrantes. Primeiro, tente fechar e abrir o app novamente. Se não funcionar, pode ser necessário atualizar o aplicativo ou limpar o cache.",
                "general_access": "Entendo sua dificuldade para acessar a conta. Para te ajudar melhor, você pode me dizer que tipo de problema está enfrentando? Login não funciona, esqueceu a senha, ou o aplicativo não abre?"
            },
            "en-US": {
                "login_failed": "I understand you're having trouble logging in. I'll help you with that. First, let's verify if you're using the correct credentials. Do you remember your registered email?",
                "password_reset": "No problem! I can help you reset your password. I'll send a reset link to your registered email. Can you confirm if owl.anunes@gmail.com is correct?",
                "locked_account": "I see your account might be locked. This usually happens after several incorrect login attempts. I'll unlock it for you. Please wait a moment.",
                "app_access": "App issues can be frustrating. First, try closing and reopening the app. If that doesn't work, you might need to update the app or clear the cache.",
                "general_access": "I understand your difficulty accessing the account. To help you better, can you tell me what kind of problem you're facing? Login not working, forgot password, or app won't open?"
            },
            "es-US": {
                "login_failed": "Entiendo que tienes problemas para iniciar sesión. Te voy a ayudar con eso. Primero, vamos a verificar si estás usando las credenciales correctas. ¿Recuerdas tu email registrado?",
                "password_reset": "¡No hay problema! Puedo ayudarte a restablecer tu contraseña. Enviaré un enlace de restablecimiento a tu email registrado. ¿Confirmas si owl.anunes@gmail.com es correcto?",
                "locked_account": "Veo que tu cuenta podría estar bloqueada. Esto suele pasar después de varios intentos de inicio de sesión incorrectos. La desbloquearé para ti. Por favor, espera un momento.",
                "app_access": "Los problemas con la aplicación pueden ser frustrantes. Primero, intenta cerrar y abrir la app nuevamente. Si no funciona, podrías necesitar actualizar la aplicación o limpiar la caché.",
                "general_access": "Entiendo tu dificultad para acceder a la cuenta. Para ayudarte mejor, ¿puedes decirme qué tipo de problema estás enfrentando? ¿El login no funciona, olvidaste la contraseña, o la app no abre?"
            }
        }
        
        content = responses.get(language, responses["pt-BR"]).get(issue_type, responses[language]["general_access"])
        
        return {
            "content": content,
            "metadata": {
                "action": "account_access_help",
                "issue_type": issue_type,
                "language": language
            }
        }
    
    def _execute_initiate_transfer(self, transfer_type: str, language: str = "pt-BR") -> Dict[str, Any]:
        """Execute transfer initiation help"""
        responses = {
            "pt-BR": {
                "pix": "Perfeito! Para fazer um PIX, preciso de algumas informações. Você quer enviar para uma chave PIX (como CPF, email, telefone) ou para dados bancários? E qual o valor que deseja transferir?",
                "ted": "Para uma TED, preciso dos dados bancários completos do destinatário: banco, agência, conta e CPF/CNPJ. Qual o valor da transferência?",
                "doc": "Para um DOC, preciso dos dados bancários: banco, agência, conta e CPF/CNPJ do destinatário. Lembrando que DOCs têm limite diário. Qual o valor?",
                "internal_transfer": "Para transferência entre suas contas, preciso saber de qual conta você quer transferir e para qual conta. Qual o valor da transferência?"
            },
            "en-US": {
                "pix": "Perfect! For a PIX transfer, I need some information. Do you want to send to a PIX key (like CPF, email, phone) or bank details? And what amount do you want to transfer?",
                "ted": "For a TED, I need complete bank details of the recipient: bank, branch, account, and CPF/CNPJ. What's the transfer amount?",
                "doc": "For a DOC, I need bank details: bank, branch, account, and recipient's CPF/CNPJ. Remember DOCs have daily limits. What's the amount?",
                "internal_transfer": "For transfer between your accounts, I need to know which account you want to transfer from and to which account. What's the transfer amount?"
            },
            "es-US": {
                "pix": "¡Perfecto! Para hacer un PIX, necesito información. ¿Quieres enviar a una clave PIX (como CPF, email, teléfono) o a datos bancarios? ¿Y cuál es el monto que deseas transferir?",
                "ted": "Para una TED, necesito los datos bancarios completos del destinatario: banco, agencia, cuenta y CPF/CNPJ. ¿Cuál es el monto de la transferencia?",
                "doc": "Para un DOC, necesito los datos bancarios: banco, agencia, cuenta y CPF/CNPJ del destinatario. Recuerda que los DOCs tienen límite diario. ¿Cuál es el monto?",
                "internal_transfer": "Para transferencia entre tus cuentas, necesito saber de qué cuenta quieres transferir y a cuál cuenta. ¿Cuál es el monto de la transferencia?"
            }
        }
        
        content = responses.get(language, responses["pt-BR"]).get(transfer_type, responses[language]["pix"])
        
        return {
            "content": content,
            "metadata": {
                "action": "transfer_initiation",
                "transfer_type": transfer_type,
                "language": language
            }
        }
    
    # Maintain backward compatibility with original interface
    def process_user_input(self, text: str, customer_phone: str, language: str = "pt-BR") -> Optional[str]:
        """Backward compatible interface - delegates to original implementation for fallback"""
        # This maintains the existing interface while the enhanced version is being integrated
        return super().process_user_input(text, customer_phone, language)


# Initialize enhanced banking tools
enhanced_banking_tools = EnhancedBankingTools()

def get_enhanced_banking_tools() -> EnhancedBankingTools:
    """Get the enhanced banking tools instance"""
    return enhanced_banking_tools
