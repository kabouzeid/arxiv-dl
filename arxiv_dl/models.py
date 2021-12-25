from typing import List

from pydantic import BaseModel


class PaperData(BaseModel):
    paper_id: str = None
    abs_url: str = None
    pdf_url: str = None
    src_website: str = None
    download_name: str = None

    title: str = None
    year: int = None
    paper_venue: str = None
    authors: List[str] = []
    abstract: str = None
    comments: str = None
    official_code_urls: List[str] = []
    pwc_page_url: str = None
    bibtex: str = None
