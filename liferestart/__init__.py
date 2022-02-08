from typing import Any, TypedDict, Generator
from collections import defaultdict
from dataclasses import dataclass, field
from .struct.achievement import Achievement, Opportunity
from .struct.event import Event
from .struct.commons import Rarity
from .struct.talent import Talent
from .struct.character import Character
from .data import AGE, TALENT, ACHIEVEMENT, EVENT
from .config import Config, TalentBoostItem, StatRarityItem
from random import Random

class SerializedStatistics(TypedDict):
  inherited_talent: int
  finished_games: int
  talents: list[int]
  events: list[int]
  achievements: list[int]
  unique_seed: int | None
  unique_name: str
  unique_talents: list[int]
  unique_charm: int
  unique_intelligence: int
  unique_strength: int
  unique_money: int

@dataclass
class Statistics:
  inherited_talent: int = -1
  finished_games: int = 0
  talents: set[int] = field(default_factory=set)
  events: set[int] = field(default_factory=set)
  achievements: set[int] = field(default_factory=set)
  unique_seed: int | None = None
  unique_name: str = ""
  unique_talents: list[int] = field(default_factory=list)
  unique_charm: int = 0
  unique_intelligence: int = 0
  unique_strength: int = 0
  unique_money: int = 0

  def serialize(self) -> SerializedStatistics:
    return {
      "inherited_talent": self.inherited_talent,
      "finished_games": self.finished_games,
      "talents": list(self.talents),
      "events": list(self.events),
      "achievements": list(self.achievements),
      "unique_seed": self.unique_seed,
      "unique_name": self.unique_name,
      "unique_talents": self.unique_talents,
      "unique_charm": self.unique_charm,
      "unique_intelligence": self.unique_intelligence,
      "unique_strength": self.unique_strength,
      "unique_money": self.unique_money,
    }

  def deserialize(self, serialized: SerializedStatistics):
    self.inherited_talent = serialized["inherited_talent"]
    self.finished_games = serialized["finished_games"]
    self.talents = set(serialized["talents"])
    self.events = set(serialized["events"])
    self.achievements = set(serialized["achievements"])
    self.unique_seed = serialized["unique_seed"]
    self.unique_name = serialized["unique_name"]
    self.unique_talents = serialized["unique_talents"]
    self.unique_charm = serialized["unique_charm"]
    self.unique_intelligence = serialized["unique_intelligence"]
    self.unique_strength = serialized["unique_strength"]
    self.unique_money = serialized["unique_money"]

@dataclass
class Progress:
  age: int
  talents: list[Talent]
  events: list[tuple[Event, bool]]
  achievements: list[Achievement]
  charm: int
  intelligence: int
  strength: int
  money: int
  spirit: int

@dataclass
class End:
  talents: list[Talent]
  achievements: list[Achievement]
  age: int
  charm: int
  intelligence: int
  strength: int
  money: int
  spirit: int
  overall: int
  summary_age: StatRarityItem
  summary_charm: StatRarityItem
  summary_intelligence: StatRarityItem
  summary_strength: StatRarityItem
  summary_money: StatRarityItem
  summary_spirit: StatRarityItem
  summary_overall: StatRarityItem

