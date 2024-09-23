from sqlmodel import Session

from app.services import category_service


class TestCategory:
    def test_add_expense_category_group(self, db: Session):
        category_group_name: str = 'Cash'
        new_category_group = category_service.create_expense_category_group(session=db, name=category_group_name)
        assert new_category_group.name == category_group_name

    def test_add_expense_category(self, db: Session):
        category_name: str = 'Cleaner'
        new_category = category_service.create_expense_category(session=db, name=category_name)
        assert new_category.name == category_name

    def test_add_income_category(self, db: Session):
        category_name: str = 'Amichai Salary'
        new_category = category_service.create_income_category(session=db, name=category_name)
        assert new_category.name == category_name
