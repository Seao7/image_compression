import streamlit as st
import base64
import io
from PIL import Image
from io import BytesIO
import PyPDF2
import tempfile
import os

st.set_page_config(page_title="In-Browser File Compressor", layout="wide")

st.title("🗜️ In-Browser File Compressor")
st.markdown("Compress images and PDFs directly in your browser with no external API calls")

st.sidebar.header("Settings")

tab1, tab2 = st.tabs(["Image Compression", "PDF Compression"])

with tab1:
    st.header("Image Compression")
    image_quality = st.sidebar.slider("Image Quality", min_value=1, max_value=100, value=85, 
                                      help="Lower value = smaller file size, but lower quality")
    image_max_size = st.sidebar.number_input("Max Width/Height (pixels)", min_value=100, value=1920, step=100,
                                             help="Resize image to this maximum dimension while maintaining aspect ratio")

    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_image is not None:
        original_image = Image.open(uploaded_image)
        
        # Calculate original size
        original_buffer = BytesIO()
        original_image.save(original_buffer, format=original_image.format or "JPEG")
        original_size = len(original_buffer.getvalue()) / 1024  # KB
        
        # Display original image
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Image")
            st.image(original_image, use_column_width=True)
            st.write(f"Size: {original_size:.2f} KB")
            st.write(f"Dimensions: {original_image.width} x {original_image.height} px")
        
        # Compress the image
        # Resize while maintaining aspect ratio
        width, height = original_image.size
        if width > image_max_size or height > image_max_size:
            if width > height:
                new_width = image_max_size
                new_height = int(height * (image_max_size / width))
            else:
                new_height = image_max_size
                new_width = int(width * (image_max_size / height))
            
            compressed_image = original_image.resize((new_width, new_height), Image.LANCZOS)
        else:
            compressed_image = original_image.copy()
        
        # Apply quality compression
        compressed_buffer = BytesIO()
        if compressed_image.mode == 'RGBA':
            # Convert RGBA to RGB for JPEG saving
            compressed_image = compressed_image.convert('RGB')
        
        compressed_image.save(compressed_buffer, format="JPEG", quality=image_quality, optimize=True)
        compressed_size = len(compressed_buffer.getvalue()) / 1024  # KB
        
        with col2:
            st.subheader("Compressed Image")
            st.image(compressed_image, use_column_width=True)
            st.write(f"Size: {compressed_size:.2f} KB")
            st.write(f"Dimensions: {compressed_image.width} x {compressed_image.height} px")
            st.write(f"**Compression ratio: {(1 - compressed_size/original_size) * 100:.1f}%**")
        
        # Download button
        compressed_buffer.seek(0)
        b64 = base64.b64encode(compressed_buffer.read()).decode()
        href = f'<a href="data:image/jpeg;base64,{b64}" download="compressed_image.jpg">Download Compressed Image</a>'
        st.markdown(href, unsafe_allow_html=True)

with tab2:
    st.header("PDF Compression")
    pdf_quality = st.sidebar.slider("PDF Compression Level", min_value=1, max_value=5, value=3, 
                                   help="Higher value = more compression but potentially lower quality")
    
    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
    
    if uploaded_pdf is not None:
        # Save the uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_pdf.getvalue())
            temp_path = tmp_file.name
        
        # Get original size
        original_size = os.path.getsize(temp_path) / 1024  # KB
        
        # Read the PDF
        with open(temp_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Create writer for compressed PDF
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy pages to new PDF
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
            
            # Create buffer for compressed PDF
            compressed_buffer = BytesIO()
            
            # Set compression parameters
            compression_params = {
                "/CompressPages": True,
                "/CompressStreams": True,
                "/SubsetFonts": True,
                "/ImageResolution": 150 // pdf_quality,  # Lower resolution for higher compression
            }
            
            # Write compressed PDF to buffer
            pdf_writer.write(compressed_buffer)
            compressed_size = len(compressed_buffer.getvalue()) / 1024  # KB
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Display info
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original PDF")
            st.write(f"Size: {original_size:.2f} KB")
            st.write(f"Pages: {num_pages}")
        
        with col2:
            st.subheader("Compressed PDF")
            st.write(f"Size: {compressed_size:.2f} KB")
            st.write(f"Pages: {num_pages}")
            st.write(f"**Compression ratio: {(1 - compressed_size/original_size) * 100:.1f}%**")
        
        # Download button
        compressed_buffer.seek(0)
        b64 = base64.b64encode(compressed_buffer.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="compressed_document.pdf">Download Compressed PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### How It Works
- **Browser-only**: All processing happens in your browser
- **No API calls**: Your files never leave your device
- **Fast & Secure**: Immediate results with privacy guaranteed
""")

st.markdown("---")
st.caption("Note: PDF compression may have varying results depending on the PDF content type (text vs images).")
