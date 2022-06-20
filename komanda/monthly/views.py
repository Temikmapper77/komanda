from calendar import monthrange
from datetime import datetime, timedelta
from decimal import ROUND_FLOOR, Decimal

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.views import MONTH_NAMES, MONTHES
from expenses.models import UsualExpenses
from incomes.models import Incomes
from expenses.views import get_sum_constant_expenses
from incomes.views import get_sum_constant_incomes


@login_required
def view_month(request, year, month):
    """Представление страницы месяца с актуальной для него информацией"""

    last_day = monthrange(year, month)[1]

    global START_OF_MONTH
    global END_OF_MONTH

    START_OF_MONTH = datetime(year, month, 1)
    END_OF_MONTH = datetime(year, month, last_day)

    monthly_income = get_sum_special_income().quantize(Decimal("1.00"), ROUND_FLOOR)
    daily_income = get_daily_income().quantize(Decimal("1.00"), ROUND_FLOOR)
    total_expenses = (
        UsualExpenses.objects.filter(date__gte=START_OF_MONTH)
        .filter(date__lte=END_OF_MONTH)
        .aggregate(Sum("amount"))["amount__sum"]
    )
    data = get_balance_for_monthly_table()

    constant_expenses = get_sum_constant_expenses(START_OF_MONTH, END_OF_MONTH)
    constant_incomes = get_sum_total_incomes()

    free_money = get_free_money_in_month()

    return render(
        request,
        "monthly.html",
        {
            "days": data,
            "daily_income": daily_income,
            "monthly_income": monthly_income,
            "total_expenses": total_expenses,
            "year": year,
            "month": month,
            "monthes": MONTHES,
            "cur_month": MONTH_NAMES[month],
            "constant_expenses": constant_expenses,
            "constant_incomes": constant_incomes,
            "free_money": free_money,
        },
    )


@login_required
def monthly_raw_expenses(request, year, month):

    last_day = monthrange(year, month)[1]
    START_OF_MONTH = datetime(year, month, 1)
    END_OF_MONTH = datetime(year, month, last_day)

    data = (
        UsualExpenses.objects.filter(date__gte=START_OF_MONTH)
        .filter(date__lte=END_OF_MONTH)
        .order_by("date")
    )

    return render(
        request,
        "monthly_raw.html",
        {
            "expenses": data,
            "year": year,
            "month": month,
            "monthes": MONTHES,
            "cur_month": MONTH_NAMES[month],
        },
    )


def get_sum_special_income():

    total_monthly_income = Incomes.objects.filter(date=START_OF_MONTH).aggregate(
        Sum("value")
    )
    if total_monthly_income["value__sum"] == None:

        return Decimal(0.00)

    return total_monthly_income["value__sum"]


def get_sum_total_incomes():

    special_incomes = get_sum_special_income()
    monthly_incomes = get_sum_constant_incomes(START_OF_MONTH, END_OF_MONTH)

    return special_incomes + monthly_incomes


def get_daily_income():

    monthly_income = get_free_money_in_month()
    num_of_days = abs((END_OF_MONTH - START_OF_MONTH).days + 1)
    daily_income = Decimal(monthly_income / num_of_days)

    return daily_income


def get_free_money_in_month():

    return get_sum_total_incomes() - get_sum_constant_expenses(
        START_OF_MONTH, END_OF_MONTH
    )


def get_balance_for_monthly_table():

    cur_day = START_OF_MONTH
    data = []
    accumulated = Decimal(0)
    daily_income = get_daily_income()
    accumulated_income = Decimal(0)
    accumulated_balance = Decimal(0)

    while cur_day != END_OF_MONTH + timedelta(1):
        spends_in_day = UsualExpenses.objects.filter(date=cur_day)
        accumulated_income += daily_income
        accumulated_balance += daily_income
        if len(spends_in_day) != 0:
            spends_list = []
            total_amount = Decimal(0)
            for spend in spends_in_day:
                spends_list.append(spend.category.name)
                total_amount += spend.amount
            accumulated += total_amount
            accumulated_balance -= total_amount
            data.append(
                {
                    "date": cur_day.date(),
                    "amount": total_amount,
                    "category": spends_list,
                    "accumulated_balance": accumulated_balance.quantize(
                        Decimal("1.00"), ROUND_FLOOR
                    ),
                }
            )
        else:
            data.append(
                {
                    "date": cur_day.date(),
                    "amount": Decimal(0).quantize(Decimal("1.00"), ROUND_FLOOR),
                    "category": ["No spends"],
                    "accumulated_balance": accumulated_balance.quantize(
                        Decimal("1.00"), ROUND_FLOOR
                    ),
                }
            )
        cur_day += timedelta(1)

    return data


def expenses_chart(request, year, month):

    last_day = monthrange(year, month)[1]

    START_OF_MONTH = datetime(year, month, 1)
    END_OF_MONTH = datetime(year, month, last_day)

    labels = []
    data = []

    for i in range(START_OF_MONTH.day, END_OF_MONTH.day + 1):
        labels.append(i)
        day = START_OF_MONTH + timedelta(i - 1)
        try:
            value = (
                UsualExpenses.objects.filter(date=day)
                .aggregate(Sum("amount"))["amount__sum"]
                .quantize(Decimal("1.00"), ROUND_FLOOR)
            )
            data.append(float(value))
        except AttributeError:
            data.append(None)

    return JsonResponse(
        data={
            "labels": labels,
            "data": data,
        },
        status=200,
    )
