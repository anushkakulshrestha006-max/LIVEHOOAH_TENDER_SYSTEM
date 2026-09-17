"""
Official source configuration for the LiveHooah Tender Intelligence System.

Only official organization websites belong here.

Tender aggregators (BidAssist, TenderDetail, Tender247, etc.)
must NEVER be added.

Each source is represented as a dictionary so that the scraper can
intelligently decide:
- when to search it,
- where to search,
- how important it is,
- which tender/procurement paths to probe.
"""


def source(
    name,
    url,
    keywords,
    category,
    services=None,
    sectors=None,
    priority=5,
    enabled=True,
    portal_type=None,
    states=None,
    crawl_depth=1,
    paths=None,
):
    """
    Helper for defining official sources.
    """

    return {
    "name": name,
    "url": url,
    "category": category,
    "services": services or [],
    "sectors": sectors or [],
    "keywords": keywords,
    "priority": priority,
    "enabled": enabled,
    "portal_type": portal_type,
    "states": states or [],
    "crawl_depth": crawl_depth,
    "paths": paths or [
        "/tenders",
        "/tender",
        "/tenders/current",
        "/tenders/archive",
        "/procurement",
        "/procurements",
        "/eprocurement",
        "/e-procurement",
        "/etenders",
        "/e-tenders",
        "/rfp",
        "/rfqs",
        "/eoi",
        "/notice",
        "/notices",
        "/tendernotice",
        "/vendor",
        "/vendors",
    ],
}


