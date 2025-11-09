import os
import pdfplumber  # imports text from text-based pdfs
import pandas as pd  # for excel files
# import pytesseract  # for OCR scanned images (optional)
from PIL import Image
from fastapi import HTTPException, status
from app.services.preprocessing_service import clean_text
from dotenv import load_dotenv

load_dotenv()

from typing import Optional

# Validate file path and extensions
def validate_file(file_path: str):
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found on server"
        )

    allowed_ext = (".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png")
    if not file_path.lower().endswith(allowed_ext):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format."
        )


def extract_text(file_path: str) -> dict:
    """
    Extracts text and simple table structures from supported file types.
    Returns dictionary with keys: raw_text, cleaned_text, tables
    """
    validate_file(file_path)

    ext = os.path.splitext(file_path)[1].lower()
    raw_text = ""
    tables = []

    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        raw_text += "\n" + page_text
                    # extract tables (list of lists)
                    page_tables = page.extract_tables() or []
                    for tbl in page_tables:
                        if tbl and isinstance(tbl, list):
                            tables.append(tbl)

            if not raw_text.strip():
                # scanned PDF (no text layer) -- raise informative error
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="It is a scanned PDF or PDF text extraction returned empty. Upload a text-based PDF or enable OCR pathway."
                )

        elif ext in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(file_path)
                tables.append(df.values.tolist())
                raw_text = df.to_string(index=False)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Excel parsing failed ({type(e).__name__})"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type."
            )

        try:
            cleaned_text = clean_text(raw_text or "")
            if not cleaned_text.strip():
                cleaned_text = raw_text
        except Exception:
            cleaned_text = raw_text

        return {
            "raw_text": (raw_text or "").strip()[:50000],
            "cleaned_text": (cleaned_text or "").strip()[:50000],
            "tables": tables or []
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected extraction failure: {type(e).__name__}"
        )

# import os
# import pdfplumber #imports text from text-based pdfs
# import pandas as pd #for excel files
# import pytesseract #for OCR(Optical Character Recognition) for scanned images files
# from PIL import Image #opens and processes image files (png, jpg) before OCR
# from fastapi import HTTPException, status
# from app.services.preprocessing_service import clean_text
# from dotenv import load_dotenv

# #pytesseract.pytesseract.tesseract_cmd = r"C:\Users\kesha\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
# load_dotenv()

# #optional import only used for scanned PDFs (lazy import pattern)
# #this avoids unnecessary dependency load for non-PDF files
# from typing import Optional

# #POPPLER_PATH=os.getenv("POPPLER_PATH")
# #TESSERACT_CMD=os.getenv("TESSERACT_CMD")

# # if not POPPLER_PATH or not TESSERACT_CMD:
# #     print("Warning missing Poppler or Tesseract path\n")

# # if TESSERACT_CMD:
# #     pytesseract.pytesseract.tesseract_cmd=TESSERACT_CMD

# def validate_file(file_path: str):
#     if not os.path.exists(file_path): #check if file exists or not
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="File not found on server"
#         )
    
#     allowed_ext=(".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png")
#     if not file_path.lower().endswith(allowed_ext):
#         raise HTTPException(
#             status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#             detail="Unsupported file format."
#         )

# def extract_text(file_path: str)-> str:
#     #Extracts text from pdfs, images and excel sheets
#     validate_file(file_path)

#     ext=os.path.splitext(file_path)[1].lower()
#     #text_output=""
#     raw_text=""
#     tables=[]

#     try:
#         #for pdfs
#         if ext==".pdf":
#             with pdfplumber.open(file_path) as pdf:
#                 for page in pdf.pages:
#                     page_text=page.extract_text()
#                     if page_text:
#                         raw_text+="\n"+page_text
#                     #extract tables
#                     page_tables=page.extract_tables() or []
#                     for tbl in page_tables:
#                         if tbl and isinstance(tbl, list):
#                             tables.append(tbl)
#             if not raw_text.strip():
#                 # try:
#                 #     from pdf2image import convert_from_path
#                 #     images=convert_from_path(
#                 #         file_path,
#                 #         dpi=200,
#                 #         poppler_path=POPPLER_PATH if POPPLER_PATH else None
#                 #     )
#                 #     ocr_text=""
#                 #     for img in images:
#                 #         ocr_text+=pytesseract.image_to_string(img, config="--psm 6", lang="eng")+"\n"
#                 #     raw_text=ocr_text
#                 # except Exception as e:
#                 #     raise HTTPException(
#                 #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 #         detail="Poppler is not installed or PDF conversion failed. Please install Poppler and try again."
#                 #     )
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="It is a scanned PDF. Upload a text-based PDF and try again."
#                 )

#         elif ext in [".xlsx", ".xls"]: #for excel files
#             try:
#                 df=pd.read_excel(file_path)
#                 tables.append(df.values.tolist()) #store as table-like structure
#                 raw_text=df.to_string(index=False)
#             except Exception as e:
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail=f"Excel parsing failed ({type(e).__name__})"
#                 )
        
#         # elif ext in ["jpg", "jpeg", "png"]: #for image files
#         #     try:
#         #         image=Image.open(file_path).convert("L") #convert to grayscale for better OCR
#         #         raw_text=pytesseract.image_to_string(image, config="--psm 6", lang="eng")
#         #     except Exception as e:
#         #         raise HTTPException(
#         #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #             detail=f"OCR failed for image ({type(e).__name__})"
#         #         )
        
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#                 detail="Unsupported file type."
#             )
    
#         try:
#             cleaned_text=clean_text(raw_text or "")
#             if not cleaned_text.strip():
#                 cleaned_text=raw_text
#         except Exception:
#             cleaned_text=raw_text

#         return {
#             "raw_text": (raw_text or "").strip()[:50000],
#             "cleaned_text": (cleaned_text or "").strip()[:50000],
#             "tables": tables or []
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         #log and rethrow as clean FastAPI HTTPException
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Unexpected extraction failure: {type(e).__name__}"
#         )