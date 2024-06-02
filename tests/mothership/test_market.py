import brownie


def test_initialize_market(mothership, market, gov):
    total = mothership.totalMarkets()

    tx = mothership.initializeMarket(market, {"from": gov})

    assert mothership.marketExists(market) is True
    assert mothership.marketActive(market) is True
    assert mothership.totalMarkets() == total + 1

    # pushed to end of list of markets stored by mothership
    assert mothership.allMarkets(total) == market

    assert 'UpdateMarket' in tx.events
    assert 'market' in tx.events['UpdateMarket']
    assert 'active' in tx.events['UpdateMarket']
    assert tx.events['UpdateMarket']['market'] == market
    assert tx.events['UpdateMarket']['active'] is True


def test_disable_market(mothership, market, gov):
    # init state
    _ = mothership.initializeMarket(market, {"from": gov})
    total = mothership.totalMarkets()

    tx = mothership.disableMarket(market, {"from": gov})

    assert mothership.marketExists(market) is True
    assert mothership.marketActive(market) is False
    assert mothership.totalMarkets() == total

    assert 'UpdateMarket' in tx.events
    assert 'market' in tx.events['UpdateMarket']
    assert 'active' in tx.events['UpdateMarket']
    assert tx.events['UpdateMarket']['market'] == market
    assert tx.events['UpdateMarket']['active'] is False


def test_enable_market(mothership, market, gov):
    # init state
    _ = mothership.initializeMarket(market, {"from": gov})
    _ = mothership.disableMarket(market, {"from": gov})
    total = mothership.totalMarkets()

    tx = mothership.enableMarket(market, {"from": gov})

    assert mothership.marketExists(market) is True
    assert mothership.marketActive(market) is True
    assert mothership.totalMarkets() == total

    assert 'UpdateMarket' in tx.events
    assert 'market' in tx.events['UpdateMarket']
    assert 'active' in tx.events['UpdateMarket']
    assert tx.events['UpdateMarket']['market'] == market
    assert tx.events['UpdateMarket']['active'] is True


def test_enable_then_disable_market(mothership, market, gov, bob):
    # init state
    _ = mothership.initializeMarket(market, {"from": gov})
    _ = mothership.disableMarket(market, {"from": gov})
    total = mothership.totalMarkets()

    _ = mothership.enableMarket(market, {"from": gov})

    assert mothership.marketExists(market) is True
    assert mothership.marketActive(market) is True
    assert mothership.totalMarkets() == total

    _ = mothership.disableMarket(market, {"from": gov})

    assert mothership.marketExists(market) is True
    assert mothership.marketActive(market) is False
    assert mothership.totalMarkets() == total


def test_initialize_market_reverts_when_exists(mothership, market, gov):
    _ = mothership.initializeMarket(market, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1: market exists'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.initializeMarket(market, {"from": gov})


def test_initialize_market_reverts_when_not_gov(mothership, market, bob):
    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.initializeMarket(market, {"from": bob})


def test_enable_market_reverts_when_not_initialized(mothership, market, gov):
    EXPECTED_ERROR_MESSAGE = 'OVLV1: market !exists'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.enableMarket(market, {"from": gov})


def test_enable_market_reverts_when_not_disabled(mothership, market, gov):
    _ = mothership.initializeMarket(market, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1: market !disabled'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.enableMarket(market, {"from": gov})


def test_enable_market_reverts_when_not_gov(mothership, market, gov, bob):
    _ = mothership.initializeMarket(market, {"from": gov})
    _ = mothership.disableMarket(market, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.enableMarket(market, {"from": bob})


def test_disable_market_reverts_when_not_initialized(mothership, market, gov):
    EXPECTED_ERROR_MESSAGE = 'OVLV1: market !exists'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.disableMarket(market, {"from": gov})


def test_disable_market_reverts_when_not_enabled(mothership, market, gov):
    _ = mothership.initializeMarket(market, {"from": gov})
    _ = mothership.disableMarket(market, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1: market !enabled'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.disableMarket(market, {"from": gov})


def test_disable_market_reverts_when_not_gov(mothership, market, gov, bob):
    _ = mothership.initializeMarket(market, {"from": gov})

    EXPECTED_ERROR_MESSAGE = 'OVLV1:!gov'
    with brownie.reverts(EXPECTED_ERROR_MESSAGE):
        mothership.disableMarket(market, {"from": bob})
