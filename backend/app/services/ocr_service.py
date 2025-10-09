import os
import pdfplumber #imports text from text-based pdfs
import pandas as pd #for excel files
import pytesseract #for OCR(Optical Character Recognition) for scanned images files
from PIL import Image #opens and processes image files (png, jpg) before OCR
from fastapi import HTTPException, status

#optional import only used for scanned PDFs (lazy import pattern)
#this avoids unnecessary dependency load for non-PDF files
from typing import Optional

def validate_file(file_path: str):
    if not os.path.exists(file_path): #check if file exists or not
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found on server"
        )
    
    allowed_ext=(".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png")
    if not file_path.lower().endswith(allowed_ext):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format."
        )

def extract_text(file_path: str)-> str:
    #Extracts text from pdfs, images and excel sheets
    validate_file(file_path)

    ext=file_path.lower().split('.')[-1] #split file path ert '.' then through [-1] get the last element
    text_output=""

    try:
        #for pdfs
        if ext=="pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text=page.extract_text()
                    #page_table=page.extract_table()
                    if page_text:
                        text_output+=page_text+"\n"
                    # if page_table:
                    #     text_output+=page_table+"\n"
            if not text_output.strip():
                #if no text found then fallback OCR for scanned pdfs
                from pdf2image import convert_from_path
                images=convert_from_path(file_path, dpi=200) #convert pdf to images
                for img in images:
                    text_output+=pytesseract.image_to_string(img, lang='eng')+"\n"

        elif ext in ["xlsx", "xls"]: #for excel files
            df=pd.read_excel(file_path)
            text_output=df.to_string(index=False)
        
        elif ext in ["jpg", "jpeg", "png"]: #for image files
            image=Image.open(file_path)
            text_output=pytesseract.image_to_string(image, lang='eng')
        
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type."
            )
    
    except HTTPException:
        raise

    except Exception as e:
        #avoid leaking internal info-> only give generic message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed due to an internal error. ({type(e).__name__})"
        )
    
    return text_output.strip()