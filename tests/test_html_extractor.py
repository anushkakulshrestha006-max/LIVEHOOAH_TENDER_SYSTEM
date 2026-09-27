from core.services.html_extractor import HTMLExtractor


def test_extract_text_preserves_normal_main_content():
    extractor = HTMLExtractor()

    html = b"""
    <html>
    <body>
        <main>
            <h1>Notice Inviting Tender</h1>
            <p>
                Applications are invited for structural consultancy services
                including structural assessment and design review.
            </p>
            <p>Deadline for submission is 30 September 2026.</p>
        </main>
    </body>
    </html>
    """

    text = extractor.extract_text(html)

    assert "Notice Inviting Tender" in text
    assert "structural consultancy services" in text
    assert "30 September 2026" in text


def test_extract_text_ignores_navigation_and_hidden_content():
    extractor = HTMLExtractor()

    html = b"""
    <html>
    <body>
        <nav>
            <a>Home</a>
            <a>Login</a>
            <a>Contact Us</a>
        </nav>

        <main>
            <h1>Structural Consultancy Tender</h1>
            <p>
                Applications are invited for structural engineering services.
            </p>
            <p>Deadline for submission is 30 September 2026.</p>

            <div style="display:none">
                Hidden navigation content should disappear.
            </div>
        </main>
    </body>
    </html>
    """

    text = extractor.extract_text(html)

    assert "Structural Consultancy Tender" in text
    assert "structural engineering services" in text
    assert "Home" not in text
    assert "Login" not in text
    assert "Hidden navigation content" not in text


def test_extract_text_preserves_definition_list_fields():
    extractor = HTMLExtractor()

    html = b"""
    <html>
    <body>
        <main>
            <h1>Notice Inviting Tender</h1>
            <p>
                Structural consultancy services are invited for building
                assessment and design review.
            </p>

            <dl>
                <dt>Organization</dt>
                <dd>Development Authority</dd>
                <dt>Deadline</dt>
                <dd>30 September 2026</dd>
            </dl>
        </main>
    </body>
    </html>
    """

    text = extractor.extract_text(html)

    assert "Organization : Development Authority" in text
    assert "Deadline : 30 September 2026" in text


def test_extract_text_preserves_tender_table():
    extractor = HTMLExtractor()

    html = b"""
    <html>
    <body>
        <main>
            <h1>Notice Inviting Tender</h1>
            <p>
                Applications are invited for structural consultancy services.
            </p>

            <table>
                <tr>
                    <th>Particular</th>
                    <th>Details</th>
                </tr>
                <tr>
                    <td>Scope of Work</td>
                    <td>
                        Structural assessment and proof checking services for
                        the proposed building project
                    </td>
                </tr>
                <tr>
                    <td>Submission</td>
                    <td>
                        Technical and financial proposals shall be submitted
                        before the stated deadline
                    </td>
                </tr>
                <tr>
                    <td>Eligibility</td>
                    <td>
                        Experienced structural engineering consultants with
                        relevant completed assignments
                    </td>
                </tr>
            </table>
        </main>
    </body>
    </html>
    """

    text = extractor.extract_text(html)

    assert "Particular | Details" in text
    assert (
        "Scope of Work | Structural assessment and proof checking services"
        in text
    )
    assert "Submission | Technical and financial proposals" in text


def test_semantic_root_with_only_placeholder_does_not_hide_tender_content():
    extractor = HTMLExtractor()

    html = b"""
    <html>
    <body>
        <main>
            <p>Loading...</p>
        </main>

        <div class="tender-content">
            <h1>Notice Inviting Tender</h1>
            <p>
                Applications are invited for structural consultancy services
                for detailed structural assessment and design review.
            </p>
            <p>
                The consultant shall inspect the building, prepare the
                technical report, drawings, recommendations and estimates.
            </p>
            <p>
                Last date for submission of proposal is 30 September 2026.
            </p>
            <p>
                Eligible structural engineering consultants may submit bids.
            </p>
        </div>
    </body>
    </html>
    """

    text = extractor.extract_text(html)

    assert "Notice Inviting Tender" in text
    assert "structural consultancy services" in text
    assert "30 September 2026" in text
    assert text != "Loading..."


def test_short_tender_specific_semantic_root_is_preserved():
    extractor = HTMLExtractor()

    html = b"""
    <html>
    <body>
        <main>
            <h1>Tender Notice</h1>
            <p>Structural consultancy bid deadline: 30 September 2026.</p>
        </main>

        <div>
            This is unrelated fallback content repeated only to make this
            container longer than the semantic tender notice. It should not
            replace the genuine tender content selected from the main element.
            Additional general website information appears here without any
            procurement purpose or structural consultancy requirement.
        </div>
    </body>
    </html>
    """

    text = extractor.extract_text(html)

    assert "Tender Notice" in text
    assert "Structural consultancy bid deadline" in text
    assert "unrelated fallback content" not in text
