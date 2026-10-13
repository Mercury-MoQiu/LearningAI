"""
基于 LangChain 的文档问答示例
参考: https://blog.csdn.net/AustinCyy/article/details/144823898
改用智谱 GLM API 替代 OpenAI API
"""

import os
import csv
from rich.console import Console
from rich.markdown import Markdown
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA

console = Console()

# ====== 智谱 API 配置（从 .env 读取，.env 不入库） ======
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
if not os.getenv("ZHIPUAI_API_KEY"):
    raise RuntimeError("请先在项目根目录的 .env 文件中设置 ZHIPUAI_API_KEY（参考 .env.example）")

# ====== 创建示例 CSV 数据（模拟原文的户外服装产品目录） ======
CSV_FILE = "OutdoorClothingCatalog_1000.csv"

def create_sample_csv():
    """创建示例户外服装产品目录 CSV 文件"""
    rows = [
        {"name": "Sun Protection Shirt - Model A", "description": "UPF 50+ 防晒衬衫，轻薄透气，适合夏季户外徒步，有防晒功能。", "price": "299"},
        {"name": "Quick Dry T-Shirt - Model B", "description": "速干 T 恤，吸湿排汗，适合跑步和健身。", "price": "159"},
        {"name": "Sun Protection Shirt - Model C", "description": "UPF 40 防晒衬衫，长袖设计，可防紫外线，适合登山和钓鱼。", "price": "349"},
        {"name": "Fleece Jacket - Model D", "description": "抓绒外套，保暖舒适，适合秋冬户外运动。", "price": "399"},
        {"name": "Sun Protection Hat - Model E", "description": "宽檐防晒帽，UPF 50+，可遮挡面部和颈部阳光。", "price": "89"},
        {"name": "Waterproof Jacket - Model F", "description": "防水冲锋衣，防风防雨，适合恶劣天气户外活动。", "price": "599"},
        {"name": "Sun Protection Shirt - Model G", "description": "防晒衬衫，UPF 50+，可转换袖长，多功能设计，适合旅行。", "price": "329"},
        {"name": "Compression Leggings - Model H", "description": "压缩运动裤，提高运动表现，适合跑步和训练。", "price": "199"},
    ]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "description", "price"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"已创建示例 CSV 文件: {CSV_FILE}")


def demo_simple_qa():
    """方式一：使用 VectorstoreIndexCreator 一行代码实现文档问答"""
    print("\n" + "=" * 60)
    print("方式一：VectorstoreIndexCreator 一行代码问答")
    print("=" * 60)

    loader = CSVLoader(file_path=CSV_FILE, encoding="utf-8")

    index = VectorstoreIndexCreator(
        vectorstore_cls=DocArrayInMemorySearch,
        embedding=ZhipuAIEmbeddings(),
    ).from_loaders([loader])

    llm = ChatZhipuAI(model="glm-4-flash", temperature=0.0)

    query = "请列出所有具有防晒功能的衬衫，用 Markdown 表格展示并简要总结。"
    print(f"提问: {query}\n")

    response = index.query(query, llm=llm)
    console.print("\n[bold cyan]回答:[/bold cyan]\n")
    console.print(Markdown(response))


def demo_step_by_step():
    """方式二：逐步拆解文档问答的每个环节"""
    print("\n" + "=" * 60)
    print("方式二：逐步拆解文档问答原理")
    print("=" * 60)

    # 1. 加载文档
    loader = CSVLoader(file_path=CSV_FILE, encoding="utf-8")
    docs = loader.load()
    print(f"\n1. 加载了 {len(docs)} 个文档")
    print(f"   第一个文档内容: {docs[0].page_content[:80]}...")

    # 2. 创建 Embedding
    embeddings = ZhipuAIEmbeddings()
    embed = embeddings.embed_query("你好，我是一件防晒衬衫")
    print(f"\n2. Embedding 维度: {len(embed)}")
    print(f"   前5个值: {embed[:5]}")

    # 3. 创建向量存储
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)
    print(f"\n3. 已将 {len(docs)} 个文档存入向量存储")

    # 4. 相似度搜索
    query = "请推荐有防晒功能的衬衫"
    results = db.similarity_search(query)
    print(f"\n4. 搜索 '{query}' 返回了 {len(results)} 个相关文档")
    print(f"   最相关: {results[0].page_content[:80]}...")

    # 5. 创建检索器
    retriever = db.as_retriever()
    llm = ChatZhipuAI(model="glm-4-flash", temperature=0.3)

    # 6. 使用 RetrievalQA 链
    qa_stuff = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        verbose=False,
    )

    final_query = "请列出所有具有防晒功能的衬衫，用 Markdown 表格展示并简要总结。"
    print(f"\n5. 最终提问: {final_query}\n")

    response = qa_stuff.invoke(final_query)
    result = response["result"] if isinstance(response, dict) else response
    console.print("\n[bold cyan]回答:[/bold cyan]\n")
    console.print(Markdown(result))


if __name__ == "__main__":
    create_sample_csv()
    demo_simple_qa()
    demo_step_by_step()
