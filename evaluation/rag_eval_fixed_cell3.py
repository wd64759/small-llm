from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma

# 修复：移除 DashScopeEmbeddings 中的 collection_name 参数
embeddings = DashScopeEmbeddings(model="text-embedding-v3", api_key=os.getenv("DASHSCOPE_API_KEY"))
# 修复：将 collection_name 参数移到 Chroma 中
vector_store = Chroma(embedding_function=embeddings, persist_directory="chroma_db", collection_name="news")
vector_store.add_documents(docs) 