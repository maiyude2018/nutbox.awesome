# nutbox.awesome
基于steem区块链的彩票系统。

- main.py 区块监控主程序
- set.json 设定文件
- tickets.db 日志数据库
- winner.py 开奖程序

## 用法：
- 1、购买彩票：向nutbow.awesome转账任意整数STEEM，memo：buy，即可购买。购买成功会自动回复彩卷号码
- 2、查询自己的彩卷号：任意位置留言!tickets
- 3、查询开奖情况：任意位置回复!season+期号，可以获取当前期数的中奖号码。例：!season1

## 奖励设置（暂定）：
- 一等奖一名：总奖池50%奖金
- 二等奖一名：总奖池20%奖金
- 三等奖两名：各总奖池5%奖金

10%奖金进入下期，10%奖金作为开发资金池。


## 开奖办法：
取第一章彩卷号的区块+86400区块作为开奖区块号。
取开奖区块号所有交易的哈希相加，作为开奖哈希。

然后把开奖哈希放入winner.py程序运行，得出中奖者。

哈希随机不可控，中间结果可查询回溯。


抽奖代码：其中min_n为最小奖卷号，默认为0。max_n为最大奖卷号，视销售情况而定。num_win为抽奖数量。block_num为开奖区块号。
```
def get_winners(min_n, max_n, num_win, block_num):
    data = {"jsonrpc": "2.0", "method": "condenser_api.get_block", "params": [block_num], "id": 1}
    r = requests.post(url=nodes, json=data)
    rjson = r.json()
    transaction_ids = rjson["result"]['transaction_ids']
    hash = ""
    for i in transaction_ids:
        hash += i
    print(hash)

    res = hash
    winners = set()
    while len(winners) < num_win:
        res = hashlib.sha256(res.encode('utf-8')).hexdigest()
        winners.add(int(res, 16) % (max_n-min_n+1) + min_n)
    return winners

```
