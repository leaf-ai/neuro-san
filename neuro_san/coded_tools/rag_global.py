from typing import Any
from typing import Dict
from typing import List
from typing import Union

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from neuro_san.interfaces.coded_tool import CodedTool


class RAG(CodedTool):
    """
    CodedTool implementation which provides a way to utilize different websites' search feature
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: An argument dictionary whose keys are the parameters
                to the coded tool and whose values are the values passed for them
                by the calling agent.  This dictionary is to be treated as read-only.

                The argument dictionary expects the following keys:
                    "urls" the list of URLs to do embedding and put in vectorstore.
                    "query" the question for RAG.

        :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
                but whose values are meant to be kept out of the chat stream.

                This dictionary is largely to be treated as read-only.
                It is possible to add key/value pairs to this dict that do not
                yet exist as a bulletin board, as long as the responsibility
                for which coded_tool publishes new entries is well understood
                by the agent chain implementation and the coded_tool implementation
                adding the data is not invoke()-ed more than once.

                Keys expected for this implementation are:
                    None

        :return:
            In case of successful execution:
                The output string from RAG.
            otherwise:
                a text string an error message in the format:
                "Error: <error message>"
        """
        urls: List[str] = args.get("urls")
        query: str = args.get("query", "")

        if not urls:
            return "Error: No URLs provided."

        if query == "":
            return "Error: No query provided."

        docs: List[List[Document]] = [WebBaseLoader(url).load() for url in urls]
        docs_list: List[Document] = [item for sublist in docs for item in sublist]

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=100, chunk_overlap=50
        )
        doc_splits: List[Document] = text_splitter.split_documents(docs_list)

        # Add to vectorDB
        vectorstore = InMemoryVectorStore.from_documents(
            documents=doc_splits,
            collection_name="rag-in-memory",
            embedding=OpenAIEmbeddings(),
        )
        retriever: VectorStoreRetriever = vectorstore.as_retriever()
        page_contents: List[Document] = retriever.invoke(query)

        rag_str: str = ""
        for content in page_contents:
            rag_str += content.page_content + "\n\n"

        return rag_str

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        raise NotImplementedError
