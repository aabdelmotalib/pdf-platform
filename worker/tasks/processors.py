"""
PDF and Document Processors
Handles all file conversion operations
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from pypdf import PdfWriter, PdfReader
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
LIBREOFFICE_PATH = "/usr/bin/libreoffice"
IMAGEMAGICK_PATH = "/usr/bin/convert"
TEMP_DIR = tempfile.gettempdir()


class ConversionError(Exception):
    """Raised when conversion fails"""
    pass


def run_libreoffice(
    input_path: str,
    output_format: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Run LibreOffice headless conversion
    
    Args:
        input_path: Path to input file
        output_format: Output format (docx, calc, pdf, etc)
        output_dir: Directory for output file
    
    Returns:
        Path to output file
    
    Raises:
        ConversionError: If conversion fails
    """
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        cmd = [
            LIBREOFFICE_PATH,
            "--headless",
            "--convert-to",
            output_format,
            "--outdir",
            output_dir,
            input_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            raise ConversionError(
                f"LibreOffice conversion failed: {result.stderr or result.stdout}"
            )
        
        # Find output file
        input_filename = Path(input_path).stem
        # LibreOffice adds the extension automatically
        output_filename = f"{input_filename}.{output_format.split(':')[0]}"
        output_path = os.path.join(output_dir, output_filename)
        
        if not os.path.exists(output_path):
            raise ConversionError(f"Output file not created: {output_path}")
        
        return output_path
    
    except subprocess.TimeoutExpired:
        raise ConversionError("LibreOffice conversion timed out (120s)")
    except Exception as e:
        raise ConversionError(f"LibreOffice error: {str(e)}")


# PROCESSOR FUNCTIONS

def pdf_to_word(input_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert PDF to DOCX using PyMuPDF (text extraction) + python-docx.

    LibreOffice cannot export PDF→DOCX directly, so we extract text
    block-by-block and write it into a Word document.

    Args:
        input_path: Path to input PDF
        output_dir: Output directory

    Returns:
        Path to output DOCX file
    """
    from docx import Document as DocxDocument

    if not output_dir:
        output_dir = tempfile.gettempdir()
    os.makedirs(output_dir, exist_ok=True)

    try:
        logger.info(f"Converting PDF to WORD: {input_path}")
        doc = fitz.open(input_path)
        word_doc = DocxDocument()

        for page_num in range(len(doc)):
            page = doc[page_num]

            if page_num > 0:
                word_doc.add_page_break()

            # Extract text blocks preserving structure
            blocks = page.get_text("blocks")
            for block in blocks:
                # block = (x0, y0, x1, y1, text, block_no, block_type)
                if block[6] == 0:  # text block
                    text = block[4].strip()
                    if text:
                        word_doc.add_paragraph(text)

        doc.close()

        output_filename = f"{Path(input_path).stem}.docx"
        output_path = os.path.join(output_dir, output_filename)
        word_doc.save(output_path)

        logger.info(f"PDF to DOCX conversion complete: {output_path}")
        return output_path

    except Exception as e:
        raise ConversionError(f"PDF to Word conversion failed: {str(e)}")


def pdf_to_excel(input_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert PDF to XLSX using LibreOffice Calc
    
    Args:
        input_path: Path to input PDF
        output_dir: Output directory
    
    Returns:
        Path to output XLSX file
    """
    logger.info(f"Converting PDF to EXCEL: {input_path}")
    return run_libreoffice(input_path, "xlsx", output_dir)


def pdf_to_image(
    input_path: str,
    page_num: int = 1,
    dpi: int = 200,
    output_dir: Optional[str] = None
) -> str:
    """
    Convert PDF page to JPEG image using pdf2image
    
    Args:
        input_path: Path to input PDF
        page_num: Page number to convert (1-indexed)
        dpi: Output DPI
        output_dir: Output directory
    
    Returns:
        Path to output JPEG file
    
    Raises:
        ConversionError: If conversion fails
    """
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Converting PDF page {page_num} to IMAGE: {input_path}")
        
        # Convert single page
        images = convert_from_path(
            input_path,
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
            fmt="jpeg"
        )
        
        if not images:
            raise ConversionError(f"No pages found at page {page_num}")
        
        # Save image
        filename = f"{Path(input_path).stem}_page_{page_num}.jpg"
        output_path = os.path.join(output_dir, filename)
        images[0].save(output_path, "JPEG", quality=95)
        
        return output_path
    
    except Exception as e:
        raise ConversionError(f"PDF to image conversion failed: {str(e)}")


def word_to_pdf(input_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert DOCX/DOC to PDF using LibreOffice
    
    Args:
        input_path: Path to input Word document
        output_dir: Output directory
    
    Returns:
        Path to output PDF file
    """
    logger.info(f"Converting WORD to PDF: {input_path}")
    return run_libreoffice(input_path, "pdf", output_dir)


def pdf_merge(input_paths: List[str], output_dir: Optional[str] = None) -> str:
    """
    Merge multiple PDFs into one using pypdf
    
    Args:
        input_paths: List of paths to input PDFs
        output_dir: Output directory
    
    Returns:
        Path to merged PDF
    
    Raises:
        ConversionError: If merge fails
    """
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Merging {len(input_paths)} PDFs")
        
        writer = PdfWriter()
        
        for pdf_path in input_paths:
            if not os.path.exists(pdf_path):
                raise ConversionError(f"Input file not found: {pdf_path}")
            
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        
        # Save merged PDF
        output_path = os.path.join(output_dir, "merged.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        
        logger.info(f"Merged PDF created: {output_path}")
        return output_path
    
    except Exception as e:
        raise ConversionError(f"PDF merge failed: {str(e)}")


def pdf_split(
    input_path: str,
    pages: List[int],
    output_dir: Optional[str] = None
) -> str:
    """
    Extract specific pages from PDF using pypdf
    
    Args:
        input_path: Path to input PDF
        pages: List of page numbers to extract (1-indexed)
        output_dir: Output directory
    
    Returns:
        Path to output PDF
    
    Raises:
        ConversionError: If split fails
    """
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Splitting PDF pages {pages}: {input_path}")
        
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page_num in pages:
            # Convert 1-indexed to 0-indexed
            idx = page_num - 1
            if idx < 0 or idx >= len(reader.pages):
                raise ConversionError(f"Page {page_num} out of range")
            
            writer.add_page(reader.pages[idx])
        
        # Save split PDF
        output_path = os.path.join(output_dir, f"split_{datetime.now().timestamp()}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        
        logger.info(f"Split PDF created: {output_path}")
        return output_path
    
    except Exception as e:
        raise ConversionError(f"PDF split failed: {str(e)}")


def pdf_annotate(
    input_path: str,
    annotations: List[dict],
    output_dir: Optional[str] = None
) -> str:
    """
    Add annotations (text, highlights) to PDF using PyMuPDF
    
    Args:
        input_path: Path to input PDF
        annotations: List of annotations:
            [
                {"type": "text", "page": 1, "x": 100, "y": 100, "text": "Note"},
                {"type": "highlight", "page": 1, "rect": [100, 100, 200, 150]},
                {"type": "circle", "page": 1, "rect": [100, 100, 200, 150]}
            ]
        output_dir: Output directory
    
    Returns:
        Path to annotated PDF
    
    Raises:
        ConversionError: If annotation fails
    """
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Adding {len(annotations)} annotations to PDF: {input_path}")
        
        doc = fitz.open(input_path)
        
        for ann in annotations:
            page_num = ann.get("page", 1) - 1  # Convert to 0-indexed
            
            if page_num < 0 or page_num >= len(doc):
                logger.warning(f"Page {page_num + 1} out of range, skipping")
                continue
            
            page = doc[page_num]
            ann_type = ann.get("type", "text")
            
            if ann_type == "text":
                text = ann.get("text", "")
                x = ann.get("x", 50)
                y = ann.get("y", 50)
                page.insert_textbox(fitz.Rect(x, y, x + 200, y + 50), text)
            
            elif ann_type == "highlight":
                rect = fitz.Rect(ann.get("rect", [50, 50, 150, 100]))
                page.draw_rect(rect, color=(1, 1, 0), fill=(1, 1, 0), fill_opacity=0.3)
            
            elif ann_type == "circle":
                rect = fitz.Rect(ann.get("rect", [50, 50, 150, 150]))
                page.draw_circle(rect.get_center(), rect.get_size()[0] / 2, color=(1, 0, 0))
        
        # Save annotated PDF
        output_path = os.path.join(output_dir, f"annotated_{datetime.now().timestamp()}.pdf")
        doc.save(output_path)
        doc.close()
        
        logger.info(f"Annotated PDF created: {output_path}")
        return output_path
    
    except Exception as e:
        raise ConversionError(f"PDF annotation failed: {str(e)}")


def pdf_watermark(
    input_path: str,
    text: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Add diagonal text watermark to all PDF pages using PyMuPDF
    
    Args:
        input_path: Path to input PDF
        text: Watermark text
        output_dir: Output directory
    
    Returns:
        Path to watermarked PDF
    
    Raises:
        ConversionError: If watermarking fails
    """
    if not output_dir:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Adding watermark '{text}' to PDF: {input_path}")
        
        doc = fitz.open(input_path)
        
        # Add watermark to all pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Draw diagonal text across page
            # Get page size
            rect = page.rect
            center_x = rect.width / 2
            center_y = rect.height / 2
            
            # Insert watermark text at 45-degree angle
            page.insert_textbox(
                fitz.Rect(0, 0, rect.width, rect.height),
                text,
                fontsize=48,
                color=(0.8, 0.8, 0.8),  # Light gray
                align=fitz.TEXT_ALIGN_CENTER,
                rotate=45  # 45-degree rotation
            )
        
        # Save watermarked PDF
        output_path = os.path.join(output_dir, f"watermarked_{datetime.now().timestamp()}.pdf")
        doc.save(output_path)
        doc.close()
        
        logger.info(f"Watermarked PDF created: {output_path}")
        return output_path
    
    except Exception as e:
        raise ConversionError(f"PDF watermarking failed: {str(e)}")


# Processor registry
PROCESSORS = {
    "pdf_to_word": pdf_to_word,
    "pdf_to_excel": pdf_to_excel,
    "pdf_to_image": pdf_to_image,
    "word_to_pdf": word_to_pdf,
    "pdf_merge": pdf_merge,
    "pdf_split": pdf_split,
    "pdf_annotate": pdf_annotate,
    "pdf_watermark": pdf_watermark,
}


def detect_conversion_type(
    input_mime: str,
    converison_type: Optional[str] = None
) -> str:
    """
    Detect conversion type from MIME type
    
    Args:
        input_mime: Input file MIME type
        converison_type: Explicit conversion type (overrides detection)
    
    Returns:
        Conversion type string
    
    Raises:
        ConversionError: If conversion type cannot be determined
    """
    if converison_type:
        if converison_type not in PROCESSORS:
            raise ConversionError(f"Unknown conversion type: {converison_type}")
        return converison_type
    
    # Map MIME type to default conversion
    mime_to_conversion = {
        "application/pdf": "pdf_to_word",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word_to_pdf",
        "application/msword": "word_to_pdf",
    }
    
    conversion = mime_to_conversion.get(input_mime, "pdf_to_word")
    return conversion
