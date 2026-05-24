from datetime import datetime, timedelta
from extensions import db


class CitationPattern(db.Model):
    __tablename__ = "citation_patterns"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pattern_name = db.Column(db.String(50), nullable=False)
    regex = db.Column(db.String(500), nullable=False)
    format_template = db.Column(db.String(200), nullable=True)
    example = db.Column(db.String(200), nullable=True)
    jurisdiction = db.Column(db.String(100), default="India")
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "pattern_name": self.pattern_name,
            "regex": self.regex,
            "format_template": self.format_template,
            "example": self.example,
            "jurisdiction": self.jurisdiction,
            "is_active": self.is_active,
        }


class SectionMapping(db.Model):
    __tablename__ = "section_mappings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    old_section = db.Column(db.String(50), nullable=False)
    new_section = db.Column(db.String(50), nullable=False)
    old_act = db.Column(db.String(100), nullable=False)
    new_act = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "old_section": self.old_section,
            "new_section": self.new_section,
            "old_act": self.old_act,
            "new_act": self.new_act,
            "is_active": self.is_active,
        }


class VerificationCache(db.Model):
    __tablename__ = "verification_cache"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    citation_text = db.Column(db.String(200), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False)  # VERIFIED, NOT_FOUND, UNVERIFIED
    ik_doc_id = db.Column(db.String(50), nullable=True)
    case_name = db.Column(db.String(500), nullable=True)
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "citation_text": self.citation_text,
            "status": self.status,
            "ik_doc_id": self.ik_doc_id,
            "case_name": self.case_name,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class LegalMatter(db.Model):
    __tablename__ = "legal_matters"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    practice_area = db.Column(db.String(50), nullable=False)
    court = db.Column(db.String(100), nullable=False)
    lawyer_query = db.Column("query", db.Text, nullable=False)
    scenario_type = db.Column(db.String(50), nullable=True)
    sample_output = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "client_name": self.client_name,
            "practice_area": self.practice_area,
            "court": self.court,
            "query": self.lawyer_query,
            "scenario_type": self.scenario_type,
            "has_sample_output": bool(self.sample_output),
        }