from utils.logger import logger


def is_duplicate(
    opportunity: dict,
    existing_records: list
) -> bool:

    title = opportunity.get(
        "title",
        ""
    ).strip().lower()

    source_url = opportunity.get(
        "source_url",
        ""
    ).strip().lower()

    logger.info("=" * 80)
    logger.info("DUPLICATE CHECK")
    logger.info(f"Incoming Title : {title}")
    logger.info(f"Incoming URL   : {source_url}")
    logger.info(f"Checking against {len(existing_records)} existing records")

    for record in existing_records:

        existing_title = str(
            record.get("Title", "")
        ).strip().lower()

        existing_url = str(
            record.get("Source_Link", "")
        ).strip().lower()

        if (
            title == existing_title
            and
            source_url == existing_url
        ):

            logger.warning("DUPLICATE FOUND")
            logger.warning(f"Existing Title : {existing_title}")
            logger.warning(f"Existing URL   : {existing_url}")

            return True

    logger.info("No duplicate found")

    return False