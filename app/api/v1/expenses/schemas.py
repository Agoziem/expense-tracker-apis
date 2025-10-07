import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from app.api.v1.expenses.models import ExpenseCategory


# ===============================================
# Request Schemas
# ===============================================

class ExpenseCreateModel(BaseModel):
    """Schema for creating a new expense"""
    title: str = Field(..., min_length=1, max_length=100, description="Expense title")
    amount: float = Field(..., gt=0, description="Expense amount (must be positive)")
    category: ExpenseCategory = Field(..., description="Expense category")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    expense_date: Optional[datetime] = Field(None, description="Date of expense (defaults to current date)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Grocery Shopping",
                "amount": 45.50,
                "category": "Food",
                "description": "Weekly grocery shopping at the local market",
                "expense_date": "2025-10-07T10:30:00Z"
            }
        }
    )


class ExpenseUpdateModel(BaseModel):
    """Schema for updating an existing expense"""
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="Expense title")
    amount: Optional[float] = Field(None, gt=0, description="Expense amount (must be positive)")
    category: Optional[ExpenseCategory] = Field(None, description="Expense category")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    expense_date: Optional[datetime] = Field(None, description="Date of expense")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Grocery Shopping - Updated",
                "amount": 50.00,
                "category": "Food",
                "description": "Updated grocery shopping expense"
            }
        }
    )


# ===============================================
# Response Schemas
# ===============================================

class ExpenseResponseModel(BaseModel):
    """Schema for expense response"""
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    amount: float
    category: ExpenseCategory
    description: Optional[str] = None
    expense_date: datetime
    created_at: datetime
    updated_at: datetime

    @field_serializer("id", "user_id")
    def serialize_uuid(self, value: uuid.UUID) -> str:
        return str(value)

    @field_serializer("created_at", "updated_at", "expense_date")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()

    model_config = ConfigDict(from_attributes=True)


class ExpenseListResponseModel(BaseModel):
    """Schema for list of expenses with pagination info"""
    expenses: list[ExpenseResponseModel]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class CategorySpendingModel(BaseModel):
    """Schema for spending by category"""
    category: ExpenseCategory
    total_amount: float
    expense_count: int

    @field_serializer("total_amount")
    def serialize_decimal(self, value: float) -> float:
        return round(float(value), 2)

    model_config = ConfigDict(from_attributes=True)


class SpendingSummaryModel(BaseModel):
    """Schema for overall spending summary"""
    total_spending: float
    expense_count: int
    category_breakdown: list[CategorySpendingModel]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_serializer("total_spending")
    def serialize_total(self, value: float) -> float:
        return round(float(value), 2)

    @field_serializer("start_date", "end_date")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    model_config = ConfigDict(from_attributes=True)


class ExpenseStatisticsModel(BaseModel):
    """Schema for expense statistics"""
    period: str  # e.g., "2025-10", "2025-Q4", "2025"
    total_spending: float
    average_expense: float
    expense_count: int
    top_category: Optional[ExpenseCategory] = None
    top_category_amount: Optional[float] = None

    @field_serializer("total_spending", "average_expense")
    def serialize_amounts(self, value: float) -> float:
        return round(float(value), 2)

    @field_serializer("top_category_amount")
    def serialize_top_amount(self, value: Optional[float]) -> Optional[float]:
        return round(float(value), 2) if value else None

    model_config = ConfigDict(from_attributes=True)


# ===============================================
# Chart/Visualization Schemas
# ===============================================

class ChartDataPointModel(BaseModel):
    """Schema for a single data point in chart visualization"""
    period: str = Field(..., description="Period label (e.g., '2025-10', '2025', '2025-10-07')")
    total_amount: float = Field(..., description="Total spending for this period")
    expense_count: int = Field(..., description="Number of expenses in this period")

    @field_serializer("total_amount")
    def serialize_amount(self, value: float) -> float:
        return round(float(value), 2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": "2025-10",
                "total_amount": 1250.75,
                "expense_count": 45
            }
        }
    )


class ChartVisualizationResponseModel(BaseModel):
    """Schema for chart visualization response"""
    period_type: str = Field(..., description="Type of period aggregation (day, week, month, year)")
    data_points: list[ChartDataPointModel] = Field(..., description="List of data points for the chart")
    total_periods: int = Field(..., description="Total number of periods returned")
    total_spending: float = Field(..., description="Sum of all spending across all periods")
    average_spending: float = Field(..., description="Average spending per period")

    @field_serializer("total_spending", "average_spending")
    def serialize_amounts(self, value: float) -> float:
        return round(float(value), 2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period_type": "month",
                "data_points": [
                    {"period": "2024-11", "total_amount": 980.50, "expense_count": 35},
                    {"period": "2024-12", "total_amount": 1150.00, "expense_count": 42},
                    {"period": "2025-01", "total_amount": 1250.75, "expense_count": 45}
                ],
                "total_periods": 3,
                "total_spending": 3381.25,
                "average_spending": 1127.08
            }
        }
    )


class CategoryChartDataModel(BaseModel):
    """Schema for category-based chart data (e.g., pie chart, bar chart)"""
    category: ExpenseCategory = Field(..., description="Expense category")
    total_amount: float = Field(..., description="Total spending in this category")
    expense_count: int = Field(..., description="Number of expenses in this category")
    percentage: float = Field(..., description="Percentage of total spending")

    @field_serializer("total_amount", "percentage")
    def serialize_amounts(self, value: float) -> float:
        return round(float(value), 2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "Food",
                "total_amount": 450.50,
                "expense_count": 15,
                "percentage": 36.04
            }
        }
    )


class CategoryChartResponseModel(BaseModel):
    """Schema for category chart response"""
    categories: list[CategoryChartDataModel] = Field(..., description="List of categories with their data")
    total_spending: float = Field(..., description="Total spending across all categories")
    total_expenses: int = Field(..., description="Total number of expenses")

    @field_serializer("total_spending")
    def serialize_total(self, value: float) -> float:
        return round(float(value), 2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categories": [
                    {"category": "Food", "total_amount": 450.50, "expense_count": 15, "percentage": 36.04},
                    {"category": "Transport", "total_amount": 200.00, "expense_count": 8, "percentage": 16.00}
                ],
                "total_spending": 1250.00,
                "total_expenses": 50
            }
        }
    )


# ===============================================
# Base Response Schemas
# ===============================================

class BaseResponse(BaseModel):
    """Base response schema"""
    message: str
    status: str = "success"


class ExpenseDeleteResponse(BaseResponse):
    """Response for expense deletion"""
    message: str = "Expense deleted successfully"


class ExpenseCreateResponse(BaseResponse):
    """Response for expense creation"""
    message: str = "Expense created successfully"
    expense: ExpenseResponseModel


class ExpenseUpdateResponse(BaseResponse):
    """Response for expense update"""
    message: str = "Expense updated successfully"
    expense: ExpenseResponseModel
