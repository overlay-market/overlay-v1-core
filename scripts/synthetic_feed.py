import json
import os
import brownie
from brownie import (
    accounts,
    chain,
    interface
)

from datetime import datetime
import time

def main():

    cur_tick = -80000
    cum_tick = 0

    delta = 15

    now = int(time.time())

    print(time.time())

    feed = {
        'description': 'A synthesized price feed for our UniswapV3 oracle mock.',
        'observations': [],
        'shims': [],

    }
    obs = []
    shims = []

    for i in range(1000):

        now += delta

        cum_tick += cur_tick * delta

        ob = [now, cum_tick, 0, True]

        shim = [now, 8870817966431808984, cur_tick, i]

        obs.append(ob)
        shims.append(shim)
        feed['observations'].append(ob)
        feed['shims'].append(shim)

        cur_tick -= 1

    print(feed)

    factory = accounts[0].deploy(getattr(brownie, 'UniswapV3FactoryMock'))

    print("deployed")

    IUniswapV3OracleMock = getattr(interface, 'IUniswapV3OracleMock')

    zeroth = "0x0000000000000000000000000000000000000000"

    factory.createPool(zeroth, zeroth)

    print("created")

    mock = IUniswapV3OracleMock(factory.allPools(0))

    print("got mock")

    mock.loadObservations(obs, shims, {'from': accounts[0]})

    print("loaded observation")

    spots = []
    
    now = int(time.time())
    start = now + 15
    for x in range(950):
        
        chain.mine(timestamp=start + (x*delta))

        ob = mock.observe([1, 0])

        spot = 1.0001 ** (ob[0][1]-ob[0][0])

        print("spot", spot)

        spots.append(spot)

    base = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(base, '../feeds/synthetic.json')
    
    with open(os.path.normpath(path), 'w+') as f:
        json.dump(feed, f)
