import csv
from typing import Any, Dict, List, Optional, Iterator
from pydantic import BaseModel, Field 
from .text_splitter import CTSplitter
from abc import ABC, abstractmethod

class Document(BaseModel):
    """Interface for interacting with a document."""

    page_content: str
    lookup_str: str = ""
    lookup_index:int = 0
    metadata: dict = Field(default_factory=dict)

    @property
    def paragraphs(self) -> List[str]:
        """Paragraphs of the page."""
        return self.page_content.split("\n\n")

    @property
    def summary(self) -> str:
        """Summary of the page (the first paragraph)."""
        return self.paragraphs[0]

    def lookup(self, string: str) -> str:
        """Lookup a term in the page, imitating cmd-F functionality."""
        if string.lower() != self.lookup_str:
            self.lookup_str = string.lower()
            self.lookup_index = 0
        else:
            self.lookup_index += 1
        lookups = [p for p in self.paragraphs if self.lookup_str in p.lower()]
        if len(lookups) == 0:
            return "No Results"
        elif self.lookup_index >= len(lookups):
            return "No More Results"
        else:
            result_prefix = f"(Result {self.lookup_index + 1}/{len(lookups)})"
            return f"{result_prefix} {lookups[self.lookup_index]}"


class BaseLoader(ABC):
    """Interface for Document Loader.

    Implementations should implement the lazy-loading method using generators
    to avoid loading all Documents into memory at once.

    The `load` method will remain as is for backwards compatibility, but its
    implementation should be just `list(self.lazy_load())`.
    """

    # Sub-classes should implement this method
    # as return list(self.lazy_load()).
    # This method returns a List which is materialized in memory.
    @abstractmethod
    def load(self) -> List[Document]:
        """Load data into Document objects."""

    def load_and_split(
        self, text_splitter: Optional[CTSplitter] = None
    ) -> List[Document]:
        """Load Documents and split into chunks. Chunks are returned as Documents.

        Args:
            text_splitter: TextSplitter instance to use for splitting documents.
              Defaults to RecursiveCharacterTextSplitter.

        Returns:
            List of Documents.
        """
        if text_splitter is None:
            _text_splitter: TextSplitter = RecursiveCharacterTextSplitter()
        else:
            _text_splitter = text_splitter
        docs = self.load()
        return _text_splitter.split_documents(docs)

    # Attention: This method will be upgraded into an abstractmethod once it's
    #            implemented in all the existing subclasses.
    def lazy_load(
        self,
    ) -> Iterator[Document]:
        """A lazy loader for Documents."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement lazy_load()"
        )



class CSVLoader(BaseLoader):
    """Load a CSV file into a list of Documents with dynamic columns."""

    def __init__(
        self,
        file_path: str,
        source_column: Optional[str] = None,
        csv_args: Optional[Dict] = None,
        encoding: Optional[str] = None,
    ):
        """
        Args:
            file_path: The path to the CSV file.
            source_column: The name of the column in the CSV file to use as the source.
              Optional. Defaults to None.
            csv_args: A dictionary of arguments to pass to the csv.DictReader.
              Optional. Defaults to None.
            encoding: The encoding of the CSV file. Optional. Defaults to None.
        """
        self.file_path = file_path
        self.source_column = source_column
        self.encoding = encoding
        self.csv_args = csv_args or {}

    def load(self) -> List[Document]:
        """Load data into document objects."""

        docs = []
        with open(self.file_path, newline="", encoding=self.encoding) as csvfile:
            csv_reader = csv.DictReader(csvfile, **self.csv_args)
            for i, row in enumerate(csv_reader):
                # Construct the content for the document dynamically based on CSV columns
                content_parts = []
                for k, v in row.items():
                    if k is not None and v is not None:
                        if isinstance(v, list):
                            # Handle the case where the value is a list
                            content_parts.append((v).strip())
                        else:
                            content_parts.append(str(v).strip())
                content = " | ".join(content_parts)


                
                # try:
                #     source = (
                #         row[self.source_column]
                #         if self.source_column is not None
                #         else self.file_path
                #     )
                # except KeyError:
                #     raise ValueError(
                #         f"Source column '{self.source_column}' not found in CSV file."
                #     )
                metadata = {"source": self.source_column, "row": i}
                doc = Document(page_content=content, metadata=metadata)
                docs.append(doc)

        return docs

