import operator
import re
from typing import Any, Callable, Dict, Iterable, List, Set, TypeVar, Union, cast


def equals(a: Any, b: Any) -> bool:
  if isinstance(a, set):
    return b in a
  return a == b


def not_equals(a: Any, b: Any) -> bool:
  if isinstance(a, set):
    return b not in a
  return a != b


def contains(val: Any, seq: Set[Any]):
  if isinstance(val, Iterable):
    return len(seq.intersection(cast(Iterable[Any], val))) > 0
  return val in seq


def not_contains(val: Any, seq: Set[Any]):
  if isinstance(val, Iterable):
    return len(seq.intersection(cast(Iterable[Any], val))) == 0
  return val not in seq


Tree = List[Union[str, "Tree"]]


class Condition:
  COMPARISON_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*(<|<=|==?|>=|>|!=|~=)\s*(-?\d+)\s*$")
  INCLUDE_RE = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9]*)\s*([!\?])\s*\[((?:(?:\s*-?\d+\s*,)*\s*-?\d+(?:\s*,)?)?)\s*\]\s*$")
  OPERATORS: Dict[str, Callable[[Any, Any], bool]] = {
    "<": operator.lt,
    "<=": operator.le,
    "=": equals,
    "==": equals,
    ">=": operator.ge,
    ">": operator.gt,
    "!=": not_equals,
    "~=": not_equals,
    "?": contains,
    "!": not_contains,
  }
  FALSE: "NoopCondition"
  TRUE: "NoopCondition"

  @classmethod
  def parse(cls, data: str) -> "Condition":
    def append(value: Union[str, Tree]):
      cur = tree
      for _ in range(level):
        cur = cur[-1]
      cast(Tree, cur).append(value)
    tree: Tree = []
    level = 0
    for ch in data:
      if ch == '(':
        append([])
        level += 1
      elif ch == ')':
        if level == 0:
          raise ValueError("Unmatched right parentheses")
        level -= 1
      elif ch != " ":
        append(ch)
    if level != 0:
      raise ValueError("Unmatched left parentheses")
    return cls.build(tree)

  @classmethod
  def build(cls, tree: Tree) -> "Condition":
    while len(tree) == 1:
      tree = cast(Tree, tree[0])
    for index, item in enumerate(tree):
      if item == "&":
        return BoolCondition(cls.build(tree[:index]), operator.and_, cls.build(tree[index + 1:]))
      elif item == "|":
        return BoolCondition(cls.build(tree[:index]), operator.or_, cls.build(tree[index + 1:]))
    exp = "".join(cast(List[str], tree))
    if include := cls.INCLUDE_RE.match(exp):
      return VarCondition(
        include[1], cls.OPERATORS[include[2]],
        {int(x) for x in include[3].split(",") if x.strip()})
    elif comparison := cls.COMPARISON_RE.match(exp):
      return VarCondition(comparison[1], cls.OPERATORS[comparison[2]], int(comparison[3]))
    raise ValueError("Unknown condition")

  def __call__(self, **vars: Any) -> bool:
    raise NotImplementedError

  def _pformat(self, indention: str, level: int) -> str:
    return repr(self)

  def pformat(self, indention: str = "  ") -> str:
    return self._pformat(indention, 0)


class NoopCondition(Condition):
  def __init__(self, value: bool) -> None:
    self.value = value

  def __repr__(self) -> str:
    return f"NoopCondition({self.value})"

  def __call__(self, **vars: Any) -> bool:
    return self.value


Condition.FALSE = NoopCondition(False)
Condition.TRUE = NoopCondition(True)


class BoolCondition(Condition):
  def __init__(self, left: Condition, operator: Callable[[bool, bool], bool], right: Condition):
    self.left = left
    self.operator = operator
    self.right = right

  def __call__(self, **vars: Any) -> bool:
    return self.operator(self.left(**vars), self.right(**vars))

  def __repr__(self) -> str:
    return f"BoolCondition({repr(self.left)}, {repr(self.operator)}, {repr(self.right)})"

  def _pformat(self, indention: str, level: int) -> str:
    level += 1
    current = indention * level
    return f'''BoolCondition(
{current}{self.left._pformat(indention, level)},
{current}{repr(self.operator)},
{current}{self.right._pformat(indention, level)})'''


TRight = TypeVar("TRight")


class VarCondition(Condition):
  def __init__(self, key: str, operator: Callable[[Any, TRight], bool], right: TRight) -> None:
    super().__init__()
    self.key = key
    self.operator = operator
    self.right = right

  def __call__(self, **vars: Any) -> bool:
    return self.operator(vars[self.key], self.right)

  def __repr__(self) -> str:
    return f"VarCondition({repr(self.key)}, {repr(self.operator)}, {repr(self.right)})"
