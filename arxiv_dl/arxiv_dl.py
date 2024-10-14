# https://arxiv.org/help/api/user-manual

import json
import logging
from pathlib import Path

from .helpers import (
    add_to_paper_list,
    create_paper_note,
    download_pdf,
    get_download_dest,
    process_arxiv_target,
    process_cvf_target,
    process_ecva_target,
    process_nips_target,
    process_openreview_target,
)
from .logger import logger
from .models import PaperData
from .scrapers import scrape_metadata


def main(
    target: str,
    verbose: bool = False,
    download_dir: Path = None,
    n_threads: int = 5,
    pdf_only: bool = False,
    *args,
    **kwargs,
) -> bool:
    """
    Entry point

    Download paper and extract paper metadata
    """

    ### Get Target Download Directory
    try:
        if download_dir is None:
            download_dir: Path = get_download_dest()
        else:
            download_dir: Path = Path(download_dir).resolve()
            assert download_dir.is_dir()
    except Exception as e:
        logger.exception(e)
        logger.error("[Abort] Environment Variable Error")
        return False

    ### Filter Invalid Target String
    if not target or not isinstance(target, str):
        logger.error("[Abort] Target is not specified correctly")
        return False

    if (
        not target.startswith(("http://", "https://", "www."))
        and not target[0].isdigit()
    ):
        logger.error(
            f"[Abort] Target should be a URL or an ArXiv ID. Unknown target: '{target}'"
        )
        return False

    ### Identify Paper Source/Venues
    if target[0].isdigit() or "arxiv.org" in target:
        # assume target is an ArXiv ID
        paper_data: PaperData = process_arxiv_target(target)
    elif "openaccess.thecvf.com" in target:  # assume target is a CVF URL
        # CVPR, ICCV, WACV
        paper_data: PaperData = process_cvf_target(target)
    elif "papers.nips.cc/paper" in target:  # assume target is a NeurIPS URL
        paper_data: PaperData = process_nips_target(target)
    elif "openreview.net" in target:  # assume target is an OpenReview URL
        paper_data: PaperData = process_openreview_target(target)
    elif "ecva.net" in target:  # assume target is an ECCV URL
        paper_data: PaperData = process_ecva_target(target)
    elif target.endswith(".pdf"):  # assume target is a PDF file
        # TODO: download the pdf file only
        ...
    else:
        logger.error(f"[Abort] Unknown target: {target}")
        return False

    # start scraping from source website
    scrape_metadata(paper_data)

    # adjust logging level
    logger.setLevel(logging.DEBUG)
    if verbose:
        logger.debug(json.dumps(paper_data.dict(), indent=4))

    # download paper
    try:
        if paper_data.pdf_url:
            download_pdf(
                paper_data, download_dir=download_dir, parallel_connections=n_threads
            )
        else:
            # TODO: think how to handle this; maybe improve error message
            logger.warning("[Warn] No PDF URL found")
    except Exception as err:
        logger.exception(err)
        logger.error("[Abort] Error while downloading paper")
        return False

    # update paper list
    try:
        add_to_paper_list(paper_data, download_dir=download_dir)
    except Exception as err:
        logger.exception(err)
        logger.warning("[Warn] Error while updating paper list")
        return False

    # Create paper notes
    try:
        if not pdf_only:
            create_paper_note(paper_data, download_dir=download_dir)
    except Exception as err:
        logger.exception(err)
        logger.warning("[Warn] Error while creating note")
        return False

    return True


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent.parent
    tmp_dir = root_dir / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    from puts import timeitprint

    @timeitprint
    def test_performances():
        main("1506.01497", verbose=True, download_dir=tmp_dir)
        # main("https://arxiv.org/abs/1506.01497", verbose=True, download_dir=tmp_dir)

    test_performances()
