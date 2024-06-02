// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "./IOverlayToken.sol";

interface IOverlayV1Mothership {

    function ovl () external view returns (
        IOverlayToken ovl_
    );

    function marketActive(
        address
    ) external view returns (
        bool
    );

    function marketExists(
        address
    ) external view returns (
        bool
    );

    function allMarkets(
        uint marketIndex
    ) external view returns (
        address marketAddress
    );

    function collateralActive(
        address
    ) external view returns (
        bool
    );

    function collateralExists(
        address
    ) external view returns (
        bool
    );

    function allCollaterals(
        uint collateralIndex
    ) external view returns (
        address collateralAddress
    );

    function totalMarkets () external view returns (
            uint
    );

    function getGlobalParams() external view returns (
        address feeTo_,
        uint fee_,
        uint feeBurnRate_,
        uint marginBurnRate_
    );

    function fee() external view returns (uint256);

    function hasRole(
        bytes32 _role,
        address _account
    ) external view returns (
        bool
    );

    function setFeeTo(address _feeTo) external;
    function setFee(uint _fee) external;
    function setFeeBurnRate(uint _feeBurnRate) external;
    function setMarginBurnRate(uint _marginBurnRate) external;

}
