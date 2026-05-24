"""
BRAHMO Citation Safety Engine — Flask Application

A deterministic citation safety pipeline that runs AFTER AI generates
legal responses. Verifies citations, detects hallucinations, normalizes
repealed law sections (IPC→BNS), and annotates output.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, Response
from config import Config
from extensions import db
from models import CitationPattern, SectionMapping, VerificationCache, LegalMatter
from engines.citation_extractor import CitationExtractor
from engines.hallucination_detector import HallucinationDetector
from engines.citation_verifier import CitationVerifier
from engines.section_normalizer import SectionNormalizer
from engines.citation_annotator import CitationAnnotator
from services.llm_service import LLMService
from services.indian_kanoon import IndianKanoonClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Load patterns from DB (fallback to built-in)
        try:
            db_patterns = [
                {"pattern_name": p.pattern_name, "regex": p.regex}
                for p in CitationPattern.query.filter_by(is_active=True).all()
            ]
            logger.info(f"Loaded {len(db_patterns)} citation patterns from DB")
        except Exception:
            db_patterns = None
            logger.warning("Using built-in citation patterns (DB not available)")

        try:
            db_mappings = [
                {
                    "old_section": m.old_section,
                    "new_section": m.new_section,
                    "old_act": m.old_act,
                    "new_act": m.new_act,
                }
                for m in SectionMapping.query.filter_by(is_active=True).all()
            ]
            logger.info(f"Loaded {len(db_mappings)} section mappings from DB")
        except Exception:
            db_mappings = None
            logger.warning("Using built-in section mappings (DB not available)")

        # Initialize engines (app-scoped)
        app.citation_extractor = CitationExtractor(db_patterns)
        app.hallucination_detector = HallucinationDetector(
            current_year=Config.CURRENT_YEAR
        )
        app.section_normalizer = SectionNormalizer(db_mappings)
        app.citation_annotator = CitationAnnotator()

        # Initialize services
        app.llm_service = None
        app.ik_client = None
        app.citation_verifier = None

        if Config.LLM_API_KEY:
            app.llm_service = LLMService(
                api_key=Config.LLM_API_KEY,
                base_url=Config.LLM_BASE_URL,
                model=Config.LLM_MODEL,
            )

        if Config.IK_API_KEY:
            app.ik_client = IndianKanoonClient(
                api_key=Config.IK_API_KEY,
                base_url=Config.IK_BASE_URL,
            )
            app.citation_verifier = CitationVerifier(
                ik_client=app.ik_client,
                db=db,
                cache_ttl_days=Config.CACHE_TTL_DAYS,
            )

    # ─── Routes ──────────────────────────────────────────────────────

    @app.route("/")
    def index():
        """Main page — demo UI."""
        matters = LegalMatter.query.order_by(LegalMatter.id).all()
        return render_template("index.html", matters=matters)

    @app.route("/health")
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "BRAHMO Citation Safety Engine"})

    @app.route("/api/matters")
    def api_matters():
        """List all legal matters."""
        matters = LegalMatter.query.order_by(LegalMatter.id).all()
        return jsonify([m.to_dict() for m in matters])

    @app.route("/api/matters/<int:matter_id>")
    def api_matter_detail(matter_id):
        """Get matter details including sample output."""
        matter = LegalMatter.query.get_or_404(matter_id)
        result = matter.to_dict()
        result["sample_output"] = matter.sample_output
        return jsonify(result)

    @app.route("/api/ask", methods=["POST"])
    def ask():
        """
        Main endpoint: query LLM + run full citation verification pipeline.

        Request body: {
            "query": "...",
            "matter_id": 1,
            "use_sample": false  // if true, use pre-loaded sample output
        }
        """
        data = request.get_json()
        query = data.get("query", "")
        matter_id = data.get("matter_id")
        use_sample = data.get("use_sample", False)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Step 0: Run section normalizer on the query
        _, query_alerts = app.section_normalizer.normalize(query)

        # Step 1: Get AI response
        matter = None
        if matter_id:
            matter = LegalMatter.query.get(matter_id)

        if use_sample and matter and matter.sample_output:
            # Use pre-loaded sample output for demo scenarios
            ai_response = {
                "content": matter.sample_output,
                "model": "sample-data",
                "usage": {},
                "success": True,
            }
        elif app.llm_service:
            context = ""
            if matter:
                context = f"Practice: {matter.practice_area} | Court: {matter.court}"
            ai_response = app.llm_service.generate_legal_memo(query, context)
        else:
            return jsonify({"error": "LLM service not configured"}), 503

        if not ai_response.get("success", True):
            error_msg = ai_response.get("content", "LLM error")
            # Provide user-friendly error messages
            if "401" in str(error_msg) or "Unauthorized" in str(error_msg):
                error_msg = "LLM API authentication failed. Please check your API key configuration or use demo mode (select a matter with sample data and check 'Use sample output')."
            elif "429" in str(error_msg):
                error_msg = "LLM API rate limit exceeded. Please wait a moment and try again, or use demo mode."
            return jsonify({"error": error_msg}), 503

        ai_text = ai_response["content"]

        # Step 2: Extract citations
        citations = app.citation_extractor.extract(ai_text)

        # Step 3: Run hallucination pre-filter
        hallucinations = []
        for cit in citations:
            result = app.hallucination_detector.check(
                cit.text, cit.pattern_name, cit.groups
            )
            hallucinations.append(result)

        # Step 4: Verify citations (parallel via Indian Kanoon API)
        if app.citation_verifier and citations:
            verifications = app.citation_verifier.verify_batch(
                citations, hallucinations
            )
        else:
            # No IK API — use pre-filter only, mark rest as UNVERIFIED
            from engines.citation_verifier import VerificationResult
            verifications = []
            for cit, hal in zip(citations, hallucinations):
                if hal.is_hallucinated:
                    verifications.append(VerificationResult(
                        citation=cit.text,
                        normalized=cit.normalized,
                        status="HALLUCINATED",
                        source="pre_filter",
                        reason=hal.reason,
                    ))
                elif hal.is_suspicious:
                    verifications.append(VerificationResult(
                        citation=cit.text,
                        normalized=cit.normalized,
                        status="UNVERIFIED",
                        source="pre_filter_suspicious",
                        reason=hal.reason,
                    ))
                else:
                    verifications.append(VerificationResult(
                        citation=cit.text,
                        normalized=cit.normalized,
                        status="UNVERIFIED",
                        source="no_ik_api",
                        reason="Indian Kanoon API not configured. Connect IK API key to enable live verification.",
                    ))

        # Step 5: Run section normalizer on AI output
        _, output_alerts = app.section_normalizer.normalize(ai_text)

        # Step 6: Annotate
        annotation = app.citation_annotator.annotate(
            ai_text, citations, verifications
        )

        return jsonify({
            "success": True,
            "query": query,
            "ai_response": ai_text,
            "annotated_html": annotation["annotated_html"],
            "report": annotation["report"].to_dict(),
            "citations": annotation["citations"],
            "query_alerts": [a.to_dict() for a in query_alerts],
            "output_alerts": [a.to_dict() for a in output_alerts],
            "model": ai_response.get("model", ""),
            "usage": ai_response.get("usage", {}),
        })

    @app.route("/api/ask-generic", methods=["POST"])
    def ask_generic():
        """
        Generic AI response (no verification) — for side-by-side comparison.

        Request body: {"query": "...", "matter_id": 1, "use_sample": false}
        """
        data = request.get_json()
        query = data.get("query", "")
        matter_id = data.get("matter_id")
        use_sample = data.get("use_sample", False)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # For generic mode, we still use the same sample output or LLM
        matter = None
        if matter_id:
            matter = LegalMatter.query.get(matter_id)

        if use_sample and matter and matter.sample_output:
            ai_response = {
                "content": matter.sample_output,
                "model": "sample-data",
                "usage": {},
                "success": True,
            }
        elif app.llm_service:
            ai_response = app.llm_service.generate_generic(query)
        else:
            return jsonify({"error": "LLM service not configured"}), 503

        return jsonify({
            "success": True,
            "query": query,
            "ai_response": ai_response.get("content", ""),
            "model": ai_response.get("model", ""),
            "usage": ai_response.get("usage", {}),
        })

    @app.route("/api/normalize-sections", methods=["POST"])
    def normalize_sections():
        """
        Normalize section references in text.

        Request body: {"text": "..."}
        """
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        normalized_text, alerts = app.section_normalizer.normalize(text)

        return jsonify({
            "original": text,
            "normalized": normalized_text,
            "alerts": [a.to_dict() for a in alerts],
            "total_alerts": len(alerts),
        })

    @app.route("/api/verify-citation", methods=["POST"])
    def verify_citation():
        """
        Verify a single citation.

        Request body: {"citation": "(2021) 10 SCC 1"}
        """
        data = request.get_json()
        citation_text = data.get("citation", "")

        if not citation_text:
            return jsonify({"error": "Citation text is required"}), 400

        # Extract using our patterns
        from engines.citation_extractor import ExtractedCitation
        citations = app.citation_extractor.extract(citation_text)
        if not citations:
            return jsonify({"error": "Could not parse citation format"}), 400

        cit = citations[0]

        # Run hallucination check
        hal_result = app.hallucination_detector.check(
            cit.text, cit.pattern_name, cit.groups
        )

        # Verify
        if app.citation_verifier:
            result = app.citation_verifier.verify_citation(cit, hal_result)
            return jsonify(result.to_dict())
        else:
            return jsonify({
                "citation": citation_text,
                "status": "UNVERIFIED",
                "reason": "Indian Kanoon API not configured",
            })

    @app.route("/api/stats")
    def stats():
        """Get database statistics."""
        try:
            return jsonify({
                "patterns": CitationPattern.query.filter_by(is_active=True).count(),
                "mappings": SectionMapping.query.filter_by(is_active=True).count(),
                "cached_citations": VerificationCache.query.count(),
                "matters": LegalMatter.query.count(),
                "ik_configured": bool(Config.IK_API_KEY),
                "llm_configured": bool(Config.LLM_API_KEY),
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# Create app instance for gunicorn
application = create_app()

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)