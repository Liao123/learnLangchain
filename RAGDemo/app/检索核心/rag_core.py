"""父子知识库 RAG 的可复用检索部分。"""

import hashlib
import json
from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer, util


# rag_core.py 现在位于 RAGDemo/app/检索核心/，所以要向上 2 层才回到 RAGDemo 根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARENT_CHILD_INDEX = PROJECT_ROOT / "data" / "indexes" / "父子知识库索引.json"
PARENT_METADATA_FILE = PROJECT_ROOT / "data" / "indexes" / "父子知识库元数据.json"
LOCAL_MODEL_DIR = PROJECT_ROOT / "models" / "bge-small-zh-v1.5"
LOCAL_RERANKER_DIR = PROJECT_ROOT / "models" / "bge-reranker-base"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


def get_index_content_version(index_file: Path = PARENT_CHILD_INDEX) -> str:
    """根据索引 JSON 文件内容生成短版本号，内容改变时版本自动改变。"""
    # read_bytes() 读取完整索引内容；SHA-256 前 12 位足够作为当前项目的短缓存版本。
    index_hash = hashlib.sha256(index_file.read_bytes()).hexdigest()
    return f"index-{index_hash[:12]}"


def load_parent_child_index(
    index_file: Path = PARENT_CHILD_INDEX,
    metadata_file: Path = PARENT_METADATA_FILE,
) -> dict:
    """读取索引和元数据，并检查它们能否和父章节一一对应。"""
    index_data = json.loads(index_file.read_text(encoding="utf-8"))
    metadata_by_parent_id = json.loads(metadata_file.read_text(encoding="utf-8"))
    parents = index_data["parents"]
    children = index_data["children"]
    child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

    if len(children) != len(child_embeddings):
        raise ValueError("父子知识库索引损坏：子片段数量与子向量数量不一致。")

    # 给每个父章节加上元数据，例如“商品类型：咖啡豆”。
    # get() 表示按 parent_id 取元数据；找不到时先得到 None，再报清楚的错误。
    for parent in parents:
        metadata = metadata_by_parent_id.get(parent["parent_id"])
        if metadata is None:
            raise ValueError(f"缺少父章节 {parent['parent_id']} 的元数据。")
        parent["metadata"] = metadata

    index_data["children"] = children
    index_data["child_embeddings"] = child_embeddings
    index_data["parents_by_id"] = {
        parent["parent_id"]: parent
        for parent in parents
    }
    return index_data

def load_embedding_model(model_name: str) -> tuple[SentenceTransformer, str]:
    """优先加载项目内模型，其次使用已下载缓存，最后才联网下载。"""
    # 第一优先级：RAGDemo/models/ 里有模型时，直接读这个项目自己的模型文件夹。
    if LOCAL_MODEL_DIR.exists():
        model_source = str(LOCAL_MODEL_DIR)
        return SentenceTransformer(model_source), model_source

    # 第二优先级：模型以前下载成功过时，Hugging Face 会把它放进用户本地缓存。
    # local_files_only=True 表示只读缓存，不先联网检查最新版本。
    # 这样离线也能运行，网络慢时也不会卡在“检查模型仓库”这一步。
    try:
        cached_model = SentenceTransformer(model_name, local_files_only=True)
        return cached_model, f"{model_name}（本地缓存）"
    except OSError:
        # 第三优先级：本机从未下载过模型，才允许 SentenceTransformer 联网下载。
        downloaded_model = SentenceTransformer(model_name)
        return downloaded_model, model_name


def load_reranker_model(
    model_name: str = RERANKER_MODEL_NAME,
) -> tuple[CrossEncoder, str]:
    """加载重排序模型；它负责逐条精读问题和候选片段。"""
    model_source = str(LOCAL_RERANKER_DIR) if LOCAL_RERANKER_DIR.exists() else model_name
    return CrossEncoder(model_source), model_source


def rerank_matches(
    question: str,
    matches: list[dict],
    reranker_model: CrossEncoder,
) -> list[dict]:
    """让 reranker 为候选子片段重新打分，并按新分数从高到低排序。"""
    if not matches:
        return []

    # pairs 里的每一项都是“用户问题 + 一个候选片段”。
    # reranker 不把它们变成独立向量，而是同时阅读这一对文字后直接给相关性分数。
    pairs = []
    for match in matches:
        pairs.append([question, match["child"]["content"]])

    rerank_scores = reranker_model.predict(pairs)
    reranked_matches = []

    # BGE 原始分数保留在 match["score"]；新的 rerank_score 单独保存，方便前后对比。
    for position in range(len(matches)):
        reranked_match = {
            "score": matches[position]["score"],
            "child": matches[position]["child"],
            "rerank_score": float(rerank_scores[position]),
        }
        reranked_matches.append(reranked_match)

    # sort() 会原地排序。key 指定“按哪个值排序”，reverse=True 表示分数高的排在前面。
    reranked_matches.sort(
        key=lambda match: match["rerank_score"],
        reverse=True,
    )
    return reranked_matches


def parent_matches_metadata(parent: dict, metadata_filters: dict[str, str] | None) -> bool:
    """检查一个父章节是否满足全部元数据条件。"""
    if metadata_filters is None:
        return True

    # items() 会一次拿出“字段名 + 期待值”，例如“商品类型 + 现制饮品”。
    for field_name, expected_value in metadata_filters.items():
        # get() 读取元数据字段；实际值和期待值不同，就不让这章参加检索。
        if parent["metadata"].get(field_name) != expected_value:
            return False

    return True


