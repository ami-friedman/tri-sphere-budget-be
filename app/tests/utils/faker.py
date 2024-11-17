import random

from faker import Faker

expense_categories = [
    'Landline Phone',
    'Toras Moshe',
    'Therapy',
    'Cell Phone',
    'Internet',
    'Kupat Cholim',
    'Family Help',
    'Electric Bill',
    'Yeshiva',
]

expense_category_groups = ['Cash', 'Monthly', 'Savings']

income_categories = ['Husband Salary', 'Wife Salary', 'Child Care', 'Stocks']


def random_expense_category_group() -> str:
    return random.choice(expense_category_groups)


def random_expense_category() -> str:
    return random.choice(expense_categories)


def random_income_category() -> str:
    return random.choice(income_categories)


def random_expense_amount() -> float:
    return Faker().pyfloat(min_value=5, max_value=1000, right_digits=2)


def random_income_amount() -> float:
    return Faker().pyfloat(min_value=5, max_value=40000, right_digits=2)
