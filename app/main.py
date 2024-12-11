from flask import Flask, render_template, request, send_file
import os
import subprocess
import nbformat
from nbconvert import PDFExporter
import tempfile
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add MiKTeX to PATH
miktex_path = r"C:\Users\KIIT\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
if miktex_path not in os.environ['PATH']:
    os.environ['PATH'] = miktex_path + os.pathsep + os.environ['PATH']

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "No file uploaded", 400
    
    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400
        
    if not file.filename.endswith(".ipynb"):
        return "Invalid file format. Please upload a Jupyter notebook (.ipynb)", 400

    temp_dir = None
    try:
        logger.info("Starting conversion process...")
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        notebook_path = os.path.join(temp_dir, file.filename)
        file.save(notebook_path)
        logger.debug(f"Saved notebook to: {notebook_path}")
        
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        logger.debug("Successfully read notebook")
        
        # Configure PDF exporter with verbose output
        pdf_exporter = PDFExporter()
        pdf_exporter.verbose = True
        logger.debug("Configured PDF exporter")
        
        try:
            logger.info("Starting PDF conversion...")
            pdf_data, resources = pdf_exporter.from_notebook_node(notebook)
            logger.info("PDF conversion completed")
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise
        
        pdf_path = os.path.join(temp_dir, file.filename.replace(".ipynb", ".pdf"))
        logger.debug(f"Writing PDF to: {pdf_path}")
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)
        
        # Create a copy of the PDF in a new location
        final_pdf_path = os.path.join(temp_dir, "output.pdf")
        shutil.copy2(pdf_path, final_pdf_path)
        
        logger.info("Sending PDF file...")
        return send_file(
            final_pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=file.filename.replace(".ipynb", ".pdf")
        )
            
    except Exception as e:
        error_msg = f"Conversion failed: {str(e)}"
        logger.error(error_msg)
        return error_msg, 500
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
