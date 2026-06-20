"""
JD-derived constants: skill sets, title tiers, company lists.
All scoring decisions are grounded in the job description text.
"""

TIER_1_TITLES = {
    "Senior AI Engineer", "Lead AI Engineer", "Staff Machine Learning Engineer",
    "Senior Machine Learning Engineer", "Senior NLP Engineer", "Senior Applied Scientist",
    "Machine Learning Engineer", "Applied ML Engineer", "Search Engineer",
    "NLP Engineer", "Recommendation Systems Engineer", "AI Engineer", "Senior Data Scientist"
}
TIER_2_TITLES = {
    "ML Engineer", "AI Research Engineer", "Data Scientist",
    "Senior Software Engineer (ML)", "AI Specialist", "Junior ML Engineer",
    "Computer Vision Engineer"
}
TIER_3_TITLES = {
    "Data Engineer", "Senior Data Engineer", "Data Analyst", "Analytics Engineer",
    "Backend Engineer", "Senior Software Engineer", "Software Engineer"
}
ML_TITLES = TIER_1_TITLES | TIER_2_TITLES

# JD explicitly names these as disqualifying consulting firms
CONSULTING_FIRMS = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "tech mahindra", "hcl", "mphasis", "hexaware", "mindtree", "l&t infotech",
    "ltimindtree", "niit technologies", "mastech", "kpit", "cyient"
}
# Fictional companies used in the synthetic dataset
NON_PRODUCT = {
    "acme", "dunder mifflin", "initech", "globex", "hooli",
    "pied piper", "wayne enterprises", "stark industries"
}

CV_SPEECH_SKILLS = {
    "image classification", "object detection", "computer vision", "speech recognition",
    "tts", "text to speech", "speech synthesis", "robotics", "ros", "slam",
    "autonomous driving", "lidar"
}
NLP_IR_SKILLS = {
    "nlp", "natural language processing", "information retrieval", "text classification",
    "named entity recognition", "ner", "embeddings", "sentence transformers", "bert",
    "transformers", "semantic search", "vector search", "faiss", "elasticsearch",
    "opensearch", "bm25", "ranking", "retrieval", "rag", "question answering",
    "text mining", "llm", "large language models"
}
RESEARCH_ONLY_SIGNALS = {
    "latex", "matlab", "r programming", "stata", "spss",
    "academic research", "literature review", "arxiv"
}
PRODUCTION_SIGNALS = {
    "mlops", "mlflow", "model deployment", "fastapi", "flask", "docker",
    "kubernetes", "airflow", "kubeflow", "bentoml", "triton", "torchserve",
    "onnx", "model serving", "a/b testing", "feature store", "data pipeline", "ci/cd"
}

# JD section: "Things you absolutely need"
JD_MUST_HAVE_SKILLS = {
    "embeddings", "sentence transformers", "faiss", "vector search", "semantic search",
    "information retrieval", "dense retrieval", "pinecone", "weaviate", "qdrant",
    "milvus", "opensearch", "elasticsearch", "chroma", "bm25", "hybrid search",
    "sparse retrieval", "ndcg", "mrr", "map", "ranking evaluation", "a/b testing",
    "offline evaluation", "online evaluation", "python", "ranking", "learning to rank",
    "reranking", "re-ranking", "recommendation systems", "search ranking",
}
# JD section: "Things we would like you to have"
JD_NICE_TO_HAVE_SKILLS = {
    "lora", "qlora", "peft", "fine-tuning llms", "fine tuning", "xgboost", "lightgbm",
    "nlp", "natural language processing", "transformers", "hugging face transformers",
    "bert", "rag", "mlflow", "mlops", "model deployment", "kubeflow", "llm",
    "large language models", "gpt", "claude", "pytorch", "tensorflow",
    "scikit-learn", "machine learning",
}
# JD section: "Things we explicitly do NOT want"
JD_NEGATIVE_SKILLS = {"langchain"}

ML_EVIDENCE_KEYWORDS = [
    "model", "train", "embedding", "retrieval", "ranking", "vector", "nlp",
    "machine learning", "neural", "inference", "deploy", "recommendation", "search",
    "classifier", "fine-tun", "llm", "transformer", "bert", "pipeline", "feature", "dataset"
]
PROF_WEIGHTS = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.8, "expert": 1.0}
