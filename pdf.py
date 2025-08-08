from PyPDF2 import PdfReader

def pdf_to_text_pypdf2(pdf_path):
    reader = PdfReader(pdf_path)
    with open("output.txt", "w", encoding="utf-8") as f:
        for page in reader.pages:
            text = page.extract_text()
            if text:
                f.write(text + '\n')