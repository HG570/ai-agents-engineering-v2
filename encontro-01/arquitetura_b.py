"""Arquitetura B — workflow determinístico.   (COMPLETE OS TODOs 1 e 2)

O fluxo está escrito no código. O modelo só faz duas tarefas pequenas:
classificar a pergunta e redigir a resposta.

    pergunta ──► classificar ──► tema?
                                   ├── "elegibilidade" ──► escalar (sem chamar o modelo)
                                   └── "rh" | "ti" | "beneficios"
                                          ──► buscar(tema, pergunta) ──► [ modelo + 3 documentos ] ──► resposta

Quem decide o próximo passo é o CÓDIGO, não o modelo.
"""
from comum import modelo
from comum.resultado import Resultado
from ferramentas import buscar, formatar
from politica_de_resposta import FORMATO_JSON, REGRAS

CATEGORIAS = ("rh", "ti", "beneficios", "elegibilidade")


# --------------------------------------------------------------------------
# TODO 1 — o classificador
#
# Escreva o prompt de sistema que faz o modelo responder com UMA das
# CATEGORIAS acima, e nada mais. Dicas:
#   - diga o que entra em cada categoria (ex.: "ti: notebook, senha, VPN...");
#   - "elegibilidade" é quando a pessoa pergunta se ELA tem direito a algo;
#   - peça a resposta em minúsculas, sem pontuação.
# --------------------------------------------------------------------------
PROMPT_CLASSIFICADOR = """Você é um classificador de perguntas para suporte interno de colaboradores da Aurora Tecnologia.
Sua tarefa é classificar a pergunta do colaborador em EXATAMENTE UMA das 4 categorias a seguir:

1. elegibilidade: A pessoa pergunta se ELA (ou o dependente dela) tem direito a algum benefício ou regra ("eu tenho direito?", "posso receber?", "tenho direito ao auxílio...?").
2. ti: Perguntas sobre equipamentos, notebooks que quebraram ou caíram, senhas, bloqueio de conta, VPN, acesso remoto, suporte técnico de TI.
3. beneficios: Perguntas sobre regras de benefícios gerais (plano de saúde, inclusão de dependente no plano, vale-refeição, vale-transporte, etc.).
4. rh: Perguntas sobre trabalho remoto (dias em casa), férias (divisão de períodos), licenças (maternidade/paternidade), conduta, normas gerais de trabalho.

Responda APENAS o nome da categoria em minúsculas, sem pontuação e sem nenhuma outra palavra:
rh, ti, beneficios ou elegibilidade"""


def classificar(pergunta: str) -> str:
    resposta = modelo.chamar([modelo.mensagem_do_usuario(pergunta)],
                             sistema=PROMPT_CLASSIFICADOR, max_tokens=10)
    categoria = resposta.texto.strip().lower()

    # Se vier pontuação ou palavras extras, tenta encontrar uma categoria válida
    for cat in CATEGORIAS:
        if cat in categoria:
            return cat

    # Decisão de comportamento padrão se não identificar: rh
    return "rh"


def resolver(pergunta: str) -> Resultado:
    categoria = classificar(pergunta)

    # ----------------------------------------------------------------------
    # TODO 2 — o roteamento
    # ----------------------------------------------------------------------
    # a) Se a categoria for "elegibilidade", escala direto para o RH
    if categoria == "elegibilidade":
        return Resultado("escalar", [], "Análise de elegibilidade deve ser realizada pelo RH.")

    # b) Senão, busca os documentos do tema
    docs = buscar(categoria, pergunta)
    if not docs:
        return Resultado("nao_sei", [], "Nenhum documento encontrado sobre este assunto.")

    # c) Monta o prompt com REGRAS, FORMATO_JSON e os documentos encontrados
    documentos = "\n\n".join(formatar(doc) for doc in docs)
    sistema = f"{REGRAS}\n\n{FORMATO_JSON}\n\nDocumentos disponíveis:\n\n{documentos}"

    resposta = modelo.chamar([modelo.mensagem_do_usuario(pergunta)], sistema=sistema)
    return Resultado.de_json(resposta.texto)

