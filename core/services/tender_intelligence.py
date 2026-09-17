# core/services/tender_intelligence.py

import re
from typing import Dict, List


class TenderIntelligence:
    """
    Deterministic Tender Intelligence Layer.

    Purpose:
        Analyze a discovered tender/opportunity and determine whether it
        is relevant to LiveHooah's structural-engineering business.

    Responsibilities:
        - Detect genuine structural-engineering relevance
        - Detect service category
        - Reject obvious directory/listing pages
        - Reject non-structural retrofit work
        - Detect negative/unrelated services
        - Produce deterministic reasoning and confidence

    Input:
        {
            "title": "...",
            "description": "...",
            "source_url": "..."
        }

    Output:
        {
            "is_relevant": bool,
            "service_category": str,
            "summary": str,
            "why_selected": str,
            "confidence": float
        }

    NOT responsible for:
        - Web searching
        - Document downloading
        - PDF/HTML extraction
        - Final opportunity persistence
        - GPT/Hermes reasoning
        - Final business scoring
    """

    # ==========================================================
    # SERVICE CATEGORIES
    # ==========================================================

    SERVICE_CATEGORIES = {
        "structural audit": [
            "structural audit",
            "building audit",
            "condition assessment",
            "condition survey",
            "structural assessment",
            "structural health monitoring",
            "structural health assessment",
        ],

        "proof checking": [
            "proof checking",
            "proof check",
            "proof consultant",
            "design verification",
            "design review",
            "independent design review",
        ],

        "retrofit consultancy": [
            "structural retrofit",
            "structural retrofitting",
            "retrofitting of structure",
            "retrofitting of building",
            "building retrofit",
            "building retrofitting",
            "rehabilitation of structure",
            "rehabilitation of building",
            "structural rehabilitation",
            "structural strengthening",
            "strengthening of structure",
            "strengthening of building",
            "rcc strengthening",
            "rcc retrofitting",
        ],

        "structural consultancy": [
            "structural consultant",
            "structural consultants",
            "structural consultancy",
            "structural engineering",
            "structural engineer",
            "structural engineers",
            "structural design",
            "structural analysis",
            "structural services",
            "civil structural",
            "structural drawings",
            "structural drawing",
            "structural design services",
            "structural engineering services",
        ],

        "industrial building": [
            "industrial building",
            "industrial buildings",
            "factory building",
            "factory buildings",
            "plant building",
            "plant buildings",
            "industrial structure",
            "industrial structures",
            "industrial shed",
            "industrial sheds",
        ],

        "warehouse": [
            "warehouse",
            "warehouses",
            "logistics park",
            "logistics parks",
            "logistics hub",
            "distribution center",
            "distribution centre",
            "storage facility",
        ],

        "peb design": [
            "peb",
            "peb structure",
            "peb structures",
            "pre engineered building",
            "pre-engineered building",
            "pre engineered buildings",
            "pre-engineered buildings",
        ],
    }

    # ==========================================================
    # POSITIVE STRUCTURAL SIGNALS
    # ==========================================================

    POSITIVE_KEYWORDS = [
        "structural consultant",
        "structural consultants",
        "structural consultancy",
        "structural engineering",
        "structural engineer",
        "structural engineers",
        "structural design",
        "structural analysis",
        "structural services",
        "structural drawings",
        "proof checking",
        "proof check",
        "structural audit",
        "condition assessment",
        "condition survey",
        "structural assessment",
        "structural health monitoring",
        "peer review",
        "design verification",
        "design review",
        "retrofit",
        "retrofitting",
        "rehabilitation",
        "strengthening",
        "rcc",
        "rcc design",
        "steel structure",
        "steel structures",
        "warehouse",
        "warehouses",
        "logistics park",
        "logistics hub",
        "industrial building",
        "industrial structure",
        "industrial shed",
        "peb",
        "pre engineered building",
        "pre-engineered building",
    ]

    # ==========================================================
    # GENERIC TERMS THAT REQUIRE STRUCTURAL CONTEXT
    # ==========================================================

    CONTEXT_DEPENDENT_KEYWORDS = [
        "retrofit",
        "retrofitting",
        "rehabilitation",
        "strengthening",
        "warehouse",
        "warehouses",
        "rcc",
        "peb",
    ]

    # ==========================================================
    # STRUCTURAL CONTEXT
    # ==========================================================

    STRUCTURAL_CONTEXT_KEYWORDS = [
        "structural",
        "structure",
        "structures",
        "building",
        "buildings",
        "rcc",
        "reinforced concrete",
        "concrete structure",
        "steel structure",
        "steel structures",
        "beam",
        "beams",
        "column",
        "columns",
        "slab",
        "slabs",
        "foundation",
        "foundations",
        "framing",
        "structural drawing",
        "structural drawings",
        "structural design",
        "structural analysis",
        "structural engineering",
        "civil structural",
        "load bearing",
        "load-bearing",
        "seismic",
        "earthquake",
    ]

    # ==========================================================
    # NON-STRUCTURAL RETROFIT / SERVICE CONTEXT
    # ==========================================================

    NON_STRUCTURAL_RETROFIT_KEYWORDS = [
        "hvac",
        "chiller",
        "chillers",
        "cooling tower",
        "cooling towers",
        "vfd",
        "variable frequency drive",
        "air conditioning",
        "air-conditioning",
        "electrical panel",
        "electrical panels",
        "electrical equipment",
        "electrical system",
        "electrical systems",
        "transformer",
        "transformers",
        "switchgear",
        "cable",
        "cables",
        "plumbing",
        "fire fighting system",
        "firefighting system",
        "mechanical equipment",
        "mechanical system",
        "mechanical systems",
        "lift",
        "lifts",
        "elevator",
        "elevators",
    ]

    # ==========================================================
    # HARD NEGATIVE / UNRELATED SERVICES
    # ==========================================================

    NEGATIVE_KEYWORDS = [
        "road",
        "roads",
        "highway",
        "highways",
        "expressway",
        "expressways",
        "bridge",
        "bridges",
        "airport",
        "airports",
        "railway",
        "railways",
        "rail",
        "flyover",
        "overpass",
        "underpass",
        "port",
        "ports",
        "dam",
        "dams",
        "irrigation",
        "canal",
        "canals",
        "water supply",
        "sewage",
        "drainage",
        "pipeline",
        "pipelines",
        "power transmission",
        "transmission line",
        "solar plant",
        "wind energy",
        "housekeeping",
        "sanitation",
        "sweeping",
        "cleaning services",
        "janitorial",
        "security services",
        "manpower supply",
        "landscaping",
        "landscape maintenance",
        "tree cutting",
        "tree plantation",
        "gardening",
        "horticulture",
        "restaurant",
        "catering",
        "food services",
        "pest control",
        "facility management",
    ]

    # ==========================================================
    # DIRECTORY / LISTING / INFORMATIONAL PAGE SIGNALS
    # ==========================================================

    DIRECTORY_KEYWORDS = [
        "top 10",
        "top 20",
        "top 50",
        "top 100",
        "best structural consultants",
        "best structural consultant",
        "list of structural consultants",
        "list of structural engineers",
        "directory",
        "directories",
        "listing",
        "listings",
        "find a consultant",
        "find consultants",
        "consultants in",
        "consultant in",
        "consultants near",
        "consultant near",
        "companies in",
        "firms in",
        "service providers",
        "business directory",
        "review",
        "reviews",
        "rating",
        "ratings",
        "rankings",
        "profile",
        "profiles",
    ]

    DIRECTORY_URL_PATTERNS = [
        "/directory",
        "/directories",
        "/listing",
        "/listings",
        "/reviews",
        "/rating",
        "/ratings",
        "/top-",
        "/best-",
    ]

    # ==========================================================
    # TENDER / PROCUREMENT SIGNALS
    # ==========================================================

    TENDER_KEYWORDS = [
        "tender",
        "tenders",
        "rfp",
        "request for proposal",
        "rfq",
        "request for quotation",
        "eoi",
        "expression of interest",
        "empanelment",
        "bid",
        "bidding",
        "invitation for bids",
        "notice inviting tender",
        "nit",
        "procurement",
        "appointment",
        "selection of consultant",
        "selection of consultants",
        "engagement of consultant",
        "engagement of consultants",
    ]

    TENDER_URL_HINTS = [
        "/tender",
        "/tenders",
        "/procurement",
        "/rfp",
        "/rfq",
        "/eoi",
        "/bid",
        "/bids",
        "/empanelment",
        "/notice",
        "/nit",
    ]

    # ==========================================================
    # TEXT HELPERS
    # ==========================================================

    @staticmethod
    def _normalize_text(value: str) -> str:
        """
        Normalize text for deterministic keyword matching.
        """

        value = str(value or "").lower()

        value = value.replace("-", " ")

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        return value

    @classmethod
    def _contains_keyword(
        cls,
        text: str,
        keyword: str,
    ) -> bool:
        """
        Perform word-boundary-aware keyword matching.
        """

        text = cls._normalize_text(text)
        keyword = cls._normalize_text(keyword)

        if not text or not keyword:
            return False

        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"

        return bool(
            re.search(
                pattern,
                text,
            )
        )

    @classmethod
    def _matching_keywords(
        cls,
        text: str,
        keywords: List[str],
    ) -> List[str]:
        """
        Return all matching keywords.
        """

        return [
            keyword
            for keyword in keywords
            if cls._contains_keyword(
                text,
                keyword,
            )
        ]

    # ==========================================================
    # OPPORTUNITY TEXT
    # ==========================================================

    @classmethod
    def _get_text_parts(
        cls,
        opportunity: Dict,
    ) -> Dict[str, str]:
        """
        Extract and normalize title, description, snippet and URL.
        """

        title = cls._normalize_text(
            opportunity.get(
                "title",
                "",
            )
        )

        description = cls._normalize_text(
            opportunity.get(
                "description",
                "",
            )
        )

        snippet = cls._normalize_text(
            opportunity.get(
                "snippet",
                "",
            )
        )

        url = str(
            opportunity.get(
                "source_url",
                "",
            )
            or opportunity.get(
                "url",
                "",
            )
            or ""
        ).strip().lower()

        combined = " ".join(
            part
            for part in [
                title,
                snippet,
                description,
                url,
            ]
            if part
        )

        return {
            "title": title,
            "description": description,
            "snippet": snippet,
            "url": url,
            "combined": combined,
        }

    # ==========================================================
    # TENDER DETECTION
    # ==========================================================

    @classmethod
    def _has_tender_signal(
        cls,
        text: str,
        url: str,
    ) -> bool:
        """
        Determine whether the opportunity contains a procurement/tender
        signal in its content or URL.
        """

        if cls._matching_keywords(
            text,
            cls.TENDER_KEYWORDS,
        ):
            return True

        return any(
            hint in url
            for hint in cls.TENDER_URL_HINTS
        )

    # ==========================================================
    # DIRECTORY DETECTION
    # ==========================================================

    @classmethod
    def _is_directory_page(
        cls,
        title: str,
        description: str,
        url: str,
    ) -> bool:
        """
        Reject informational/listing pages that happen to mention
        structural consultants.

        Example:
            "Top 10 Structural Consultants in Pune"
        """

        title_matches = cls._matching_keywords(
            title,
            cls.DIRECTORY_KEYWORDS,
        )

        description_matches = cls._matching_keywords(
            description,
            cls.DIRECTORY_KEYWORDS,
        )

        url_match = any(
            pattern in url
            for pattern in cls.DIRECTORY_URL_PATTERNS
        )

        # Strong title-level directory signal.
        if title_matches:
            return True

        # URL-only directory signal is also sufficient when the page
        # has no procurement/tender signal.
        if url_match and not cls._has_tender_signal(
            f"{title} {description}",
            url,
        ):
            return True

        # Informational language in the description without tender
        # signals is also treated as a directory/listing page.
        if (
            description_matches
            and not cls._has_tender_signal(
                f"{title} {description}",
                url,
            )
        ):
            return True

        return False

    # ==========================================================
    # NON-STRUCTURAL RETROFIT DETECTION
    # ==========================================================

    @classmethod
    def _is_non_structural_retrofit(
        cls,
        text: str,
    ) -> bool:
        """
        Reject generic retrofit opportunities when the actual work is
        clearly HVAC/electrical/mechanical rather than structural.

        Important:
            We do NOT reject every occurrence of "retrofit".
            Structural context can override generic retrofit ambiguity.
        """

        retrofit_matches = cls._matching_keywords(
            text,
            [
                "retrofit",
                "retrofitting",
                "rehabilitation",
                "strengthening",
            ],
        )

        if not retrofit_matches:
            return False

        non_structural_matches = cls._matching_keywords(
            text,
            cls.NON_STRUCTURAL_RETROFIT_KEYWORDS,
        )

        if not non_structural_matches:
            return False

        structural_matches = cls._matching_keywords(
            text,
            cls.STRUCTURAL_CONTEXT_KEYWORDS,
        )

        # Genuine structural context takes precedence.
        if structural_matches:
            return False

        return True

    # ==========================================================
    # CATEGORY DETECTION
    # ==========================================================

    @classmethod
    def _detect_category(
        cls,
        text: str,
    ) -> str:
        """
        Determine the most specific structural service category.

        Category order matters:
            Structural audit / proof checking / retrofit are more
            specific than generic structural consultancy.
        """

        category_order = [
            "structural audit",
            "proof checking",
            "retrofit consultancy",
            "peb design",
            "warehouse",
            "industrial building",
            "structural consultancy",
        ]

        for category in category_order:

            keywords = cls.SERVICE_CATEGORIES.get(
                category,
                [],
            )

            if any(
                cls._contains_keyword(
                    text,
                    keyword,
                )
                for keyword in keywords
            ):
                return category

        return "general structural consultancy"

    # ==========================================================
    # STRUCTURAL RELEVANCE
    # ==========================================================

    @classmethod
    def _get_structural_matches(
        cls,
        text: str,
    ) -> List[str]:
        """
        Return meaningful structural/business matches.

        Generic context-dependent words are only counted when they
        occur with actual structural context.
        """

        matches = []

        direct_keywords = [
            keyword
            for keyword in cls.POSITIVE_KEYWORDS
            if keyword not in cls.CONTEXT_DEPENDENT_KEYWORDS
        ]

        matches.extend(
            cls._matching_keywords(
                text,
                direct_keywords,
            )
        )

        structural_context = cls._matching_keywords(
            text,
            cls.STRUCTURAL_CONTEXT_KEYWORDS,
        )

        for keyword in cls.CONTEXT_DEPENDENT_KEYWORDS:

            if cls._contains_keyword(
                text,
                keyword,
            ) and structural_context:

                matches.append(keyword)

        # Preserve order while removing duplicates.
        return list(
            dict.fromkeys(matches)
        )

    # ==========================================================
    # REASONING
    # ==========================================================

    @staticmethod
    def _build_reasoning(
        positive_hits: List[str],
        negative_hits: List[str],
        rejection_reason: str = "",
    ) -> str:
        """
        Build deterministic human-readable reasoning.
        """

        reasons = []

        if rejection_reason:
            reasons.append(
                rejection_reason
            )

        if positive_hits:
            reasons.append(
                "Matched structural signals: "
                + ", ".join(positive_hits)
            )

        if negative_hits:
            reasons.append(
                "Negative signals found: "
                + ", ".join(negative_hits)
            )

        if not reasons:
            reasons.append(
                "No strong structural-engineering signals detected."
            )

        return " | ".join(reasons)

    # ==========================================================
    # SUMMARY
    # ==========================================================

    @staticmethod
    def _generate_summary(
        title: str,
        category: str,
    ) -> str:
        """
        Generate deterministic internal summary.
        """

        return (
            f"Tender appears related to "
            f"{category}. Title: {title}"
        )

    # ==========================================================
    # MAIN ANALYSIS
    # ==========================================================

    def analyze(
        self,
        opportunity: Dict,
    ) -> Dict:
        """
        Analyze one tender/opportunity.

        The method intentionally remains deterministic and does not
        call an LLM.
        """

        parts = self._get_text_parts(
            opportunity
        )

        title = parts["title"]
        description = parts["description"]
        snippet = parts["snippet"]
        url = parts["url"]
        combined = parts["combined"]

        # ------------------------------------------------------
        # Empty input
        # ------------------------------------------------------

        if not title and not description and not snippet:
            return {
                "is_relevant": False,
                "service_category": "general structural consultancy",
                "summary": "No usable tender information available.",
                "why_selected": "No usable title, description or snippet.",
                "confidence": 0.0,
            }

        # ------------------------------------------------------
        # Detect tender/procurement signal
        # ------------------------------------------------------

        has_tender_signal = self._has_tender_signal(
            combined,
            url,
        )

        # ------------------------------------------------------
        # Detect directory/listing pages
        # ------------------------------------------------------

        if self._is_directory_page(
            title=title,
            description=description,
            url=url,
        ):

            return {
                "is_relevant": False,
                "service_category": "general structural consultancy",
                "summary": (
                    f"Page appears to be an informational or directory "
                    f"listing rather than a LiveHooah opportunity. "
                    f"Title: {title}"
                ),
                "why_selected": (
                    "Rejected informational/directory/listing page."
                ),
                "confidence": 0.0,
            }

        # ------------------------------------------------------
        # Negative service detection
        # ------------------------------------------------------

        negative_hits = self._matching_keywords(
            combined,
            self.NEGATIVE_KEYWORDS,
        )

        # ------------------------------------------------------
        # Structural/business relevance
        # ------------------------------------------------------

        positive_hits = self._get_structural_matches(
            combined
        )

        # ------------------------------------------------------
        # Non-structural retrofit detection
        # ------------------------------------------------------

        if self._is_non_structural_retrofit(
            combined
        ):

            non_structural_hits = self._matching_keywords(
                combined,
                self.NON_STRUCTURAL_RETROFIT_KEYWORDS,
            )

            return {
                "is_relevant": False,
                "service_category": "general structural consultancy",
                "summary": (
                    f"Opportunity appears to concern "
                    f"non-structural retrofit work. "
                    f"Title: {title}"
                ),
                "why_selected": (
                    "Rejected non-structural retrofit/service work: "
                    + ", ".join(non_structural_hits)
                ),
                "confidence": 0.0,
            }

        # ------------------------------------------------------
        # No structural signal
        # ------------------------------------------------------

        if not positive_hits:

            return {
                "is_relevant": False,
                "service_category": "general structural consultancy",
                "summary": (
                    f"No clear LiveHooah structural-engineering "
                    f"relevance detected. Title: {title}"
                ),
                "why_selected": self._build_reasoning(
                    positive_hits=[],
                    negative_hits=negative_hits,
                ),
                "confidence": 0.0,
            }

        # ------------------------------------------------------
        # Strong unrelated-service dominance
        # ------------------------------------------------------

        if negative_hits:

            # If the opportunity contains strong structural language
            # but also unrelated infrastructure terms, do not
            # automatically reject it. Instead compare the signals.
            #
            # This allows legitimate structural consultancy involving
            # buildings that may mention minor unrelated work.
            if len(negative_hits) >= len(positive_hits):

                return {
                    "is_relevant": False,
                    "service_category": "general structural consultancy",
                    "summary": (
                        f"Opportunity is dominated by unrelated "
                        f"infrastructure/service signals. "
                        f"Title: {title}"
                    ),
                    "why_selected": self._build_reasoning(
                        positive_hits=positive_hits,
                        negative_hits=negative_hits,
                        rejection_reason=(
                            "Negative service signals outweigh "
                            "structural relevance."
                        ),
                    ),
                    "confidence": 0.0,
                }

        # ------------------------------------------------------
        # Tender signal check
        # ------------------------------------------------------

        # A strong structural signal can still be useful when the
        # discovery layer has already established that this is a
        # procurement opportunity.
        #
        # But an ordinary web page without tender context should not
        # become a saved opportunity merely because it mentions
        # "structural consultant".
        if not has_tender_signal:

            return {
                "is_relevant": False,
                "service_category": self._detect_category(
                    combined
                ),
                "summary": (
                    f"Structural relevance detected, but the page "
                    f"does not contain a clear tender/procurement "
                    f"signal. Title: {title}"
                ),
                "why_selected": self._build_reasoning(
                    positive_hits=positive_hits,
                    negative_hits=negative_hits,
                    rejection_reason=(
                        "Rejected because no tender/procurement "
                        "signal was detected."
                    ),
                ),
                "confidence": 0.0,
            }

        # ------------------------------------------------------
        # FINAL RELEVANCE CLASSIFICATION
        # ------------------------------------------------------

        service_category = self._detect_category(
        combined
    )

        positive_score = len(
        positive_hits
    )

        negative_score = len(
        negative_hits
    )

        # ------------------------------------------------------
        # INFORMATIONAL / DIRECTORY PAGE DETECTION
        #
        # Reject obvious listing/directory pages such as:
        # "Top 10 Structural Consultants in Pune"
        #
        # Do NOT reject legitimate service pages such as:
        # "Structural Consultants in Delhi"
        # ------------------------------------------------------
    
        informational_patterns = [
            "top 10",
            "top 5",
            "top 20",
            "top 50",
            "directory",
            "list of consultants",
            "list of structural consultants",
            "consultant listing",
            "consultants listing",
            "find consultants",
            "best structural consultants",
            "best consultants",
        ] 

        is_informational_page = any(
            pattern in combined
            for pattern in informational_patterns
        )
    
        # HARD NEGATIVE REJECTION
        # ------------------------------------------------------
        #
        # Negative service/infrastructure signals override
        # positive structural keyword matches.
        # ------------------------------------------------------
    
        if is_informational_page:

            confidence = 0.0
            is_relevant = False
            rejection_reason = (
                "Rejected informational/directory/listing page."
            )
 
        elif negative_score > 0:

            confidence = 0.0
            is_relevant = False
            rejection_reason = ""

        else:

            confidence = positive_score / max(
                positive_score + negative_score,
                1,
            )

            confidence = min(
                max(confidence, 0.0),
                1.0,
            )

            is_relevant = positive_score > 0
            rejection_reason = ""

        # ------------------------------------------------------
        # RETURN FINAL INTELLIGENCE RESULT
        # ------------------------------------------------------

        return {
            "is_relevant": is_relevant,
            "service_category": (
                service_category
                if is_relevant
                else "general structural consultancy"
            ),
            "summary": self._generate_summary(
                title=title,
                category=(
                    service_category
                    if is_relevant
                    else "general structural consultancy"
                ),        
            ),
            "why_selected": self._build_reasoning(
                positive_hits=positive_hits,
                negative_hits=negative_hits,
                rejection_reason=rejection_reason,
            ),            
            "confidence": round(
                confidence,
                2,
            ),
        }