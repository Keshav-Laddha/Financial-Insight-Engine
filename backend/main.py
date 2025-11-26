# from dotenv import load_dotenv
# load_dotenv()

# from fastapi import FastAPI
# from app.routes import upload, analysis, news
# from fastapi.middleware.cors import CORSMiddleware
# from starlette.middleware.trustedhost import TrustedHostMiddleware

# app=FastAPI( #instantiate app with metadata
#     title="Financial Document Analaysis API",
#     description="Secure backend for OCR, text extraction, and analysis of financial reports."
# )

# #To prevent Host Header Injection Attack
# #Attackers can attack host header to perform cache poisning or redirect attackks
# app.add_middleware( #add only trusted host middleware (OWASP- prevent host header attacks)
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"] #allow req from these specific hostnames only
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_credentials=True,
#     # allow_methods=["GET", "POST", "OPTIONS"],
#     # allow_headers=["Authorization", "Content-Type"]
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

# app.include_router(upload.router, prefix="/upload", tags=["Upload"])
# app.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
# app.include_router(news.router, prefix="/news", tags=["News"])


# @app.get("/ping", tags=["Health"])
# def ping():
#     """
#     Simple endpoint to verify that backend is running.
#     Does not expose sensitive info (OWASP: A6 Sensitive Data Exposure)
#     """
#     return {"status": "ok", "message": "Backend is alive and secure!"}

# main.py (project root or app/main.py whichever you use as entry)
from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI
from app.routes import upload, analysis, news, summary, files
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
#from config.logging_config import configure_logging

#configure_logging()
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Financial Document Analysis API",
    description="Secure backend for OCR, text extraction, and analysis of financial reports."
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# mount routers: upload -> /upload/, analysis -> /analyze/
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
app.include_router(news.router, prefix="/news", tags=["News"])
app.include_router(summary.router, prefix="/summary", tags=["Summary"])
app.include_router(files.router, prefix="/files", tags=["Files"])


@app.get("/ping", tags=["Health"])
def ping():
    return {"status": "ok", "message": "Backend is alive and secure!"}