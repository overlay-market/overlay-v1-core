import brownie
import unittest
from brownie.test import given, strategy
from hypothesis import settings
from decimal import Decimal

MIN_COLLATERAL = 1e14  # min amount to build
TOKEN_DECIMALS = 18
TOKEN_TOTAL_SUPPLY = 8000000
OI_CAP = 800000e18
FEE_RESOLUTION = 1e18

@unittest.skip('REMOVE')
@given(
    collateral=strategy('uint256', min_value=1e18, max_value=OI_CAP - 1e4),
    leverage=strategy('uint8', min_value=1, max_value=100),
    is_long=strategy('bool')
    )
@settings(max_examples=1)
def test_build_success_zero_impact(
        ovl_collateral,
        token,
        mothership,
        market,
        bob,
        rewards,
        collateral,
        leverage,
        is_long
        ):

    oi = collateral * leverage
    trade_fee = oi * mothership.fee() / FEE_RESOLUTION

    breakpoint()
    # get prior state of collateral manager
    fee_bucket = ovl_collateral.fees()
    ovl_balance = token.balanceOf(ovl_collateral)

    # get prior state of market
    queued_oi = market.queuedOiLong() if is_long else market.queuedOiShort()

    # approve collateral contract to spend bob's ovl to build position
    token.approve(ovl_collateral, collateral, {"from": bob})

    # build the position
    tx = ovl_collateral.build(
        market,
        collateral,
        leverage,
        is_long,
        {"from": bob}
    )

    assert 'Build' in tx.events
    assert 'positionId' in tx.events['Build']
    pid = tx.events['Build']['positionId']

    # fees should be sent to fee bucket in collateral manager
    assert fee_bucket + trade_fee == (ovl_collateral.fees())

    # check collateral sent to collateral manager
    assert ovl_balance + collateral == (token.balanceOf(ovl_collateral))

    # check position token issued with correct oi shares
    collateral_adjusted = collateral - trade_fee
    oi_adjusted = collateral_adjusted * leverage
    assert ovl_collateral.balanceOf(bob, pid) == oi_adjusted

    # check position attributes for PID
    (pos_market, pos_islong, pos_lev, _, pos_oishares,
     pos_debt, pos_cost, _) = ovl_collateral.positions(pid)

    assert pos_market == market
    assert pos_islong == is_long
    assert pos_lev == leverage
    assert pos_oishares == oi_adjusted
    assert pos_debt == (oi_adjusted - collateral_adjusted)
    assert pos_cost == collateral_adjusted

    # check oi has been queued on the market for respective side of trade
    if is_long:
        assert queued_oi + oi_adjusted == market.queuedOiLong()
    else:
        assert queued_oi + oi_adjusted == market.queuedOiShort()


def test_build_when_market_not_supported(mothership, market, bob):
    pass


# @unittest.skip('REMOVE')
@given(
    # collateral=strategy('uint256', min_value=2e18, max_value=OI_CAP - 1e4),
    leverage=strategy('uint8', min_value=1, max_value=100),
    is_long=strategy('bool')
    )
@settings(max_examples=1)
def test_build_min_collateral(
    ovl_collateral,
    token,
    mothership,
    market,
    bob,
    # collateral,
    leverage,
    is_long
    ):
    
    EXPECTED_ERROR_MESSAGE = 'OVLV1:collat<min'
    epsilon = 1e-18

    # approve collateral contract to spend bob's ovl to build position
    token.approve(ovl_collateral, 1e18, {"from": bob})

    fee = mothership.fee()
    fee = Decimal(fee) / Decimal(1e18)
    fee_offset = float(Decimal(MIN_COLLATERAL)*(1/fee - Decimal(leverage)))
    trade_amt = MIN_COLLATERAL + fee_offset
    breakpoint()

    #higher than min collateral passes
    tx = ovl_collateral.build(market, trade_amt, leverage, is_long, {'from':bob})
    assert isinstance(tx, brownie.network.transaction.TransactionReceipt)

    #lower than min collateral fails
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        ovl_collateral.build(market, trade_amt - epsilon, leverage, is_long, {'from':bob})


@unittest.skip('REMOVE')
@given(
    collateral=strategy('uint256', min_value=1e18, max_value=OI_CAP - 1e4),
    # leverage=strategy('uint8', min_value=1, max_value=100),
    is_long=strategy('bool')
    )
@settings(max_examples=1)
def test_build_max_leverage(
    ovl_collateral, 
    token, 
    market, 
    bob,
    collateral,
    # leverage,
    is_long
    ):

    breakpoint()
    
    EXPECTED_ERROR_MESSAGE = 'OVLV1:lev>max'

    # approve collateral contract to spend bob's ovl to build position
    token.approve(ovl_collateral, collateral, {"from": bob})

    for leverage in range(1, market.leverageMax() + 100, 10):
        if leverage > market.leverageMax():
            with brownie.reverts(EXPECTED_ERROR_MESSAGE):
                ovl_collateral.build(market, MIN_COLLATERAL, leverage, is_long, {'from':bob})
        else:
            tx = ovl_collateral.build(market, MIN_COLLATERAL, leverage, is_long, {'from':bob})
            assert isinstance(tx, brownie.network.transaction.TransactionReceipt)



@given(
    oi=strategy('uint256',
                min_value=1.01*OI_CAP*10**TOKEN_DECIMALS, max_value=2**144-1),
    leverage=strategy('uint8', min_value=1, max_value=100),
    is_long=strategy('bool'))
def test_build_breach_cap(token, ovl_collateral, market, bob,
                          oi, leverage, is_long):
    collateral = int(oi / leverage)
    token.approve(ovl_collateral, collateral, {"from": bob})
    with brownie.reverts("OVLV1:>cap"):
        ovl_collateral.build(market, collateral, leverage,
                             is_long, {"from": bob})
