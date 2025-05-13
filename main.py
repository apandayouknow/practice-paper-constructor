import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import re

def is_suspicious_text(text):
    if not text or '�' in text:
        return True
    bad_chars = ['â', 'Ã', 'ˆ', '‰', '∕', '⎯']
    fraction_regex = r"\d+\s*/\s*\d+"

    if any(bad in text for bad in bad_chars):
        return True
    if not re.search(r'[a-zA-Z0-9]', text):  # nearly empty
        return True
    if '/' in text and not re.search(fraction_regex, text):  # likely broken fraction
        return True
    return False

def extract_text_from_page(pdf_path, page_index):
    with pdfplumber.open(pdf_path) as pdf_file:
        page = pdf_file.pages[page_index]
        pdf_text = page.extract_text() or ''

    ocr_image = convert_from_path(pdf_path, first_page=page_index + 1, last_page=page_index + 1, dpi=300)[0]
    ocr_text = pytesseract.image_to_string(ocr_image)

    # Prefer OCR if:
    # - PDF text is suspicious
    # - OCR seems more contentful (more digits or math)
    if is_suspicious_text(pdf_text):
        print(f"[OCR fallback triggered] Page {page_index + 1}")
        return ocr_text, 'ocr'

    # Optionally: Check for more fractions in OCR than pdf_text
    pdf_fraction_count = len(re.findall(r'\d+\s*/\s*\d+', pdf_text))
    ocr_fraction_count = len(re.findall(r'\d+\s*/\s*\d+', ocr_text))

    if ocr_fraction_count > pdf_fraction_count:
        print(f"[OCR preferred] Page {page_index + 1}")
        return ocr_text, 'ocr'

    return pdf_text, 'pdfplumber'


def extract_all_text_with_fallback(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    all_text = []
    for i in range(total_pages):
        text, method = extract_text_from_page(pdf_path, i)
        all_text.append((text.strip(), method))
    return all_text

def extract_questions_from_text_blocks(text_blocks):
    questions = []
    question_pattern = re.compile(r'^\s*(\d+[\.\)]|Q\d+)\s+', re.IGNORECASE)
    current_question = ''

    for text, source in text_blocks:
        lines = text.split('\n')
        for line in lines:
            if question_pattern.match(line):
                if current_question:
                    questions.append(current_question.strip())
                current_question = line
            else:
                current_question += ' ' + line
        if current_question:
            questions.append(current_question.strip())
            current_question = ''
    return questions

# === RUN EXAMPLE ===
pdf_file = 'files/2024 Y5Promo H2 Math Topical Revision qns.pdf'
text_blocks = extract_all_text_with_fallback(pdf_file)
questions = extract_questions_from_text_blocks(text_blocks)

for i, q in enumerate(questions, 1):
    print(f"Q{i}: {q}\n")
