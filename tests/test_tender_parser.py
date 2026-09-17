from core.services.tender_parser import TenderParser


def main():
    parser = TenderParser()

    sample_text = """
    KERALA INDUSTRIAL INFRASTRUCTURE DEVELOPMENT CORPORATION

    NOTICE INVITING TENDER

    Appointment of Structural Consultant for Structural Audit
    and Engineering Consultancy Services for Industrial Buildings

    Organization: Kerala Industrial Infrastructure Development Corporation
    Tender Reference: KINFRA/SC/2026/001
    Location: Kochi, Kerala

    Scope of Work:
    The consultant shall carry out structural audit, structural assessment,
    structural analysis, structural design, proof checking and related
    engineering consultancy services for industrial buildings.

    Last Date for Submission: 15/09/2026

    Tender Fee: Rs. 5,000/-
    EMD: Rs. 1,00,000/-

    Contact:
    Email: tenders@kinfra.org
    Phone: +91 9876543210
    """

    result = parser.parse(
        sample_text,
        source_url="https://example.com/tender.pdf",
    )

    print("\n" + "=" * 80)
    print("TENDER PARSER TEST")
    print("=" * 80)

    for key, value in result.items():
        print(f"{key:20}: {value}")

    print("=" * 80)


if __name__ == "__main__":
    main()