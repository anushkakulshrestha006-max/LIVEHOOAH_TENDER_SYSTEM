"""
Focused deterministic regression test for the discovery-to-extraction metadata handoff in core.services.opportunity_pipeline.

This test proves:
1. Discovery candidate contains relevant metadata (e.g. intelligence, discovery_source, discovery_score).
2. Extraction returns authoritative structured fields (title, organization, description, deadline, etc.).
3. Discovery metadata survives into the structured tender record.
4. Authoritative extracted fields are not overwritten by discovery candidate fields.
"""

from unittest.mock import patch, MagicMock
import pytest

from core.services.opportunity_pipeline import run_pipeline


def test_discovery_metadata_handoff_to_structured_extraction():
    # 1. Discovery candidate containing rich discovery/intelligence metadata
    discovery_candidate = {
        "title": "Search Snippet: Empanelment for Structural Audit",
        "description": "Short SERP snippet text",
        "organization": "Snippet Org",
        "source_url": "https://example.gov.in/tenders/tender-101.html",
        "discovery_source": "serp",
        "discovery_score": 92,
        "discovery_reasoning": "Matched structural audit",
        "snippet": "Short SERP snippet text",
        "source": "etenders.gov.in",
        "intelligence": {
            "is_relevant": True,
            "service_category": "structural audit",
            "summary": "Structural audit and safety assessment",
            "why_selected": "Structural audit keywords",
            "confidence": 0.95,
        },
    }

    # Verify discovery candidate contains the expected metadata
    assert discovery_candidate["intelligence"]["service_category"] == "structural audit"
    assert discovery_candidate["discovery_source"] == "serp"
    assert discovery_candidate["discovery_score"] == 92

    # 2. Authoritative extraction result produced by parser/extraction engine
    authoritative_extracted = {
        "title": "Detailed Notice Inviting Tender for Structural Audit and Consultancy",
        "organization": "Central Public Works Department",
        "deadline": "2026-11-30",
        "location": "New Delhi",
        "description": "Comprehensive scope of services for structural engineering consultancy and audit of towers.",
        "tender_type": "Notice Inviting Tender",
        "emd": "25000",
        "document_fee": "1000",
        "email": "audit@cpwd.gov.in",
        "phone": "011-23000000",
        "source_url": "https://example.gov.in/tenders/tender-101.html",
    }

    # Captured structured items passed into deduplicator
    captured_structured = []

    def mock_deduplicate(items):
        captured_structured.extend(items)
        return items

    with patch(
        "core.services.opportunity_pipeline.run_tender_discovery"
    ) as mock_discovery, patch(
        "core.services.opportunity_pipeline.engine.extract"
    ) as mock_extract, patch(
        "core.services.opportunity_pipeline.deduplicator.deduplicate",
        side_effect=mock_deduplicate,
    ), patch(
        "core.services.opportunity_pipeline.SheetsClient"
    ) as mock_sheets_cls:

        mock_discovery.return_value = {
            "status": "success",
            "opportunities": [discovery_candidate],
        }
        mock_extract.return_value = authoritative_extracted

        mock_client = MagicMock()
        mock_client.save_opportunity.return_value = {"status": "saved", "opportunity_id": "TEST-1"}
        mock_sheets_cls.return_value = mock_client

        # Run pipeline
        run_pipeline("structural audit empanelment")

    # 3. Verify that metadata survived into structured
    assert len(captured_structured) == 1
    structured_record = captured_structured[0]

    assert structured_record["intelligence"] == discovery_candidate["intelligence"]
    assert structured_record["discovery_source"] == "serp"
    assert structured_record["discovery_score"] == 92
    assert structured_record["discovery_reasoning"] == "Matched structural audit"
    assert structured_record["snippet"] == "Short SERP snippet text"
    assert structured_record["source"] == "etenders.gov.in"

    # 4. Verify authoritative extracted fields were NOT overwritten by discovery candidate
    assert (
        structured_record["title"]
        == "Detailed Notice Inviting Tender for Structural Audit and Consultancy"
    )
    assert structured_record["organization"] == "Central Public Works Department"
    assert (
        structured_record["description"]
        == "Comprehensive scope of services for structural engineering consultancy and audit of towers."
    )
    assert structured_record["deadline"] == "2026-11-30"
    assert structured_record["location"] == "New Delhi"
    assert structured_record["tender_type"] == "Notice Inviting Tender"
    assert structured_record["emd"] == "25000"
    assert structured_record["document_fee"] == "1000"
    assert structured_record["email"] == "audit@cpwd.gov.in"
    assert structured_record["phone"] == "011-23000000"
    assert (
        structured_record["source_url"]
        == "https://example.gov.in/tenders/tender-101.html"
    )


