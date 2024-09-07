from sqlmodel import Session

from app.services import category_service


class TestExpenseCategory:
    def test_add_category_group(self, db: Session):
        category_group_name: str = 'cash'
        new_category_group = category_service.create_category_group(session=db, name=category_group_name)
        assert new_category_group.name == category_group_name

    def test_add_category(self, db: Session):
        category_name: str = 'cleaner'
        new_category = category_service.create_category(session=db, name=category_name)
        assert new_category.name == category_name
