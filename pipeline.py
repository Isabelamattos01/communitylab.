import os
import json
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """Você é o CommunityLab, um agente sênior especialista em MarTech, Community-Led Growth e Engenharia de Conteúdo para ecossistemas tech e educacionais.
Sua missão é ingerir dados orgânicos da comunidade (vitórias de alunos, dúvidas em fóruns, trocas em canais de suporte e depoimentos) e convertê-los em ativos estruturados de alto impacto.

Regras de Negócio e Tom de Voz:
1. post_linkedin: Copy autêntico, persuasivo e humanizado. Use storytelling, destaque nominalmente o aluno protagonista, contextualize o aprendizado prático e adicione hashtags estratégicas (#TalentosTech, #OracleCloud, #ONE, #CarreiraDev).
2. destaque_newsletter_semanal: Formato editorial claro, conciso, focado em inspirar leitores na seção 'Vitória da Semana' ou 'Destaque da Comunidade'.
3. sugestao_conteudo_faq: Se houver dúvidas técnicas recorrentes, transforme em um mini guia / dica didática para a base de conhecimento.
4. Análise analítica: Avalie o sentimento global com rigor técnico e extraia os principais tópicos mapeados.

Retorne EXCLUSIVAMENTE um objeto JSON válido, sem qualquer bloco de texto antes ou depois, seguindo estritamente a especificação solicitada."""

def processar_interacoes_comunidade(payload_comunidade: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
    """
    Executa a pipeline de análise e síntese com o modelo Google Gemini.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Chave GEMINI_API_KEY não foi configurada.")
    
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
        system_instruction=SYSTEM_PROMPT
    )
    
    schema_prompt = f"""
    Processe o seguinte lote de interações da comunidade e responda ESTRITAMENTE com a estrutura JSON abaixo:
    {{
        "resumo_comunidade": {{
            "total_interacoes_processadas": int,
            "sentimento_predominante": "Altamente Positivo" | "Positivo" | "Neutro" | "Atenção Necessária",
            "topicos_principais": ["Tópico 1", "Tópico 2", "Tópico 3"]
        }},
        "ativos_distribuicao_gerados": {{
            "post_linkedin": {{
                "titulo": "Título de alto engajamento",
                "copy": "Texto completo do post com emojis e hashtags",
                "canal_recomendado": "LinkedIn Oficial",
                "potencial_engajamento": "Alto" | "Médio"
            }},
            "destaque_newsletter_semanal": {{
                "secao": "Vitória da Semana",
                "chamada": "Frase de impacto para chamada",
                "resumo": "Texto resumo para disparo por e-mail"
            }},
            "sugestao_conteudo_faq": {{
                "tema": "Tema central abordado na dúvida",
                "origem": "Contexto do aluno/canal",
                "status": "encaminhado_para_mentoria"
            }}
        }}
    }}

    Dados de entrada:
    {json.dumps(payload_comunidade, ensure_ascii=False, indent=2)}
    """
    
    response = model.generate_content(
        schema_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.4
        }
    )
    
    return json.loads(response.text)
