// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "./libraries/FixedPoint.sol";
import "./libraries/UniswapV3OracleLibrary/TickMath.sol";
import "./interfaces/IBalancerVault.sol";
import "./interfaces/IBalancerFeed.sol";
import "./market/OverlayV1Market.sol";

contract OverlayV1BalancerV2Market is OverlayV1Market {

    using FixedPoint for uint256;
    using LogExpMath for uint256;

    uint256 internal ONE = 1e18;
    uint256 internal X96 = 0x1000000000000000000000000;

    uint256 public immutable macroWindow; // window size for main TWAP
    uint256 public immutable microWindow; // window size for bid/ask TWAP

    address public immutable marketFeed;
    address public immutable ovlFeed;
    address public immutable base;
    address public immutable quote;
    uint128 internal immutable baseAmount;
    uint256 immutable w0;
    uint256 immutable w1;

    address internal immutable eth;
    bool internal immutable ethIs0;

    constructor(
        address _mothership,
        address _balancerVault,
        address _ovlFeed,
        address _marketFeed,
        address _quote,
        address _eth,
        uint128 _baseAmount,
        uint256 _macroWindow,
        uint256 _microWindow,
        uint256 _priceFrameCap
    ) OverlayV1Market (
        _mothership
    ) OverlayV1Comptroller (
        _microWindow
    ) OverlayV1OI (
        _microWindow
    ) OverlayV1PricePoint (
        _priceFrameCap
    ) {

        // immutables
        eth = _eth;
        ovlFeed = _ovlFeed;
        marketFeed = _marketFeed;
        baseAmount = _baseAmount;
        macroWindow = _macroWindow;
        microWindow = _microWindow;

        // TODO: just to compile for now.

        ( address[] memory _marketTokens,, ) = IBalancerVault(_balancerVault).getPoolTokens(
            IBalancerFeed(_marketFeed).getPoolId()
        );

        uint[] memory _weights = IBalancerFeed(_marketFeed).getNormalizedWeights();

        ethIs0 = _marketTokens[0] == _eth;

        w0 = _marketTokens[0] == _eth ?  _weights[0] : _weights[1];
        w1 = _marketTokens[0] != _eth ?  _weights[0] : _weights[1];

        quote = _quote;
        base = _marketTokens[1] == _quote 
            ? _marketTokens[0]
            : _marketTokens[1];

    }


    /// @notice Reads the current price and depth information
    /// @dev Reads price and depth of market feed
    /// @return price_ Price point
    function fetchPricePoint () public view override returns (
        PricePoint memory price_
    ) { 


        IBalancerFeed.Query[] memory _queries = new IBalancerFeed.Query[](3);
        _queries[0] = IBalancerFeed.Query(IBalancerFeed.Variable.PAIR_PRICE, macroWindow, 0);
        _queries[1] = IBalancerFeed.Query(IBalancerFeed.Variable.PAIR_PRICE, microWindow, 0);
        _queries[2] = IBalancerFeed.Query(IBalancerFeed.Variable.INVARIANT, microWindow, 0);

        uint[] memory _marketResults = IBalancerFeed(marketFeed).getTimeWeightedAverage(_queries);

        uint _macroPrice = ethIs0 ? ONE.divUp(_marketResults[0]) : _marketResults[0];
        uint _microPrice = ethIs0 ? ONE.divUp(_marketResults[1]) : _marketResults[1];
        uint _microInvariant = _marketResults[2];
        
        uint _marketLiquidity = ethIs0
            ? _microInvariant.pow(w0).mulDown(_microPrice)
            : _microInvariant.pow(w1).divDown(_microPrice);

    }


    /// @notice Arithmetic to get depth
    /// @dev Derived from cnstant product formula X*Y=K and tailored 
    /// to Uniswap V3 selective liquidity provision.
    /// @param _marketLiquidity Amount of liquidity in market in ETH terms.
    /// @param _ovlPrice Price of OVL against ETH.
    /// @return depth_ Depth criteria for market in OVL terms.
    function computeDepth (
        uint _marketLiquidity,
        uint _ovlPrice
    ) public override view returns (
        uint depth_
    ) {

        depth_ = ((_marketLiquidity * 1e18) / _ovlPrice)
            .mulUp(lmbda)    
            .divDown(2e18);

    }

    function _tickToPrice (
        int24 _tick
    ) public override view returns (
        uint quote_
    ) { }

}
