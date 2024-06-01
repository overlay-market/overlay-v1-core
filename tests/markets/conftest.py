import pytest
import brownie
import os
import json
from brownie import (
    OverlayTokenNew,
    ComptrollerShim,
    chain,
    interface,
    UniTest
)

TOKEN_DECIMALS = 18
TOKEN_TOTAL_SUPPLY = 8000000e18
OI_CAP = 800000
AMOUNT_IN = 1
PRICE_POINTS_START = 50
PRICE_POINTS_END = 100

PRICE_WINDOW_MACRO = 3600
PRICE_WINDOW_MICRO = 600

COMPOUND_PERIOD = 600

IMPACT_WINDOW = PRICE_WINDOW_MICRO

LAMBDA = .6e18
STATIC_CAP = 370400e18
BRRRR_EXPECTED = 26320e18
BRRRR_WINDOW_MACRO = 2592000
BRRRR_WINDOW_MICRO = 86400

WRAPPED_ETH_ADDR = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture(scope="module")
def gov(accounts):
    '''
    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for the Governor role
    '''
    yield accounts[0]


@pytest.fixture(scope="module")
def rewards(accounts):
    '''
    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for the rewards
    '''
    yield accounts[1]


@pytest.fixture(scope="module")
def alice(accounts):
    '''
    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for Alice the trader
    '''
    yield accounts[2]


@pytest.fixture(scope="module")
def bob(accounts):
    '''
    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for Bob the trader
    '''
    yield accounts[3]


@pytest.fixture(scope="module")
def fees(accounts):
    '''
    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for the fees
    '''
    yield accounts[4]


@pytest.fixture(scope="module", params=["IOverlayV1Market"])
def notamarket(accounts):
    '''
    We need this because we cannot mutate the market object in tests (mutated
    state is inherited by all future tests :HORROR:) And we cannot copy or
    deepcopy contract objects owing to RecursionError: maximum recursion depth
    exceeded while calling a Python object.

    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for market object in
                 tests
    '''
    yield accounts[5]


@pytest.fixture(scope="module")
def feed_owner(accounts):
    '''
    Input:
      accounts [Accounts]: List of brownie provided eth account addresses

    Output:
      [Account]: Brownie provided eth account address for feed owner
    '''
    yield accounts[6]


@pytest.fixture(scope="module")
def create_token(gov, alice, bob):
    '''
    Instantiates an OverlyTokenNew token contract.
    Inputs:
      gov   [EthAddress]:  Governor role account address
      alice [EthAddress]:  Trader Alice account address
      bob   [EthAddress]:  Trader Bob account address

    Outputs:
      Produces a create_token function generator
    '''
    sup = TOKEN_TOTAL_SUPPLY

    def create_token(supply=sup):
        tok = gov.deploy(OverlayTokenNew)
        tok.mint(gov, supply, {"from": gov})
        tok.transfer(bob, supply/2, {"from": gov})
        tok.transfer(alice, supply/2, {"from": gov})
        return tok

    yield create_token


@pytest.fixture(scope="module")
def token(create_token):
    yield create_token()


@pytest.fixture(scope="module")
def feed_infos():

    base = os.path.dirname(os.path.abspath(__file__))
    market_path = '../../feeds/univ3_dai_weth'
    depth_path = '../../feeds/univ3_axs_weth'

    raw_uni_framed_market_path = os.path.join(base,
                                              market_path +
                                              '_raw_uni_framed.json')
    reflected_market_path = os.path.join(base, market_path + '_reflected.json')
    raw_uni_framed_depth_path = os.path.join(base,
                                             depth_path +
                                             '_raw_uni_framed.json')
    reflected_depth_path = os.path.join(base, depth_path + '_reflected.json')

    with open(os.path.normpath(raw_uni_framed_market_path)) as f:
        market_mock = json.load(f)
    with open(os.path.normpath(reflected_market_path)) as f:
        market_reflection = json.load(f)
    with open(os.path.normpath(raw_uni_framed_depth_path)) as f:
        depth_mock = json.load(f)
    with open(os.path.normpath(reflected_depth_path)) as f:
        depth_reflection = json.load(f)

    class FeedSmuggler:
        def __init__(self, market_info, depth_info):
            self.market_info = market_info
            self.depth_info = depth_info

        def market_info(self):
            return self.market_info

        def depth_info(self):
            return self.depth_info

    yield FeedSmuggler(
        (market_mock['observations'], market_mock['shims'], market_reflection),
        (depth_mock['observations'], depth_mock['shims'], depth_reflection)
    )


