from langchain_community.document_loaders import PyPDFLoader

def extract_pdf_text(invoice_path:str) -> str:

    loader = PyPDFLoader(invoice_path)

    documents = loader.load()

    return "\n\n".join(
        document.page_content
        for document in documents
        if document.page_content.strip()
    )