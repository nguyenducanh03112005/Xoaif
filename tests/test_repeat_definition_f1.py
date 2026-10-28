from datetime import date

from scripts.analyze_repeat_definition_f1 import summarize


def _order(day: date, sequence: int) -> dict:
    return {"customer_key": "c1", "is_gift": False, "date": day,
            "order_sequence": sequence}


def test_same_day_order_is_not_repeat_event_but_later_date_is():
    rows = [
        _order(date(2024, 4, 1), 0),
        _order(date(2024, 4, 1), 1),
        _order(date(2024, 4, 20), 2),
    ]
    result = summarize(rows)
    assert result["same_day_second_customers_all_dev"] == 1
    assert result["strict_repeat_customers_all_dev"] == 1


def test_repeat_metric_bootstraps_reproducibly():
    rows = [_order(date(2024, 4, 1), 0), _order(date(2024, 4, 15), 1)]
    left = summarize(rows)
    right = summarize(rows)
    assert left["km"] == right["km"]
