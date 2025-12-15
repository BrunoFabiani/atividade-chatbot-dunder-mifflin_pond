# vector_politica.py
import os
import re
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

#Lê a política inteira
with open("politica_compliance.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Função: extrai blocos "SEÇÃO X: ..." até antes da próxima seção
section_pattern = re.compile(
    r"(=+\s*\n\s*SEÇÃO\s+(\d+)\s*:\s*(.*?)\s*\n=+\s*\n)(.*?)(?=\n=+\s*\n\s*SEÇÃO\s+\d+\s*:|\Z)",
    re.S | re.IGNORECASE
)

#Dentro de cada seção, quebra por subtópicos "2.1.", "2.2.", etc.
subsection_pattern = re.compile(r"^\s*(\d+\.\d+)\.\s*(.+?)\s*$", re.M)

documents = []
ids = []

for sec_match in section_pattern.finditer(text):
    sec_header = sec_match.group(1)         # bloco com ===== + título
    sec_num = sec_match.group(2)            # "2"
    sec_title = sec_match.group(3).strip()  # "CATEGORIZAÇÃO..."
    sec_body = sec_match.group(4).strip()   # conteúdo até a próxima seção

    #índices onde começam as subseções (2.1, 2.2, etc.)
    subs = list(subsection_pattern.finditer(sec_body))

    if not subs:
        #se a seção não tiver subseções, indexa ela inteira
        page_content = f"{sec_header}\n{sec_body}".strip()
        doc_id = f"pol_sec_{sec_num}"
        documents.append(
            Document(
                page_content=page_content,
                metadata={"type": "policy", "section": int(sec_num), "subsection": None, "title": sec_title},
            )
        )
        ids.append(doc_id)
        continue

    # se tiver subseções: cria um doc por subseção
    for i, sub_match in enumerate(subs):
        sub_code = sub_match.group(1)           # "2.1"
        sub_title = sub_match.group(2).strip()  # "REFEIÇÕES..."
        start = sub_match.start()
        end = subs[i + 1].start() if i + 1 < len(subs) else len(sec_body)

        sub_text = sec_body[start:end].strip()

        # inclui contexto (seção + subseção) no conteúdo para melhorar busca
        page_content = (
            f"SEÇÃO {sec_num}: {sec_title}\n"
            f"SUBSEÇÃO {sub_code}: {sub_title}\n\n"
            f"{sub_text}"
        ).strip()

        doc_id = f"pol_{sub_code.replace('.', '_')}"
        documents.append(
            Document(
                page_content=page_content,
                metadata={
                    "type": "policy",
                    "section": int(sec_num),
                    "subsection": sub_code,
                    "title": sub_title,
                },
            )
        )
        ids.append(doc_id)

#Vetorização e Chroma
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "./chroma_politica_db"
add_documents = not os.path.exists(os.path.join(db_location, "chroma.sqlite3"))


vector_store = Chroma(
    collection_name="politica_compliance",
    persist_directory=db_location,
    embedding_function=embeddings,
)

if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)

retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 30}
)

