import os
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def process_document(self, file_path):
        text = self._extract_text(file_path)
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    def _extract_text(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self._extract_pdf_text(file_path)
        elif file_extension == '.txt':
            return self._extract_txt_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _extract_pdf_text(self, file_path):
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"Processing PDF with {total_pages} pages")
                
                if total_pages > 50:
                    raise Exception(f"PDF too large: {total_pages} pages (max 50)")
                
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                    print(f"Processed page {i+1}/{total_pages}")
                    
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")
        
        if not text.strip():
            raise Exception("PDF contains no readable text")
        
        return text
    
    def _extract_txt_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='cp949') as file:
                text = file.read()
        except Exception as e:
            raise Exception(f"Error reading TXT file: {str(e)}")
        return text