import streamlit as st
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pipeline import processar_interacoes_comunidade
from oci_storage import salvar_ativo_no_oci

load_dotenv()

st.set_page_config(
    page_title="CommunityLab | ONE G10",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.title("⚡ CommunityLab")
    st.markdown("**Hackathon ONE - Grupo 10**")
    st.caption("Motor de Transformação & Distribuição")
    
    chave_input = st.text_input("Gemini API Key", type="password", help="Insira sua chave do Google AI Studio ou configure no .env")
    gemini_key = chave_input if chave_input else os.getenv("GEMINI_API_KEY")
    
    st.divider()
    st.subheader("Persistência OCI")
    bucket_nome = os.getenv("OCI_BUCKET_NAME", "communitylab-ativos-marketing")
    st.text_input("Bucket OCI", value=bucket_nome, disabled=True)
    modo_sim = os.getenv("MODO_SIMULACAO_OCI", "true").lower() == "true"
    if modo_sim:
        st.info("ℹ️ Modo Simulação OCI Ativo (Salva localmente sem falhar)")
    else:
        st.success("☁️ Conectado ao OCI Always Free")

st.title("🚀 CommunityLab — Motor Inteligente")
st.markdown("Transformação automatizada de conversas orgânicas da comunidade em ativos de marketing e documentação com IA e Nuvem.")

dados_padrao_edital = {
    "origem_comunidade": "Discord_Grupo_ONE_G10",
    "periodo_referencia": "Semana_04",
    "interacoes": [
        {
            "autor": "Mariana Souza",
            "canal": "#conquistas-e-vagas",
            "tipo": "depoimento",
            "texto": "Pessoal, passei no processo seletivo para Desenvolvedora Júnior de IA! O projeto do curso de LangChain e OCI que construí no portfólio fez toda a diferença na entrevista técnica. Muito grata à comunidade pelo apoio!"
        },
        {
            "autor": "Lucas Albuquerque",
            "canal": "#duvidas-langgraph",
            "tipo": "pergunta_tecnica",
            "texto": "Estou com dúvida de como estruturar os nós condicionais no LangGraph quando a resposta do Gemini precisa de retry. Alguém tem um exemplo prático de router?"
        },
        {
            "autor": "Gabriel Torres",
            "canal": "#feedbacks-projetos",
            "tipo": "depoimento",
            "texto": "Finalizei o deployment do meu backend usando a camada Always Free da OCI. A latência ficou incrível e o custo é literalmente zero. Recomendo muito estudarem as regras de firewall de lá!"
        }
    ]
}

col_esq, col_dir = st.columns([1, 1], gap="large")

with col_esq:
    st.subheader("1. Ingestão da Comunidade")
    texto_json = st.text_area(
        "Lote de Interações (JSON):", 
        value=json.dumps(dados_padrao_edital, indent=2, ensure_ascii=False), 
        height=390
    )
    btn_executar = st.button("✨ Executar Curadoria com IA", type="primary", use_container_width=True)

if btn_executar:
    if not gemini_key:
        st.error("Chave da API Gemini não encontrada. Configure no arquivo .env ou informe no menu lateral.")
    else:
        try:
            dados_validos = json.loads(texto_json)
            with st.spinner("Classificando sentimento, extraindo tópicos e gerando copys multicanal..."):
                resultado = processar_interacoes_comunidade(dados_validos, gemini_key)
                st.session_state["resultado_gerado"] = resultado
                st.session_state["lote_processado"] = dados_validos
                st.toast("Processamento concluído com sucesso!", icon="✅")
        except json.JSONDecodeError:
            st.error("O texto fornecido não é um JSON válido. Verifique a formatação.")
        except Exception as e:
            st.error(f"Erro na execução da esteira: {e}")

with col_dir:
    st.subheader("2. Painel de Curadoria & Ativos")
    
    if "resultado_gerado" in st.session_state:
        dados_resultado = st.session_state["resultado_gerado"]
        resumo = dados_resultado.get("resumo_comunidade", {})
        ativos = dados_resultado.get("ativos_distribuicao_gerados", {})
        
        met_col1, met_col2 = st.columns(2)
        with met_col1:
            st.metric("Sentimento Predominante", resumo.get("sentimento_predominante", "N/A"))
        with met_col2:
            st.metric("Mensagens Processadas", resumo.get("total_interacoes_processadas", 0))
            
        st.caption(f"**Tópicos Identificados:** {', '.join(resumo.get('topicos_principais', []))}")
        st.divider()
        
        aba_linkedin, aba_newsletter, aba_faq = st.tabs([
            "💼 Post LinkedIn", 
            "📬 Newsletter Semanal", 
            "💡 Tópico de FAQ"
        ])
        
        with aba_linkedin:
            item_in = ativos.get("post_linkedin", {})
            st.markdown(f"**Título:** {item_in.get('titulo')}")
            post_editavel = st.text_area("Copy ajustável:", value=item_in.get("copy", ""), height=170)
            col_l1, col_l2 = st.columns(2)
            col_l1.caption(f"Canal: `{item_in.get('canal_recomendado')}`")
            col_l2.caption(f"Engajamento: **{item_in.get('potencial_engajamento')}**")

        with aba_newsletter:
            item_news = ativos.get("destaque_newsletter_semanal", {})
            st.markdown(f"**Seção:** `{item_news.get('secao')}`")
            st.markdown(f"**Chamada:** *{item_news.get('chamada')}*")
            st.info(item_news.get("resumo"))

        with aba_faq:
            item_faq = ativos.get("sugestao_conteudo_faq", {})
            st.markdown(f"**Tema:** {item_faq.get('tema')}")
            st.markdown(f"**Origem:** {item_faq.get('origem')}")
            st.markdown(f"**Status:** `{item_faq.get('status')}`")

        st.divider()
        
        if st.button("💾 Aprovar e Persistir no OCI Object Storage", use_container_width=True):
            agora = datetime.now()
            nome_arquivo = f"ativos/{agora.strftime('%Y-semana-%W')}/pacote_{agora.strftime('%Y%m%d_%H%M%S')}.json"
            
            pacote_completo = {
                "status": "sucesso",
                "resumo_comunidade": resumo,
                "ativos_distribuicao_gerados": {
                    "post_linkedin": {
                        "titulo": item_in.get("titulo"),
                        "copy": post_editavel,
                        "canal_recomendado": item_in.get("canal_recomendado"),
                        "potencial_engajamento": item_in.get("potencial_engajamento")
                    },
                    "destaque_newsletter_semanal": item_news,
                    "sugestao_conteudo_faq": item_faq
                }
            }
            
            resultado_oci = salvar_ativo_no_oci(pacote_completo, nome_arquivo)
            pacote_completo["armazenamento_oci"] = resultado_oci
            
            st.success("Pacote de ativos homologado e salvo com sucesso!")
            st.json(resultado_oci)
    else:
        st.info("Aguardando execução. Clique no botão ao lado para iniciar a IA.")