def match_knowledge_base_routes(question: str, knowledge_base_routes: dict) -> list[dict]:
    """根据关键词找出问题命中的知识库主题。"""
    matched_routes = []

    # 这段循环来自第 40 课。第 41 课开始复用它，不再要求你重复阅读同一套路由循环。
    for route_name, route in knowledge_base_routes.items():
        matched_keywords = []
        for keyword in route["keywords"]:
            if keyword in question:
                matched_keywords.append(keyword)

        if matched_keywords:
            matched_routes.append({
                "route_name": route_name,
                "matched_keywords": matched_keywords,
                "parent_ids": route["parent_ids"],
            })

    return matched_routes


def choose_route_action(matched_routes: list[dict]) -> str:
    """把路由数量转换成三种明确动作：拒答、单路由、多路由回退。"""
    if len(matched_routes) == 0:
        return "reject"
    if len(matched_routes) == 1:
        return "single_route"
    return "multi_route_fallback"


def build_routed_index_data(index_data: dict, matched_routes: list[dict]) -> tuple[dict, set, list[dict]]:
    """只保留路由允许的子片段和对应向量，供后续 BGE 检索使用。"""
    allowed_parent_ids = set()
    for matched_route in matched_routes:
        allowed_parent_ids.update(matched_route["parent_ids"])

    allowed_child_indices = []
    for child_index in range(len(index_data["children"])):
        child = index_data["children"][child_index]
        if child["parent_id"] in allowed_parent_ids:
            allowed_child_indices.append(child_index)

    routed_children = []
    for child_index in allowed_child_indices:
        routed_children.append(index_data["children"][child_index])

    routed_index_data = index_data.copy()
    routed_index_data["children"] = routed_children
    routed_index_data["child_embeddings"] = index_data["child_embeddings"][allowed_child_indices]
    return routed_index_data, allowed_parent_ids, routed_children


def retrieve_parent_context(
    question: str,
    index_data: dict,
    embedding_model: SentenceTransformer,
    top_k: int = 3,
    min_relevance_score: float | None = None,
    metadata_filters: dict[str, str] | None = None,
) -> dict:
    """先按元数据缩小范围，再把问题变成可交给 AI 的完整父章节资料。"""
    # candidate_child_indices 保存“允许参加本次检索”的子片段下标。
    # range(len(...)) 会依次得到 0、1、2……，刚好对应 children 列表里的位置。
    candidate_child_indices = []
    for child_index in range(len(index_data["children"])):
        child = index_data["children"][child_index]
        parent = index_data["parents_by_id"][child["parent_id"]]

        if parent_matches_metadata(parent, metadata_filters):
            candidate_child_indices.append(child_index)

    # 过滤条件没有匹配任何章节时，不做相似度比较，直接返回空结果。
    if not candidate_child_indices:
        raw_results = []
    else:
        # 过滤完成后，才把用户问题变成向量。
        # BGE 只负责把文字变成数字；它不参与元数据的“商品类型是否相等”判断。
        query_embedding = embedding_model.encode(
            [QUERY_INSTRUCTION + question],
            normalize_embeddings=True,
        )

        # 只取允许范围内的向量。比如筛选“现制饮品”后，咖啡豆章节不会参与比较。
        candidate_embeddings = index_data["child_embeddings"][candidate_child_indices]
        candidate_results = util.semantic_search(
            query_embedding,
            candidate_embeddings,
            top_k=min(top_k, len(candidate_child_indices)),
        )[0]

        # candidate_results 的 corpus_id 是“筛选后列表”的下标。
        # 这里把它换回原始 children 列表的下标，后续代码才能正常取回原文。
        raw_results = []
        for candidate_result in candidate_results:
            original_child_index = candidate_child_indices[candidate_result["corpus_id"]]
            raw_results.append({
                "corpus_id": original_child_index,
                "score": candidate_result["score"],
            })

    # 最高分用来判断“允许范围内有没有够相关的资料”。
    best_score = raw_results[0]["score"] if raw_results else None

    # 有阈值时，只留下每一段都达到要求的结果；没有阈值时保留全部 top_k 结果。
    passed_results = [
        result
        for result in raw_results
        if min_relevance_score is None or result["score"] >= min_relevance_score
    ]

    # matched_children 给来源展示和调试使用；retrieved_parents 才是要交给 AI 的完整资料。
    matched_children = []
    retrieved_parents = []

    # set() 可以把它理解成“不重复名单”。这里用它记下已经加入过的父章节 ID。
    seen_parent_ids = set()

    for result in passed_results:
        # corpus_id 已经被换回原始 children 列表的位置，因此能找回原来的文字。
        child = index_data["children"][result["corpus_id"]]
        matched_children.append({
            "score": result["score"],
            "child": child,
        })

        parent_id = child["parent_id"]
        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        retrieved_parents.append(index_data["parents_by_id"][parent_id])

    # 把找回的完整章节拼成一段文字，后面的 ChatOpenAI 会把它当作本轮资料。
    context = "\n\n".join(
        f"【{parent['title']}】\n{parent['content']}"
        for parent in retrieved_parents
    )

    return {
        "best_score": best_score,
        "raw_results": raw_results,
        "matched_children": matched_children,
        "parents": retrieved_parents,
        "context": context,
    }

def build_source_records(result: dict, index_data: dict) -> list[dict]:
    """把通过阈值的子片段整理成可展示、可核查的资料来源。"""
    document_title = index_data["document_title"].lstrip("# ").strip()

    return [
        {
            "document_title": document_title,
            "chapter_title": index_data["parents_by_id"][child["parent_id"]]["title"],
            "child_id": child["child_id"],
            "score": match["score"],
        }
        for match in result["matched_children"]
        for child in [match["child"]]
    ]