OFFICIAL_SOURCES = {

    "government": [

        source(
            name="Central Public Procurement Portal",
            url="https://eprocure.gov.in",
            category="government",
            keywords=[
                "government",
                "procurement",
                "central",
        ],
        services=[
            "construction",
            "consultancy",
            "pmc",
            "architecture",
            "epc",
            "goods",
            "services",
        ],
        sectors=[
            "government",
            "infrastructure",
        ],
        priority=10,
    ),

        source(
            name="Government e-Marketplace",
            url="https://gem.gov.in",
            category="government",
            keywords=[
                "government",
                "gem",
                "procurement",
                "marketplace",
        ],
        services=[
            "goods",
            "services",
            "consultancy",
            "it",
            "construction",
            "engineering",
        ],
        sectors=[
            "government",
            "public_procurement",
        ],
        priority=10,
    ),
        source(

        name="CPWD",
        url="https://cpwd.gov.in",
        category="government",
        keywords=[
        "cpwd",
        "construction",
        "consultancy",
        "government",
        "engineering",
    ],

        services=[
        "structural",
        "architecture",
        "pmc",
        "consultancy",
        "project_management",
        "civil",
        "engineering",
    ],

        sectors=[
        "government_buildings",
        "infrastructure",
        "public_works",
    ],

    priority=9,

),

        source(

    name="NHAI",

    url="https://nhai.gov.in",

    category="government",

    keywords=[
        "nhai",
        "highway",
        "bridge",
        "infrastructure",
        "road",
        "expressway",
    ],

    services=[
        "civil",
        "structural",
        "infrastructure",
        "engineering",
        "project_management",
        "epc",
    ],

    sectors=[
        "highways",
        "transport_infrastructure",
        "government_infrastructure",
    ],

    priority=9,

),

        source(

    name="NBCC",

    url="https://nbccindia.in",

    category="government",

    keywords=[
        "nbcc",
        "construction",
        "pmc",
        "consultancy",
        "government",
        "turnkey",
    ],

    services=[
        "pmc",
        "project_management",
        "consultancy",
        "architecture",
        "engineering",
        "construction_management",
        "civil",
    ],

    sectors=[
        "government_buildings",
        "infrastructure",
        "urban_development",
    ],

    priority=9,

),
    ],

    "psu": [

        source(

    name="NTPC",

    url="https://ntpc.co.in",

    category="psu",

    keywords=[
        "ntpc",
        "power",
        "energy",
        "electricity",
        "thermal",
    ],

    services=[
        "engineering",
        "epc",
        "consultancy",
        "project_management",
        "civil",
        "electrical",
        "mechanical",
    ],

    sectors=[
        "power_generation",
        "energy_infrastructure",
        "government_psu",
    ],

    priority=8,

),

        source(

    name="ONGC",

    url="https://ongcindia.com",

    category="psu",

    keywords=[
        "ongc",
        "oil",
        "gas",
        "petroleum",
        "energy",
    ],

    services=[
        "engineering",
        "exploration",
        "consultancy",
        "project_management",
        "industrial",
    ],

    sectors=[
        "oil_gas",
        "energy",
        "upstream_industry",
        "government_psu",
    ],

    priority=8,

),

        source(

    name="RITES",

    url="https://rites.com",

    category="psu",

    keywords=[
        "rites",
        "railway",
        "consultancy",
        "engineering",
        "transport",
    ],

    services=[
        "consultancy",
        "engineering",
        "project_management",
        "railway_planning",
        "civil",
        "infrastructure",
    ],

    sectors=[
        "railways",
        "transport_infrastructure",
        "government_psu",
    ],

    priority=9,

),
    ],

    "state_portals": [

    ],

    "universities": [

        source(

    name="IIT Delhi",

    url="https://iitd.ac.in",

    category="university",

    keywords=[
        "iit",
        "iit delhi",
        "university",
        "research",
        "consultancy",
    ],

    services=[
        "research",
        "consultancy",
        "engineering",
        "project_management",
        "lab_services",
        "academic_projects",
    ],

    sectors=[
        "education",
        "research_institutes",
        "government_academic",
    ],

    priority=8,

),

        source(

    name="IIT Bombay",

    url="https://iitb.ac.in",

    category="university",

    keywords=[
        "iit",
        "iit bombay",
        "university",
        "research",
        "consultancy",
    ],

    services=[
        "research",
        "consultancy",
        "engineering",
        "project_management",
        "innovation",
        "academic_projects",
    ],

    sectors=[
        "education",
        "research_institutes",
        "government_academic",
    ],

    priority=8,

),

    ],

    "airports": [

        source(

    name="AAI",

    url="https://aai.aero",

    category="airports",

    keywords=[
        "aai",
        "airport",
        "aviation",
        "airports authority",
        "runway",
        "terminal",
    ],

    services=[
        "engineering",
        "construction",
        "consultancy",
        "project_management",
        "civil",
        "electrical",
        "mechanical",
        "aviation_infrastructure",
    ],

    sectors=[
        "aviation",
        "airport_infrastructure",
        "transport_infrastructure",
        "government_psu",
    ],

    priority=8,

),

    ],

    "metro": [

        source(

    name="DMRC",

    url="https://delhimetrorail.com",

    category="metro",

    keywords=[
        "dmrc",
        "metro",
        "delhi metro",
        "rail",
        "urban transport",
    ],

    services=[
        "civil",
        "tunneling",
        "structural",
        "electrical",
        "mechanical",
        "signalling",
        "consultancy",
        "project_management",
        "epc",
    ],

    sectors=[
        "urban_transport",
        "metro_infrastructure",
        "government_transport",
    ],

    priority=8,

),

    ],

    "smart_city": [

    ],

    "builders": [

    source(

        name="DLF",

        url="https://dlf.in",

        category="builder",

        keywords=[
            "dlf",
            "builder",
            "real estate",
            "commercial",
            "residential",
        ],

        services=[
            "structural",
            "architecture",
            "pmc",
            "consultancy",
            "project_management",
            "construction_management",
        ],

        sectors=[
            "commercial_real_estate",
            "residential",
            "mixed_use",
        ],

        priority=9,

    ),

    source(

        name="Godrej Properties",

        url="https://godrejproperties.com",

        category="builder",

        keywords=[
            "godrej",
            "builder",
            "real estate",
            "housing",
        ],

        services=[
            "structural",
            "architecture",
            "pmc",
            "consultancy",
            "project_management",
        ],

        sectors=[
            "residential",
            "housing",
            "real_estate",
        ],

        priority=9,

    ),

    source(

        name="Tulip Group",

        url="https://tulipgroup.com",

        category="builder",

        keywords=[
            "tulip",
            "builder",
            "housing",
        ],

        services=[
            "structural",
            "architecture",
            "pmc",
            "consultancy",
        ],

        sectors=[
            "residential",
            "housing",
        ],

        priority=9,

    ),

    source(

        name="Signature Global",

        url="https://signatureglobal.in",

        category="builder",

        keywords=[
            "signature global",
            "builder",
            "housing",
            "real estate",
        ],

        services=[
            "structural",
            "architecture",
            "pmc",
            "consultancy",
        ],

        sectors=[
            "residential",
            "affordable_housing",
        ],

        priority=9,

    ),

],

    "industrial": [

    source(

        name="KINFRA",

        url="https://kinfra.org",

        category="industrial",

        keywords=[
            "kinfra",
            "industrial",
            "park",
            "infrastructure",
        ],

        services=[
            "civil",
            "infrastructure",
            "consultancy",
            "project_management",
            "development",
        ],

        sectors=[
            "industrial_parks",
            "manufacturing_infrastructure",
        ],

        priority=8,

    ),

],

    "healthcare": [

    source(

        name="AIIMS",

        url="https://aiims.edu",

        category="healthcare",

        keywords=[
            "aiims",
            "hospital",
            "medical",
            "healthcare",
        ],

        services=[
            "hospital_infrastructure",
            "civil",
            "engineering",
            "consultancy",
            "project_management",
        ],

        sectors=[
            "healthcare",
            "medical_infrastructure",
            "government_health",
        ],

        priority=8,

    ),

],

    "ports": [

    ],

   "manufacturing": [

    source(

        name="Tata Steel",

        url="https://tatasteel.com",

        category="manufacturing",

        keywords=[
            "tata steel",
            "steel",
            "manufacturing",
            "industrial",
        ],

        services=[
            "engineering",
            "civil",
            "industrial_projects",
            "consultancy",
        ],

        sectors=[
            "steel_industry",
            "heavy_industry",
        ],

        priority=7,

    ),

],

    "warehouse_logistics": [

    source(

        name="ESR",

        url="https://esr.com",

        category="warehouse",

        keywords=[
            "esr",
            "warehouse",
            "logistics",
            "industrial",
        ],

        services=[
            "warehouse_development",
            "civil",
            "consultancy",
            "project_management",
        ],

        sectors=[
            "logistics",
            "warehousing",
            "industrial_real_estate",
        ],

        priority=8,

    ),

    source(

        name="IndoSpace",

        url="https://indospace.in",

        category="warehouse",

        keywords=[
            "indospace",
            "warehouse",
            "logistics",
        ],

        services=[
            "warehouse_development",
            "industrial",
            "consultancy",
            "project_management",
        ],

        sectors=[
            "logistics",
            "industrial_parks",
        ],

        priority=8,

    ),

],
}