def get_uni_feeds(feed_owner, feed_info):

    market_obs = feed_info.market_info[0]
    market_shims = feed_info.market_info[1]
    depth_obs = feed_info.depth_info[0]
    depth_shims = feed_info.depth_info[1]

    UniswapV3MockFactory = getattr(brownie, 'UniswapV3FactoryMock')
    IUniswapV3OracleMock = getattr(interface, 'IUniswapV3OracleMock')

    uniswapv3_factory = feed_owner.deploy(UniswapV3MockFactory)

    market_token0 = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    market_token1 = WRAPPED_ETH_ADDR
    depth_token0 = "0xBB0E17EF65F82Ab018d8EDd776e8DD940327B28b"
    depth_token1 = WRAPPED_ETH_ADDR

    # TODO: place token0 and token1 into the json
    uniswapv3_factory.createPool(market_token0, market_token1)
    uniswapv3_factory.createPool(depth_token0, depth_token1)

    market_mock = IUniswapV3OracleMock(uniswapv3_factory.allPools(0))
    depth_mock = IUniswapV3OracleMock(uniswapv3_factory.allPools(1))

    market_mock.loadObservations(
        market_obs, market_shims, {'from': feed_owner})

    depth_mock.loadObservations(depth_obs, depth_shims, {'from': feed_owner})

    chain.mine(timestamp=feed_info.market_info[2]['timestamp'][0])

    return uniswapv3_factory.address, market_mock.address, depth_mock.address, market_token1   # noqa: E501


@pytest.fixture(scope="module")
def comptroller(gov, feed_infos, token, feed_owner):

    _, marketFeed, depthFeed, quote = get_uni_feeds(feed_owner, feed_infos)

    comptroller = gov.deploy(ComptrollerShim, LAMBDA, STATIC_CAP,
                             BRRRR_EXPECTED, BRRRR_WINDOW_MACRO,
                             BRRRR_WINDOW_MICRO, PRICE_WINDOW_MACRO,
                             PRICE_WINDOW_MICRO, marketFeed, depthFeed,
                             token.address, WRAPPED_ETH_ADDR)

    yield comptroller


@pytest.fixture(
    scope="module",
    params=[
        ("OverlayV1Mothership", [
            .0015e18,      # fee
            .5e18,         # fee burn rate
            .5e18,         # margin burn rate
        ],
         "OverlayV1UniswapV3MarketZeroLambdaShim", [
            1e18,                # amount in
            PRICE_WINDOW_MACRO,  # macro window
            PRICE_WINDOW_MICRO,  # micro price window
            5e18,                # price frame cap
            343454218783234,     # k
            .00573e18,           # spread
            COMPOUND_PERIOD,     # compound period
            0,                   # lambda
            OI_CAP*1e18,         # oi cap
            BRRRR_EXPECTED,      # brrrr expected
            BRRRR_WINDOW_MACRO,  # brrrr window macro - roller window
            BRRRR_WINDOW_MICRO   # brrrr window micro - accumulator window
         ],
         "OverlayV1OVLCollateral", [
             .0015e18,           # fee
             100,                # max leverage
             .5e18,              # margin reward rate
             .06e18,             # margin maintenance
         ],
         get_uni_feeds,
        ),
    ])