class Game:
  config: Config
  statistics: Statistics

  _random: Random

  _raw_talents: list[Talent]
  _talents: list[Talent]
  _charm: int
  _intelligence: int
  _strength: int
  _money: int
  _spirit: int
  _max_charm: int
  _max_intelligence: int
  _max_strength: int
  _max_money: int
  _max_spirit: int
  _min_charm: int
  _min_intelligence: int
  _min_strength: int
  _min_money: int
  _min_spirit: int

  _age: int
  _max_age: int
  _alive: bool
  _talent_executed: dict[int, int]
  _condition_vars: dict[str, Any]

  def __init__(self):
    self.config = Config()
    self.statistics = Statistics()
    self._random = Random()
    self._talents = []
    self._charm = self._max_charm = self._min_charm = 0
    self._intelligence = self._max_intelligence = self._min_intelligence = 0
    self._strength = self._max_strength = self._min_strength = 0
    self._money = self._max_money = self._min_money = 0
    self._spirit = self._max_spirit = self._min_spirit = 0
    self._max_age = self._age = -1
    self._alive = True
    self._talent_executed = defaultdict(int)
    self._condition_vars = {
      "ATLT": self.statistics.talents,
      "AEVT": self.statistics.events,
    }

  def seed(self, seed: int = None) -> int:
    if seed is None:
      self._random.seed(None)
      seed = int.from_bytes(self._random.randbytes(4), "little")
    self._random.seed(seed)
    return seed

  def random_talents(self) -> Generator[list[Talent], None, None]:
    weight = self.config.talent.weight * sum([
      self._get_boost(self.config.talent.boost.finished_games, self.statistics.finished_games), 
      self._get_boost(self.config.talent.boost.achievements, len(self.statistics.achievements)), 
    ], TalentBoostItem.ONE)
    by_rarity: dict[Rarity, list[Talent]] = {rarity: [] for rarity in Rarity}
    for i in (i for i in TALENT.values() if not i.exclusive):
      by_rarity[i.rarity].append(i)
    while True:
      result: list[Talent] = [TALENT[1144], TALENT[1141]]
      while len(result) < self.config.talent.choices:
        rarities, weights = zip(*((rarity, weight.get(rarity)) for rarity in Rarity if by_rarity[rarity]))
        if not len(rarities):
          break
        rarity = self._random.choices(rarities, weights)[0]
        talent = self._random.choice(by_rarity[rarity])
        result.append(talent)
        by_rarity[rarity].remove(talent)
      yield list(result)
      for i in result:
        by_rarity[i.rarity].append(i)

  def _get_boost(self, boosts: list[tuple[int, TalentBoostItem]], value: int) -> TalentBoostItem:
    for min, boost in reversed(boosts):
      if value >= min:
        return boost
    return TalentBoostItem.ZERO

  def set_talents(self, talents: list[Talent]) -> list[Talent]:
    self._raw_talents = talents
    self._talents = talents.copy()
    for i, talent in enumerate(self._raw_talents):
      self.statistics.talents.add(talent.id)
      replacement = self._get_replacement(talent)
      if replacement:
        self.statistics.talents.add(replacement.id)
        self._talents[i] = replacement
    self._condition_vars["TLT"] = {talent.id for talent in self._talents}
    return self._talents

  def _get_replacement(self, current: Talent) -> Talent | None:
    if current.replacement == "rarity":
      by_rarity: dict[int, list[Talent]] = {i: [] for i in current.weights}
      for i in filter(lambda i: not i.exclusive and i.rarity in current.weights and not any(i is j or i.is_imcompatible_with(j) for j in self._talents), TALENT.values()):
        by_rarity[i.rarity].append(i)
      rarities, weights = zip(*((i, v) for i, v in current.weights.items() if by_rarity[i]))
      if rarities:
        rarity = self._random.choices(rarities, weights)[0]
        talent = self._random.choice(by_rarity[rarity])
        return talent
    elif current.replacement == "talent":
      choices, weights = zip(*((TALENT[i], v) for i, v in current.weights.items() if not any(TALENT[i] is j or TALENT[i].is_imcompatible_with(j) for j in self._talents)))
      if choices:
        talent = self._random.choices(choices, weights)[0]
        return talent
    return None

  def get_points(self) -> int:
    return self.config.stat.total + sum(i.points for i in self._talents)

  def set_stats(self, charm: int, intelligence: int, strength: int, money: int):
    self._charm = self._max_charm = self._min_charm =charm
    self._intelligence = self._max_intelligence = self._min_intelligence =intelligence
    self._strength = self._max_strength = self._min_strength =strength
    self._money = self._max_money = self._min_money =money
    self._spirit = self._max_spirit = self._min_spirit =self.config.stat.spirit
    self._update_vars()
  
  def progress(self) -> Generator[Progress, None, None]:
    self._events = set()
    self._condition_vars["EVT"] = self._events
    yield Progress(
      -1,
      self._execute_talents(),
      [],
      self._check_achievements(Opportunity.START),
      self._charm,
      self._intelligence,
      self._strength,
      self._money,
      self._spirit)
    while self._alive:
      self._age += 1
      yield Progress(
        self._age,
        self._execute_talents(),
        self._execute_events(),
        self._check_achievements(Opportunity.TRAJECTORY),
        self._charm,
        self._intelligence,
        self._strength,
        self._money,
        self._spirit)

  def _execute_talents(self) -> list[Talent]:
    talents = []
    for talent in self._talents:
      if self._talent_executed[talent.id] < talent.max_execute and talent.condition(**self._condition_vars):
        self._add_stats(talent.charm, talent.intelligence,talent.strength, talent.money, talent.spirit, talent.random)
        self._update_vars()
        self._talent_executed[talent.id] += 1
        talents.append(talent)
    return talents

  def _execute_events(self) -> list[Event]:
    events = []
    choices, weights = zip(*((EVENT[id], weight) for id, weight in AGE[self._age].items() if not EVENT[id].no_random and not EVENT[id].exclude(**self._condition_vars) and EVENT[id].include(**self._condition_vars)))
    event = self._random.choices(choices, weights)[0]
    while event is not None:
      self._alive = [False, self._alive, True][event.life + 1]
      self._age += event.age
      self._add_stats(event.charm, event.intelligence, event.strength, event.money, event.spirit, 0)
      self._update_vars()
      self.statistics.events.add(event.id)
      self._events.add(event.id)
      next_event = None
      for id, cond in event.branch:
        if cond(**self._condition_vars):
          next_event = EVENT[id]
          break
      events.append((event, next_event is not None))
      event = next_event
    return events

  def _check_achievements(self, opportunity: Opportunity) -> list[Achievement]:
    achievements = []
    for achievement in ACHIEVEMENT.values():
      if achievement.id not in self.statistics.achievements and achievement.opportunity == opportunity and achievement.condition(**self._condition_vars):
        achievements.append(achievement)
        self.statistics.achievements.add(achievement.id)
    return achievements
  
  def _add_stats(self, charm: int, intelligence: int, strength: int, money: int, spirit: int, random: int):
    random_values = [0] * 5
    if random:
      for i in range(5):
        value = self._random.randint(0, random)
        random_values[i] = value
        random -= value
    self._charm += charm + random_values[0]
    self._intelligence += intelligence + random_values[1]
    self._strength += strength + random_values[2]
    self._money += money + random_values[3]
    self._spirit += spirit + random_values[4]

  def _update_vars(self):
    self._max_age = max(self._age, self._max_age)
    self._max_charm = max(self._charm, self._max_charm)
    self._max_intelligence = max(self._intelligence, self._max_intelligence)
    self._max_strength = max(self._strength, self._max_strength)
    self._max_money = max(self._money, self._max_money)
    self._max_spirit = max(self._spirit, self._max_spirit)
    self._min_charm = min(self._charm, self._min_charm)
    self._min_intelligence = min(self._intelligence, self._min_intelligence)
    self._min_strength = min(self._strength, self._min_strength)
    self._min_money = min(self._money, self._min_money)
    self._min_spirit = min(self._spirit, self._min_spirit)
    self._condition_vars.update({
      "AGE": self._age,
      "CHR": self._charm,
      "INT": self._intelligence,
      "STR": self._strength,
      "MNY": self._money,
      "SPR": self._spirit,
      "HAGE": self._max_age,
      "HCHR": self._max_charm,
      "HINT": self._max_intelligence,
      "HSTR": self._max_strength,
      "HMNY": self._max_money,
      "HSPR": self._max_spirit,
      "LCHR": self._min_charm,
      "LINT": self._min_intelligence,
      "LSTR": self._min_strength,
      "LMNY": self._min_money,
      "LSPR": self._min_spirit,
    })

  def end(self) -> End:
    overall = sum([self._max_charm, self._max_intelligence, self._max_strength, self._max_money, self._max_spirit]) * 2 + self._max_age // 2
    self.statistics.finished_games += 1
    self._condition_vars["SUM"] = overall
    self._condition_vars["TMS"] = self.statistics.finished_games
    return End(
      self._raw_talents,
      self._check_achievements(Opportunity.END),
      self._max_age,
      self._max_charm,
      self._max_intelligence,
      self._max_strength,
      self._max_money,
      self._max_spirit,
      overall,
      self.judge(self._max_age, self.config.stat.rarity.age),
      self.judge(self._max_charm, self.config.stat.rarity.charm),
      self.judge(self._max_intelligence, self.config.stat.rarity.intelligence),
      self.judge(self._max_strength, self.config.stat.rarity.strength),
      self.judge(self._max_money, self.config.stat.rarity.money),
      self.judge(self._max_spirit, self.config.stat.rarity.spirit),
      self.judge(overall, self.config.stat.rarity.overall))

  def judge(self, value: int, standard: list[StatRarityItem]) -> StatRarityItem:
    for i in reversed(standard):
      if value > i.min:
        return i
    return standard[0]

  def get_character(self) -> Character | None:
    if self.statistics.unique_seed is None:
      return None
    return Character(
      self.statistics.unique_seed,
      self.statistics.unique_name,
      self.statistics.unique_talents,
      self.statistics.unique_charm,
      self.statistics.unique_intelligence,
      self.statistics.unique_strength,
      self.statistics.unique_money)

  def create_character(self, seed: int | None, name: str = "独一无二的我"):
    random = Random()
    if seed is None:
      seed = int.from_bytes(random.randbytes(4), "little")
    random.seed(seed)
    choices, weights = zip(*self.config.character.talent_count_weight.items())
    talent_count = random.choices(choices, weights)[0]
    talents = random.sample([id for id, talent in TALENT.items() if not talent.exclusive], talent_count)
    choices, weights = zip(*self.config.character.stat_value_weight.items())
    charm, intelligence, strength, money = random.choices(choices, weights, k=4)
    self.statistics.unique_seed = seed
    self.statistics.unique_name = name
    self.statistics.unique_talents = talents
    self.statistics.unique_charm = charm
    self.statistics.unique_intelligence = intelligence
    self.statistics.unique_strength = strength
    self.statistics.unique_money = money
    return Character(seed, name, talents, charm, intelligence, strength, money)

  def set_character(self, character: Character) -> tuple[list[Talent], list[Talent]]:
    talents = [TALENT[id] for id in character.talents]
    real_talents = self.set_talents(talents)
    self.set_stats(character.charm, character.intelligence, character.strength, character.money)
    return talents, real_talents
