from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
import os

# 修复：使用正确的参数名 dashscope_api_key 而不是 api_key
embeddings = DashScopeEmbeddings(model="text-embedding-v3", dashscope_api_key=os.getenv("API_KEY"))
vector_store = Chroma(persist_directory="chroma_db", collection_name="news", embedding=embeddings)
vector_store.add_documents(docs) 