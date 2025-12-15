from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from vector_email import retriever as email_retriever
from vector_politica import retriever as policy_retriever
import pandas as pd
import re

from compliance_checker import scan_csv, filter_findings, summarize

model = ChatOllama(model="llama3.2", temperature=0)

policy_template = """
Você é um assistente e expert sobre a política de compliance. Responda APENAS com base nos trechos da política abaixo.

TRECHOS DA POLÍTICA:
{politica}

Se a pergunta for ampla (ex.: "Como deve ser minha conduta?") e os trechos não responderem diretamente,
diga que é ampla e peça para especificar (ex.: viagens, refeições, TI, despesas > $500, reembolsos etc.).
Não chute.

Se a resposta não estiver nos trechos, diga: "Não encontrei essa regra nos trechos fornecidos".

Sempre cite (copie) 1-3 frases exatas dos trechos como evidência.

Se a pergunta for sobre valores/limites (ex.: "acima de 500"), extraia TODAS as exigências dessa faixa (autoridade, aprovações e proibições como "smurfing").




PERGUNTA:
{question}
"""

conspiracy_template = """
Você é um investigador interno. Verifique se existe evidência, nos emails abaixo, de que Michael Scott
está conspirando/planejando ações contra Toby (monitoramento, sabotagem, perseguição, "Operação Fênix", etc).

Regras:
- Use APENAS os emails fornecidos.
- Não invente fatos.
- Responda com: Confirmado / Suspeita / Inconclusivo
- Cite trechos exatos (copie linhas/frases dos emails) como evidência.

EMAILS RECUPERADOS:
{email}

HIPÓTESE/PERGUNTA:
{question}
"""



policy_chain = ChatPromptTemplate.from_template(policy_template) | model
conspiracy_chain = ChatPromptTemplate.from_template(conspiracy_template) | model



def is_conspiracy_question(q: str) -> bool:
    ql = q.lower()
    return any(k in ql for k in ["conspira", "conspiração", "michael", "toby", "operação fênix", "phoenix", "infiltrado"])

def is_transacoes_question(q: str) -> bool:
    ql = q.lower()
    return any(k in ql for k in ["transações", "transacoes", "transação", "transacao", "csv", "planilha", "histórico"])

def policy_query(q: str) -> str:
    ql = q.lower().strip()
    ql = ql.replace("rembolsar", "reembolsar")  # normalização mínima

    if re.search(r"\b500\b", ql) or "acima de 500" in ql:
        ql += " grandes despesas categoria A acima de US$ 500 pedido de compra PO CFO David Wallace"
    return ql

while True:
    print("\n\n-------------------------------")
    question = input("Pergunta (q para sair): ").strip()
    if question.lower() == "q":
        break

    if is_conspiracy_question(question):
        email_docs = email_retriever.invoke(question)
        email_ctx = "\n\n".join(d.page_content for d in email_docs)

        result = conspiracy_chain.invoke({"email": email_ctx, "question": question})
        print(result.content)

    elif is_transacoes_question(question):
        findings = scan_csv("transacoes_bancarias.csv")
        findings = filter_findings(findings, only_not_ok=True)  # keep SUSPEITA/VIOLACAO
        print(summarize(findings, limit=200))



    else:
        q_for_retrieval = policy_query(question)
        policy_docs = policy_retriever.invoke(q_for_retrieval)
        politica_ctx = "\n\n".join(d.page_content for d in policy_docs)

        ql = question.lower()
        
        result = policy_chain.invoke({"politica": politica_ctx, "question": question})
        print(result.content)
