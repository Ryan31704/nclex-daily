import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        Index(
            "uq_topics_parent_slug",
            "slug",
            unique=True,
            postgresql_where=text("parent_topic_id IS NULL"),
            sqlite_where=text("parent_topic_id IS NULL"),
        ),
        Index(
            "uq_topics_child_parent_slug",
            "parent_topic_id",
            "slug",
            unique=True,
            postgresql_where=text("parent_topic_id IS NOT NULL"),
            sqlite_where=text("parent_topic_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    parent: Mapped["Topic | None"] = relationship(
        "Topic",
        back_populates="children",
        remote_side="Topic.id",
    )
    children: Mapped[list["Topic"]] = relationship(
        "Topic",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Topic.display_order",
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="topic",
    )


from app.models.question import Question  # noqa: E402
