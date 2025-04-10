import itertools
import json
import os
import random
import sys
from typing import List, cast

from . import Game, GeneratedCharacter, Statistics
from .data import ACHIEVEMENT, CHARACTER, EVENT, TALENT
from .struct.character import Character
from .struct.commons import Rarity
from .struct.talent import Talent

CHR_WIDTHS = [
  (126, 1),
  (159, 0),
  (687, 1),
  (710, 0),
  (711, 1),
  (727, 0),
  (733, 1),
  (879, 0),
  (1154, 1),
  (1161, 0),
  (4347, 1),
  (4447, 2),
  (7467, 1),
  (7521, 0),
  (8369, 1),
  (8426, 0),
  (9000, 1),
  (9002, 2),
  (11021, 1),
  (12350, 2),
  (12351, 1),
  (12438, 2),
  (12442, 0),
  (19893, 2),
  (19967, 1),
  (55203, 2),
  (63743, 1),
  (64106, 2),
  (65039, 1),
  (65059, 0),
  (65131, 2),
  (65279, 1),
  (65376, 2),
  (65500, 1),
  (65510, 2),
  (120831, 1),
  (262141, 2),
  (1114109, 1),
]


def str_width(s: str) -> int:
  if len(s) > 1:
    return sum(str_width(c) for c in s)
  o = ord(s)
  if o == 0xe or o == 0xf:
    return 0
  for num, wid in CHR_WIDTHS:
    if o <= num:
      return wid
  return 1


def str_pad(s: str, width: int, chr: str = " ") -> str:
  return s + chr * max(width - str_width(s), 0)


def format_float(value: float) -> str:
  # 处理唯一一个属性有浮点数的角色祖冲之
  return f"{value:.7f}".rstrip(".0") or "0"


FORMAT_RESET = "\033[0m"
FORMAT_LIGHT_BLUE = "\033[94m"
FORMAT_LIGHT_PURPLE = "\033[95m"
FORMAT_LIGHT_YELLOW = "\033[93m"
RARITY_FORMATS = {
  Rarity.COMMON: FORMAT_RESET,
  Rarity.UNCOMMON: FORMAT_LIGHT_BLUE,
  Rarity.RARE: FORMAT_LIGHT_PURPLE,
  Rarity.LEGENDARY: FORMAT_LIGHT_YELLOW,
}


def format_rarity(rarity: Rarity, s: str) -> str:
  return RARITY_FORMATS[rarity] + s + FORMAT_RESET


def print_statistics(game: Game) -> None:
  print("---- 成就与统计 ----")
  for achievement in ACHIEVEMENT.values():
    granted = achievement.id in game.statistics.achievements
    hidden = achievement.hidden and not granted
    symbol = "✓" if granted else "✗"
    name = "???" if hidden else achievement.name
    description = "隐藏成就" if hidden else achievement.description
    print(f"{symbol} {format_rarity(achievement.rarity, str_pad(name, 14))} - {description}")
  finished_games = game.judge(game.statistics.finished_games, game.config.stat.rarity.finished_games)
  print(f"重开次数: {game.statistics.finished_games:3} - {format_rarity(finished_games.rarity, game.config.stat.rarity.messages[finished_games.message_id])}")
  achievements = game.judge(len(game.statistics.achievements), game.config.stat.rarity.achievements)
  print(f"成就数量: {len(game.statistics.achievements):3} - {format_rarity(achievements.rarity, game.config.stat.rarity.messages[achievements.message_id])}")
  events_value = int(len(game.statistics.events) / len(EVENT) * 100)
  events = game.judge(events_value, game.config.stat.rarity.event_percentage)
  print(f"事件收集率: {format_rarity(events.rarity, f'{events_value:3}%')}")
  talents_value = int(len(game.statistics.talents) / len(TALENT) * 100)
  talents = game.judge(talents_value, game.config.stat.rarity.talent_percentage)
  print(f"天赋游玩率: {format_rarity(talents.rarity, f'{talents_value:3}%')}")


