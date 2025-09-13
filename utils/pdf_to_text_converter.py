import fitz


def pdf_to_text(pdf_content_bytes: bytes) -> str:
    try:
        pdf_document = fitz.open(stream=pdf_content_bytes, filetype="pdf")

        full_text = []
        for page in pdf_document:
            full_text.append(page.get_text())

        return "".join(full_text)

    except Exception as e:
        print(f"PDF conversion error: {e}")
        return None