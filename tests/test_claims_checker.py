import importlib.util
from decimal import Decimal
from pathlib import Path

import pytest


@pytest.fixture(scope='module')
def checker():
    spec=importlib.util.spec_from_file_location('claim_checker',Path(__file__).parents[1]/'tools/claims.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_numbers_do_not_accept_numeric_prefixes_of_hashes_or_identifiers(checker):
    text='"123e456abcdef" case_0012 1.5suffix 7e12tag'
    assert checker.numbers(text,prose=False)==[]


def test_numbers_keep_ranges_exponents_and_sentence_punctuation(checker):
    text='0.015–0.037, -2.43e-5; 1.'
    assert [n for _,n in checker.numbers(text,prose=False)]==[
        Decimal('0.015'),Decimal('0.037'),Decimal('-2.43e-5'),Decimal('1')]


def test_extreme_evidence_exponent_does_not_overflow_during_comparison(checker):
    assert not checker.same(Decimal('0.001'),Decimal('3e9999999'))
    assert not checker.same(Decimal('0.001'),Decimal('-3e9999999'))


@pytest.mark.parametrize('canonical,expected', [('115536991713.8623',True),('115400000000',False)])
def test_scientific_display_rounds_to_its_significant_precision(checker,canonical,expected):
    assert checker.same(Decimal('1.16e11'),Decimal(canonical)) is expected