def create_mothership(token, feed_infos, fees, alice, bob, gov, feed_owner,
                      request):
    '''
    Deploys and sets up OverlayV1Mothership contract for the market related
    tests.

    Inputs:
      token       [ProjectContract]: OverlayToken contract instance
      feed_infos  []:                TODO
      alice       [EthAddress]:      Alice's account
      bob         [EthAddress]:      Bob's account
      gov         [EthAddress]:      Governor Role account
      feed_owner  [EthAddress]:      TODO
      request     [arr]:             Parameters passed in the pytest fixture
        request.params:
          ovlms_name [str]: OverlayV1Mothership contract name
          ovlms_args [arr]: OverlayV1Mothership initialization parameters
                   [int]:   fee [uint]
                   [int]:   fee burn rate [uint]
                   [int]:   margin burn rate [uint]
          ovlm_name [str]:  OverlayV1UniswapV3MarketZeroLambdaShim contract
                            name
          ovlm_args:
                   [int]:   amount in [uint128]
                   [int]:   macro price window [uint256]
                   [int]:   micro price window [uint256]
                   [int]:   micro price window [uint256]
                   [int]:   k constant
                   [int]:   spread
                   [int]:   compound period, 600s = 10 min
                   [int]:   lambda, 0
                   [int]:   OI cap
                   [int]:   Expected brrrr
                   [int]:   Roller window - brrrr window macro
                   [int]:   Accumulator window - brrrr window micro
          ovlc_name [str]:  OverlayV1OVLCollateral contract name
          ovlc_args:
                   [int]:   fee                [uint]
                   [int]:   max leverage       [uint]
                   [int]:   margin reward rate [uint]
                   [int]:   maintenance margin [uint]
          get_uni_feeds []: TODO

    Output:
      create_mothership generator produces an instantiated Mothership contract
      when called
    '''
    # Set OverlayV1Mothership, OverlayV1UniswapV3Market, and
    # OverlayV1OVLCollateral contract constructor arguments from pytest fixture
    ovlms_name, ovlms_args, ovlm_name, ovlm_args, ovlc_name, ovlc_args, get_feed = request.param  # noqa: E501

    ovlms = getattr(brownie, ovlms_name)
    ovlm = getattr(brownie, ovlm_name)
    ovlc = getattr(brownie, ovlc_name)

    # Prepend fee as first argument to OverlayV1Mothership contract constructor
    ovlms_args_w_feeto = [fees] + ovlms_args

    def create_mothership(
        tok=token,
        ovlms_type=ovlms,
        ovlms_args=ovlms_args_w_feeto,
        ovlm_type=ovlm,
        ovlm_args=ovlm_args,
        ovlc_type=ovlc,
        ovlc_args=ovlc_args,
        fd_getter=get_feed
    ):
        # Calls get_uni_feeds to return Uniswap V3 test feed info
        _, market_feed, ovl_feed, quote = fd_getter(feed_owner, feed_infos)

        # Account that deploys the OverlayV1Mothership contract takes on the
        # Governor Role
        mothership = gov.deploy(ovlms_type, *ovlms_args)

        # Governor grants the OverlayV1Mothership contract with the Admin Role
        # in the OVL ERC20 contract
        tok.grantRole(tok.ADMIN_ROLE(), mothership, {"from": gov})

        # Governor sets the ovl state variable as the tok OVL ERC20 token
        # address
        mothership.setOVL(tok, {'from': gov})

        # Governor deploys the OverlayV1UniswapV3MarketZeroLambdaShim contract
        # which takes in the OverlayV1Mothership address, the mock depth and
        # mock market addresses, the market token 1 address and eth address
        # that make up the pair, and the first four variables in ovlm_args
        market = gov.deploy(ovlm_type, mothership, ovl_feed, market_feed,
                            quote, WRAPPED_ETH_ADDR, *ovlm_args[:4])

        # Governor sets important variables in the operation of the market
        # contract, including k, spread, compound period, and the Comptroller
        # parameters
        # TODO: should remove setEverything function in sol and call each
        # function explicitly
        market.setEverything(*ovlm_args[4:], {"from": gov})

        # Governor makes call to mothership contract, making it aware of the
        # new market contract
        # TODO: check that call fails if market contract already accounted for
        mothership.initializeMarket(market, {"from": gov})

        # Governor deploys the OverlayV1OVLCollateral contract which takes a
        # URI and the OverlayV1Mothership contract address, creates a
        # Positions.Info struct containing default position parameter values
        # and appends the struct to the positions array to track them
        ovl_collateral = gov.deploy(ovlc_type, "our_uri", mothership)

        # Governor sets the market information which includes the maintenance
        # fee, max leverage, margin reward rate, margin
        ovl_collateral.addMarket(market, *ovlc_args, {"from": gov})

        print("OVLC ARGS", ovlc_args)

        # Governor makes call to mothership contract, making it aware of the
        # new collateral contract
        # TODO: check that call fails if collateral contract already accounted
        # for
        mothership.initializeCollateral(ovl_collateral, {"from": gov})

        # Governor makes call to market contract, making it aware of the new
        # collateral contract
        # TODO: must mothership.initializeCollateral and market.addCollateral
        # be called in this order? Is there some check that can be made to
        # ensure initializeCollateral is called?
        market.addCollateral(ovl_collateral, {'from': gov})

        # Alice approves the collateral contract to spend from her balance
        tok.approve(ovl_collateral, 1e50, {"from": alice})

        # Bob approves the collateral contract to spend from his balance
        tok.approve(ovl_collateral, 1e50, {"from": bob})

        return mothership

    yield create_mothership


