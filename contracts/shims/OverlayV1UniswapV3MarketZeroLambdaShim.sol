// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../OverlayV1UniswapV3Market.sol";
import "../libraries/FixedPoint.sol";

contract OverlayV1UniswapV3MarketZeroLambdaShim is OverlayV1UniswapV3Market {

    using FixedPoint for uint256;

    constructor(
        address _mothership,
        address _ovlFeed,
        address _marketFeed,
        address _quote,
        address _eth,
        uint128 _amountIn,
        uint256 _macroWindow,
        uint256 _microWindow,
        uint256 _priceFrameCap
    ) OverlayV1UniswapV3Market (
        _mothership,
        _ovlFeed,
        _marketFeed,
        _quote,
        _eth,
        _amountIn,
        _macroWindow,
        _microWindow,
        _priceFrameCap
    ) { }


    function _update (
        uint32 _updated,
        uint32 _compounded,
        uint8 _brrrrdCycloid
    ) internal virtual override returns (
        uint cap_,
        uint32 updated_,
        uint32 compounded_
    ) {

        (   cap_,
            updated_,
            compounded_ ) = super._update(
                _updated,
                _compounded,
                _brrrrdCycloid
            );

        cap_ = lmbda == 0 ? staticCap : cap_;

    }

    function oiCap () public override view returns ( 
        uint cap_ 
    ) {

        cap_ = super.oiCap();
        cap_ = lmbda == 0 ? staticCap : cap_;

    }

    function _oiCap (
        uint _depth,
        uint8 _brrrrdCycloid
    ) internal override view returns (
        uint cap_
    ) {

        cap_ = super._oiCap(_depth, _brrrrdCycloid);
        cap_ = lmbda == 0 ? staticCap : cap_;

    }

}