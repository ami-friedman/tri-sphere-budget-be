from sqlmodel import Session

from app.core.db_models.budget_models import ExpBudget
from app.core.db_models.budget_models import IncBudget
from app.core.db_models.transaction_models import ExpTransactionCreate
from app.core.db_models.transaction_models import IncTransactionCreate
from app.services import transaction_service


class TestTransaction:
    def test_add_expense_transaction(self, db: Session, expense_budget_item: ExpBudget):
        amount = 100

        new_transaction = transaction_service.create_expense_transaction(
            session=db, new_expense=ExpTransactionCreate(expense_budget_id=expense_budget_item.id, amount=amount)
        )
        assert new_transaction.id is not None
        assert new_transaction.amount == amount
        assert new_transaction.expense_budget_id == expense_budget_item.id

    def test_add_income_transaction(self, db: Session, income_budget_item: IncBudget):
        amount = 100
        new_transaction = transaction_service.create_income_transaction(
            session=db, new_income=IncTransactionCreate(income_budget_id=income_budget_item.id, amount=amount)
        )
        assert new_transaction.id is not None
        assert new_transaction.amount == amount
        assert new_transaction.income_budget_id == income_budget_item.id
