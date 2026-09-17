def validate_title(title):

    if not isinstance(title, str):
        return False

    return len(title.strip()) >= 5


def validate_url(url):

    if not isinstance(url, str):
        return False

    # ✅ FIXED: allow empty/placeholder URLs from Hermes
    # Only validate format IF a URL was actually provided
    if url.strip() == "":
        return True

    return (
        url.startswith("http://")
        or
        url.startswith("https://")
    )


def validate_email(email):

    if not isinstance(email, str):
        return False

    return (
        "@" in email
        and "." in email
    )


def validate_opportunity(data):

    required_fields = [
        "title",
        "source_url"
    ]

    for field in required_fields:
        if field not in data:
            return False

    if not validate_title(data["title"]):
        return False

    if not validate_url(data["source_url"]):
        return False

    return True