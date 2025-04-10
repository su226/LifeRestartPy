# LifeRestartPy

[人生重开模拟器](https://github.com/VickScarlet/lifeRestart)的Python移植版，目前主要用于我自己的QQ机器人，[IdhagnBot](https://github.com/su226/IdhagnBot)。

*我知道[已经有别人移植过了](https://github.com/cc004/lifeRestart-py)，但我还是自己重新造了一次轮子。*

## 特性

* 可直接使用[原版的数据](https://github.com/VickScarlet/lifeRestart/tree/master/public/data/zh-cn)
* 不依赖第三方库
* 完整的类型标注

## 使用方式

`liferestart.__main__` 模块下有一个简单的终端版本，可直接游玩。

```shell
git clone https://github.com/su226/LifeRestartPy
cd LifeRestartPy
python -m liferestart
```

也可作为依赖库，集成到其他项目中，详见 `liferestart.__main__` 的实现和 [IdhagnBot](https://github.com/su226/IdhagnBot/blob/main/plugins/liferestart.py)。

### 经典模式

```python
from liferestart import Game, Statistics
import json
game = Game()
# game.seed(123456) # 可手动设置种子
seed = game.seed() # 也可使用系统时间播种，并返回种子
# 可以无限抽天赋，也可以像原版游戏一样只抽一次
# 抽天赋的次数也会影响游戏进程
for choices in game.random_talents():
  talents = choices[:3]
  break
# 设置天赋，如果天赋中有“紫色转盘”等随机天赋，可在real_talents中获取
real_talents = game.set_talents(talents)
# 获取可分配的点数
game.get_points()
# 分配点数
game.set_stats(5, 5, 5, 5)
for progress in game.progress():
  # progress中包含发动的天赋、经历的事件和新获得的成就
  print(progress.age) # 如果age为-1则是刚出生
# 获取评价
end = game.end()
# 设置继承的天赋
game.statistics.inherited_talent = talents[0].id
# 成就、事件等也会自动记录到statistics中，可通过serialize保存到字典
data = game.statistics.serialize()
with open("statistics", "w") as f:
  json.dump(data, f)
# 保存的statistics可以通过deserialize读取
game = Game(statistics=Statistics.deserialize(data))
```

### 名人模式

```python
from liferestart import Game
from liferestart.data import CHARACTER
import random
game = Game()
# 抽取名人
characters = random.sample(list(CHARACTER.values()), 3)
character = characters[0]
# 或者创建独一无二的我
# 种子和名字都可以省略
# character = game.create_character(123456, "su226")
# 创建过的角色可以从game.statistics读取
# character = game.statistics.character
# 设置角色，如果天赋中有“紫色转盘”等随机天赋，可在real_talents中获取
talents, real_talents = game.set_character(character)
# 其他用法同上
for progress in game.progress():
  print(progress.age)
end = game.end()
```