def print_talents(talents: List[Talent], real_talents: List[Talent]) -> None:
  print("---- 当前天赋 ----")
  for talent, real in zip(talents, real_talents):
    print(f"{format_rarity(talent.rarity, str_pad(talent.name, 15))} - {talent.description}")
    if talent is not real:
      print(f"-> {format_rarity(real.rarity, str_pad(real.name, 12))} - {real.description}")


def run(game: Game) -> None:
  for progress in game.progress():
    print("---- 出生 ----" if progress.age == -1 else f"---- {progress.age}岁 ----")
    print(f"颜值 {format_float(progress.charm)} 智力 {format_float(progress.intelligence)} 体质 {format_float(progress.strength)} 家境 {format_float(progress.money)} 快乐 {progress.spirit}")
    for talent in progress.talents:
      print(format_rarity(talent.rarity, f"天赋 {talent.name} 发动: {talent.description}"))
    for event, has_next in progress.events:
      segments = [f"{event.event}"]
      if not has_next and event.post:
        segments.append(f"{event.post}")
      print(format_rarity(event.rarity, "\n".join(segments)))
    for achievement in progress.achievements:
      print(format_rarity(achievement.rarity, f"获得成就 {achievement.name}: {achievement.description}"))
    input()

  end = game.end()
  print("---- 总结 ----")
  for achievement in end.achievements:
    print(format_rarity(achievement.rarity, f"获得成就 {achievement.name}: {achievement.description}"))
  print(f"颜值: {format_float(end.charm)} - {format_rarity(end.summary_charm.rarity, game.config.stat.rarity.messages[end.summary_charm.message_id])}")
  print(f"智力: {format_float(end.intelligence)} - {format_rarity(end.summary_intelligence.rarity, game.config.stat.rarity.messages[end.summary_intelligence.message_id])}")
  print(f"体质: {format_float(end.strength)} - {format_rarity(end.summary_strength.rarity, game.config.stat.rarity.messages[end.summary_strength.message_id])}")
  print(f"家境: {format_float(end.money)} - {format_rarity(end.summary_money.rarity, game.config.stat.rarity.messages[end.summary_money.message_id])}")
  print(f"快乐: {end.spirit} - {format_rarity(end.summary_spirit.rarity, game.config.stat.rarity.messages[end.summary_spirit.message_id])}")
  print(f"享年: {end.age} - {format_rarity(end.summary_age.rarity, game.config.stat.rarity.messages[end.summary_age.message_id])}")
  print(f"总评: {end.overall} - {format_rarity(end.summary_overall.rarity, game.config.stat.rarity.messages[end.summary_overall.message_id])}")


def print_character(i: int, ch: Character) -> None:
  print(f"{i}: {ch.name}")
  print(f"颜值 {format_float(ch.charm)} 智力 {format_float(ch.intelligence)} 体质 {format_float(ch.strength)} 家境 {format_float(ch.money)}")
  for j in ch.talents:
    talent = TALENT[j]
    print(f"- {format_rarity(talent.rarity, str_pad(talent.name, 12))} - {talent.description}")


def run_character(game: Game) -> None:
  print("---- 选择角色 ----")
  while True:
    choices: list[Character] = random.sample(list(CHARACTER.values()), 3)
    if game.statistics.character is None:
      print("0: 独一无二的我 (未创建)")
    else:
      print_character(0, game.statistics.character)
    for i, ch in enumerate(choices, 1):
      print_character(i, ch)
    while True:
      choice = input("请选择, 留空换一批: ")
      try:
        choice = int(choice) if choice else None
      except ValueError:
        print("只能输入数字")
        continue
      if choice is None:
        break
      if choice < 0 or choice > 3:
        print("请输入 0 和 3 之间的数字")
        continue
      break
    if choice is None:
      continue
    if choice == 0 and game.statistics.character is None:
      print("---- 创建独一无二的我 ----")
      print("创建之后将不能修改")
      while True:
        seed = input("输入种子, 留空自动生成, cancel 放弃: ")
        if seed == "cancel":
          break
        try:
          seed = int(seed) if seed else None
        except ValueError:
          print("种子必须是整数")
        else:
          name = input("输入名字, 也可以留空: ") or "独一无二的我"
          ch = game.create_character(seed, name)
          print(f"种子: {ch.seed}")
          break
    if choice == 0:
      character = cast(GeneratedCharacter, game.statistics.character)
    else:
      character = choices[choice - 1]
    break
  talents, real_talents = game.set_character(character)
  set_seed(game)
  print_talents(talents, real_talents)
  run(game)


