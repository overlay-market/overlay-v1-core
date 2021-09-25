
import brownie
from brownie.test import given, strategy
from hypothesis import settings
from brownie import chain
from decimal import *

def print_logs(tx):
    for i in range(len(tx.events['log'])):
        print(tx.events['log'][i]['k'] + ": " + str(tx.events['log'][i]['v']))

def test_unwind(ovl_collateral, token, bob):
    pass


def test_unwind_revert_insufficient_shares(ovl_collateral, bob):

    with brownie.reverts("OVLV1:!shares"):
        ovl_collateral.unwind(
            1,
            1e18,
            { "from": bob }
        );


# warning, dependent on what the price/mocks do
def test_unwind_revert_position_was_liquidated(ovl_collateral, bob):

    # build a position
    # liquidate a position
    # try to unwind it and get a revert

    pass


def test_unwind_from_queued_oi (ovl_collateral, bob):
    # when compounding period is larger than update period 
    # we unwind before compounding period is done
    # and expect the oi to be removed from the 
    # queued oi instead of the non queued oi

    pass


def test_that_comptroller_recorded_mint_or_burn (
    ovl_collateral, 
    mothership,
    token, 
    market, 
    bob
):

    update_period = market.updatePeriod()

    # when we unwind, seeing if there was a mint/burn, 
    # and see if the brrrrd variable has recorded it
    tx = ovl_collateral.build(
        market,
        1e18,
        1,
        True,
        { 'from': bob }
    )

    pos_id = tx.events['Build']['positionId']
    bobs_shares = tx.events['Build']['oi']

    chain.mine(timedelta=update_period*2)

    tx = ovl_collateral.unwind(
        pos_id,
        bobs_shares, 
        { "from": bob }
    )

    fee = mothership.fee()

    expected_brrrr = -(Decimal(1) - Decimal(1) * ( Decimal(fee) / Decimal(1e18) ))
    brrrrd = Decimal(market.brrrrd()) / Decimal(1e18)

    assert expected_brrrr == brrrrd



