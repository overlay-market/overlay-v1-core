import brownie


def test_initialize_collateral(mothership, collateral, gov, token):
    total = mothership.totalCollaterals()
    tx = mothership.initializeCollateral(collateral, {"from": gov})

    assert mothership.collateralExists(collateral) is True
    assert mothership.collateralActive(collateral) is True
    assert mothership.totalCollaterals() == total + 1

    # pushed to end of list of collaterals stored by mothership
    assert mothership.allCollaterals(total) == collateral

    assert token.hasRole(token.MINTER_ROLE(), collateral) is True
    assert token.hasRole(token.BURNER_ROLE(), collateral) is True

    assert 'UpdateCollateral' in tx.events
    assert 'collateral' in tx.events['UpdateCollateral']
    assert 'active' in tx.events['UpdateCollateral']
    assert tx.events['UpdateCollateral']['collateral'] == collateral
    assert tx.events['UpdateCollateral']['active'] is True


def test_disable_collateral(mothership, collateral, gov, token):
    # init state
    _ = mothership.initializeCollateral(collateral, {"from": gov})
    total = mothership.totalCollaterals()

    tx = mothership.disableCollateral(collateral, {"from": gov})

    assert mothership.collateralExists(collateral) is True
    assert mothership.collateralActive(collateral) is False
    assert mothership.totalCollaterals() == total

    assert token.hasRole(token.MINTER_ROLE(), collateral) is False
    assert token.hasRole(token.BURNER_ROLE(), collateral) is False

    assert 'UpdateCollateral' in tx.events
    assert 'collateral' in tx.events['UpdateCollateral']
    assert 'active' in tx.events['UpdateCollateral']
    assert tx.events['UpdateCollateral']['collateral'] == collateral
    assert tx.events['UpdateCollateral']['active'] is False


def test_enable_collateral(mothership, collateral, gov, token):
    # init state
    _ = mothership.initializeCollateral(collateral, {"from": gov})
    _ = mothership.disableCollateral(collateral, {"from": gov})
    total = mothership.totalCollaterals()

    tx = mothership.enableCollateral(collateral, {"from": gov})

    assert mothership.collateralExists(collateral) is True
    assert mothership.collateralActive(collateral) is True
    assert mothership.totalCollaterals() == total

    assert token.hasRole(token.MINTER_ROLE(), collateral) is True
    assert token.hasRole(token.BURNER_ROLE(), collateral) is True

    assert 'UpdateCollateral' in tx.events
    assert 'collateral' in tx.events['UpdateCollateral']
    assert 'active' in tx.events['UpdateCollateral']
    assert tx.events['UpdateCollateral']['collateral'] == collateral
    assert tx.events['UpdateCollateral']['active'] is True


def test_enable_then_disable_collateral(mothership, collateral, gov,
                                        bob, token):
    # init state
    _ = mothership.initializeCollateral(collateral, {"from": gov})
    _ = mothership.disableCollateral(collateral, {"from": gov})
    total = mothership.totalCollaterals()

    _ = mothership.enableCollateral(collateral, {"from": gov})

    assert mothership.collateralExists(collateral) is True
    assert mothership.collateralActive(collateral) is True
    assert mothership.totalCollaterals() == total

    assert token.hasRole(token.MINTER_ROLE(), collateral) is True
    assert token.hasRole(token.BURNER_ROLE(), collateral) is True

    _ = mothership.disableCollateral(collateral, {"from": gov})

    assert mothership.collateralExists(collateral) is True
    assert mothership.collateralActive(collateral) is False
    assert mothership.totalCollaterals() == total

    assert token.hasRole(token.MINTER_ROLE(), collateral) is False
    assert token.hasRole(token.BURNER_ROLE(), collateral) is False


def test_initialize_collateral_reverts_when_exists(mothership, collateral,
                                                   gov):
    _ = mothership.initializeCollateral(collateral, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1: collateral exists'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.initializeCollateral(collateral, {"from": gov})


def test_initialize_collateral_reverts_when_not_gov(mothership, collateral,
                                                    bob):
    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.initializeCollateral(collateral, {"from": bob})


def test_enable_collateral_reverts_when_not_initialized(mothership, collateral,
                                                        gov):
    EXPECTED_ERROR_MESSAGE = 'OVLV1: collateral !exists'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.enableCollateral(collateral, {"from": gov})


def test_enable_collateral_reverts_when_not_disabled(mothership, collateral,
                                                     gov):
    _ = mothership.initializeCollateral(collateral, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1: collateral !disabled'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.enableCollateral(collateral, {"from": gov})


def test_enable_collateral_reverts_when_not_gov(mothership, collateral, gov,
                                                bob):
    _ = mothership.initializeCollateral(collateral, {"from": gov})
    _ = mothership.disableCollateral(collateral, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.enableCollateral(collateral, {"from": bob})


def test_disable_collateral_reverts_when_not_initialized(mothership,
                                                         collateral,
                                                         gov):
    EXPECTED_ERROR_MESSAGE = 'OVLV1: collateral !exists'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.disableCollateral(collateral, {"from": gov})


def test_disable_collateral_reverts_when_not_enabled(mothership, collateral,
                                                     gov):
    _ = mothership.initializeCollateral(collateral, {"from": gov})
    _ = mothership.disableCollateral(collateral, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1: collateral !enabled'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.disableCollateral(collateral, {"from": gov})


def test_disable_collateral_reverts_when_not_gov(mothership, collateral, gov,
                                                 bob):
    _ = mothership.initializeCollateral(collateral, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.disableCollateral(collateral, {"from": bob})
