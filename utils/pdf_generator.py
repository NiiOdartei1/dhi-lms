# utils/pdf_generator.py
from io import BytesIO
from typing import Optional, Tuple

def generate_pdf_from_html(
    html: str,
    base_url: Optional[str] = None,
    output_path: Optional[str] = None
) -> BytesIO:
    """
    Convert an HTML string to a PDF and return a BytesIO.
    If output_path is provided, the PDF is also written to that file.
    Tries WeasyPrint first, then pdfkit if available.
    """
    weasy_err = None
    pdfkit_err = None

    # Try WeasyPrint
    try:
        from weasyprint import HTML
        # If caller wants a file written:
        if output_path:
            HTML(string=html, base_url=base_url).write_pdf(output_path)
            with open(output_path, "rb") as f:
                bio = BytesIO(f.read())
            bio.seek(0)
            return bio
        # Otherwise get bytes directly
        pdf_bytes = HTML(string=html, base_url=base_url).write_pdf()
        bio = BytesIO(pdf_bytes)
        bio.seek(0)
        return bio
    except Exception as e:
        weasy_err = e

    # Try pdfkit (wkhtmltopdf)
    try:
        import pdfkit
        options = {'enable-local-file-access': None, 'quiet': ''}
        # pdfkit.from_string returns bytes if output_path is False
        if output_path:
            pdfkit.from_string(html, output_path, options=options)
            with open(output_path, "rb") as f:
                bio = BytesIO(f.read())
            bio.seek(0)
            return bio
        else:
            pdf_bytes = pdfkit.from_string(html, False, options=options)
            bio = BytesIO(pdf_bytes)
            bio.seek(0)
            return bio
    except Exception as e:
        pdfkit_err = e

    # If both backends failed, raise a helpful error
    raise RuntimeError(
        "No HTML→PDF backend available.\n"
        f"WeasyPrint error: {weasy_err!r}\n"
        f"pdfkit error: {pdfkit_err!r}"
    )
