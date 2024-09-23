from sqlmodel import Session

from app.core.models import ExpenseBudget
from app.core.models import IncomeBudget
from app.services import transaction_service


class TestTransaction:
    def test_add_expense_transaction(self, db: Session, expense_budget_item: ExpenseBudget):
        amount = 100
        new_transaction = transaction_service.create_expense_transaction(
            session=db, expense_budget_id=expense_budget_item.id, amount=amount
        )
        assert new_transaction.id is not None
        assert new_transaction.amount == amount
        assert new_transaction.expense_budget_id == expense_budget_item.id

    def test_add_income_transaction(self, db: Session, income_budget_item: IncomeBudget):
        amount = 100
        new_transaction = transaction_service.create_income_transaction(session=db, income_budget_id=income_budget_item.id, amount=amount)
        assert new_transaction.id is not None
        assert new_transaction.amount == amount
        assert new_transaction.income_budget_id == income_budget_item.id
