"""Tests for Scoremap."""
from src.core import Scoremap
def test_init(): assert Scoremap().get_stats()["ops"] == 0
def test_op(): c = Scoremap(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Scoremap(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Scoremap(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Scoremap(); r = c.process(); assert r["service"] == "scoremap"
