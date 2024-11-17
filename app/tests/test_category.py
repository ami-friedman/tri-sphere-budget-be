from sqlmodel import Session

from app.core.db_models.category_models import ExpCat
from app.core.db_models.category_models import ExpCatCreate
from app.core.db_models.category_models import ExpCatGroup
from app.core.db_models.category_models import ExpCatGroupCreate
from app.core.db_models.category_models import ExpCatGroupPub
from app.core.db_models.category_models import ExpCatPub
from app.core.db_models.category_models import IncCat
from app.core.db_models.category_models import IncCatPub
from app.services import category_service


class TestCategory:
    def test_add_expense_category_group(self, db: Session):
        category_group_name: str = 'Cash'
        new_category_group = category_service.create_expense_category_group(
            session=db, new_category=ExpCatGroupCreate(name=category_group_name)
        )
        assert new_category_group.name == category_group_name

    def test_add_expense_category(self, db: Session):
        category_name: str = 'Cleaner'
        new_category = category_service.create_expense_category(session=db, new_category=ExpCatCreate(name=category_name))
        assert new_category.name == category_name

    def test_add_income_category(self, db: Session):
        category_name: str = 'Amichai Salary'
        new_category = category_service.create_income_category(session=db, name=category_name)
        assert new_category.name == category_name

    def test_update_expense_category_group(self, db: Session, expense_category_group: ExpCatGroup):
        updated = ExpCatGroupPub.model_validate(expense_category_group)
        updated.name = 'New Name'
        updated_category = category_service.update_expense_category_group(session=db, update=updated)
        assert updated_category.name == updated.name

    def test_update_expense_category(self, db: Session, expense_category: ExpCat):
        updated = ExpCatPub.model_validate(expense_category)
        updated.name = 'New Name'
        updated_category = category_service.update_expense_category(session=db, update=updated)
        assert updated_category.name == updated.name

    def test_update_income_category(self, db: Session, income_category: IncCat):
        updated = IncCatPub.model_validate(income_category)
        updated.name = 'New Name'
        updated_category = category_service.update_income_category(session=db, update=updated)
        assert updated_category.name == updated.name
