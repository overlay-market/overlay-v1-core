import brownie


def test_get_global_params(mothership):
    fee_to, fee, fee_burn_rate, margin_burn_rate = mothership.getGlobalParams()

    assert fee_to == mothership.feeTo()
    assert fee == mothership.fee()
    assert fee_burn_rate == mothership.feeBurnRate()
    assert margin_burn_rate == mothership.marginBurnRate()


def test_set_fee_to(mothership, gov, rando):
    tx = mothership.setFeeTo(rando, {"from": gov})

    assert mothership.feeTo() == rando
    assert 'UpdateFeeTo' in tx.events
    assert 'feeTo' in tx.events['UpdateFeeTo']
    assert tx.events['UpdateFeeTo']['feeTo'] == rando


def test_set_fee(mothership, gov):
    fee_rate = 0.001e18
    tx = mothership.setFee(fee_rate, {"from": gov})

    assert mothership.fee() == fee_rate
    assert 'UpdateFee' in tx.events
    assert 'fee' in tx.events['UpdateFee']
    assert tx.events['UpdateFee']['fee'] == fee_rate


def test_set_fee_burn_rate(mothership, gov):
    fee_burn_rate = 0.20e18
    tx = mothership.setFeeBurnRate(fee_burn_rate, {"from": gov})

    assert mothership.feeBurnRate() == fee_burn_rate
    assert 'UpdateFeeBurnRate' in tx.events
    assert 'feeBurnRate' in tx.events['UpdateFeeBurnRate']
    assert tx.events['UpdateFeeBurnRate']['feeBurnRate'] == fee_burn_rate


def test_set_margin_burn_rate(mothership, gov):
    margin_burn_rate = 0.20e18
    tx = mothership.setMarginBurnRate(margin_burn_rate, {"from": gov})

    assert mothership.marginBurnRate() == margin_burn_rate
    assert 'UpdateMarginBurnRate' in tx.events
    assert 'marginBurnRate' in tx.events['UpdateMarginBurnRate']
    assert tx.events['UpdateMarginBurnRate']['marginBurnRate'] \
        == margin_burn_rate


def test_set_fee_to_reverts_when_zero_address(mothership, gov):
    EXPECTED_ERROR_MESSAGE = 'OVLV1: fees to the zero address'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFeeTo("0x0000000000000000000000000000000000000000",
                            {"from": gov})


def test_set_fee_to_reverts_when_not_gov(mothership, bob, rando):
    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFeeTo(rando, {"from": bob})


def test_set_fee_reverts_when_less_than_min(mothership, gov):
    MIN_FEE = mothership.MIN_FEE()
    fee = MIN_FEE-1

    EXPECTED_ERROR_MESSAGE = 'OVLV1: fee rate out of bounds'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFee(fee, {"from": gov})


def test_set_fee_reverts_when_greater_than_max(mothership, gov):
    MAX_FEE = mothership.MAX_FEE()
    fee = MAX_FEE+1

    EXPECTED_ERROR_MESSAGE = 'OVLV1: fee rate out of bounds'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFee(fee, {"from": gov})


def test_set_fee_reverts_when_not_gov(mothership, bob):
    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFee(0.001e18, {"from": bob})


def test_set_fee_burn_rate_reverts_when_greater_than_max(mothership, gov):
    MAX_FEE_BURN = mothership.MAX_FEE_BURN()
    fee_burn_rate = MAX_FEE_BURN+1

    EXPECTED_ERROR_MESSAGE = 'OVLV1: fee burn rate out of bounds'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFeeBurnRate(fee_burn_rate, {"from": gov})


def test_set_fee_burn_rate_reverts_when_not_gov(mothership, bob):
    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setFeeBurnRate(0.20e18, {"from": bob})


def test_set_margin_burn_rate_reverts_when_greater_than_max(mothership, gov):
    MAX_MARGIN_BURN = mothership.MAX_MARGIN_BURN()
    margin_burn_rate = MAX_MARGIN_BURN+1

    EXPECTED_ERROR_MESSAGE = 'OVLV1: margin burn rate out of bounds'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setMarginBurnRate(margin_burn_rate, {"from": gov})


def test_set_margin_burn_rate_reverts_when_not_gov(mothership, bob):
    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.setMarginBurnRate(0.20e18, {"from": bob})
