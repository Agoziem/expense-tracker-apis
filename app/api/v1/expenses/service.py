from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple
from decimal import Decimal

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, func, and_, extract, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_get_db
from app.api.v1.expenses.models import Expense, ExpenseCategory
from app.api.v1.expenses.schemas import (
    ExpenseCreateModel,
    ExpenseUpdateModel,
    CategorySpendingModel,
    SpendingSummaryModel,
    ChartDataPointModel,
    CategoryChartDataModel,
)


class ExpenseService:
    """Service class for expense-related business logic"""

    async def create_expense(
        self,
        user_id: UUID,
        expense_data: ExpenseCreateModel,
        session: AsyncSession = Depends(async_get_db)
    ) -> Expense:
        """Create a new expense for a user"""
        expense_dict = expense_data.model_dump(exclude_unset=True)
        
        # If expense_date is not provided, use current datetime
        if "expense_date" not in expense_dict or expense_dict["expense_date"] is None:
            expense_dict["expense_date"] = datetime.now()
        
        new_expense = Expense(
            user_id=user_id,
            **expense_dict
        )
        
        session.add(new_expense)
        await session.commit()
        await session.refresh(new_expense)
        return new_expense

    async def get_expense_by_id(
        self,
        expense_id: UUID,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db)
    ) -> Optional[Expense]:
        """Get a specific expense by ID, ensuring it belongs to the user"""
        statement = select(Expense).where(
            and_(
                Expense.id == expense_id,
                Expense.user_id == user_id
            )
        )
        result = await session.execute(statement)
        return result.scalars().first()

    async def get_user_expenses(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db),
        skip: int = 0,
        limit: int = 100,
        category: Optional[ExpenseCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Expense], int]:
        """
        Get all expenses for a user with optional filtering and pagination
        Returns tuple of (expenses, total_count)
        """
        # Base query
        statement = select(Expense).where(Expense.user_id == user_id)
        count_statement = select(func.count(Expense.id)).where(Expense.user_id == user_id)

        # Apply filters
        if category:
            statement = statement.where(Expense.category == category)
            count_statement = count_statement.where(Expense.category == category)

        if start_date:
            statement = statement.where(Expense.expense_date >= start_date)
            count_statement = count_statement.where(Expense.expense_date >= start_date)

        if end_date:
            statement = statement.where(Expense.expense_date <= end_date)
            count_statement = count_statement.where(Expense.expense_date <= end_date)

        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                Expense.title.ilike(search_pattern) | 
                Expense.description.ilike(search_pattern)
            )
            count_statement = count_statement.where(
                Expense.title.ilike(search_pattern) | 
                Expense.description.ilike(search_pattern)
            )

        # Get total count
        count_result = await session.execute(count_statement)
        total_count = count_result.scalar() or 0

        # Apply ordering and pagination
        statement = statement.order_by(desc(Expense.expense_date))
        statement = statement.offset(skip).limit(limit)

        # Execute query
        result = await session.execute(statement)
        expenses = list(result.scalars().all())

        return expenses, total_count

    async def update_expense(
        self,
        expense_id: UUID,
        user_id: UUID,
        expense_data: ExpenseUpdateModel,
        session: AsyncSession = Depends(async_get_db)
    ) -> Optional[Expense]:
        """Update an existing expense"""
        expense = await self.get_expense_by_id(expense_id, user_id, session)
        
        if not expense:
            return None

        # Update only provided fields
        update_data = expense_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(expense, key, value)

        await session.commit()
        await session.refresh(expense)
        return expense

    async def delete_expense(
        self,
        expense_id: UUID,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db)
    ) -> bool:
        """Delete an expense"""
        expense = await self.get_expense_by_id(expense_id, user_id, session)
        
        if not expense:
            return False

        await session.delete(expense)
        await session.commit()
        return True

    async def get_spending_by_category(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[CategorySpendingModel]:
        """Get total spending grouped by category"""
        statement = select(
            Expense.category,
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("expense_count")
        ).where(Expense.user_id == user_id)

        # Apply date filters
        if start_date:
            statement = statement.where(Expense.expense_date >= start_date)
        if end_date:
            statement = statement.where(Expense.expense_date <= end_date)

        statement = statement.group_by(Expense.category).order_by(desc("total_amount"))

        result = await session.execute(statement)
        rows = result.all()

        return [
            CategorySpendingModel(
                category=row.category,
                total_amount=float(row.total_amount),
                expense_count=row.expense_count
            )
            for row in rows
        ]

    async def get_spending_summary(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> SpendingSummaryModel:
        """Get overall spending summary with category breakdown"""
        # Get total spending
        total_statement = select(
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("expense_count")
        ).where(Expense.user_id == user_id)

        if start_date:
            total_statement = total_statement.where(Expense.expense_date >= start_date)
        if end_date:
            total_statement = total_statement.where(Expense.expense_date <= end_date)

        total_result = await session.execute(total_statement)
        total_row = total_result.first()

        total_spending = float(total_row.total) if total_row and total_row.total else 0.0
        expense_count = total_row.expense_count if total_row and total_row.expense_count else 0

        # Get category breakdown
        category_breakdown = await self.get_spending_by_category(
            user_id, session, start_date, end_date
        )

        return SpendingSummaryModel(
            total_spending=total_spending,
            expense_count=expense_count,
            category_breakdown=category_breakdown,
            start_date=start_date,
            end_date=end_date,
        )

    # =============================================================
    # Expense Statictics for Chart
    # =============================================================
    
    async def get_monthly_statistics(
        self,
        user_id: UUID,
        year: int,
        month: int,
        session: AsyncSession = Depends(async_get_db),
    ) -> Dict:
        """Get statistics for a specific month"""
        statement = select(
            func.sum(Expense.amount).label("total"),
            func.avg(Expense.amount).label("average"),
            func.count(Expense.id).label("expense_count")
        ).where(
            and_(
                Expense.user_id == user_id,
                extract("year", Expense.expense_date) == year,
                extract("month", Expense.expense_date) == month
            )
        )

        result = await session.execute(statement)
        row = result.first()

        # Get top category
        category_statement = select(
            Expense.category,
            func.sum(Expense.amount).label("category_total")
        ).where(
            and_(
                Expense.user_id == user_id,
                extract("year", Expense.expense_date) == year,
                extract("month", Expense.expense_date) == month
            )
        ).group_by(Expense.category).order_by(desc("category_total")).limit(1)

        category_result = await session.execute(category_statement)
        top_category_row = category_result.first()

        return {
            "period": f"{year}-{month:02d}",
            "total_spending": float(row.total) if row and row.total else 0.0,
            "average_expense": float(row.average) if row and row.average else 0.0,
            "expense_count": row.expense_count if row and row.expense_count else 0,
            "top_category": top_category_row.category if top_category_row else None,
            "top_category_amount": float(top_category_row.category_total) if top_category_row else None,
        }

    async def get_expenses_for_visualization(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db),
        period_type: str = "month",  # "week", "month", "year"
        limit: int = 12,
    ) -> List[ChartDataPointModel]:
        """
        Get aggregated expense data for visualization/charts
        Returns data points for the specified period
        """
        if period_type == "month":
            # Get monthly data for the last N months
            statement = select(
                extract("year", Expense.expense_date).label("year"),
                extract("month", Expense.expense_date).label("month"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("expense_count")
            ).where(
                Expense.user_id == user_id
            ).group_by("year", "month").order_by(desc("year"), desc("month")).limit(limit)

        elif period_type == "year":
            # Get yearly data
            statement = select(
                extract("year", Expense.expense_date).label("year"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("expense_count")
            ).where(
                Expense.user_id == user_id
            ).group_by("year").order_by(desc("year")).limit(limit)

        else:  # week or day
            # Get daily data for the last N days
            statement = select(
                func.date(Expense.expense_date).label("date"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.id).label("expense_count")
            ).where(
                Expense.user_id == user_id
            ).group_by("date").order_by(desc("date")).limit(limit)

        result = await session.execute(statement)
        rows = result.all()

        data_points = []
        for row in reversed(rows):  # Reverse to get chronological order
            if period_type == "month":
                data_points.append(
                    ChartDataPointModel(
                        period=f"{int(row.year)}-{int(row.month):02d}",
                        total_amount=float(row.total) if row.total else 0.0,
                        expense_count=row.expense_count if row.expense_count else 0
                    )
                )
            elif period_type == "year":
                data_points.append(
                    ChartDataPointModel(
                        period=str(int(row.year)),
                        total_amount=float(row.total) if row.total else 0.0,
                        expense_count=row.expense_count if row.expense_count else 0
                    )
                )
            else:
                data_points.append(
                    ChartDataPointModel(
                        period=str(row.date),
                        total_amount=float(row.total) if row.total else 0.0,
                        expense_count=row.expense_count if row.expense_count else 0
                    )
                )

        return data_points

    async def get_category_chart_data(
        self,
        user_id: UUID,
        session: AsyncSession = Depends(async_get_db),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[CategoryChartDataModel]:
        """
        Get category data formatted for charts (with percentages)
        Perfect for pie charts, donut charts, and bar charts
        """
        # Get spending by category
        category_spending = await self.get_spending_by_category(
            user_id, session, start_date, end_date
        )

        # Calculate total for percentage calculation
        total_spending = sum(cat.total_amount for cat in category_spending)

        # Create chart data with percentages
        chart_data = []
        for category in category_spending:
            percentage = (category.total_amount / total_spending * 100) if total_spending > 0 else 0.0
            chart_data.append(
                CategoryChartDataModel(
                    category=category.category,
                    total_amount=category.total_amount,
                    expense_count=category.expense_count,
                    percentage=percentage
                )
            )

        return chart_data
