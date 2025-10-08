from enum import Enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum

from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.auth.models import User  # Avoid circular import


class ExpenseCategory(str, Enum):
    """Predefined expense categories"""
    FOOD = "Food"
    TRANSPORT = "Transport"
    RENT = "Rent"
    GROCERIES = "Groceries"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    SHOPPING = "Shopping"
    SAVINGS = "Savings"
    FOODSTUFF = "Foodstuff"
    TRAVEL = "Travel"
    OTHERS = "Others"


class Expense(Base):
    """Expense model for tracking user expenses"""
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(SQLEnum(ExpenseCategory, name="expense_category_enum", native_enum=False), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship with User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="expenses"
    )

    def __repr__(self) -> str:
        return f"<Expense {self.title} - {self.amount} - {self.category}>"
