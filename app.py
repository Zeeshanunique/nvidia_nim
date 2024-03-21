


from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA



from langchain_community.document_loaders import WebBaseLoader
loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")


docs = loader.load()
import os
from dotenv import load_dotenv
load_dotenv()


os.environ['NVIDIA_API_KEY'] = os.getenv('NVIDIA_API_KEY')


embeddings = NVIDIAEmbeddings()

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
documents = text_splitter.split_documents(docs)
vector = FAISS.from_documents(documents, embeddings)
retriever = vector.as_retriever()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


model = ChatNVIDIA(model="mistral_7b")

model

hyde_template = """Even if you do not know the full answer, generate a one-paragraph hypothetical answer to the below question:

{question}"""
hyde_prompt = ChatPromptTemplate.from_template(hyde_template)
hyde_query_transformer = hyde_prompt | model | StrOutputParser()

from langchain_core.runnables import chain

@chain
def hyde_retriever(question):
    hypothetical_document = hyde_query_transformer.invoke({"question": question})
    return retriever.invoke(hypothetical_document)

template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
answer_chain = prompt | model | StrOutputParser()

@chain
def final_chain(question):
    documents = hyde_retriever.invoke(question)
    for s in answer_chain.stream({"question": question, "context": documents}):
        yield s

for s in final_chain.stream("how can langsmith help with testing"):
    print(s, end="")