@pytest.fixture(scope="module")
def start_time():
    '''
    Output:
        [int]: current chain time from brownie plus 200 seconds
    '''
    return chain.time() + 200


@pytest.fixture(scope="module")
def mothership(create_mothership):
    yield create_mothership()


@pytest.fixture(scope="module", params=['IOverlayV1OVLCollateral'])
def ovl_collateral(mothership, request):
    '''
    Gets the IOverlayV1OVLCollateral contract address for 0th collateral index
    stored in the OverlayV1Mothership contract.

    Inputs:
      mothership [ProjectContract]: OverlayV1Mothership contract instance
      request    [arr]:             Parameters passed in the pytest fixture
        request.param [str]:        Collateral contract string

    Output:
      ovl_collateral generator produces a collateral contract instance of the
      0th collateral index stored in the OverlayV1Mothership contract
    '''
    addr = mothership.allCollateral(0)
    ovl_collateral = getattr(interface, request.param)(addr)
    yield ovl_collateral


@pytest.fixture(scope="module", params=["IOverlayV1Market"])
def market(mothership, request):
    '''
    Gets the IOverlayV1Market contract address for 0th market index stored in
    the OverlayV1Mothership contract.

    Inputs:
      mothership [ProjectContract]: OverlayV1Mothership contract instance
      request    [arr]:             Parameters passed in the pytest fixture
        request.param [str]:        Market contract string

    Output:
      market generator produces a market contract instance of the 0th market
      index stored in the OverlayV1Mothership contract
    '''
    addr = mothership.allMarkets(0)
    market = getattr(interface, request.param)(addr)
    yield market


@pytest.fixture(scope="module")
def uni_test(gov, rewards, accounts):

    #  dai_eth = "0xc2e9f25be6257c210d7adf0d4cd6e3e881ba25f8"
    usdc_eth = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    #  wbtc_eth = "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed"
    #  uni_eth = "0x1d42064Fc4Beb5F8aAF85F4617AE8b3b5B8Bd801"
    #  link_eth = "0xa6Cc3C2531FdaA6Ae1A3CA84c2855806728693e8"
    aave_eth = "0x5aB53EE1d50eeF2C1DD3d5402789cd27bB52c1bB"

    usdc = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    #  wbtc = "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    #  uni = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    #  link = "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    aave = "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"

    # we are trying to find amount USDC in OVL terms

    unitest = rewards.deploy(UniTest, WRAPPED_ETH_ADDR, usdc, usdc_eth, aave,
                             WRAPPED_ETH_ADDR, aave_eth)

    yield unitest
