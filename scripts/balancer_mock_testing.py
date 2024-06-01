import time
from brownie import (
    accounts,
    MockPoolPriceOracle,
    QueryProcessor
)

print("hello")

def main():

    # print("hello")

    # print(MockPoolPriceOracle)

    # qp = accounts[0].deploy(QueryProcessor)

    # mock = accounts[0].deploy(MockPoolPriceOracle)

    # print("mock", MockPoolPriceOracle)

    # struct Sample {
    #     int256 logPairPrice;
    #     int256 accLogPairPrice;
    #     int256 logBptPrice;
    #     int256 accLogBptPrice;
    #     int256 logInvariant;
    #     int256 accLogInvariant;
    #     uint256 timestamp;
    # }

    x = 10000
    y = 10000

    now = int(time.time())

    samples = []

    for i in range(1000):

        spot = x/y
        v = (x ** .5) * (y ** .5)

        print("now ", now)

        # print("spot", spot)
        # print("v   ", v)
        # print("x   ", x)
        # print("y   ", y)

        ai = 1

        # print("x/ai ", x/(x+ai))

        ao = y * (1 - (x/(x+ai)))

        # print("ai  ", ai)
        # print("ao  ", ao)

        x += ai
        y -= ao

        now += 15


