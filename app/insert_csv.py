from .helper_csv import CSVLoader
from .utils import generate_random_string

def get_csv_embeddings(tmp_path, source_id):
    loader = CSVLoader(file_path=tmp_path, source_column=source_id)
    data = loader.load()
    documents = [document.page_content for document in data]
    metadatas = [document.metadata for document in data]
    ids = [generate_random_string(28) for _ in data]
    return {"documents": documents, "metadatas": metadatas, "ids": ids}