def random_alloc(game: Game, total: int) -> List[int]:
  result = [game.config.stat.min] * 4
  for _ in range(total):
    result[random.choice([i for i, v in enumerate(result) if v < game.config.stat.max])] += 1
  return result


def run_classic(game: Game) -> None:
  set_seed(game)
  print("---- 选择天赋 ----")
  inherited = None if game.statistics.inherited_talent == -1 else TALENT[game.statistics.inherited_talent]
  talents: List[Talent] = []
  for choices in game.random_talents():
    min_choice = 1
    if inherited:
      min_choice = 0
      choices.insert(0, inherited)
    for i, talent in enumerate(choices, min_choice):
      print(f"{i:2}: {format_rarity(talent.rarity, str_pad(talent.name, 12))} - {talent.description}")
    while True:
      raw = input(f"选择 {game.config.talent.limit} 个天赋, 第一个天赋将会被继承, 留空换一批: ").split()
      try:
        selected = [int(i) for i in raw]
      except ValueError:
        print("只能输入数字")
        continue
      if any(i < min_choice or i > len(choices) for i in selected):
        print(f"只能输入 {min_choice} 和 {len(choices)} 之间的数字")
        continue
      errors: List[str] = []
      talents = [choices[i - min_choice] for i in selected]
      for i, j in itertools.combinations(talents, 2):
        if i.is_imcompatible_with(j):
          errors.append(f"不能同时选择 {format_rarity(i.rarity, i.name)} 和 {format_rarity(j.rarity, j.name)}")
        elif i is j:
          errors.append("每个天赋只能选择一次")
      if len(talents) > 0 and len(talents) != game.config.talent.limit:
        errors.append(f"只能选择恰好 {game.config.talent.limit} 个天赋")
      if not len(errors):
        break
      print("\n".join(errors))
    if len(talents):
      break
  game.statistics.inherited_talent = talents[0].id
  real_talents = game.set_talents(talents)
  print_talents(talents, real_talents)
  print("---- 分配属性 ----")
  points = game.get_points()
  print(f"可分配 {points} 点属性")
  while True:
    raw = input("请输入 4 个数字分配颜值、智力、体质和家境, 留空为随机: ")
    try:
      stats = list(int(i) for i in raw.split())
    except ValueError:
      print("只能输入数字")
      continue
    if len(stats) == 0:
      stats = random_alloc(game, points)
      break
    if len(stats) != 4:
      print("请输入恰好 4 个数字")
      continue
    if any(x < game.config.stat.min or x > game.config.stat.max for x in stats):
      print(f"属性必须在 {game.config.stat.min} 和 {game.config.stat.max} 之间")
      continue
    if sum(stats) != points:
      print(f"必须刚好分配完 {points} 点属性")
      continue
    break
  game.set_stats(*stats)
  run(game)


def set_seed(game: Game) -> None:
  print("---- 开始游戏 ----")
  while True:
    seed = input("输入种子, 留空自动生成: ")
    try:
      seed = int(seed) if seed else None
      break
    except ValueError:
      print("种子必须是整数")
  game_seed = game.seed(seed)
  print(f"本局种子: {game_seed}")


def main():
  if os.path.exists("statistics.json"):
    with open("statistics.json") as f:
      statistics = Statistics.deserialize(json.load(f))
  else:
    statistics = Statistics()
  game = Game(statistics=statistics)

  print("---- 人生重开模拟器 ----")
  print("1: 经典模式")
  print("2: 名人模式")
  print("3: 成就与统计")
  while True:
    try:
      mode = int(input("请选择: "))
    except ValueError:
      print("请输入数字")
      continue
    if mode < 1 or mode > 3:
      print("请输入 1 到 3 之间的数字")
      continue
    break

  if mode == 3:
    print_statistics(game)
    sys.exit()
  elif mode == 2:
    run_character(game)
  else:
    run_classic(game)

  with open("statistics.json", "w") as f:
    json.dump(game.statistics.serialize(), f)

if __name__ == "__main__":
  main()
