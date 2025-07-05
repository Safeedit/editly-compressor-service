from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import os
import tempfile
import platform
import zipfile

app = Flask(__name__)
CORS(app)

@app.route("/compress", methods=["POST"])
def compress_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        output_path = os.path.join(tmpdir, "output.pdf")
        file.save(input_path)

        gs_cmd = "gswin64c" if platform.system() == "Windows" else "gs"
        command = [
            gs_cmd,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/screen",
            "-dDownsampleColorImages=true",
            "-dColorImageResolution=72",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]

        try:
            subprocess.run(command, check=True)
            return send_file(output_path, as_attachment=True, download_name="compressed.pdf")
        except Exception as e:
            return jsonify({"error": f"Ghostscript failed: {str(e)}"}), 500

@app.route("/compress-any", methods=["POST"])
def compress_any_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = file.filename
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)
        file.save(file_path)

        zip_path = os.path.join(tmpdir, f"{filename}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=filename)

        return send_file(zip_path, as_attachment=True, download_name=f"{filename}.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
