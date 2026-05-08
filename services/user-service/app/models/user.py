import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    TRADER = "TRADER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    PARTNER = "PARTNER"
    POWER_USER = "POWER_USER"
    SUPER_USER = "SUPER_USER"


class TradingMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class KYCStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class KYCDocumentType(str, enum.Enum):
    PASSPORT = "PASSPORT"
    EMIRATES_ID = "EMIRATES_ID"
    SELFIE = "SELFIE"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS"


class KYCDocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class LanguagePreference(str, enum.Enum):
    EN = "en"
    AR = "ar"


# ── ORM Models ────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SAEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.STUDENT,
        server_default=UserRole.STUDENT.value,
    )
    trading_mode = Column(
        SAEnum(TradingMode, name="trading_mode"),
        nullable=False,
        default=TradingMode.SIMULATION,
        server_default=TradingMode.SIMULATION.value,
    )
    kyc_status = Column(
        SAEnum(KYCStatus, name="kyc_status"),
        nullable=False,
        default=KYCStatus.PENDING,
        server_default=KYCStatus.PENDING.value,
    )
    language_preference = Column(
        SAEnum(LanguagePreference, name="language_preference"),
        nullable=False,
        default=LanguagePreference.EN,
        server_default=LanguagePreference.EN.value,
    )
    # Partner referral — set to the PARTNER user who referred this account
    referred_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    # Sprint 20 / 21 platform controls
    live_trading_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    max_leverage_override = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="noload",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    kyc_documents = relationship(
        "KYCDocument",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    # Users referred by this partner account
    referred_users = relationship(
        "User",
        primaryjoin="User.referred_by == User.id",
        foreign_keys="User.referred_by",
        lazy="noload",
    )
    partner_permissions = relationship(
        "PartnerPermission",
        back_populates="partner",
        cascade="all, delete-orphan",
        lazy="noload",
        foreign_keys="PartnerPermission.partner_user_id",
    )
    commissions_earned = relationship(
        "CommissionLedger",
        back_populates="partner",
        cascade="all, delete-orphan",
        lazy="noload",
        foreign_keys="CommissionLedger.partner_user_id",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="profile")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    # Python attribute 'extra_data' maps to DB column 'metadata'
    extra_data = Column("metadata", JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    user = relationship("User", back_populates="audit_logs")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type = Column(
        SAEnum(KYCDocumentType, name="kyc_document_type"),
        nullable=False,
    )
    file_reference = Column(String(500), nullable=False)
    verification_status = Column(
        SAEnum(KYCDocumentStatus, name="kyc_document_status"),
        nullable=False,
        default=KYCDocumentStatus.PENDING,
        server_default=KYCDocumentStatus.PENDING.value,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="kyc_documents")


class PartnerPermission(Base):
    """
    Stores discretionary permissions granted by Super Admin to a PARTNER account.
    Example permission: 'VIEW_REFERRED_TRADE_HISTORY'
    """
    __tablename__ = "partner_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission = Column(String(100), nullable=False)
    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    partner = relationship(
        "User",
        back_populates="partner_permissions",
        foreign_keys=[partner_user_id],
    )


class CommissionLedger(Base):
    """
    Immutable log of brokerage income share entries for PARTNER accounts.
    Entries are created by admin/worker when a referred user generates revenue.
    """
    __tablename__ = "commission_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Reference to the trade/fill that generated this commission (external to user-service)
    trade_reference = Column(String(255), nullable=True)
    commission_amount = Column(Numeric(28, 8), nullable=False)
    commission_rate = Column(Numeric(10, 6), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    partner = relationship(
        "User",
        back_populates="commissions_earned",
        foreign_keys=[partner_user_id],
    )
