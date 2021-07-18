from brownie import reverts
from brownie.test import given, strategy
from collections import OrderedDict


MIN_COLLATERAL_AMOUNT = 10**4  # min amount to build
TOKEN_DECIMALS = 18
TOKEN_TOTAL_SUPPLY = 8000000
OI_CAP = 800000
FEE_RESOLUTION = 1e4


@given(
    collateral=strategy('uint256',
                        min_value=MIN_COLLATERAL_AMOUNT,
                        max_value=0.00999*OI_CAP*10**TOKEN_DECIMALS),
    leverage=strategy('uint8', min_value=1, max_value=100),
    is_long=strategy('bool'))
def test_build(token, factory, market, bob, collateral, leverage, is_long):
    oi = collateral * leverage
    fee = factory.fee()
    fee_perc = fee / FEE_RESOLUTION

    # prior token balances
    prior_balance_market = token.balanceOf(market)
    prior_balance_trader = token.balanceOf(bob)

    # prior oi state
    prior_queued_oi_long = market.queuedOiLong()
    prior_queued_oi_short = market.queuedOiShort()
    prior_oi_long = market.oiLong()
    prior_oi_short = market.oiShort()

    # prior fee state
    prior_fees = market.fees()

    # prior price info
    prior_price_point_idx = market.pricePointCurrentIndex()

    # adjust for build fees
    oi_adjusted = int(oi * (1 - fee_perc))
    collateral_adjusted = int(oi_adjusted / leverage)
    debt_adjusted = oi_adjusted - collateral_adjusted
    fee_adjustment = oi - oi_adjusted

    # approve market to spend bob's ovl to build position
    token.approve(market, collateral, {"from": bob})
    # build the position
    tx = market.build(collateral, is_long, leverage, bob, {"from": bob})
    assert 'Build' in tx.events
    assert 'positionId' in tx.events['Build']
    pid = tx.events['Build']['positionId']
    # TODO: Fix for precision and not with +1 in rounding ...
    assert (
        tx.events['Build']['oi'] == oi_adjusted
        or tx.events['Build']['oi'] == oi_adjusted+1
    )
    assert (
        tx.events['Build']['debt'] == debt_adjusted
        or tx.events['Build']['debt'] == debt_adjusted+1
    )

    # check collateral transferred from bob's address
    expected_balance_trader = prior_balance_trader - collateral
    # mints debt to contract + additional collateral sent from trader
    expected_balance_market = prior_balance_market + collateral
    assert token.balanceOf(bob) == expected_balance_trader
    assert token.balanceOf(market) == expected_balance_market

    # check shares of erc 1155 match contribution to oi
    curr_shares_balance = market.balanceOf(bob, pid)
    assert (
        curr_shares_balance == oi_adjusted
        or curr_shares_balance == oi_adjusted + 1
    )

    # check position info
    # info = (isLong, leverage, pricePoint, oiShares, debt, cost)
    info = market.positions(pid)
    assert info[0] == is_long
    assert info[1] == leverage
    assert info[2] == prior_price_point_idx
    assert info[3] == oi_adjusted or info[3] == oi_adjusted + 1
    assert info[4] == debt_adjusted or info[4] == debt_adjusted + 1
    assert info[5] == collateral_adjusted or info[5] == collateral_adjusted + 1

    # oi aggregates should be unchanged as build settles at T+1
    curr_oi_long = market.oiLong()
    curr_oi_short = market.oiShort()
    assert prior_oi_long == curr_oi_long
    assert prior_oi_short == curr_oi_short

    # queued oi aggregates should increase prior to T+1 tho
    expected_queued_oi_long = (
        prior_queued_oi_long + oi_adjusted
        if is_long else prior_queued_oi_long
    )
    expected_queued_oi_short = (
        prior_queued_oi_short + oi_adjusted
        if not is_long else prior_queued_oi_short
    )
    curr_queued_oi_long = market.queuedOiLong()
    curr_queued_oi_short = market.queuedOiShort()
    assert (
        curr_queued_oi_long == expected_queued_oi_long
        or curr_queued_oi_long == expected_queued_oi_long + 1
    )
    assert (
        curr_queued_oi_short == expected_queued_oi_short
        or curr_queued_oi_short == expected_queued_oi_short + 1
    )

    # check position receives current price point index ...
    current_price_point_idx = market.pricePointCurrentIndex()
    assert current_price_point_idx == prior_price_point_idx

    # ... and price hasn't settled
    with reverts(''):
        market.pricePoints(current_price_point_idx)

    assert market.pricePoints(current_price_point_idx - 1) == 0

    # check fees assessed and accounted for in fee bucket
    # +1 with or rounding catch given fee_adjustment var definition
    expected_fees = prior_fees + fee_adjustment
    curr_fees = market.fees()
    assert (
        curr_fees == expected_fees
        or curr_fees == expected_fees - 1
    )


def test_build_breach_min_collateral(token, market, bob):
    pass


def test_build_breach_max_leverage(token, market, bob):
    pass


@given(
    oi=strategy('uint256',
                min_value=1.01*OI_CAP*10**TOKEN_DECIMALS, max_value=2**144-1),
    leverage=strategy('uint8', min_value=1, max_value=100),
    is_long=strategy('bool'))
def test_build_breach_cap(token, factory, market, bob, oi, leverage, is_long):
    collateral = int(oi / leverage)
    token.approve(market, collateral, {"from": bob})
    with reverts("OverlayV1: breached oi cap"):
        market.build(collateral, is_long, leverage, bob, {"from": bob})