def test_run_pipeline_extraction_failure_returns_no_structured_tenders():
    query = "structural audit consultancy"
    candidate_url = "https://example.gov.in/tenders/tender-extraction-fail-202.html"
    candidate_opportunity = {
        "title": "Discovery Candidate Without Usable Extraction",
        "source_url": candidate_url,
    }

    with patch(
        "core.services.opportunity_pipeline.run_tender_discovery"
    ) as mock_discovery, patch(
        "core.services.opportunity_pipeline.engine.extract"
    ) as mock_extract, patch(
        "core.services.opportunity_pipeline.time.sleep"
    ) as mock_sleep, patch(
        "core.services.opportunity_pipeline.deduplicator.deduplicate"
    ) as mock_deduplicate:

        mock_discovery.return_value = {
            "status": "success",
            "opportunities": [candidate_opportunity],
        }
        mock_extract.return_value = {}

        result = run_pipeline(query)

    # Discovery succeeded on first attempt, so no retry occurs
    mock_discovery.assert_called_once_with(query)
    mock_sleep.assert_not_called()

    # Engine extract was called once with candidate source_url
    mock_extract.assert_called_once_with(candidate_url)

    # Deduplicator must NOT be called when extraction yields no structured records
    mock_deduplicate.assert_not_called()

    # Assert returned meta fields
    meta = result["meta"]
    assert meta["total_found"] == 0
    assert meta["saved"] == 0
    assert meta["duplicates"] == 0
    assert meta["failed"] == 1
    assert meta["note"] == "No structured tenders"

    # Assert returned opportunities is empty
    assert result["opportunities"] == []

def test_run_pipeline_qualifies_transforms_and_saves_qualified_opportunity():
    query = "structural consultancy tender"

    discovery_candidate = {
        "title": "Discovery Candidate",
        "source_url": "https://example.gov.in/tenders/pipeline-qualification-303.html",
    }

    extracted_opportunity = {
        "title": "Notice Inviting Tender for Structural Consultancy",
        "organization": "Central Public Works Department",
        "deadline": "2099-12-31",
        "location": "New Delhi",
        "description": "Structural consultancy services for building works.",
        "tender_type": "Notice Inviting Tender",
        "source_url": discovery_candidate["source_url"],
    }

    with patch(
        "core.services.opportunity_pipeline.run_tender_discovery"
    ) as mock_discovery, patch(
        "core.services.opportunity_pipeline.engine.extract"
    ) as mock_extract, patch(
        "core.services.opportunity_pipeline.deduplicator.deduplicate"
    ) as mock_deduplicate, patch(
        "core.services.opportunity_pipeline.compute_livehooah_score"
    ) as mock_score, patch(
        "core.services.opportunity_pipeline.qualify_opportunity"
    ) as mock_qualify, patch(
        "core.services.opportunity_pipeline.SheetsClient"
    ) as mock_sheets_cls:

        mock_discovery.return_value = {
            "status": "success",
            "opportunities": [discovery_candidate],
        }

        mock_extract.return_value = extracted_opportunity
        mock_deduplicate.return_value = [extracted_opportunity]

        mock_score.return_value = (
            0.85,
            ["MATCHER_REASONING"],
        )

        mock_qualify.return_value = (
            True,
            ["QUALIFICATION_REASONING"],
        )

        mock_client = MagicMock()
        mock_client.save_opportunity.return_value = {
            "status": "saved",
            "opportunity_id": "OPP-TEST-303",
        }
        mock_sheets_cls.return_value = mock_client

        result = run_pipeline(query)

    mock_discovery.assert_called_once_with(query)
    mock_extract.assert_called_once_with(
        discovery_candidate["source_url"]
    )
    mock_deduplicate.assert_called_once_with(
        [extracted_opportunity]
    )
    mock_score.assert_called_once_with(
        extracted_opportunity
    )
    mock_qualify.assert_called_once_with(
        extracted_opportunity
    )

    mock_client.save_opportunity.assert_called_once()

    saved_opportunity = (
        mock_client.save_opportunity.call_args.args[0]
    )

    assert saved_opportunity["score"] == 0.85
    assert saved_opportunity["reasoning"] == "MATCHER_REASONING"
    assert (
        saved_opportunity["qualification_status"]
        == "QUALIFIED"
    )
    assert (
        saved_opportunity["qualification_reasoning"]
        == "QUALIFICATION_REASONING"
    )
    assert saved_opportunity["qualified"] is True

    assert result["meta"]["total_found"] == 1
    assert result["meta"]["saved"] == 1
    assert result["meta"]["duplicates"] == 0
    assert result["meta"]["failed"] == 0

    assert len(result["opportunities"]) == 1

    transformed = result["opportunities"][0]

    assert transformed["title"] == extracted_opportunity["title"]
    assert transformed["qualification_status"] == "QUALIFIED"
    assert (
        transformed["qualification_reasoning"]
        == "QUALIFICATION_REASONING"
    )


