from brownie import interface
from brownie import \
    UniswapV3FactoryMock, \
    OverlayV1Mothership, \
    OverlayV1OVLCollateral, \
    OverlayV1UniswapV3Market, \
    OverlayToken, \
    chain, \
    accounts
import os
import json


''' OVERLAY TOKEN PARAMETERS '''
TOKEN_TOTAL_SUPPLY = 8000000e18

''' OVERLAY QUANTO DAI/ETH MARKET PARAMETERS '''
AMOUNT_IN = 1e18
PRICE_WINDOW_MACRO = 3600
PRICE_WINDOW_MICRO = 600

K = 343454218783234
PRICE_FRAME_CAP = 5e18
SPREAD = .00573e18

UPDATE_PERIOD = 100
COMPOUND_PERIOD = 600

IMPACT_WINDOW = 600

LAMBDA = .6e18
STATIC_CAP = 370400e18
BRRRR_EXPECTED = 26320e18
BRRRR_WINDOW_MACRO = 2592000
BRRRR_WINDOW_MICRO = 86400

''' OVERLAY QUANTO DAI_ETH MARKET PARAMETERS ON OVL COLLATERAL MANAGER '''
MARGIN_MAINTENANCE = .06e18
MARGIN_REWARD_RATE = .5e18
MAX_LEVERAGE = 100

''' OVERLAY MOTHERSHIP PARAMETERS '''
FEE = .0015e18
FEE_BURN_RATE = .5e18
MARGIN_BURN_RATE = .5e18

''' GENERAL FEED PARAMETERS '''
DAI = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
AXS = "0xBB0E17EF65F82Ab018d8EDd776e8DD940327B28b"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

''' GENERAL ACCOUNTS '''
ALICE = accounts[2]
BOB = accounts[3]
FEED_OWNER = accounts[6]
GOV = accounts[0]
FEE_TO = accounts[4]


def open_json(path):
    '''
    Opens json file.

    Input:
      path [str]:  Path to json file relative to this file location

    Output:
      [dict]:      Json data
    '''
    base = os.path.dirname(os.path.abspath(__file__))
    reflected_path = os.path.join(base, path)

    with open(os.path.normpath(reflected_path)) as f:
        data = json.load(f)

    return data


def open_reflected_json(path):
    '''
    Reads files post-fixed with '_reflected.json' in the feeds directory.

    Input:
      path [str]:  Prefix of file name, e.g. '../feeds/univ3_axs_weth'

    Output:
      [dict]:
         timestamp [Array(int)]:    Timestamp
         one_hr    [Array(float)]:  TODO
         ten_min   [Array(float)]:  TODO
         spot      [Array(float)]:  TODO
         bids      [Array(float)]:  TODO
         asks      [Array(float)]:  TODO
    '''
    return open_json('../feeds/univ3_axs_weth_reflected.json')


def open_raw_uni_framed_json(path):
    '''
    Reads files post-fixed with '_raw_uni_framed.json' in the feeds directory.

    Input:
      path [str]:  Prefix of file name, e.g. '../feeds/univ3_axs_weth'

    Output:
      [dict]:
         observations [Array(Array)]:
           [int]:   block timestamp, uint32
           [int]:   the tick accumulator, i.e. tick * time elapsed since the
                    pool was first initialized, int56
           [int]:   Seconds per liquidity,
                    i.e. seconds elapsed / max(1, liquidity) since the pool was
                    first initialized
           [bool]:  Whether the observation is initialized
         shims        [Array(Array)]:
           [int]:   block timestamp, uint
           [int]:   TODO liquidity, uint128
           [int]:   block timestamp, uint32
           [int]:   block timestamp, uint32
    '''
    return open_json('../feeds/univ3_axs_weth_raw_uni_framed.json')


def deploy_uni_factory():
    '''
    Deploys the UniswapV3FactoryMock on the Feed Owner's behalf.

    Output:
      [Contract]:  UniswapV3FactoryMock contract instance
    '''
    return FEED_OWNER.deploy(UniswapV3FactoryMock)


