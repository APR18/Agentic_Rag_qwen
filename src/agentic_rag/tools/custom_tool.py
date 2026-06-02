from crewai.tools import BaseTool
from typing import Type,Any
from pydantic import BaseModel, Field
import os 
from pathlib import Path 
from qdrant_client import QdrantClient
from markitdown import MarkItDown
from chonkie import SemanticChunker
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
import uuid
class SearchToolInput(BaseModel):
    """Input schema for SearchTool."""
    query: str = Field(..., description="Question from user to search in the document.")

class SearchTool(BaseTool):
    name: str = "SearchTool"
    description: str = (
        "Serching the document using the given query"
    )
    args_schema: Type[BaseModel] = SearchToolInput
    file_path :Any = None
    qdrant_client : Any = None

    def __init__(self,file_path:str,**kwargs):
        super().__init__(**kwargs)  
        self.file_path = file_path
        self.qdrant_client = QdrantClient(":memory:")
        self._ingest_docs()

    def _extract_text(self)->str:
        md = MarkItDown()
        result = md.convert(self.file_path)
        # print(result.text_content)
        return result.text_content
    def _get_chunks(self,text)-> list:
        chunker = SemanticChunker(
            model = "minishlab/potion-base-8M",
            threshold=0.5,
            chunk_size=512,
            min_sentences_per_chunk=1)
        return chunker.chunk(text)
    
    def _ingest_docs(self):
        text = self._extract_text()
        chunks = self._get_chunks(text)
        chunk_texts = [chunk.text for chunk in chunks]
        metadata = [{"source": os.path.basename(self.file_path)} for _ in range(len(chunks))]

        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if "demo_collection" in collection_names:
            existing_count = self.qdrant_client.count(collection_name="demo_collection").count
            if existing_count > 0:
                print(f"Collection already has {existing_count} documents. Skipping ingestion.")
                return
        
        ids = list(range(len(chunks)))

        self.qdrant_client.add(
            collection_name="demo_collection",
            documents=chunk_texts,
            metadata=metadata,
            ids=ids
        )

        # embeddings = list(self.embedding_model.embed(chunk_texts))
        # all_points = []

        # for chunk_text,embedding in zip(chunk_texts,embeddings):
        #     point = PointStruct(id= str(uuid.uuid4()),
        #                 vector = embedding.tolist(),
        #                 payload = {"text":chunk_text,
        #                            "source" : Path(self.file_path).name})
        #     all_points.append(point)
        # if all_points:
        #     self.qdrant_client.upsert(
        #         collection_name="Research Collection",
        #         points=all_points
        #     )
        #     print(f"\nIngested {len(all_points)} chunks from {Path(__file__).parent.parent.parent.parent / "knowledge" / "dspy.pdf"}")



    def _run(self, query: str) -> str:
        # query_embedding = list(self.embedding_model.embed([query]))[0].tolist()
        relevant_chunks = self.qdrant_client.query(
            collection_name="demo_collection",
            query_text=query
        )
        if not relevant_chunks:
            return "No relevant information found."
        docs = [chunk.document for chunk in relevant_chunks]
        separator = "\n___\n"
        return separator.join(docs)


if __name__ == "__main__":
    pdf_path = file_path = Path.joinpath(Path.cwd(),"knowledge","dspy.pdf")
    st = SearchTool(pdf_path)
    print(st._run("What is dspy?"))