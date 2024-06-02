from brownie.convert import EthAddress
from brownie.network.account import Account


def test_accounts(alice, bob, feed_owner, fees, gov, notamarket, rewards):
    '''
    Test that the python fixtures that setup the eth accounts, return eth
    accounts.
    '''
    assert isinstance(alice, Account)
    assert isinstance(bob, Account)
    assert isinstance(feed_owner, Account)
    assert isinstance(fees, Account)
    assert isinstance(gov, Account)
    assert isinstance(notamarket, Account)
    assert isinstance(rewards, Account)


def test_create_token(token, gov, alice, bob):
    print(dir(token))

    # Test token total supply
    actual = 8000000000000000000000000
    expect = token.totalSupply()
    assert actual == expect

    # Test tokens transferred from gov to alice and bob
    actual_gov_balance = token.balanceOf(gov)
    expect_gov_balance = 0
    assert actual_gov_balance == expect_gov_balance

    actual_alice_balance = token.balanceOf(alice)
    expect_alice_balance = 4000000000000000000000000
    assert actual_alice_balance == expect_alice_balance

    expect_bob_balance = 4000000000000000000000000
    actual_bob_balance = token.balanceOf(bob)
    assert actual_bob_balance == expect_bob_balance

    # Test roles were setup
    # TODO: test MINTER_ROLE and BURNER_ROLE
    # RR: We should have an entire test dedicated to the token
    expect_num_admin_roles = token.getRoleMemberCount(0x00)
    assert 1 == expect_num_admin_roles
    expect_admin_role = token.getRoleMember(0x00, 0)
    #  expect_admin_role = token.ADMIN_ROLE()
    print(token.ADMIN_ROLE())
    assert gov == expect_admin_role
    print(token)


def test_create_mothership(mothership, gov):
    '''
    TODO: ovl(), marketExists(), allMarkets(), totalMarkets()
    - check mothership events fired
    Inputs:
        mothership  [ProjectContract]: OverlayV1Mothership contract instance
    '''
    print(type(mothership))
    print()
    print(mothership.totalMarkets())
    print()

    # Test `ovl` function returns an eth address
    assert isinstance(mothership.ovl(), EthAddress)

    # Test mothership `fee` external view function
    expect = mothership.fee()
    actual = 0.0015e18
    assert actual == expect

    # RRQ: why doesn't this function exist if it is defined in
    # IOverlayMothership.sol
    #  print(mothership.getGlobalParams())

    # Test mothership `getGlobalParams` external view function
    margin_burn_rate = 0.5e18
    fee_burn_rate = 0.5e18
    fee_to = '0x46C0a5326E643E4f71D3149d50B48216e174Ae84'
    fee = 0.0015e18
    expect = (fee_to, fee, fee_burn_rate, margin_burn_rate)

    actual = mothership.getGlobalParams()
    assert actual == expect

    #  eth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    assert 523 == 523
    #  assert 3 == 3
    #  assert 5 == 5
    #  assert 5 == 5
