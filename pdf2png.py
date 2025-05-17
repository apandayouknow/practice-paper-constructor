from pdf2image import convert_from_path

pages = convert_from_path('files/2024 Y5Promo H2 Math Topical Revision qns.pdf', dpi=300)
for i, page in enumerate(pages):
    page.save(f'input/page_{i+1}.png', 'PNG')
