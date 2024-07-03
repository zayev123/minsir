from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import timedelta
import re
import json

Base = declarative_base()

class SQLEmailData(Base):
    __tablename__ = 'emails'
    id = Column(Integer, primary_key=True)
    from_email = Column(String(255))
    to_emails = Column(ARRAY(String(255)), default=list)
    date = Column(DateTime, nullable=True)
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)

    def __repr__(self):
        return f"<EmailData(id={self.id}, subject={self.subject})>"

class SQLEmailAttachment(Base):
    __tablename__ = 'email_attachments'
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=True)
    name = Column(String(255))
    file = Column(String(255))  # Adjusted to store the file path as a string

    email = relationship("SQLEmailData", backref=backref("attachments", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<EmailAttachment(id={self.id}, name={self.name})>"

class SQLUser(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(255), unique=True, nullable=True)
    name = Column(String(100), nullable=True)
    nin = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(100), nullable=True)
    image_url = Column(String(100), nullable=True)
    base64Image = Column(Text, nullable=True)
    imageType = Column(String(10), nullable=True)
    is_admin = Column(Boolean, default=False)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    digi6Code = Column(String(6), nullable=True)
    is6Code_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"

class SQLInsuranceCompany(Base):
    __tablename__ = 'insurance_companies'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    phone = Column(String(255))
    email = Column(String(255))
    address_area = Column(Text)
    rating = Column(String(255))

    def __repr__(self):
        return f"<InsuranceCompany(id={self.id}, name={self.name})>"

class SQLClauseCategory(Base):
    __tablename__ = 'clause_categories'
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ClauseCategory(name={self.name})>"

class SQLAgent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    type = Column(String(255))

    user = relationship("SQLUser", backref=backref("agent", uselist=False))

    def __repr__(self):
        return f"<Agent(id={self.id}, user_id={self.user_id})>"

class SQLClient(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    address_area = Column(Text)
    industry = Column(String(255))
    relation = Column(String(255))
    connected_through = Column(String(255))
    follow_up_frequency_days = Column(Integer)
    notes = Column(Text)

    agent = relationship("SQLAgent", backref=backref("clients", cascade="all, delete-orphan"))
    user = relationship("SQLUser", backref=backref("client", uselist=False))

    def __repr__(self):
        return f"<Client(id={self.id}, agent_id={self.agent_id}, user_id={self.user_id})>"

class SQLClientDocument(Base):
    __tablename__ = 'client_documents'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    risk_id = Column(Integer, ForeignKey('risks.id'), nullable=True)
    name = Column(String(255))
    description = Column(Text, nullable=True)
    file = Column(String(255))

    client = relationship("SQLClient", backref=backref("documents", cascade="all, delete-orphan"))
    risk = relationship("SQLRisk", backref=backref("documents", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClientDocument(id={self.id}, client_id={self.client_id})>"

class SQLClientStatus(Base):
    __tablename__ = 'client_statuses'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    current_status = Column(String(255))
    status_changed_at = Column(DateTime)

    client = relationship("SQLClient", backref=backref("client_statuses", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClientStatus(id={self.id}, client_id={self.client_id})>"

class SQLRisk(Base):
    __tablename__ = 'risks'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    sum_insured = Column(Float)
    type = Column(String(255))
    description = Column(Text, nullable=True)

    client = relationship("SQLClient", backref=backref("risks", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Risk(id={self.id}, client_id={self.client_id})>"

class SQLMeeting(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    insurance_company_id = Column(Integer, ForeignKey('insurance_companies.id'), nullable=True)
    risk_id = Column(Integer, ForeignKey('risks.id'), nullable=True)
    date = Column(DateTime)
    type = Column(String(255))
    mode = Column(String(255))
    primary_issue_type = Column(String(255))
    main_points = Column(Text, nullable=True)

    client = relationship("SQLClient", backref=backref("meetings", cascade="all, delete-orphan"))
    insurance_company = relationship("SQLInsuranceCompany", backref=backref("meetings", cascade="all, delete-orphan"))
    risk = relationship("SQLRisk", backref=backref("meetings", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Meeting(id={self.id}, client_id={self.client_id})>"

class SQLPolicy(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True)
    risk_id = Column(Integer, ForeignKey('risks.id'), nullable=True)
    issue_date = Column(DateTime)
    renewal_date = Column(DateTime)
    number = Column(String(255))
    file = Column(String(255))
    description = Column(Text, nullable=True)
    net_premium = Column(Float)
    commission_type = Column(String(255))
    commission_value = Column(Float)

    risk = relationship("SQLRisk", backref=backref("policies", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Policy(id={self.id}, risk_id={self.risk_id})>"

class SQLPolicyFile(Base):
    __tablename__ = 'policy_files'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    name = Column(String(255))
    file = Column(String(255))  # Adjusted to store the file path as a string

    policy = relationship("SQLPolicy", backref=backref("files", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<PolicyFile(id={self.id}, name={self.name})>"

class SQLPremiumCredited(Base):
    __tablename__ = 'premiums_credited'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    date = Column(DateTime)
    amount = Column(Float)
    payment_proof = Column(String(255))

    policy = relationship("SQLPolicy", backref=backref("crediteds", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<PremiumCredited(id={self.id}, policy_id={self.policy_id})>"

class SQLPremiumCreditedFile(Base):
    __tablename__ = 'premiums_credited_files'
    id = Column(Integer, primary_key=True)
    premium_credited_id = Column(Integer, ForeignKey('premiums_credited.id'), nullable=True)
    name = Column(String(255))
    file = Column(String(255))  # Adjusted to store the file path as a string

    premium_credited = relationship("SQLPremiumCredited", backref=backref("files", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<PremiumCreditedFile(id={self.id}, name={self.name})>"

class SQLInsuranceLine(Base):
    __tablename__ = 'insurance_lines'
    id = Column(Integer, primary_key=True)
    insurance_company_id = Column(Integer, ForeignKey('insurance_companies.id'), nullable=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    date = Column(DateTime)
    policy_number = Column(String(255))
    line_written = Column(Float)
    share_percentage = Column(Float)
    notes = Column(Text, nullable=True)
    net_premium = Column(Float)

    insurance_company = relationship("SQLInsuranceCompany", backref=backref("lines", cascade="all, delete-orphan"))
    policy = relationship("SQLPolicy", backref=backref("lines", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<InsuranceLine(id={self.id}, policy_id={self.policy_id})>"

class SQLPremiumDebited(Base):
    __tablename__ = 'premiums_debited'
    id = Column(Integer, primary_key=True)
    insurance_line_id = Column(Integer, ForeignKey('insurance_lines.id'), nullable=True)
    date = Column(DateTime)
    amount = Column(Float)
    payment_proof = Column(String(255))

    insurance_line = relationship("SQLInsuranceLine", backref=backref("debiteds", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<PremiumDebited(id={self.id}, insurance_line_id={self.insurance_line_id})>"

class SQLQuotation(Base):
    __tablename__ = 'quotations'
    id = Column(Integer, primary_key=True)
    insurance_company_id = Column(Integer, ForeignKey('insurance_companies.id'), nullable=True)
    risk_id = Column(Integer, ForeignKey('risks.id'), nullable=True)
    date = Column(DateTime)
    quoted_rate = Column(Float)
    line_written = Column(Float)
    share_percentage = Column(Float)
    notes = Column(Text, nullable=True)

    insurance_company = relationship("SQLInsuranceCompany", backref=backref("quotations", cascade="all, delete-orphan"))
    risk = relationship("SQLRisk", backref=backref("quotations", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Quotation(id={self.id}, insurance_company_id={self.insurance_company_id})>"

class SQLQuotationClause(Base):
    __tablename__ = 'quotation_clauses'
    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey('quotations.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('clause_categories.id'), nullable=True)
    name = Column(String(255))
    description = Column(Text, nullable=True)

    quotation = relationship("SQLQuotation", backref=backref("qlauses", cascade="all, delete-orphan"))
    category = relationship("SQLClauseCategory", backref=backref("qlauses", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<QuotationClause(id={self.id}, quotation_id={self.quotation_id})>"

class SQLCommissionRealized(Base):
    __tablename__ = 'commissions_realized'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    premium_credited_id = Column(Integer, ForeignKey('premiums_credited.id'), nullable=True)
    amount = Column(Float)

    policy = relationship("SQLPolicy", backref=backref("commissions", cascade="all, delete-orphan"))
    premium_credited = relationship("SQLPremiumCredited", backref=backref("commission", uselist=False))

    def __repr__(self):
        return f"<CommissionRealized(id={self.id}, policy_id={self.policy_id})>"

class SQLEndorsement(Base):
    __tablename__ = 'endorsements'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    date = Column(DateTime)
    new_renewal_date = Column(DateTime)
    number = Column(String(255))
    file = Column(String(255))
    description = Column(Text, nullable=True)
    new_net_premium = Column(Float)

    policy = relationship("SQLPolicy", backref=backref("endorsements", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Endorsement(id={self.id}, policy_id={self.policy_id})>"

class SQLImportantClause(Base):
    __tablename__ = 'important_clauses'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('clause_categories.id'), nullable=True)
    name = Column(String(255))
    description = Column(Text, nullable=True)

    policy = relationship("SQLPolicy", backref=backref("clauses", cascade="all, delete-orphan"))
    category = relationship("SQLClauseCategory", backref=backref("clauses", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ImportantClause(id={self.id}, policy_id={self.policy_id})>"

class SQLClaim(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), nullable=True)
    number = Column(String(255))
    date_of_intimation = Column(DateTime)
    date_of_occurrence = Column(DateTime)
    description = Column(Text, nullable=True)
    cash_call_amount = Column(Float)
    settlement_amount = Column(Float)

    policy = relationship("SQLPolicy", backref=backref("claims", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Claim(id={self.id}, policy_id={self.policy_id})>"

class SQLClaimCredited(Base):
    __tablename__ = 'claims_credited'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey('claims.id'), nullable=True)
    insurance_line_id = Column(Integer, ForeignKey('insurance_lines.id'), nullable=True)
    date = Column(DateTime)
    amount = Column(Float)
    payment_proof = Column(String(255))

    claim = relationship("SQLClaim", backref=backref("crediteds", cascade="all, delete-orphan"))
    insurance_line = relationship("SQLInsuranceLine", backref=backref("crediteds", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClaimCredited(id={self.id}, claim_id={self.claim_id})>"

class SQLClaimDebited(Base):
    __tablename__ = 'claims_debited'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey('claims.id'), nullable=True)
    date = Column(DateTime)
    amount = Column(Float)
    payment_proof = Column(String(255))

    claim = relationship("SQLClaim", backref=backref("debiteds", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClaimDebited(id={self.id}, claim_id={self.claim_id})>"

class SQLClaimDocument(Base):
    __tablename__ = 'claim_documents'
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey('claims.id'), nullable=True)
    name = Column(String(255))
    description = Column(Text, nullable=True)
    file = Column(String(255))

    claim = relationship("SQLClaim", backref=backref("documents", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ClaimDocument(id={self.id}, claim_id={self.claim_id})>"
