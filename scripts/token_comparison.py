from brownie import (
    accounts,
    OverlayToken,
    OverlayTokenNew,
    GeneralShim
)

dev0 = accounts.load('development0')
dev1 = accounts.load('development1')
dev2 = accounts.load('development2')

def main():

    ovl1 = dev0.deploy(OverlayToken)
    ovl2 = dev0.deploy(OverlayTokenNew)


    shim = dev0.deploy(GeneralShim, ovl1, ovl2)

    ovl1.grantRole(ovl1.BURNER_ROLE(), shim, { 'from': dev0 })
    ovl2.grantRole(ovl2.BURNER_ROLE(), shim, { 'from': dev0 })
    ovl1.grantRole(ovl1.MINTER_ROLE(), shim, { 'from': dev0 })
    ovl2.grantRole(ovl2.MINTER_ROLE(), shim, { 'from': dev0 })

    ovl1.mint(dev0, 8000e18, { 'from': dev0 })
    ovl2.mint(dev0, 8000e18, { 'from': dev0 })

    ovl1.approve(shim, 1e50, { 'from': dev0 })
    ovl2.approve(shim, 1e50, { 'from': dev0 })

    old_tx1 = shim.burnOld(1e18, 1e18, { 'from': dev0 })
    old_tx2 = shim.burnOld(1e18, 1e18, { 'from': dev0 })
    old_tx3 = shim.burnOld(1e18, 1e18, { 'from': dev0 })

    new_tx1 = shim.burnNew(1e18, 1e18, { 'from': dev0 })
    new_tx2 = shim.burnNew(1e18, 1e18, { 'from': dev0 })
    new_tx3 = shim.burnNew(1e18, 1e18, { 'from': dev0 })

    print("old_tx1 gas", old_tx1.gas_used)
    print("old_tx2 gas", old_tx2.gas_used)
    print("old_tx3 gas", old_tx3.gas_used)

    print("new_tx1 gas", new_tx1.gas_used)
    print("new_tx2 gas", new_tx2.gas_used)
    print("new_tx3 gas", new_tx3.gas_used)
