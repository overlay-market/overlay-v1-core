import brownie


def test_only_minter(token, alice):
    EXPECTED_ERROR_MSG = 'OVL:!minter'
    with brownie.reverts(EXPECTED_ERROR_MSG):
        token.mint(alice, 1 * 10 ** token.decimals(), {"from": alice})


def test_only_burner(token, bob):
    EXPECTED_ERROR_MSG = 'OVL:!burner'
    with brownie.reverts(EXPECTED_ERROR_MSG):
        token.burn(bob, 1 * 10 ** token.decimals(), {"from": bob})


def test_mint(token, minter, alice):
    before = token.balanceOf(alice)
    amount = 1 * 10 ** token.decimals()
    token.mint(alice, amount, {"from": minter})
    assert token.balanceOf(alice) == before + amount


def test_burn(token, burner, bob):
    before = token.balanceOf(bob)
    amount = 1 * 10 ** token.decimals()
    token.burn(bob, amount, {"from": burner})
    assert token.balanceOf(bob) == before - amount


def test_mint_then_burn(token, market, alice):
    before = token.balanceOf(alice)
    token.mint(alice, 20 * 10 ** token.decimals(), {"from": market})
    mid = before + 20 * 10 ** token.decimals()
    assert token.balanceOf(alice) == mid
    token.burn(alice, 15 * 10 ** token.decimals(), {"from": market})
    assert token.balanceOf(alice) == mid - 15 * 10 ** token.decimals()

def test_transfer_burn(token, market, gov, alice, bob):

    alice_before_mint = token.balanceOf(alice)

    mint_amount = 2e18

    token.mint(alice, mint_amount, { "from": market })

    alice_after_mint = token.balanceOf(alice)

    bob_before = token.balanceOf(bob)

    assert alice_after_mint == alice_before_mint + mint_amount, 'alice != mint amount'

    token.grantRole(token.BURNER_ROLE(), alice, { 'from': gov })

    total_supply_before_transfer_burn = token.totalSupply()

    token.transferBurn(bob, 1e18, 1e18, { 'from': alice })

    alice_after_transfer_burn = token.balanceOf(alice)

    assert alice_after_transfer_burn == alice_after_mint - 2e18, 'alice after != -2'

    bob_after = token.balanceOf(bob)

    assert bob_after == bob_before + 1e18, 'bob after != +1'

    total_supply_after_transfer_burn = token.totalSupply()

    assert total_supply_after_transfer_burn == total_supply_before_transfer_burn - 1e18, 'total supply after != -1'


def test_transfer_mint(token, market, gov, alice, bob):

    alice_before_mint = token.balanceOf(alice)

    mint_amount = 2e18

    token.mint(alice, mint_amount, { "from": market })

    alice_after_mint = token.balanceOf(alice)

    bob_before = token.balanceOf(bob)

    assert alice_after_mint == alice_before_mint + mint_amount, 'alice != mint amount'

    token.grantRole(token.MINTER_ROLE(), alice, { 'from': gov })

    total_supply_before_transfer_mint = token.totalSupply()

    token.transferMint(bob, 1e18, 1e18, { 'from': alice })

    alice_after_transfer_mint = token.balanceOf(alice)

    assert alice_after_transfer_mint == alice_after_mint - 1e18, 'alice after != -1'

    bob_after = token.balanceOf(bob)

    assert bob_after == bob_before + 2e18, 'bob after != +2'

    total_supply_after_transfer_mint = token.totalSupply()

    assert total_supply_after_transfer_mint == total_supply_before_transfer_mint + 1e18, 'total supply after != +1'

def test_transfer_from_mint(token, market, gov, alice, bob):

    mint_amount = 2e18

    token.mint(alice, mint_amount, { 'from': market })

    token.approve(bob, 2e18, { 'from': alice })

    bob_before = token.balanceOf(bob)

    alice_before = token.balanceOf(alice)

    alice_approve_bob_before = token.allowance(alice, bob)

    total_supply_before = token.totalSupply()

    token.grantRole(token.MINTER_ROLE(), bob, { 'from': gov })

    token.transferFromMint(alice, bob, 2e18, 2e18, { 'from': bob })

    alice_after = token.balanceOf(alice)

    bob_after = token.balanceOf(bob)

    alice_approve_bob_after = token.allowance(alice, bob)

    total_supply_after = token.totalSupply()

    assert alice_after == alice_before - 2e18

    assert bob_after == bob_before + 4e18

    assert alice_approve_bob_after == alice_approve_bob_before - 2e18

    assert total_supply_after == total_supply_before + 2e18



def test_transfer_from_burn (token, market, gov, alice, bob):

    mint_amount = 4e18

    token.mint(alice, mint_amount, { 'from': market })

    token.approve(bob, 4e18, { 'from': alice })

    bob_before = token.balanceOf(bob)

    alice_before = token.balanceOf(alice)

    alice_approve_bob_before = token.allowance(alice, bob)

    total_supply_before = token.totalSupply()

    token.grantRole(token.BURNER_ROLE(), bob, { 'from': gov })

    token.transferFromBurn(alice, bob, 2e18, 2e18, { 'from': bob })

    alice_after = token.balanceOf(alice)

    bob_after = token.balanceOf(bob)

    alice_approve_bob_after = token.allowance(alice, bob)

    total_supply_after = token.totalSupply()

    assert alice_after == alice_before - 4e18

    assert bob_after == bob_before + 2e18

    assert alice_approve_bob_after == alice_approve_bob_before - 4e18

    assert total_supply_after == total_supply_before - 2e18


