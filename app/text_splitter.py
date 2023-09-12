import logging
from typing import List, Any, Iterable, Callable, Optional


class CTSplitter():
    """Implementation of splitting text that looks at characters."""

    def __init__(self, chunk_size=1000,separator: str = "\n\n",**kwargs: Any):
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator
        # Modified to add the chunk size as a parameter
        self.chunk_size=chunk_size

    def _join_docs(self, docs: List[str], separator: str) -> Optional[str]:
        text = separator.join(docs)
        text = text.strip()
        if text == "":
            return None
        else:
            return text

    def split_text(self, text: str) -> List[str]:
        """Split incoming text and return chunks."""
        # First we naively split the large input into a bunch of smaller ones.
        if self._separator:
            splits = text.split(self._separator)
        else:
            splits = list(text)
        return self._merge_splits(splits, self._separator)

    def _merge_splits(self, splits: Iterable[str], separator: str) -> List[str]:
        # We now want to combine these smaller pieces into medium size
        # chunks to send to the LLM.
        #length_function: Callable[[str], int] = len,

        separator_len = len(separator)

        docs = []
        current_doc: List[str] = []
        total = 0
        for d in splits:
            _len = len(d)
            if (
                    total + _len + (separator_len if len(current_doc) > 0 else 0)
                    > self.chunk_size
            ):
                if total > self.chunk_size:
                    logging.warning(
                        f"Created a chunk of size {total}, "
                        f"which is longer than the specified"
                    )
                if len(current_doc) > 0:
                    doc = self._join_docs(current_doc, separator)
                    if doc is not None:
                        docs.append(doc)
                    # Keep on popping if:
                    # - we have a larger chunk than in the chunk overlap
                    # - or if we still have any chunks and the length is long
                    while total > 0 or (
                            total + _len + (separator_len if len(current_doc) > 0 else 0)
                            > self.chunk_size
                            and total > 0
                    ):
                        total -= len(current_doc[0]) + (
                            separator_len if len(current_doc) > 1 else 0
                        )
                        current_doc = current_doc[1:]
            current_doc.append(d)
            total += _len + (separator_len if len(current_doc) > 1 else 0)
        doc = self._join_docs(current_doc, separator)
        if doc is not None:
            docs.append(doc)
        return docs

if __name__=="__main__":
    cts = CTSplitter(chunk_size=600)
    with open("./documents/messi.txt") as f:
        content = f.read()

    docs = cts.split_text(content)
    i=0
    for doc in docs:
        i=i+1
        print("----------")
        print(doc)
