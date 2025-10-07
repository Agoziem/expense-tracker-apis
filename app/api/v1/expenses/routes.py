from uuid import UUID
from datetime import datetime
from typing import Optional, List
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_get_db
from app.api.v1.auth.dependencies import AccessTokenBearer, get_current_user, RoleChecker
from app.api.v1.auth.schemas.schemas import UserModel
from app.api.v1.expenses.models import ExpenseCategory
from app.api.v1.expenses.schemas import (
    ExpenseCreateModel,
    ExpenseUpdateModel,
    ExpenseResponseModel,
    ExpenseListResponseModel,
    ExpenseCreateResponse,
    ExpenseUpdateResponse,
    ExpenseDeleteResponse,
    CategorySpendingModel,
    SpendingSummaryModel,
    ExpenseStatisticsModel,
    ChartVisualizationResponseModel,
    ChartDataPointModel,
    CategoryChartResponseModel,
    CategoryChartDataModel,
    BaseResponse,
)
from app.api.v1.expenses.service import ExpenseService


expense_router = APIRouter()
expense_service = ExpenseService()
access_token_bearer = AccessTokenBearer()


# ===============================================
# Expense CRUD Endpoints
# ===============================================

@expense_router.post(
    "/",
    response_model=ExpenseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense"
)
async def create_expense(
    expense_data: ExpenseCreateModel,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Create a new expense for the authenticated user.
    
    - **title**: Name/title of the expense
    - **amount**: Amount spent (must be positive)
    - **category**: Expense category (Food, Transport, Rent, etc.)
    - **description**: Optional description
    - **expense_date**: Date of expense (defaults to current date if not provided)
    """
    new_expense = await expense_service.create_expense(
        user_id=current_user.id,
        expense_data=expense_data,
        session=session
    )
    
    return ExpenseCreateResponse(
        message="Expense created successfully",
        expense=ExpenseResponseModel.model_validate(new_expense)
    )


@expense_router.get(
    "/",
    response_model=ExpenseListResponseModel,
    summary="Get all expenses with filters"
)
async def get_expenses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[ExpenseCategory] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Filter expenses from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter expenses until this date"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get all expenses for the authenticated user with optional filtering and pagination.
    
    Filters:
    - **category**: Filter by expense category
    - **start_date**: Get expenses from this date onwards
    - **end_date**: Get expenses until this date
    - **search**: Search in expense title and description
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    """
    skip = (page - 1) * page_size
    
    expenses, total_count = await expense_service.get_user_expenses(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=page_size,
        category=category,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
    
    return ExpenseListResponseModel(
        expenses=[ExpenseResponseModel.model_validate(exp) for exp in expenses],
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@expense_router.get(
    "/{expense_id}",
    response_model=ExpenseResponseModel,
    summary="Get a specific expense"
)
async def get_expense(
    expense_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get details of a specific expense by ID.
    
    Returns 404 if expense not found or doesn't belong to the user.
    """
    expense = await expense_service.get_expense_by_id(
        expense_id=expense_id,
        user_id=current_user.id,
        session=session
    )
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return ExpenseResponseModel.model_validate(expense)


@expense_router.patch(
    "/{expense_id}",
    response_model=ExpenseUpdateResponse,
    summary="Update an expense"
)
async def update_expense(
    expense_id: UUID,
    expense_data: ExpenseUpdateModel,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Update an existing expense.
    
    Only provided fields will be updated. Returns 404 if expense not found.
    """
    updated_expense = await expense_service.update_expense(
        expense_id=expense_id,
        user_id=current_user.id,
        expense_data=expense_data,
        session=session
    )
    
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return ExpenseUpdateResponse(
        message="Expense updated successfully",
        expense=ExpenseResponseModel.model_validate(updated_expense)
    )


@expense_router.delete(
    "/{expense_id}",
    response_model=ExpenseDeleteResponse,
    summary="Delete an expense"
)
async def delete_expense(
    expense_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Delete an expense by ID.
    
    Returns 404 if expense not found or doesn't belong to the user.
    """
    deleted = await expense_service.delete_expense(
        expense_id=expense_id,
        user_id=current_user.id,
        session=session
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return ExpenseDeleteResponse(message="Expense deleted successfully")


# ===============================================
# Analytics & Summary Endpoints
# ===============================================

@expense_router.get(
    "/analytics/by-category",
    response_model=List[CategorySpendingModel],
    summary="Get spending by category"
)
async def get_spending_by_category(
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get total spending grouped by category.
    
    Optionally filter by date range.
    Returns categories ordered by total spending (highest first).
    """
    category_spending = await expense_service.get_spending_by_category(
        user_id=current_user.id,
        session=session,
        start_date=start_date,
        end_date=end_date,
    )
    
    return category_spending


@expense_router.get(
    "/analytics/summary",
    response_model=SpendingSummaryModel,
    summary="Get spending summary"
)
async def get_spending_summary(
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get overall spending summary with category breakdown.
    
    Includes:
    - Total spending
    - Number of expenses
    - Breakdown by category
    - Date range (if filtered)
    """
    summary = await expense_service.get_spending_summary(
        user_id=current_user.id,
        session=session,
        start_date=start_date,
        end_date=end_date,
    )
    
    return summary


@expense_router.get(
    "/analytics/monthly/{year}/{month}",
    response_model=ExpenseStatisticsModel,
    summary="Get monthly statistics"
)
async def get_monthly_statistics(
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get statistics for a specific month.
    
    Includes:
    - Total spending
    - Average expense amount
    - Number of expenses
    - Top category and its total
    """
    statistics = await expense_service.get_monthly_statistics(
        user_id=current_user.id,
        year=year,
        month=month,
        session=session,
    )
    
    return ExpenseStatisticsModel(**statistics)


@expense_router.get(
    "/analytics/visualization",
    response_model=ChartVisualizationResponseModel,
    summary="Get data for time-series visualization/charts"
)
async def get_visualization_data(
    period_type: str = Query(
        "month",
        description="Period type: 'day', 'week', 'month', or 'year'"
    ),
    limit: int = Query(
        12,
        ge=1,
        le=100,
        description="Number of periods to return"
    ),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get aggregated expense data for time-series visualization (line charts, area charts).
    
    Returns time-series data showing spending trends over time.
    Perfect for:
    - Line charts showing spending over time
    - Area charts for cumulative spending
    - Trend analysis
    
    - **period_type**: Aggregation period (day, week, month, year)
    - **limit**: Number of periods to return (e.g., last 12 months)
    """
    if period_type not in ["day", "week", "month", "year"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period_type. Must be one of: day, week, month, year"
        )
    
    data_points = await expense_service.get_expenses_for_visualization(
        user_id=current_user.id,
        session=session,
        period_type=period_type,
        limit=limit,
    )
    
    # Calculate totals and averages
    total_spending = sum(point.total_amount for point in data_points)
    average_spending = total_spending / len(data_points) if data_points else 0.0
    
    return ChartVisualizationResponseModel(
        period_type=period_type,
        data_points=data_points,
        total_periods=len(data_points),
        total_spending=total_spending,
        average_spending=average_spending,
    )


@expense_router.get(
    "/analytics/category-chart",
    response_model=CategoryChartResponseModel,
    summary="Get data for category-based visualization/charts"
)
async def get_category_chart_data(
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Get category spending data formatted for charts (pie, donut, bar charts).
    
    Returns category breakdown with percentages, perfect for:
    - Pie charts showing category distribution
    - Donut charts for spending breakdown
    - Horizontal/vertical bar charts
    - Category comparison visualizations
    
    Includes percentage calculations for each category relative to total spending.
    """
    categories = await expense_service.get_category_chart_data(
        user_id=current_user.id,
        session=session,
        start_date=start_date,
        end_date=end_date,
    )
    
    total_spending = sum(cat.total_amount for cat in categories)
    total_expenses = sum(cat.expense_count for cat in categories)
    
    return CategoryChartResponseModel(
        categories=categories,
        total_spending=total_spending,
        total_expenses=total_expenses,
    )


# ===============================================
# Utility Endpoints
# ===============================================

@expense_router.get(
    "/categories/list",
    summary="Get all available categories"
)
async def get_categories():
    """
    Get list of all available expense categories.
    
    Returns all predefined categories that can be used when creating expenses.
    """
    return {
        "categories": [category.value for category in ExpenseCategory],
        "total": len(ExpenseCategory),
    }
