# CHATBOT PARA AUXILIAR NAS POLITICAS DE COMPLIANCE DO DUNDER MIFFLIN

# ARQUITETURA
DIAGRAMA:

                 (usuário digita pergunta)
                            |
                            v
                        [ Router ]
                 /            |             \
                v             v              v
      [Agente: Policy]  [Agente: Emails]  [Agente: Transações]
            |                |                  |
            v                v                  v
   policy_retriever      email_retriever     compliance_checker.py
  (OllamaEmbeddings)   (OllamaEmbeddings)      (pandas)
            |                |                  |
            v                v                  v
  trechos da política     emails relevantes   lista SUSPEITA/VIOLACAO
      (Chroma_DB)        (Chroma_DB)           (CSV)
            |                |                  |
            v                v                  v
   policy_template     conspiracy_template     (print/relatório)
            \                /
             \              /
              v            v
               [ ChatOllama (llama3.2) ]
                          |
                          v
                      (resposta)

### Framework: langchain
Langchain que traz o template para formata o prompt, chamar o chat e devolver a resposta.
Junto com organizar o fluxo do RAG.
## RAG:
pegam seus arquivos (política e emails), dividem o conteúdo em pedaços menores (“chunks”) e geram embeddings desses pedaços usando mxbai-embed-large. Esses embeddings ficam salvos no ChromaDB.
Quando o usuário faz uma pergunta, o sistema gera o embedding da pergunta, busca no Chroma os trechos mais parecidos (top-k) e coloca esses trechos junto com a pergunta dentro do prompt. A resposta é gerada pelo ChatOllama (llama3.2) usando apenas esse contexto recuperado.

## FERRAMENTAS USADAS:
- Python
- LangChain (`langchain-core`)
- Ollama (`langchain-ollama`)
- ChatOllama (modelo `llama3.2`)
- OllamaEmbeddings (modelo `mxbai-embed-large`)
- ChromaDB (`langchain-chroma` / `chromadb`)
- Pandas (`pandas`)


## video 
https://drive.google.com/file/d/1XhT33KC9ZCQ25Tk_K9OyAlcGyRo6ceIL/view?usp=sharing

# Como rodar o chatbot:
Instale a o repositorio dentro de um pasta

Entre na pasta:

cd folder_name

## Crie um ambiente virtual:
python3 -m venv .venv
source .venv/bin/activate

## Então instale as dependencias:
pip install -r requirements.txt

Com as dependencias instaladas:

## Rode o chatbot
python3 ./main.py

## Faça perguntas como:
Qual regra para despesas acima de 500?
Alguém está conspirando contra Toby?
Cheque as transações para ver se elas estão de acordo com a política de compliance






