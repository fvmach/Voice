# product_discovery.py
# Structured discovery questions for different banking products

import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class ProductDiscoveryGuide:
    """Guide agent through discovery questions for different banking products"""
    
    def __init__(self):
        self.discovery_templates = {
            "investments": {
                "category": "Investimentos",
                "discovery_questions": [
                    {
                        "key": "experience_level",
                        "question_pt": "Para começar, você já investiu antes ou esta seria sua primeira experiência com investimentos?",
                        "question_en": "To start, have you invested before or would this be your first experience with investments?",
                        "type": "choice",
                        "options": ["iniciante", "intermediário", "avançado", "beginner", "intermediate", "advanced"]
                    },
                    {
                        "key": "risk_tolerance", 
                        "question_pt": "Em relação ao risco, você prefere investimentos mais seguros mesmo com menor rentabilidade, ou aceita mais risco para ter potencial de maior retorno?",
                        "question_en": "Regarding risk, do you prefer safer investments even with lower returns, or do you accept more risk for potential higher returns?",
                        "type": "choice",
                        "options": ["conservador", "moderado", "arrojado", "conservative", "moderate", "aggressive"]
                    },
                    {
                        "key": "investment_term",
                        "question_pt": "Qual é o prazo que você pretende deixar esse dinheiro investido? É para usar em breve ou é um investimento de longo prazo?",
                        "question_en": "What timeframe are you planning to keep this money invested? Is it for short-term use or long-term investment?",
                        "type": "choice", 
                        "options": ["curto prazo", "médio prazo", "longo prazo", "short term", "medium term", "long term"]
                    },
                    {
                        "key": "investment_goal",
                        "question_pt": "Qual é o objetivo principal desse investimento? Reserva de emergência, aposentadoria, comprar algo específico?",
                        "question_en": "What's the main goal for this investment? Emergency fund, retirement, buying something specific?",
                        "type": "open"
                    }
                ],
                "personalized_recommendations": {
                    "conservative_short": "Com seu perfil conservador e prazo mais curto, recomendo começar com CDB ou Tesouro Selic.",
                    "conservative_long": "Para investimentos conservadores de longo prazo, o Tesouro IPCA+ é uma excelente opção.",
                    "moderate_short": "Com perfil moderado e prazo curto, uma combinação de renda fixa e fundos pode ser interessante.",
                    "moderate_long": "Para médio/longo prazo com perfil moderado, podemos dividir entre renda fixa e alguns fundos multimercado.",
                    "aggressive_short": "Mesmo com perfil mais arrojado, para curto prazo recomendo manter em renda fixa para ter liquidez.",
                    "aggressive_long": "Com perfil arrojado e longo prazo, podemos explorar fundos de ações e multimercados."
                }
            },
            "loans": {
                "category": "Empréstimos",
                "discovery_questions": [
                    {
                        "key": "loan_purpose",
                        "question_pt": "Para que você precisa do empréstimo? É para quitar dívidas, reformar a casa, investir no negócio?",
                        "question_en": "What do you need the loan for? To pay off debts, home renovation, business investment?",
                        "type": "open"
                    },
                    {
                        "key": "loan_amount",
                        "question_pt": "Qual valor aproximado você precisa?",
                        "question_en": "What approximate amount do you need?",
                        "type": "amount"
                    },
                    {
                        "key": "repayment_preference",
                        "question_pt": "Você prefere pagar em mais parcelas (valor menor por mês) ou em menos parcelas (terminar mais rápido)?",
                        "question_en": "Do you prefer to pay in more installments (lower monthly amount) or fewer installments (finish sooner)?",
                        "type": "choice",
                        "options": ["mais parcelas", "menos parcelas", "more installments", "fewer installments"]
                    }
                ]
            },
            "cards": {
                "category": "Cartões", 
                "discovery_questions": [
                    {
                        "key": "card_usage",
                        "question_pt": "Como você pretende usar o cartão? Mais para compras do dia a dia, emergências, ou gastos maiores?",
                        "question_en": "How do you plan to use the card? More for daily purchases, emergencies, or larger expenses?",
                        "type": "choice",
                        "options": ["dia a dia", "emergências", "gastos maiores", "daily use", "emergencies", "larger expenses"]
                    },
                    {
                        "key": "benefits_preference",
                        "question_pt": "O que é mais importante para você: cashback, milhas, anuidade baixa, ou programa de pontos?",
                        "question_en": "What's most important to you: cashback, miles, low annual fee, or points program?",
                        "type": "choice",
                        "options": ["cashback", "milhas", "anuidade baixa", "pontos", "miles", "low annual fee", "points"]
                    }
                ]
            }
        }
    
    def detect_product_category(self, text: str) -> Optional[str]:
        """Detect which product category the customer is interested in"""
        text_lower = text.lower()
        
        # Investment keywords
        investment_keywords = [
            "investir", "investimento", "aplicar", "render", "rentabilidade",
            "invest", "investment", "apply", "return", "yield", "comissão"
        ]
        
        # Loan keywords  
        loan_keywords = [
            "empréstimo", "emprestar", "financiamento", "crédito",
            "loan", "lending", "financing", "credit"
        ]
        
        # Card keywords
        card_keywords = [
            "cartão", "card", "débito", "crédito", "debit", "credit"
        ]
        
        if any(keyword in text_lower for keyword in investment_keywords):
            return "investments"
        elif any(keyword in text_lower for keyword in loan_keywords):
            return "loans" 
        elif any(keyword in text_lower for keyword in card_keywords):
            return "cards"
            
        return None
    
    def get_next_discovery_question(self, category: str, language: str = "pt-BR") -> Optional[Dict[str, Any]]:
        """Get the first discovery question for a category"""
        if category not in self.discovery_templates:
            return None
            
        questions = self.discovery_templates[category]["discovery_questions"]
        if not questions:
            return None
            
        question = questions[0]  # Start with first question
        question_text = question[f"question_{language[:2]}"] if f"question_{language[:2]}" in question else question["question_pt"]
        
        return {
            "key": question["key"],
            "question": question_text,
            "type": question["type"],
            "options": question.get("options", [])
        }
    
    def get_discovery_question_by_key(self, category: str, question_key: str, language: str = "pt-BR") -> Optional[Dict[str, Any]]:
        """Get a specific discovery question by its key"""
        if category not in self.discovery_templates:
            return None
            
        questions = self.discovery_templates[category]["discovery_questions"]
        for question in questions:
            if question["key"] == question_key:
                question_text = question[f"question_{language[:2]}"] if f"question_{language[:2]}" in question else question["question_pt"]
                return {
                    "key": question["key"],
                    "question": question_text,
                    "type": question["type"],
                    "options": question.get("options", [])
                }
        return None
    
    def generate_discovery_prompt(self, category: str, language: str = "pt-BR") -> str:
        """Generate a prompt to guide the agent through discovery questions"""
        
        if category not in self.discovery_templates:
            return ""
        
        template = self.discovery_templates[category]
        questions = template["discovery_questions"]
        
        if language.startswith("pt"):
            prompt = f"""
INSTRUÇÕES PARA DESCOBERTA DE PRODUTOS - {template['category']}:

Antes de recomendar produtos específicos, você DEVE fazer perguntas de descoberta para entender melhor as necessidades do cliente.

PERGUNTAS OBRIGATÓRIAS (faça UMA de cada vez e aguarde a resposta):
"""
            for i, q in enumerate(questions, 1):
                prompt += f"\n{i}. {q['question_pt']}"
                if q.get('options'):
                    prompt += f"\n   Opções possíveis: {', '.join(q['options'][:3])}..."  # Show first 3 options as example
            
            prompt += """

REGRAS IMPORTANTES:
- Faça APENAS UMA pergunta por vez
- Aguarde a resposta do cliente antes de fazer a próxima pergunta  
- NÃO liste vários produtos de uma vez
- Use as respostas para dar recomendações personalizadas
- Seja conversacional e amigável
- Pergunte se o cliente quer continuar passo a passo ou receber um resumo
"""
        
        else:  # English
            prompt = f"""
PRODUCT DISCOVERY INSTRUCTIONS - {template['category']}:

Before recommending specific products, you MUST ask discovery questions to better understand customer needs.

MANDATORY QUESTIONS (ask ONE at a time and wait for response):
"""
            for i, q in enumerate(questions, 1):
                question_text = q.get('question_en', q['question_pt'])
                prompt += f"\n{i}. {question_text}"
                if q.get('options'):
                    prompt += f"\n   Possible options: {', '.join(q['options'][:3])}..."
            
            prompt += """

IMPORTANT RULES:
- Ask ONLY ONE question at a time
- Wait for customer response before asking next question
- DO NOT list multiple products at once  
- Use responses to give personalized recommendations
- Be conversational and friendly
- Ask if customer wants to continue step-by-step or get a summary
"""
        
        return prompt.strip()
    
    def should_ask_step_preference(self, text: str) -> bool:
        """Check if we should ask about step-by-step vs summary preference"""
        # Look for indicators that the customer might want a different approach
        step_indicators = [
            "passo a passo", "devagar", "calma", "um de cada vez", 
            "step by step", "slowly", "one at a time", "wait"
        ]
        
        summary_indicators = [
            "resumo", "tudo de uma vez", "todas as etapas", "lista",
            "summary", "all at once", "all steps", "list everything"
        ]
        
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in step_indicators):
            return False  # Customer already indicated step preference
        elif any(indicator in text_lower for indicator in summary_indicators): 
            return False  # Customer already indicated summary preference
        else:
            return True  # Ask their preference
    
    def generate_step_preference_question(self, language: str = "pt-BR") -> str:
        """Generate question asking about step-by-step vs summary preference"""
        if language.startswith("pt"):
            return "Prefere que eu te ajude passo a passo, esperando sua confirmação a cada etapa, ou você gostaria de receber um resumo com todas as etapas de uma vez?"
        else:
            return "Would you prefer that I help you step by step, waiting for your confirmation at each stage, or would you like to receive a summary with all the steps at once?"

# Global instance
product_discovery = ProductDiscoveryGuide()

def get_product_discovery() -> ProductDiscoveryGuide:
    """Get the product discovery instance"""
    return product_discovery
