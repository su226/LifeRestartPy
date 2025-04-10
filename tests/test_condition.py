import unittest
from typing import Dict, Set, Union

from liferestart.condition import Condition

variables: Dict[str, Union[int, Set[int]]] = {
  "n1": 0,
  "n2": -10,
  "n3": 10,
  "nl1": {1, 2, 3},
  "nl2": {0},
  "nl3": set(),
}


def check(expr: str) -> bool:
  cond = Condition.parse(expr)
  return cond(**variables)


class ConditionTestCase(unittest.TestCase):
  def test_gt(self) -> None:
    self.assertFalse(check('n3>11'))
    self.assertFalse(check('n3>10'))
    self.assertTrue(check('n3>9'))

  def test_gte(self) -> None:
    self.assertFalse(check('n3>=11'))
    self.assertTrue(check('n3>=10'))
    self.assertTrue(check('n3>=9'))

  def test_lt(self) -> None:
    self.assertFalse(check('n3<9'))
    self.assertFalse(check('n3<10'))
    self.assertTrue(check('n3<11'))

  def test_lte(self) -> None:
    self.assertFalse(check('n3<=9'))
    self.assertTrue(check('n3<=10'))
    self.assertTrue(check('n3<=11'))

  def test_eq(self) -> None:
    self.assertFalse(check('n3=9'))
    self.assertTrue(check('n3=10'))
    self.assertFalse(check('n3=11'))
    self.assertFalse(check('nl1=0'))
    self.assertTrue(check('nl1=1'))
    self.assertTrue(check('nl1=2'))
    self.assertTrue(check('nl1=3'))

  def test_ne(self) -> None:
    self.assertTrue(check('n3!=9'))
    self.assertFalse(check('n3!=10'))
    self.assertTrue(check('n3!=11'))
    self.assertTrue(check('nl1!=0'))
    self.assertFalse(check('nl1!=1'))
    self.assertFalse(check('nl1!=2'))
    self.assertFalse(check('nl1!=3'))

  def test_in(self) -> None:
    self.assertFalse(check('n3?[1,2,3]'))
    self.assertTrue(check('n3?[10,11,12]'))
    self.assertTrue(check('nl1?[0,1]'))
    self.assertFalse(check('nl2?[1,2,3]'))
    self.assertFalse(check('nl3?[1,2,3]'))
    self.assertFalse(check('nl2?[]'))
    self.assertFalse(check('nl3?[]'))

  def test_notin(self) -> None:
    self.assertTrue(check('n3![1,2,3]'))
    self.assertFalse(check('n3![10,11,12]'))
    self.assertFalse(check('nl1![0,1]'))
    self.assertTrue(check('nl2![1,2,3]'))
    self.assertTrue(check('nl3![1,2,3]'))
    self.assertTrue(check('nl2![]'))
    self.assertTrue(check('nl3![]'))

  def test_and(self) -> None:
    self.assertTrue(check('n1>=0&n2<0'))
    self.assertFalse(check('n2>0&n3>0'))
    self.assertFalse(check('n2<0&n3<0'))
    self.assertTrue(check('n2<0&n3>0'))
    self.assertTrue(check('n1=0&n2<0&n3>0'))
    self.assertFalse(check('n1=0&n2>0&n3>0'))

  def test_or(self) -> None:
    self.assertTrue(check('n1>=0|n2<0'))
    self.assertTrue(check('n2>0|n3>0'))
    self.assertTrue(check('n2<0|n3<0'))
    self.assertTrue(check('n2<0|n3>0'))
    self.assertFalse(check('n2>0|n3<0'))
    self.assertTrue(check('n1=0|n2<0|n3>0'))
    self.assertTrue(check('n1=0|n2>0|n3>0'))
    self.assertFalse(check('n1!=0|n2>0|n3<0'))

  def test_mix(self) -> None:
    self.assertTrue(check('(n1=0|n2<0|n3>0)&(n1=0|n2>0|n3>0)'))
    self.assertFalse(check('(n1=0|n2<0|n3>0)&(n1!=0|n2>0|n3<0)'))
    self.assertTrue(check('n1=0|n2<0|n3>0&n1!=0|n2>0|n3<0'))
    self.assertTrue(check('(n1>0|n1?[-10,0])&(n2>0|n3![0,1])'))
    self.assertTrue(check('(n1>0&n1?[-10,0])|(n2<0&n3![0,1])'))
