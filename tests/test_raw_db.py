"""Smoke tests on the raw database.

These don't test any modelling, there isn't any yet. They check the file I
copied in is the file I think it is, so that when something breaks in phase 1
I can rule this out first.
"""

import sqlite3

import pytest

from src.features import RAW_DB, SEATS_TOTAL, SEATS_POLLED_2026, connect


def test_database_is_there():
    assert RAW_DB.exists(), f"expected the database at {RAW_DB}"


def test_tables_i_expect():
    with connect() as con:
        found = {
            row[0]
            for row in con.execute(
                "select name from sqlite_master where type='table'"
            )
        }
    expected = {
        "constituencies",
        "results",
        "winners",
        "electorate",
        "nota",
        "seat_status",
        "name_flags",
    }
    assert expected <= found, f"missing: {sorted(expected - found)}"


def test_294_constituencies():
    with connect() as con:
        (n,) = con.execute("select count(*) from constituencies").fetchone()
    assert n == SEATS_TOTAL


def test_one_seat_short_in_2026():
    """Falta didn't poll, so 2026 has 293 winners against 2021's 294."""
    with connect() as con:
        counts = dict(
            con.execute("select year, count(*) from winners group by year")
        )
    assert counts[2021] == SEATS_TOTAL
    assert counts[2026] == SEATS_POLLED_2026


def test_falta_is_the_missing_seat():
    """Pinning the ac_no because I got it wrong from memory once already."""
    with connect() as con:
        rows = con.execute(
            "select ac_no from seat_status where result_status = 'no_poll'"
        ).fetchall()
    assert rows == [(144,)]


def test_raw_database_is_read_only():
    """src.connect opens read-only. Guard against anyone quietly changing it."""
    with connect() as con:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("create table scribble (x int)")
