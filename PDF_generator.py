import random
import tempfile
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

def generate_random_image():
    width, height = random.randint(50, 200), random.randint(50, 200)
    image = PILImage.new('RGB', (width, height), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def generate_javascript():
    actions = [
        "app.alert('Hello from JavaScript!');",
        "app.beep(0);",
        "this.resetForm();",
        "this.print({bUI: true, bSilent: false, bShrinkToFit: true});",
        "this.closeDoc(true);",
        "var field = this.getField('MyField'); if (field) field.value = 'New Value';",
        "var field = this.getField('MyCheckBox'); if (field) field.checkThisBox(0, true);",
        "this.insertPages({nPage: 0, cPath: '/C/example.pdf'});",
        "this.deletePage(0);",
        "this.info.Title = 'New Title';",
        "this.info.Author = 'Fuzzer';",
        "this.gotoNamedDest('SomeDestination');",
        "this.pageNum = 0;",
        "app.launchURL('https://google.com');",
        "this.submitForm('https://example.com/submit');"
    ]
    return random.choice(actions)

def generate_random_content():
    content_type = random.choice(['text', 'table', 'shape', 'image'])
    if content_type == 'text':
        return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for _ in range(random.randint(10, 100)))
    elif content_type == 'table':
        rows = random.randint(1, 5)
        cols = random.randint(1, 5)
        return [[random.randint(0, 100) for _ in range(cols)] for _ in range(rows)]
    elif content_type == 'shape':
        return random.choice(['circle', 'rectangle', 'line'])
    else:  # image
        return generate_random_image()

def create_pdf(filename):
    # Create a temporary file for the main PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as main_tmp_file:
        main_tmp_filename = main_tmp_file.name
        doc = SimpleDocTemplate(main_tmp_filename, pagesize=letter)
        elements = []
        
        for _ in range(random.randint(3, 30)):  # 3 to 30 elements per PDF
            content = generate_random_content()
            if isinstance(content, str):
                # It's text
                style = getSampleStyleSheet()['Normal']
                elements.append(Paragraph(content, style))
            elif isinstance(content, list):  # Table
                t = Table(content)
                t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.white),
                                       ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                       ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                                       ('FONTSIZE', (0, 0), (-1, -1), 8),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                                       ('TOPPADDING', (0, 0), (-1, -1), 0),
                                       ('GRID', (0, 0), (-1, -1), 0.25, colors.black)]))
                elements.append(t)
            elif isinstance(content, bytes):  # Image
                img_buffer = BytesIO(content)
                img = Image(img_buffer, width=2*inch, height=2*inch)
                elements.append(img)
        
        doc.build(elements)
    
    # Create a temporary file for the JavaScript PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as js_tmp_file:
        js_tmp_filename = js_tmp_file.name
        c = canvas.Canvas(js_tmp_filename, pagesize=letter)
        c.setFont("Helvetica", 10)
        c.drawString(100, 700, "This PDF contains JavaScript")
        c.save()
    
    try:
        merger = PdfMerger()
        merger.append(main_tmp_filename)
        merger.append(js_tmp_filename)
        
        merger.write(filename)
        merger.close()
        
        # Add JavaScript action
        reader = PdfReader(filename)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        writer.add_js(generate_javascript())
        
        with open(filename, 'wb') as f:
            writer.write(f)
        
    except Exception as e:
        print(f"An error occurred while creating the PDF: {str(e)}")
    finally:
        # Clean up the temporary files
        os.unlink(main_tmp_filename)
        os.unlink(js_tmp_filename)

def generate_pdfs(num_pdfs):
    for i in range(num_pdfs):
        filename = f"Testcases\\testcase_{i+1}.pdf"
        create_pdf(filename)
        print(f"Generated {filename}")

if __name__ == "__main__":
    num_pdfs = 50  # Change this to generate more or fewer PDFs
    generate_pdfs(num_pdfs)