from sqlmodel import Session

from app.core.db_models.category_models import ExpenseCategory
from app.core.db_models.category_models import ExpenseCategoryCreate
from app.core.db_models.category_models import ExpenseCategoryGroup
from app.core.db_models.category_models import ExpenseCategoryGroupCreate
from app.core.db_models.category_models import IncomeCategory
from app.services import category_service


class TestCategory:
    def test_add_expense_category_group(self, db: Session):
        category_group_name: str = 'Cash'
        new_category_group = category_service.create_expense_category_group(
            session=db, new_category=ExpenseCategoryGroupCreate(name=category_group_name)
        )
        assert new_category_group.name == category_group_name

    def test_add_expense_category(self, db: Session):
        category_name: str = 'Cleaner'
        new_category = category_service.create_expense_category(session=db, new_category=ExpenseCategoryCreate(name=category_name))
        assert new_category.name == category_name

    def test_add_income_category(self, db: Session):
        category_name: str = 'Amichai Salary'
        new_category = category_service.create_income_category(session=db, name=category_name)
        assert new_category.name == category_name

    def test_update_expense_category_group(self, db: Session, expense_category_group: ExpenseCategoryGroup):
        new_name = 'New Name'
        updated_category = category_service.update_expense_category_group(session=db, group_id=expense_category_group.id, name=new_name)
        assert updated_category.name == new_name

    def test_update_expense_category(self, db: Session, expense_category: ExpenseCategory):
        new_name = 'New Name'
        updated_category = category_service.update_expense_category(session=db, category_id=expense_category.id, name=new_name)
        assert updated_category.name == new_name

    def test_update_income_category(self, db: Session, income_category: IncomeCategory):
        new_name = 'New Name'
        updated_category = category_service.update_income_category(session=db, category_id=income_category.id, name=new_name)
        assert updated_category.name == new_name