def deploy_uni_pool(factory, token0, token1, path):
    '''
    Deploys a UniswapV3OracleMock contract instance initialized with token pair
    test data.

    Inputs:
      factory [Contract]:  UniswapV3FactoryMock contract instance
      token0  [str]:       First token contract address in the token pair
      token1  [str]:       Second token contract address in the token pair
      path    [str]:       Path to directory containing mock feed data

    Output:
      [Contract]:          UniswapV3OracleMock contract instance initialized
                           with a token pair
    '''

    # Load test observation and shim data to create UniswapV3OracleMock token
    # pair pool
    data = open_raw_uni_framed_json('../feeds/univ3_axs_weth')

    # Get initial timestamp of test pair to initialize the chain time with
    reflected_data = open_raw_uni_framed_json('../feeds/univ3_axs_weth')
    beginning = reflected_data['timestamp'][0]

    # Creates a pool with the provided token pair
    factory.createPool(token0, token1)

    # Get instance of the IUniswapV3OracleMock contract interface
    IUniswapV3OracleMock = getattr(interface, 'IUniswapV3OracleMock')

    # Gets new UniswapV3OracleMock token pair contract address
    uniswapv3_pool = IUniswapV3OracleMock(factory.allPools(0))

    # Loads test data for the token pair into the UniswapV3OracleMock contract
    uniswapv3_pool.loadObservations(
        data['observations'],
        data['shims'],
        {'from': FEED_OWNER}
    )

    # Start chain at the first timestamp in the *_reflected.json file
    chain.mine(timestamp=beginning)

    # Return instance of UniswapV3OracleMock initialized with a token pair
    return uniswapv3_pool


def deploy_ovl():
    '''
    The Governor role deploys the OverlayToken OVL ERC20 token contract.
    The Governor role mints half the total supply to Alice, and half to Bob.

    Output:
      [Contract]:  OverlayToken contract instance
    '''
    ovl = GOV.deploy(OverlayToken)
    ovl.mint(ALICE, TOKEN_TOTAL_SUPPLY / 2, {"from": GOV})
    ovl.mint(BOB, TOKEN_TOTAL_SUPPLY / 2, {"from": GOV})

    return ovl


def deploy_mothership(ovl):
    '''
    The Governor role deploys the OverlayV1Mothership contract.

    Input:
      ovl [Contract]:         OverlayToken contract instance

    Output:
      mothership [Contract]:  OverlayV1Mothership contract instance
    '''
    # Governor deploys OverlayV1Mothership contract
    mothership = GOV.deploy(OverlayV1Mothership, FEE_TO, FEE, FEE_BURN_RATE,
                            MARGIN_BURN_RATE)

    # Governor registers the OverlayToken OVL ERC20 token contract address with
    # the OverlayV1Mothership contract instance
    mothership.setOVL(ovl, {"from": GOV})

    # Governor grants the OverlayV1Mothership contract address ADMIN_ROLE
    # rights.
    ovl.grantRole(ovl.ADMIN_ROLE(), mothership, {"from": GOV})

    # Return OverlayV1Mothership contract instance
    return mothership


