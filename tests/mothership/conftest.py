import pytest
from brownie import OverlayToken, OverlayV1Mothership


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture(scope="module")
def gov(accounts):
    yield accounts[0]


@pytest.fixture(scope="module")
def alice(accounts):
    yield accounts[1]


@pytest.fixture(scope="module")
def bob(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def rando(accounts):
    yield accounts[3]


@pytest.fixture(scope="module")
def collateral(accounts):
    yield accounts[4]


@pytest.fixture(scope="module")
def market(accounts):
    yield accounts[5]


@pytest.fixture(scope="module")
def depository(accounts):
    yield accounts[6]


@pytest.fixture(scope="module", params=[8000000])
def create_token(gov, alice, bob, request):
    sup = request.param

    def create_token(supply=sup):
        tok = gov.deploy(OverlayToken)
        tok.mint(gov, supply * 10 ** tok.decimals(), {"from": gov})
        tok.transfer(bob, supply * 10 ** tok.decimals(), {"from": gov})
        return tok

    yield create_token


@pytest.fixture(scope="module")
def token(create_token):
    yield create_token()


@pytest.fixture(scope="module", params=[(0.00075e18, .1e18, .05e18)])
def create_mothership(gov, token, depository, request):
    fee_rate, fee_burn_rate, margin_burn_rate = request.param

    def create_mothership(tok=token, fee=fee_rate, fee_burn=fee_burn_rate,
                          margin_burn=margin_burn_rate):
        mothership = gov.deploy(OverlayV1Mothership,
                                tok, depository, fee, fee_burn, margin_burn)
        tok.grantRole(tok.ADMIN_ROLE(), mothership, {"from": gov})
        return mothership

    yield create_mothership


@pytest.fixture(scope="module")
def mothership(create_mothership):
    yield create_mothership()
