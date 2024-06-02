

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../interfaces/IOverlayToken.sol";
import "../interfaces/IOverlayTokenNew.sol";

contract GeneralShim {


    IOverlayToken immutable ovlOld;
    IOverlayTokenNew immutable ovlNew;

    constructor (
        address _ovlOld,
        address _ovlNew
    ) {

        ovlOld = IOverlayToken(_ovlOld);
        ovlNew = IOverlayTokenNew(_ovlNew);

    }


    function burnNew (
        uint _amount,
        uint _burnt
    ) public {

        ovlNew.transferFromBurn(msg.sender, address(this), _amount, _burnt);


    }

    function burnOld (
        uint _amount,
        uint _burnt
    ) public {

        ovlOld.transferFrom(msg.sender, address(this), _amount + _burnt);
        ovlOld.burn(address(this), _burnt);

    }


}