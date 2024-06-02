def test_balances(token, gov, alice, bob):
    assert token.totalSupply() == token.balanceOf(bob)
    assert token.balanceOf(gov) == 0
    assert token.balanceOf(alice) == 0


def test_roles(token, mothership, gov, collateral):
    assert token.hasRole(token.ADMIN_ROLE(), gov) is True
    assert token.hasRole(token.MINTER_ROLE(), collateral) is False
    assert token.hasRole(token.BURNER_ROLE(), collateral) is False

    assert mothership.hasRole(mothership.ADMIN(), gov) is True
    assert mothership.hasRole(mothership.GOVERNOR(), gov) is True


def test_params(mothership, depository, token):
    assert mothership.ovl() == token
    assert mothership.fee() == 0.00075e18
    assert mothership.feeBurnRate() == .1e18
    assert mothership.marginBurnRate() == .05e18
    assert mothership.feeTo() == depository


def test_markets(mothership, market):
    assert mothership.totalMarkets() == 0
    assert mothership.marketActive(market) is False
    assert mothership.marketExists(market) is False


def test_collateral(mothership, collateral):
    assert mothership.totalCollaterals() == 0
    assert mothership.collateralActive(collateral) is False
    assert mothership.collateralExists(collateral) is False


def test_erc20(token):
    assert token.decimals() == 18
    assert token.name() == "Overlay"
    assert token.symbol() == "OVL"
