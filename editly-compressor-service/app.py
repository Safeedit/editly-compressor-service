from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import os
import tempfile
import platform
import zipfile
from PIL import Image

app = Flask(__name__)
CORS(app)

def compress_image(in_path, out_path, quality=40):
    try:
        with Image.open(in_path) as img:
            img.save(out_path, optimize=True, quality=quality)
    except Exception as e:
        print(f"Image compression failed for {in_path}: {e}")
        return False
    return True

@app.route("/compress", methods=["POST"])
def compress_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    quality = request.form.get("quality", "/screen")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        output_path = os.path.join(tmpdir, "output.pdf")
        file.save(input_path)

        original_size = os.path.getsize(input_path)

        gs_cmd = "gswin64c" if platform.system() == "Windows" else "gs"
        command = [
            gs_cmd,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={quality}",
            "-dDownsampleColorImages=true",
            "-dColorImageDownsampleType=/Average",
            "-dColorImageResolution=50",
            "-dGrayImageDownsampleType=/Average",
            "-dGrayImageResolution=50",
            "-dMonoImageDownsampleType=/Subsample",
            "-dMonoImageResolution=50",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]

        try:
            subprocess.run(command, check=True)
            compressed_size = os.path.getsize(output_path)

            if compressed_size >= original_size:
                return jsonify({
                    "message": "📦 File is already optimized. No further compression possible.",
                    "original_kb": round(original_size / 1024, 2),
                    "compressed_kb": round(compressed_size / 1024, 2)
                })

            return send_file(output_path, as_attachment=True, download_name="compressed.pdf")
        except Exception as e:
            return jsonify({"error": f"Ghostscript failed: {str(e)}"}), 500

@app.route("/compress-any", methods=["POST"])
def compress_any_files():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "compressed_files.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f in files:
                filename = f.filename
                original_path = os.path.join(tmpdir, filename)
                f.save(original_path)

                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    compressed_path = os.path.join(tmpdir, f"compressed_{filename}")
                    success = compress_image(original_path, compressed_path, quality=40)

                    if success:
                        zipf.write(compressed_path, arcname=f"compressed_{filename}")
                    else:
                        zipf.write(original_path, arcname=filename)
                else:
                    zipf.write(original_path, arcname=filename)

        return send_file(zip_path, as_attachment=True, download_name="compressed_files.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
