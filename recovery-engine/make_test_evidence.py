import os, io, zipfile
from PIL import Image

img = Image.new('RGB', (64, 64), color=(200, 30, 30))
jpeg_buf = io.BytesIO()
img.save(jpeg_buf, format='JPEG')

zip_buf = io.BytesIO()
with zipfile.ZipFile(zip_buf, 'w') as zf:
    zf.writestr('case_notes.txt', 'Suspect confessed at 10:32 PM near warehouse district.')

pdf_bytes = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'

blob = os.urandom(5000) + jpeg_buf.getvalue() + os.urandom(8000) + zip_buf.getvalue() + os.urandom(3000) + pdf_bytes + os.urandom(2000)

with open('seized_drive.dd', 'wb') as f:
    f.write(blob)

print(f'Created seized_drive.dd ({len(blob)} bytes) with 1 JPEG, 1 ZIP, 1 PDF embedded')
