import streamlit as st
import requests
import matplotlib.pyplot as plt
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Análise de Conteúdo - Brand Framework", layout="wide")
APIFY_TOKEN = st.secrets["apify_token"]



hide_elements = """
        <style>
            div[data-testid="stSliderTickBarMin"],
            div[data-testid="stSliderTickBarMax"] {
                display: none;
            }
        </style>
"""

st.markdown(hide_elements, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS  ▸  Pontuação por regra
# ──────────────────────────────────────────────────────────────────────────────
def score_alcance_da_fonte(followers_est: int) -> int:
    """
    Regra temporária baseada em LIKES x20  ➜  substituir por followers reais
    >1 M   = 10   | ≤1 M = 8 | ≤500 k = 6 | ≤150 k = 4 | ≤30 k = 2 | abaixo = 0
    """
    if followers_est > 1_000_000: return 5
    elif followers_est > 500_000: return 4
    elif followers_est > 150_000: return 3
    elif followers_est > 30_000:  return 2
    else:                         return 1

def score_massa_critica(comments: int) -> int:
    """
    >1000 = 10 | ≤1000 = 8 | ≤500 = 6 | ≤150 = 4 | ≤30 = 2 | abaixo = 0
    """
    if comments > 1_000: return 5
    elif comments > 500: return 4
    elif comments > 150: return 3
    elif comments > 30:  return 2
    else:                return 1


def calc_alcance(fonte:int, massa:int, infl:int) -> float:
    return (fonte + massa + infl) / 3 * 2  # escala de 0 a 10 

def calc_relevancia(especialista:bool,
                    publico_medico:bool,
                    impacto:int,
                    risco_saude:bool,
                    sobre_novo:bool) -> int:
    base = 0
    base += 1 if especialista else 0
    base += 1 if publico_medico else 0
    base += 1 if impacto else 0
    base += 1 if risco_saude else 0
    base += 1 if sobre_novo else 0
    #calcula média ponderada
    return round(base / 5 * 10)  # escala de 0 a 10

# ──────────────────────────────────────────────────────────────────────────────
# Instascraper  ▸  Apify
# ──────────────────────────────────────────────────────────────────────────────
def buscar_dados_instagram(link_post: str):
    run_url = (
        "https://api.apify.com/v2/acts/"
        "apify~instagram-scraper/run-sync-get-dataset-items"
        f"?token={APIFY_TOKEN}"
    )
    payload = {
        "directUrls": [link_post],
        "resultsLimit": 1,
        "mediaDownload": False,
        "proxy": {"useApifyProxy": True}
    }
    r = requests.post(run_url, json=payload, timeout=120)
    if not r.ok:
        st.error(f"Erro {r.status_code}: {r.text}")
        return None
    items = r.json()
    print(items)
    return items[0] if items else None

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR  ▸  URL + PARAMS
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    url_col, btn_col = st.columns([6, 1])
    with url_col:
        link = st.text_input(
            "", placeholder="https://www.instagram.com/p/...",
            value="https://www.instagram.com/p/DJmmBjOvT3a",
            label_visibility="collapsed"
        )
    with btn_col:
        if st.button("🔍"):
            dados = buscar_dados_instagram(link)
            if dados:
                st.session_state["dados"] = dados      # guarda o JSON

                # calcula autoscores e _força_ o valor inicial dos sliders
                auto_fonte  = score_alcance_da_fonte(dados.get("likesCount", 0) * 20)
                auto_massa  = score_massa_critica(dados.get("commentsCount", 0))
                print(auto_massa, auto_fonte)
                st.session_state["fonte_score"] = auto_fonte
                st.session_state["massa_score"] = auto_massa
                st.session_state["influencia_score"] = auto_fonte  # valor padrão
                print(f"Fonte Score: {auto_fonte}, Massa Score: {auto_massa}")

# Dados do último fetch
dados = st.session_state.get("dados")
if not dados:
    st.warning("Por favor, insira um link válido do Instagram e clique em 🔍 para buscar os dados.")
    st.stop()
caption = dados.get("caption", "") if dados else ""
img_url = dados.get("displayUrl") if dados else None
likes    = dados.get("likesCount", 0) if dados else 0
comments = dados.get("commentsCount", 0) if dados else 0
is_video = True if dados.get("type") == "Video" else False
followers_est = likes * 20  # ← placeholder (likes≈5 % dos followers)

# AUTO-SCORES
fonte_auto  = score_alcance_da_fonte(followers_est)
massa_auto  = score_massa_critica(comments)

# ── Controles de Avaliação
with st.sidebar:
    st.subheader("📡 Alcance")
    # Alcance: até 30 mil, 2 pontos; até 150 mil, 4 pontos; até 500 mil, 6 pontos; até 1 milhão, 8 pontos; acima disso, 10 pontos. use label descritivo para cada categoria

    fonte_labels = [
        "Até 30 mil seguidores",
        "Até 150 mil seguidores",
        "Até 500 mil seguidores",
        "Até 1 milhão de seguidores",
        ">1 milhão de seguidores"
    ]

    massa_labels = [
        "Até 30 comentários",
        "Até 150 comentários",
        "Até 500 comentários",
        "Até 1 mil comentários",
        ">1 mil comentários"
    ]

    categoria_labels = [
        "Nada influente",
        "Pouco influente",
        "Influente",
        "Muito influente",
        "Celebridade"
    ]

    

    fonte_score = st.select_slider(label="Alcance do Autor do Post",
                                   options=list(range(1, 6)),
                                   key="fonte_score",
                                   format_func=lambda x: fonte_labels[x-1] if x > 0 else "Nenhum seguidor",
                                   help="Pontuação baseada no número de seguidores do autor do post.")
    
    massa_score = st.select_slider(label="Massa Crítica",
                                   options=list(range(1, 6)),
                                   key="massa_score",
                                   format_func=lambda x: massa_labels[x-1] if x > 0 else "Nenhum comentário",
                                   help="Pontuação baseada no número de comentários no post.")
    categoria_influencia = st.select_slider(
        label="Potencial de Influência",
        options=list(range(1, 6)),
        key="influencia_score",
        format_func=lambda x: categoria_labels[x-1] if x > 0 else "Nenhuma influência",
        help="Pontuação baseada no potencial de influência do autor do post."
    )
    influencia_score = categoria_influencia

    st.subheader("🧠 Relevância do Conteúdo")
    
    #especialista yes / no ao invés de  checkbox

    especialista = st.toggle(
        "É um especialista na área?",
        value=False,
        help = "Ex.: médico, farmacêutico, enfermeiro, etc."
    )
    publico_medico = st.toggle(
        "É direcionado a público médico?",
        value=False,
        help = "Ex.: médicos, farmacêuticos, enfermeiros, etc."
    )
    impacto_vendas = st.toggle(
        "Pode impactar na percepção do paciente?",
        value=False,
        help = "Ex.: pode influenciar na decisão de compra do paciente, ou gerar dúvidas sobre o produto."
    )
    risco_saude = st.toggle(
        "Risco à saúde do paciente?",
        value=False,
        help = "Ex.: pode causar efeitos colaterais graves, ou gerar dúvidas sobre a segurança do produto."
    )
    sobre_novo = st.toggle(
        "Fala sobre a Novo?",
        value=False,
        help = "Ex.: menciona a Novo Nordisk, ou fala sobre o produto da Novo."
    )

# ──────────────────────────────────────────────────────────────────────────────
# SCORES  ▸  ALCANCE & RELEVÂNCIA
# ──────────────────────────────────────────────────────────────────────────────
alcance_score    = calc_alcance(fonte_score, massa_score, influencia_score)
relevancia_score = calc_relevancia(especialista, publico_medico,
                                   impacto_vendas, risco_saude, sobre_novo)

# Zona
if 4.5 <= alcance_score <= 5.5 and 4.5 <= relevancia_score <= 5.5:
    zona = "COMITÊ"
elif alcance_score >= 6 and relevancia_score >= 6:
    zona = "ENTRAR NA CONVERSA"
elif alcance_score < 5 and relevancia_score < 5:
    zona = "SILENCIAR E MONITORAR"
else:
    zona = "EDUCAR"

cores = {
    "ENTRAR NA CONVERSA": "#00B140",
    "EDUCAR": "#F2B600",
    "COMITÊ": "#FF3B1F",
    "SILENCIAR E MONITORAR": "#00B140",
}

# ──────────────────────────────────────────────────────────────────────────────
# LAYOUT  ▸  INFO + GRÁFICO
# ──────────────────────────────────────────────────────────────────────────────

info_col, chart_col = st.columns([1, 2])

with info_col:
    with st.expander("Post", expanded=True):
        
        if is_video:
            video_col = st.columns([1,5,1])
            with video_col[1]:
                st.video(dados.get("videoUrl"))
        elif img_url:
            st.image(img_url, use_container_width=True)
        st.markdown(f"**Texto:** {caption} [🔗]({link})")
        
        st.markdown(f"**Usuário:** {dados.get('ownerUsername', 'Desconhecido')}")
        if is_video:
            st.markdown(f"**Likes:** {likes} | **Comentários:** {comments} | **Visualizações:** {dados['videoPlayCount']}")
        else:
            st.markdown(f"**Likes:** {likes} | **Comentários:** {comments}")
        st.markdown(f"**Data:** {dados.get('timestamp', 'Desconhecida')}")
        st.json(dados, expanded=False) 

   
with chart_col:
    fig, ax = plt.subplots(figsize=(6,6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axhline(5, color='gray', linestyle='--'); ax.axvline(5, color='gray', linestyle='--')
    #fill a triangle
    ax.scatter(relevancia_score, alcance_score, color=cores[zona], s=160, zorder=5)
    if relevancia_score > 5:
        ax.text(relevancia_score-0.2, alcance_score+0.2, zona.replace(" ","\n"), weight='bold', horizontalalignment='center')
    else:
        ax.text(relevancia_score+0.2, alcance_score+0.2, zona, weight='bold')
    ax.set_xlabel("Relevância")
    ax.set_ylabel("Alcance")
    ax.grid(False)
    #cria um warning em x5 y5 caso risco a saude E sobre_novo forem true em alcance_score for 5 ou menos
    if risco_saude and sobre_novo and alcance_score < 5:
        ax.text(5, 2, "⚠️ Risco à saúde - Avisar SQUAD!", fontsize=12, color='red', ha='center', va='center')
        # da pra ter uma caixa vermelha com o texto
        ax.add_patch(plt.Rectangle((2, 1.5), 6, 1, color='red', alpha=0.1))
    st.pyplot(fig)