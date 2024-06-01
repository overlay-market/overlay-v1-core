from brownie import (
    accounts,
    interface,
    BalancerQueries
)


account = accounts.load('tester')


def main():

    balancer = account.deploy(
        BalancerQueries,
        "0x0b09dea16768f0799065c475be02919503cb2a35", # 40/60 DAI/ETH
        # "0xa6f548df93de924d73be7d25dc02554c6bd66db5", # 50/50 WBTC/ETH
        # "0xf4c0dd9b82da36c07605df83c8a416f11724d88b", # 80/20 GNO/ETH
        "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    )


    weights = balancer.weights()

    print("weights", weights)

    id = balancer.id()

    print("id", id)

    tokens = balancer.tokens()

    print("tokens", tokens)

    balances = balancer.balances()

    print("balances", balances)

    ten, hour, ten_inv = balancer.twa()

    print("ten", ten)

    print("hour", hour)

    print("ten_inv", ten_inv)

    depth = balancer.depth()

    print("depth", depth)