def deploy_market(mothership, feed_depth, feed_market):
    '''
    The Governor deploys a new WETH/WETH market via the
    OverlayV1UniswapV3Market contract, then sets several state variables
    associated with the OverlayV1UniswapV3Market contract instance. The
    Governor role then makes the previously initialized OverlayV1Mothership
    contract aware of the new OverlayV1UniswapV3Market market.

    Inputs:
      mothership  [Contract]:  OverlayV1Mothership contract instance
      feed_depth  [Contract]:  OverlayV3OracleMock contract instance, TODO
      feed_market [Contract]:  OverlayV3OracleMock contract instance, TODO

    Output:
      [Contract]: OverlayV1Mothership contract instance initialized with the
                  new OverlayV1UniswapV3Market contract instance
    '''
    # Governor role deploys OverlayV1UniswapV3Market 
    # Sets a lot of variables inherited from OverlayV1Market,
    # OverlayV1Comptroller, OverlayV1OI, OverlayV1PricePoint. 
    # TODO: unclear in the contract which contract all the variables are
    # defined in. Variables, events, and functions that are only called in one
    # contract should be defined in that contract. Ex: NewPricePoint event
    market = GOV.deploy(OverlayV1UniswapV3Market, mothership, feed_depth,
                        feed_market, WETH, WETH, AMOUNT_IN, PRICE_WINDOW_MACRO,
                        PRICE_WINDOW_MICRO)

    # Governor role sets the funding constant (k), static spread (pbnj),
    # compounding period (compoundingPeriod), market impact (lmbda), open
    # interest cap (staticCap) TODO (brrrrExpected), macro rolling window
    # (brrrrdWindowMacro, and micro rolling window (brrrrdWindowMicro) state
    # variables
    # setEverything function is called only in OverlayV1UniswapV3Market, but is
    # inherited from the OverlayV1Goverance to OverlayV1Market to
    # OverlayV1UniswapV3Market
    market.setEverything(K, PRICE_FRAME_CAP, SPREAD, UPDATE_PERIOD,
                         COMPOUND_PERIOD, IMPACT_WINDOW, LAMBDA, STATIC_CAP,
                         BRRRR_EXPECTED, BRRRR_WINDOW_MACRO,
                         BRRRR_WINDOW_MICRO, {"from": GOV})

    # Governor role makes the OverlayV1Mothership contract instance aware of
    # the newly initialized market
    mothership.initializeMarket(market, {"from": GOV})

    return market


def deploy_ovl_collateral(mothership, market, ovl):
    '''
    The Governor role deploys the OverlayV1OVLCollateral contract.
    '''

    # Governor role deploys the OverlayV1OVLCollateral contract
    ovl_collateral = GOV.deploy(OverlayV1OVLCollateral, "uri", mothership)

    ovl_collateral.setMarketInfo(market, MARGIN_MAINTENANCE,
                                 MARGIN_REWARD_RATE, MAX_LEVERAGE,
                                 {"from": GOV})

    market.addCollateral(ovl_collateral, {"from": GOV})

    mothership.initializeCollateral(ovl_collateral, {"from": GOV})

    ovl.approve(ovl_collateral, 1e50, {"from": ALICE})
    ovl.approve(ovl_collateral, 1e50, {"from": BOB})

    return ovl_collateral


def build_position(collateral_manager, market, collateral, leverage, is_long,
                   taker):

    tx_build = collateral_manager.build(market, collateral, leverage, is_long,
                                        {"from": taker})

    position = tx_build.events['Build']['positionId']
    oi = tx_build.events['Build']['oi']
    debt = tx_build.events['Build']['debt']
    collateral = oi - debt

    return {
        'market': market,
        'collateral_manager': collateral_manager,
        'id': position,
        'oi': oi,
        'collateral': collateral,
        'leverage': leverage,
        'is_long': is_long
    }


def unwind_position(collateral_manager, position_id, position_shares,
                    unwinder):
    collateral_manager.unwind(position_id, position_shares, {"from": unwinder})


def transfer_position_shares(collateral_manager, sender, receiver, position_id,
                             amount):
    collateral_manager.safeTransferFrom(sender, receiver, position_id, amount,
                                        "", {"from": sender})


def transfer_position_shares_batch(collateral_manager, sender, receiver,
                                   position_ids, amounts):
    collateral_manager.safeBatchTransferFrom(sender, receiver, position_ids,
                                             amounts, "", {"from": sender})


