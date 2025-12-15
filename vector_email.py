# vector_email.py
import os
import re
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

with open("emails.txt", "r", encoding="utf-8") as f:
    raw = f.read()

blocks = [b.strip() for b in raw.split("-------------------------------------------------------------------------------") if b.strip()]

documents = []
ids = []

for idx, b in enumerate(blocks):
    de = re.search(r"De:\s*(.*)", b)
    para = re.search(r"Para:\s*(.*)", b)
    data = re.search(r"Data:\s*(.*)", b)
    assunto = re.search(r"Assunto:\s*(.*)", b)
    msg = re.search(r"Mensagem:\s*(.*)", b, re.S)

    de_val = de.group(1).strip() if de else ""
    para_val = para.group(1).strip() if para else ""
    data_val = data.group(1).strip() if data else ""
    assunto_val = assunto.group(1).strip() if assunto else ""
    msg_val = msg.group(1).strip() if msg else b

    page_content = f"Assunto: {assunto_val}\nMensagem:\n{msg_val}"

    documents.append(
        Document(
            page_content=page_content,
            metadata={
                "type": "email",
                "from": de_val,
                "to": para_val,
                "date": data_val,
                "subject": assunto_val,
            },
        )
    )
    ids.append(f"email_{idx}")

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "./chroma_emails_db"
add_documents = not os.path.exists(db_location)

vector_store = Chroma(
    collection_name="emails",
    persist_directory=db_location,
    embedding_function=embeddings,
)

if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)

retriever = vector_store.as_retriever(search_kwargs={"k": 5})
