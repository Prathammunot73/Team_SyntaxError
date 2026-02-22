import os
from datetime import datetime

def highlight_pdf(original_pdf_path, question_number):
    """
    Highlight specific question in PDF answer sheet
    
    Args:
        original_pdf_path (str): Path to original answer sheet
        question_number (str): Question to highlight (e.g., "Q2")
        
    Returns:
        str: Path to highlighted PDF
    """
    try:
        # Check if original file exists
        if not os.path.exists(original_pdf_path):
            print(f"Warning: Original PDF not found at {original_pdf_path}")
            return None
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"highlighted_{question_number}_{timestamp}.pdf"
        output_path = os.path.join('static', 'uploads', 'highlighted', filename)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try to use PyPDF2 for actual highlighting
        try:
            from PyPDF2 import PdfReader, PdfWriter
            from PyPDF2.generic import AnnotationBuilder
            
            reader = PdfReader(original_pdf_path)
            writer = PdfWriter()
            
            # Copy all pages and add highlight annotation to first page
            for page_num, page in enumerate(reader.pages):
                if page_num == 0:  # Add highlight to first page as placeholder
                    # Create a highlight annotation (simplified version)
                    # In production, you'd use OCR to find exact question location
                    annotation = AnnotationBuilder.highlight(
                        rect=(50, 700, 550, 750),  # Placeholder coordinates
                        color=(1, 1, 0)  # Yellow highlight
                    )
                    page.add_annotation(annotation)
                
                writer.add_page(page)
            
            # Write output
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            print(f"✓ PDF highlighted successfully: {output_path}")
            return output_path
            
        except ImportError:
            # Fallback: Copy original file with new name
            print("PyPDF2 not installed. Creating copy instead of highlighting.")
            import shutil
            shutil.copy2(original_pdf_path, output_path)
            return output_path
            
    except Exception as e:
        print(f"Error highlighting PDF: {str(e)}")
        return None

def extract_question_location(pdf_path, question_number):
    """
    Extract coordinates of specific question in PDF
    This is a placeholder for OCR-based question detection
    
    Args:
        pdf_path (str): Path to PDF file
        question_number (str): Question to locate
        
    Returns:
        tuple: (page_number, x1, y1, x2, y2) coordinates
    """
    # Placeholder logic
    # In production, use OCR (pytesseract + pdf2image) to:
    # 1. Convert PDF pages to images
    # 2. Run OCR to extract text with coordinates
    # 3. Search for question number pattern
    # 4. Return bounding box coordinates
    
    # For now, return default coordinates
    return (0, 50, 700, 550, 750)

def create_sample_pdf():
    """Create a sample PDF for testing purposes"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        output_path = 'static/uploads/sample_answer_sheet.pdf'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        c = canvas.Canvas(output_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        
        # Title
        c.drawString(100, 750, "Sample Answer Sheet - Mathematics Mid-Term 2024")
        c.drawString(100, 730, "Student: John Doe")
        c.line(100, 720, 500, 720)
        
        # Questions
        y_position = 680
        questions = [
            ("Q1", "Solve: 2x + 5 = 15", "Answer: x = 5", "Marks: 8/10"),
            ("Q2", "Find derivative of f(x) = x^2 + 3x", "Answer: f'(x) = 2x + 3", "Marks: 5/10"),
            ("Q3", "Calculate integral of sin(x)", "Answer: -cos(x) + C", "Marks: 9/10"),
        ]
        
        for q_num, question, answer, marks in questions:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(100, y_position, f"{q_num}. {question}")
            c.setFont("Helvetica", 10)
            c.drawString(120, y_position - 20, answer)
            c.drawString(120, y_position - 40, marks)
            y_position -= 80
        
        c.save()
        print(f"✓ Sample PDF created: {output_path}")
        
    except ImportError:
        print("reportlab not installed. Sample PDF not created.")
    except Exception as e:
        print(f"Error creating sample PDF: {str(e)}")

# Create sample PDF on module import
if __name__ == "__main__":
    create_sample_pdf()