def main():

    #  Deploy the UniswapV3FactoryMock on the Feed Owner's behalf
    uni_factory = deploy_uni_factory()

    # Deploy UniswapV3OracleMock contract initialized with an AXS/WETH pair
    feed_depth = deploy_uni_pool(uni_factory, AXS, WETH,
                                 '../feeds/univ3_axs_weth')

    # Deploy UniswapV3OracleMock contract initialized with an DAI/WETH pair
    feed_market = deploy_uni_pool(uni_factory, DAI, WETH,
                                  '../feeds/univ3_dai_weth')

    # Governor deploys the OverlayToken contract for the OVL ERC20 token
    ovl = deploy_ovl()

    # Deploy OverlayV1Mothership contract
    mothership = deploy_mothership(ovl)

    market = deploy_market(mothership, feed_depth, feed_market)

    ovl_collateral = deploy_ovl_collateral(mothership, market, ovl)

    chain.mine(timedelta=market.compoundingPeriod() * 3)

    position_1 = build_position(ovl_collateral, market, 5e18, 1, True, ALICE)

    chain.mine(timedelta=market.updatePeriod() * 2)

    position_2 = build_position(ovl_collateral, market, 5e18, 5, False, ALICE)

    transfer_position_shares(ovl_collateral, ALICE, BOB, position_1['id'],
                             position_1['oi'] / 2)

    unwind_position(ovl_collateral, position_1['id'],
                    ovl_collateral.balanceOf(BOB, position_1['id']), BOB)

    unwind_position(ovl_collateral, position_1['id'],
                    ovl_collateral.balanceOf(ALICE, position_1['id']), ALICE)

    chain.mine(timedelta=UPDATE_PERIOD)

    position_3 = build_position(ovl_collateral, market, 5e18, 1, True, ALICE)

    chain.mine(timedelta=UPDATE_PERIOD)

    position_4 = build_position(ovl_collateral, market, 5e18, 1, True, ALICE)

    chain.mine(timedelta=UPDATE_PERIOD)

    position_5 = build_position(ovl_collateral, market, 5e18, 1, True, ALICE)

    position_ids = [position_3['id'], position_4['id'], position_5['id']]
    amounts = [position_3['oi'], position_4['oi'] / 2, position_5['oi'] / 4]
    transfer_position_shares_batch(ovl_collateral, ALICE, BOB, position_ids,
                                   amounts)

    chain.mine(timedelta=UPDATE_PERIOD)

    position_6 = build_position(ovl_collateral, market, 5e18, 1, True, ALICE)

    chain.mine(timedelta=UPDATE_PERIOD)

    chain.mine(timedelta=COMPOUND_PERIOD)

    with open(".subgraph.test.env", "w") as f:
        f.write('OVL={}\n'.format(ovl))
        f.write('MOTHERSHIP={}\n'.format(mothership))
        f.write('MARKET={}\n'.format(market))
        f.write('OVL_COLLATERAL={}\n'.format(ovl_collateral))
        f.write('ALICE={}\n'.format(ALICE))
        f.write('BOB={}\n'.format(BOB))
        f.write('GOV={}\n'.format(GOV))
        f.write('FEE_TO={}\n'.format(FEE_TO))
        f.write('BOB_POSITION_1={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_1['id'])))
        f.write('BOB_POSITION_2={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_2['id'])))
        f.write('BOB_POSITION_3={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_3['id'])))
        f.write('BOB_POSITION_4={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_4['id'])))
        f.write('BOB_POSITION_5={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_5['id'])))
        f.write('BOB_POSITION_5={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_5['id'])))
        f.write('BOB_POSITION_6={}\n'.format(ovl_collateral.balanceOf(BOB,
                position_6['id'])))
        f.write('ALICE_POSITION_1={}\n'.format(ovl_collateral.balanceOf(ALICE,
                position_1['id'])))
        f.write('ALICE_POSITION_2={}\n'.format(ovl_collateral.balanceOf(ALICE,
                position_2['id'])))
        f.write('ALICE_POSITION_3={}\n'.format(ovl_collateral.balanceOf(ALICE,
                position_3['id'])))
        f.write('ALICE_POSITION_4={}\n'.format(ovl_collateral.balanceOf(ALICE,
                position_4['id'])))
        f.write('ALICE_POSITION_5={}\n'.format(ovl_collateral.balanceOf(ALICE,
                position_5['id'])))
        f.write('ALICE_POSITION_6={}\n'.format(ovl_collateral.balanceOf(ALICE,
                position_6['id'])))
