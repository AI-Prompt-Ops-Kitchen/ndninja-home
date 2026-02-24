import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Standard(Base):
    __tablename__ = "standards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    requirements: Mapped[list["Requirement"]] = relationship(back_populates="standard", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    standard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    clause_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    standard: Mapped["Standard"] = relationship(back_populates="requirements")
    sop_mappings: Mapped[list["RequirementSOPMapping"]] = relationship(back_populates="requirement")

    __table_args__ = (
        UniqueConstraint("standard_id", "clause_number", name="uq_requirement_clause"),
    )


class SOP(Base):
    __tablename__ = "sops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    content_blocks: Mapped[list["ContentBlock"]] = relationship(back_populates="sop", cascade="all, delete-orphan")
    requirement_mappings: Mapped[list["RequirementSOPMapping"]] = relationship(back_populates="sop")
    cross_references_from: Mapped[list["SOPCrossReference"]] = relationship(
        back_populates="source_sop", foreign_keys="SOPCrossReference.source_sop_id"
    )
    cross_references_to: Mapped[list["SOPCrossReference"]] = relationship(
        back_populates="target_sop", foreign_keys="SOPCrossReference.target_sop_id"
    )


class ContentBlock(Base):
    __tablename__ = "content_blocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    section_number: Mapped[str] = mapped_column(String(20), nullable=False)
    section_title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    combo_key: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    block_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sop: Mapped["SOP"] = relationship(back_populates="content_blocks")
    versions: Mapped[list["ContentBlockVersion"]] = relationship(back_populates="content_block", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("content_tier IN ('standard', 'enhanced')", name="ck_content_tier"),
        UniqueConstraint("sop_id", "section_number", "content_tier", "combo_key", name="uq_block_section_tier_combo"),
        Index("ix_content_blocks_combo_key", "combo_key"),
        Index("ix_content_blocks_sop_tier", "sop_id", "content_tier"),
    )


class ContentBlockVersion(Base):
    __tablename__ = "content_block_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_block_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_blocks.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    content_block: Mapped["ContentBlock"] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("content_block_id", "version_number", name="uq_block_version"),
    )


class RequirementSOPMapping(Base):
    __tablename__ = "requirement_sop_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    sop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    section_number: Mapped[str | None] = mapped_column(String(20))
    coverage_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requirement: Mapped["Requirement"] = relationship(back_populates="sop_mappings")
    sop: Mapped["SOP"] = relationship(back_populates="requirement_mappings")

    __table_args__ = (
        UniqueConstraint("requirement_id", "sop_id", name="uq_req_sop_mapping"),
    )


class SOPCrossReference(Base):
    __tablename__ = "sop_cross_references"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_sop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    target_sop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sops.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_sop: Mapped["SOP"] = relationship(back_populates="cross_references_from", foreign_keys=[source_sop_id])
    target_sop: Mapped["SOP"] = relationship(back_populates="cross_references_to", foreign_keys=[target_sop_id])

    __table_args__ = (
        CheckConstraint("source_sop_id != target_sop_id", name="ck_no_self_reference"),
        UniqueConstraint("source_sop_id", "target_sop_id", "relationship_type", name="uq_cross_ref"),
    )


class TemplateStructure(Base):
    __tablename__ = "template_structures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sections: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StandardCombination(Base):
    __tablename__ = "standard_combinations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    combo_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    standard_codes: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