def test_run_pipeline_counts_sheets_duplicate_result():
    query = "structural consultancy duplicate tender"

    discovery_candidate = {
        "title": "Discovery Candidate",
        "source_url": "https://example.gov.in/tenders/duplicate-404.html",
    }

    extracted_opportunity = {
        "title": "Notice Inviting Tender for Structural Consultancy",
        "organization": "Central Public Works Department",
        "deadline": "2099-12-31",
        "location": "New Delhi",
        "description": "Structural consultancy services for building works.",
        "tender_type": "Notice Inviting Tender",
        "source_url": discovery_candidate["source_url"],
    }

    with patch(
        "core.services.opportunity_pipeline.run_tender_discovery"
    ) as mock_discovery, patch(
        "core.services.opportunity_pipeline.engine.extract"
    ) as mock_extract, patch(
        "core.services.opportunity_pipeline.deduplicator.deduplicate"
    ) as mock_deduplicate, patch(
        "core.services.opportunity_pipeline.compute_livehooah_score"
    ) as mock_score, patch(
        "core.services.opportunity_pipeline.qualify_opportunity"
    ) as mock_qualify, patch(
        "core.services.opportunity_pipeline.SheetsClient"
    ) as mock_sheets_cls:

        mock_discovery.return_value = {
            "status": "success",
            "opportunities": [discovery_candidate],
        }
        mock_extract.return_value = extracted_opportunity
        mock_deduplicate.return_value = [extracted_opportunity]
        mock_score.return_value = (0.85, ["MATCHER_REASONING"])
        mock_qualify.return_value = (
            True,
            ["QUALIFICATION_REASONING"],
        )

        mock_client = MagicMock()
        mock_client.save_opportunity.return_value = {
            "status": "duplicate",
        }
        mock_sheets_cls.return_value = mock_client

        result = run_pipeline(query)

    mock_client.save_opportunity.assert_called_once()

    assert result["meta"]["total_found"] == 1
    assert result["meta"]["saved"] == 0
    assert result["meta"]["duplicates"] == 1
    assert result["meta"]["failed"] == 0


def test_run_pipeline_counts_sheets_write_exception_as_failed():
    query = "structural consultancy sheets failure"

    discovery_candidate = {
        "title": "Discovery Candidate",
        "source_url": "https://example.gov.in/tenders/sheets-failure-505.html",
    }

    extracted_opportunity = {
        "title": "Notice Inviting Tender for Structural Consultancy",
        "organization": "Central Public Works Department",
        "deadline": "2099-12-31",
        "location": "New Delhi",
        "description": "Structural consultancy services for building works.",
        "tender_type": "Notice Inviting Tender",
        "source_url": discovery_candidate["source_url"],
    }

    with patch(
        "core.services.opportunity_pipeline.run_tender_discovery"
    ) as mock_discovery, patch(
        "core.services.opportunity_pipeline.engine.extract"
    ) as mock_extract, patch(
        "core.services.opportunity_pipeline.deduplicator.deduplicate"
    ) as mock_deduplicate, patch(
        "core.services.opportunity_pipeline.compute_livehooah_score"
    ) as mock_score, patch(
        "core.services.opportunity_pipeline.qualify_opportunity"
    ) as mock_qualify, patch(
        "core.services.opportunity_pipeline.SheetsClient"
    ) as mock_sheets_cls:

        mock_discovery.return_value = {
            "status": "success",
            "opportunities": [discovery_candidate],
        }
        mock_extract.return_value = extracted_opportunity
        mock_deduplicate.return_value = [extracted_opportunity]
        mock_score.return_value = (0.85, ["MATCHER_REASONING"])
        mock_qualify.return_value = (
            True,
            ["QUALIFICATION_REASONING"],
        )

        mock_client = MagicMock()
        mock_client.save_opportunity.side_effect = RuntimeError(
            "Simulated Google Sheets write failure"
        )
        mock_sheets_cls.return_value = mock_client

        result = run_pipeline(query)

    mock_client.save_opportunity.assert_called_once()

    assert result["meta"]["total_found"] == 1
    assert result["meta"]["saved"] == 0
    assert result["meta"]["duplicates"] == 0
    assert result["meta"]["failed"] == 1
    assert len(result["opportunities"]) == 1


if __name__ == "__main__":
    test_discovery_metadata_handoff_to_structured_extraction()
    print("PASS: test_discovery_metadata_handoff_to_structured_extraction")
