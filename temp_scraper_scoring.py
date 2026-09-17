from core.services.scraper_search import ScraperSearch

s = ScraperSearch()

q = "structural consultant empanelment"

tests = [
    "Empanelment of Architectural consultants for providing Comprehensive Architectural and Engineering Consultancy Services",
    "Rehabilitation and Retrofitting of RCC Slabs/Beams of Various Rooms, Corridors and Toilets",
    "Special Structural Repair work in B-Type 36 nos. houses",
    "Structural Glazing facade work to prevent rainwater",
    "Providing and fixing of Anti-Bird Spikes/Pigeon Control Spikes System on Stainless steel space frame structure",
    "Providing (Retrofitting) VF Drive in 3 x 300 TR Screw Chiller Units and Cooling Towers",
]

for title in tests:

    combined = title.lower()

    print("\n" + "=" * 80)
    print("TITLE:", title)

    print("QUERY SCORE:",
          s._query_relevance_score(combined, q))

    print("STRUCTURAL SCORE:",
          s._structural_relevance_score(combined))

    print("OPPORTUNITY SCORE:",
          s._opportunity_evidence_score(combined))

    print("STRONG STRUCTURAL COUNT:",
          s._strong_structural_signal_count(combined))

    print("STRONG STRUCTURAL:",
          s._has_strong_structural_signal(combined))

    print("STRONG PROCUREMENT:",
          s._has_strong_procurement_signal(combined))

    print("CANDIDATE SCORE:",
          s._candidate_score(
              title,
              "https://example.com/test.pdf",
              q,
              "",
          ))

    print("LOOKS LIKE TENDER:",
          s._looks_like_tender_link(
              title,
              "https://example.com/test.pdf",
              q,
              "",
          ))
