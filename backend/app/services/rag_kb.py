"""
RAG知识库服务 - Agent驱动检索架构
路由 → 子索引 → 重排序
"""
import os
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer


class RAGKnowledgeBase:
    """Agent驱动的RAG知识库"""
    
    def __init__(self):
        self.chroma_client = None
        self.collections = {}
        self.embedding_model = None
        self._use_mock_embedding = False
        self._knowledge_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge')
        
        # 尝试加载嵌入模型
        try:
            self.embedding_model = SentenceTransformer('shibing624/text2vec-base-chinese')
        except Exception as e:
            print(f"⚠️ 嵌入模型加载失败，使用模拟嵌入: {e}")
            self._use_mock_embedding = True
        
        self._init_knowledge_base()
    
    def _init_knowledge_base(self):
        """初始化知识库"""
        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            
            self.collections = {
                "cases": self.chroma_client.get_or_create_collection("industry_cases"),
                "attribution": self.chroma_client.get_or_create_collection("attribution_models"),
                "creative": self.chroma_client.get_or_create_collection("creative_templates"),
                "strategy": self.chroma_client.get_or_create_collection("strategies"),
            }
            
            # 加载本地知识库文档
            self._load_knowledge_documents()
        except Exception as e:
            print(f"⚠️ ChromaDB初始化失败，使用本地检索: {e}")
    
    def _load_knowledge_documents(self):
        """加载本地知识库文档到向量库"""
        if not self.collections:
            return
        
        # 加载行业案例
        self._load_json_files("cases", "industry_cases")
        
        # 加载归因模型
        self._load_md_files("attribution", "attribution_models")
        
        # 加载创意模板
        self._load_json_files("creative", "creative_templates")
        
        # 加载策略文档
        self._load_md_files("strategy", "strategies")
    
    def _load_json_files(self, collection_name: str, subdir: str):
        """加载JSON文件到指定集合"""
        subdir_path = os.path.join(self._knowledge_dir, subdir)
        if not os.path.exists(subdir_path):
            return
        
        collection = self.collections.get(collection_name)
        if not collection:
            return
        
        for filename in os.listdir(subdir_path):
            if filename.endswith('.json'):
                filepath = os.path.join(subdir_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    content = json.dumps(data, ensure_ascii=False)
                    doc_id = f"{subdir}_{filename}"
                    
                    self._add_document(collection, doc_id, content, {"source": filename, "type": subdir})
                except Exception as e:
                    print(f"加载{filename}失败: {e}")
    
    def _load_md_files(self, collection_name: str, subdir: str):
        """加载Markdown文件到指定集合"""
        subdir_path = os.path.join(self._knowledge_dir, subdir)
        if not os.path.exists(subdir_path):
            return
        
        collection = self.collections.get(collection_name)
        if not collection:
            return
        
        for filename in os.listdir(subdir_path):
            if filename.endswith('.md'):
                filepath = os.path.join(subdir_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    doc_id = f"{subdir}_{filename}"
                    self._add_document(collection, doc_id, content, {"source": filename, "type": subdir})
                except Exception as e:
                    print(f"加载{filename}失败: {e}")
    
    def _encode_text(self, text: str) -> list:
        """文本编码为向量"""
        if self._use_mock_embedding:
            # 模拟嵌入：使用hash生成固定维度向量
            import hashlib
            h = hashlib.md5(text.encode('utf-8')).hexdigest()
            return [int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
        return self.embedding_model.encode(text).tolist()
    
    def _add_document(self, collection, doc_id: str, content: str, metadata: dict):
        """添加文档到集合"""
        try:
            embedding = self._encode_text(content)
            collection.add(
                embeddings=[embedding],
                documents=[content],
                ids=[doc_id],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"添加文档{doc_id}失败: {e}")
    
    async def query(self, query_text: str, n_results: int = 5) -> dict:
        """Agent驱动检索：路由→检索→重排序"""
        if not self.collections:
            return {"results": [], "message": "知识库未初始化"}
        
        # 1. 顶层路由：判断查询类型
        route = await self._route_query(query_text)
        
        # 2. 子索引检索
        collection = self.collections.get(route)
        if not collection:
            return {"results": [], "route": route, "message": f"未找到集合: {route}"}
        
        try:
            query_embedding = self._encode_text(query_text)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results * 2, collection.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            # 3. 重排序（按距离排序）
            ranked = self._rerank_results(results, n_results)
            
            return {
                "route": route,
                "results": ranked,
                "count": len(ranked)
            }
        except Exception as e:
            return {"results": [], "error": str(e)}
    
    async def _route_query(self, query_text: str) -> str:
        """路由查询：根据查询内容选择最相关的集合"""
        query_lower = query_text.lower()
        
        # 路由规则
        if any(kw in query_lower for kw in ["案例", "case", "行业", "成功"]):
            return "cases"
        elif any(kw in query_lower for kw in ["归因", "attribution", "模型", "touch"]):
            return "attribution"
        elif any(kw in query_lower for kw in ["创意", "creative", "素材", "文案", "aigc"]):
            return "creative"
        elif any(kw in query_lower for kw in ["策略", "strategy", "优化", "建议", "投放"]):
            return "strategy"
        else:
            # 默认使用策略集合
            return "strategy"
    
    def _rerank_results(self, results: dict, n_results: int) -> list:
        """重排序结果"""
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        # 按距离排序（距离越小越相关）
        ranked = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            ranked.append({
                "content": doc,
                "metadata": meta,
                "distance": dist,
                "relevance_score": 1.0 / (1.0 + dist)
            })
        
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked[:n_results]
    
    def add_document(self, collection_name: str, doc_id: str, content: str, metadata: dict = None):
        """手动添加文档"""
        collection = self.collections.get(collection_name)
        if not collection:
            raise ValueError(f"集合不存在: {collection_name}")
        
        self._add_document(collection, doc_id, content, metadata or {})


# 全局实例
rag_kb = RAGKnowledgeBase()
