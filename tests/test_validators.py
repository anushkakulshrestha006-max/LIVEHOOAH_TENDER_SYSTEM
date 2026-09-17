from utils.validators import (
    validate_title,
    validate_url,
    validate_email,
    validate_opportunity
)

print(validate_title("Indian Army Tender"))

print(validate_url(
    "https://gem.gov.in"
))

print(validate_email(
    "test@example.com"
))

print(
    validate_opportunity(
        {
            "title": "Indian Army Tender",
            "source_url": "https://gem.gov.in"
        }
    )
)