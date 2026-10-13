"""
可视化展示：8个文档的Embedding向量 + query的Embedding向量 + 余弦相似度计算
"""

import os
import csv
import numpy as np
from rich.console import Console
from rich.table import Table
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader

console = Console()

# API Key 从项目根目录 .env 读取（.env 不入库，见 .gitignore）
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
if not os.getenv("ZHIPUAI_API_KEY"):
    raise RuntimeError("请先在项目根目录的 .env 文件中设置 ZHIPUAI_API_KEY（参考 .env.example）")

CSV_FILE = "OutdoorClothingCatalog_1000.csv"


def cosine_similarity(a, b):
    """余弦相似度 —— 复现 docarray numpy_backend.py:213-223 的计算逻辑"""
    eps = 1e-7
    return float(np.clip(
        (np.dot(a, b) + eps) /
        (np.linalg.norm(a) * np.linalg.norm(b) + eps),
        -1, 1
    ))


def main():
    # 1. 加载 8 个文档
    loader = CSVLoader(file_path=CSV_FILE, encoding="utf-8")
    docs = loader.load()

    console.print(f"\n[bold green]加载了 {len(docs)} 个文档[/bold green]\n")

    # 2. 生成 8 个文档的 Embedding
    embeddings = ZhipuAIEmbeddings()
    texts = [d.page_content for d in docs]
    doc_vectors = embeddings.embed_documents(texts)

    # 3. 生成 query 的 Embedding
    query = "请推荐有防晒功能的衬衫"
    query_vector = embeddings.embed_query(query)

    # 4. 展示每个文档的向量信息
    console.print("[bold cyan]═══ 8个文档的 Embedding 向量 ═══[/bold cyan]\n")

    for i, (doc, vec) in enumerate(zip(docs, doc_vectors)):
        content_preview = doc.page_content[:60].replace("\n", " ")
        console.print(f"[yellow]文档 {i}[/yellow]: {content_preview}...")
        console.print(f"  向量维度: {len(vec)}")
        console.print(f"  前8个值:  [{', '.join(f'{v:.6f}' for v in vec[:8])}, ...]")
        console.print(f"  向量模长: {np.linalg.norm(vec):.6f}")
        console.print()

    # 5. 展示 query 的向量
    console.print("[bold cyan]═══ Query 的 Embedding 向量 ═══[/bold cyan]\n")
    console.print(f"[yellow]Query[/yellow]: {query}")
    console.print(f"  向量维度: {len(query_vector)}")
    console.print(f"  前8个值:  [{', '.join(f'{v:.6f}' for v in query_vector[:8])}, ...]")
    console.print(f"  向量模长: {np.linalg.norm(query_vector):.6f}\n")

    # 6. 计算并展示余弦相似度
    console.print("[bold cyan]═══ 余弦相似度计算（query 与每个文档） ═══[/bold cyan]\n")

    console.print("[dim]公式: cos_sim(A, B) = (A·B) / (|A| × |B|)[/dim]")
    console.print("[dim]源码: docarray/computation/numpy_backend.py:213-223[/dim]\n")

    scores = []
    for i, (doc, vec) in enumerate(zip(docs, doc_vectors)):
        sim = cosine_similarity(query_vector, vec)
        scores.append((i, sim, doc))

        # 展示点积和模长
        dot_product = float(np.dot(query_vector, vec))
        norm_q = np.linalg.norm(query_vector)
        norm_d = np.linalg.norm(vec)

        content_preview = doc.page_content[:50].replace("\n", " ")
        console.print(f"[yellow]文档 {i}[/yellow]: {content_preview}...")
        console.print(f"  A·B (点积)     = {dot_product:.6f}")
        console.print(f"  |A| (query模长) = {norm_q:.6f}")
        console.print(f"  |B| (文档模长)  = {norm_d:.6f}")
        console.print(f"  cos_sim         = {dot_product:.6f} / ({norm_q:.6f} × {norm_d:.6f})")
        console.print(f"                 = [bold green]{sim:.6f}[/bold green]")
        console.print()

    # 7. 排序展示
    scores.sort(key=lambda x: x[1], reverse=True)

    console.print("[bold cyan]═══ 按相似度排序（从高到低） ═══[/bold cyan]\n")

    table = Table(title="Query 与 8 个文档的余弦相似度排名")
    table.add_column("排名", style="bold magenta")
    table.add_column("文档编号", style="yellow")
    table.add_column("相似度", style="green")
    table.add_column("内容预览")

    for rank, (doc_idx, sim, doc) in enumerate(scores, 1):
        content = doc.page_content[:50].replace("\n", " ")
        table.add_row(str(rank), str(doc_idx), f"{sim:.6f}", content + "...")

    console.print(table)
    console.print()

    # 8. 说明 similarity_search 如何工作
    console.print("[bold cyan]═══ similarity_search 的完整流程 ═══[/bold cyan]\n")
    console.print("""
[1] 用户调用 db.similarity_search("请推荐有防晒功能的衬衫")

[2] base.py:105  query_embedding = self.embedding.embed_query(query)
    → 调用智谱 embedding-2 模型，把 query 文本转成 1024 维向量

[3] base.py:106  query_doc = self.doc_cls(embedding=query_embedding)
    → 把 query 向量包装成 docarray 文档对象

[4] base.py:107  docs, scores = self.doc_index.find(query_doc, search_field="embedding", limit=k)
    → docarray 在所有存储的文档向量中，用余弦相似度逐一比对
    → numpy_backend.py:213-223 核心计算：
       cos_sim = (A·B + eps) / (|A| × |B| + eps)
    → 按相似度从高到低排序，取前 k=4 个

[5] base.py:109-113  返回 [(Document, score), ...] 列表
    → similarity_search 只取 Document，丢弃 score
""")


if __name__ == "__main__":
    main()
