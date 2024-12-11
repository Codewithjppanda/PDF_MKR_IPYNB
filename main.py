from flask import Flask, render_template, request, send_file
import os
import nbformat
from nbconvert import HTMLExporter
import tempfile
import logging
import weasyprint

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        notebook_path = os.path.join(temp_dir, file.filename)
        file.save(notebook_path)
        
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        
        # Convert to HTML first
        html_exporter = HTMLExporter()
        html_data, _ = html_exporter.from_notebook_node(notebook)
        
        # Convert HTML to PDF using WeasyPrint
        pdf_path = os.path.join(temp_dir, file.filename.replace(".ipynb", ".pdf"))
        weasyprint.HTML(string=html_data).write_pdf(pdf_path)
        
        logger.info("Sending PDF file...")
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=file.filename.replace(".ipynb", ".pdf")
        )
            
    except Exception as e:
        error_msg = f"Conversion failed: {str(e)}"
        logger.error(error_msg)
        return error_msg, 500
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
