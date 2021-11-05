// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "./libraries/FixedPoint.sol";
import "./libraries/UniswapV3OracleLibrary/UniswapV3OracleLibraryV2.sol";
import "./interfaces/IUniswapV3Pool.sol";
import "./market/OverlayV1Market.sol";

contract OverlayV1UniswapV3Market is OverlayV1Market {

    using FixedPoint for uint256;

    uint256 internal X96 = 0x1000000000000000000000000;

    uint256 public immutable macroWindow; // window size for main TWAP
    uint256 public immutable microWindow; // window size for bid/ask TWAP

    address public immutable marketFeed;
    address public immutable ovlFeed;
    address public immutable base;
    address public immutable quote;
    uint128 internal immutable amountIn;

    address internal immutable eth;
    bool internal immutable ethIs0;

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
    ) OverlayV1Market (
        _mothership
    ) OverlayV1Comptroller (
        _microWindow
    ) OverlayV1PricePoint (
        _priceFrameCap
    ) {

        // immutables
        eth = _eth;
        ethIs0 = IUniswapV3Pool(_ovlFeed).token0() == _eth;
        ovlFeed = _ovlFeed;
        marketFeed = _marketFeed;
        amountIn = _amountIn;
        macroWindow = _macroWindow;
        microWindow = _microWindow;

        address _token0 = IUniswapV3Pool(_marketFeed).token0();
        address _token1 = IUniswapV3Pool(_marketFeed).token1();

        base = _token0 != _quote ? _token0 : _token1;
        quote = _token0 == _quote ? _token0 : _token1;

        int24 _tick = OracleLibraryV2.consult(
            _marketFeed,
            uint32(_macroWindow),
            uint32(0)
        );

        uint _price = OracleLibraryV2.getQuoteAtTick(
            _tick,
            uint128(_amountIn),
            _token0 != _quote ? _token0 : _token1,
            _token0 == _quote ? _token0 : _token1
        );

        setPricePointNext(insertSpread(_price, _price));

        updated = block.timestamp;
        compounded = block.timestamp;

    }


    /// @notice Reads the current price and depth information
    /// @dev Conditionall reads price and time weighted liquidity of market feed
    /// @param _price To read the price or not
    /// @param _depth To read the depth or not
    /// @return price_ Current price. Returns emptry struct if price isn't read
    /// @return depth_ Current depth. Returns 0 if depth is not read.
    function readFeed (
        bool _price,
        bool _depth
    ) public view returns (
        PricePoint memory price_,
        uint256 depth_
    ) {

        int56[] memory _ticks;
        uint160[] memory _liqs;

        if (_price) {

            uint32[] memory _secondsAgo = new uint32[](3);
            _secondsAgo[2] = uint32(macroWindow);
            _secondsAgo[1] = uint32(microWindow);

            ( _ticks, _liqs ) = IUniswapV3Pool(marketFeed).observe(_secondsAgo);

            uint _macroPrice = OracleLibraryV2.getQuoteAtTick(
                int24((_ticks[0] - _ticks[2]) / int56(int32(int(macroWindow)))),
                amountIn,
                base,
                quote
            );

            uint _microPrice = OracleLibraryV2.getQuoteAtTick(
                int24((_ticks[0] - _ticks[1]) / int56(int32(int(microWindow)))),
                amountIn,
                base,
                quote
            );

            price_ = insertSpread(_microPrice, _macroPrice);

        }

        if (_depth) {

            uint32[] memory _secondsAgo = new uint32[](2);

            if (!_price) {

                _secondsAgo[1] = uint32(microWindow);

                ( _ticks, _liqs ) = IUniswapV3Pool(marketFeed).observe(_secondsAgo);

            }

            uint256 _sqrtPrice = TickMath.getSqrtRatioAtTick(
                int24((_ticks[0] - _ticks[1]) / int56(int32(int(microWindow))))
            );

            uint256 _liquidity = (uint160(microWindow) << 128) / ( _liqs[0] - _liqs[1] );

            uint _ethAmount = ethIs0
                ? ( uint256(_liquidity) << 96 ) / _sqrtPrice
                : FullMath.mulDiv(uint256(_liquidity), _sqrtPrice, X96);

            _secondsAgo[1] = uint32(macroWindow);

            ( _ticks, ) = IUniswapV3Pool(ovlFeed).observe(_secondsAgo);

            uint _ovlPrice = OracleLibraryV2.getQuoteAtTick(
                int24((_ticks[0] - _ticks[1]) / int56(int32(int(macroWindow)))),
                1e18,
                ovl,
                eth
            );

            depth_ = lmbda.mulUp(( _ethAmount * 1e18 ) / _ovlPrice).divDown(2e18);

        }

    }


    /// @notice The price at the current block
    /// @dev Returns the price of the current block.
    /// @return price_ The price point for the current block consisting of 
    /// the bid, the ask, TODO: ...and maybe the depth.
    function price () public view override returns (PricePoint memory price_) {

        ( price_, ) = readFeed(true, false);

    }


    /// @notice The depth of the market feed in OVL terms at the current block.
    /// @dev Returns the time weighted liquidity of the market feed in 
    /// OVL terms at the current block.
    /// @return depth_ The time weighted liquidity in OVL terms.
    function depth () public view override returns (uint depth_) {

        (   ,depth_ ) = readFeed(false, true);

    }


    /// @notice The compounding information for computing funding.
    /// @dev This returns the number of compoundings that have passed since 
    /// the last time funding was paid as well as the timestamp of the 
    /// current compounding epoch, which come at regular intervals according
    /// to the compounding period.
    /// @param _now The timestamp of the current block.
    /// @param _compounded The last time compounding occurred.
    /// @return compoundings_ The number of compounding periods passed since
    /// the last time funding was compounded.
    /// @return tCompounding_ The current compounding epoch.
    function epochs (
        uint _now,
        uint _compounded
    ) public view returns (
        uint compoundings_,
        uint tCompounding_
    ) {

        uint _compoundPeriod = compoundingPeriod;

        compoundings_ = ( _now - _compounded ) / _compoundPeriod;

        tCompounding_ = _compounded + ( compoundings_ * _compoundPeriod );

    }


    /// @notice Internal update function to price, cap, and pay funding.
    /// @dev This function updates the market with the latest price and 
    /// conditionally reads the depth of the market feed. The market needs
    /// an update on the first call of any block.
    /// @param _readDepth Whether or not to read the depth of the market feed.
    /// @return cap_ The open interest cap for the market.
    function _update (
        bool _readDepth
    ) internal virtual override returns (
        uint cap_
    ) {

        uint _brrrrdExpected;
        uint _now = block.timestamp;
        uint _updated = updated;

        uint _depth;
        PricePoint memory _price;
        bool _readPrice = _now != _updated;

        if (_readDepth) {

            (   uint _brrrrd,
                uint _antiBrrrrd ) = getBrrrrd();

            bool _burnt;
            bool _expected;
            bool _surpassed;

            if (_brrrrd < _antiBrrrrd) _burnt = true;
            else {
                _brrrrdExpected = brrrrdExpected;
                _brrrrd -= _antiBrrrrd;
                _expected = _brrrrd < _brrrrdExpected;
                _surpassed = _brrrrd > _brrrrdExpected * 2;
            }

            ( _price, _depth ) = readFeed(_readPrice, _burnt || _expected || !_surpassed);

            if (_readPrice) setPricePointNext(_price);

            cap_ = _surpassed ? 0 : _burnt || _expected
                ? _oiCap(false, _depth, staticCap, 0, 0)
                : _oiCap(true, _depth, staticCap, _brrrrd, _brrrrdExpected);

        } else if (_readPrice) {

            ( _price, ) = readFeed(true, false);

            setPricePointNext(_price);

        }

        (   uint _compoundings,
            uint _tCompounding  ) = epochs(_now, compounded);

        if (0 < _compoundings) {

            payFunding(k, _compoundings);
            compounded = _tCompounding;

        }

    }


    /// @notice The current open interest on both sides of the market.
    /// @dev Returns all up to date open interest data for the market.
    /// @return oiLong_ Current open interest on long side.
    /// @return oiShort_ Current open interest on short side.
    /// @return oiLongShares_ Current open interest shares on the long side.
    /// @return oiShortShares_ Current open interest shares on the short side.
    function oi () public view returns (
        uint oiLong_,
        uint oiShort_,
        uint oiLongShares_,
        uint oiShortShares_
    ) {

        ( uint _compoundings, ) = epochs(block.timestamp, compounded);

        (   oiLong_,
            oiShort_,
            oiLongShares_,
            oiShortShares_ ) = _oi(_compoundings);

    }


    /// @notice Internal function to retrieve up to date open interest.
    /// @dev Computes the current open interest values and returns them.
    /// @param _compoundings Number of compoundings yet to be paid in funding.
    /// @return oiLong_ Current open interest on the long side.
    /// @return oiShort_ Current open interest on the short side.
    /// @return oiLongShares_ Current open interest shares on the long side.
    /// @return oiShortShares_ Current open interest shares on the short side.
    function _oi (
        uint _compoundings
    ) internal view returns (
        uint oiLong_,
        uint oiShort_,
        uint oiLongShares_,
        uint oiShortShares_
    ) {

        oiLong_ = __oiLong__;
        oiShort_ = __oiShort__;
        oiLongShares_ = oiLongShares;
        oiShortShares_ = oiShortShares;

        if (0 < _compoundings) {

            ( oiLong_, oiShort_, ) = computeFunding(
                oiLong_,
                oiShort_,
                _compoundings,
                k
            );

        }

    }

    /// @notice The current open interest on the long side.
    /// @return oiLong_ The current open interest on the long side.
    function oiLong () external view returns (uint oiLong_) {
        (   oiLong_,,, ) = oi();
    }


    /// @notice The current open interest on the short side.    
    /// @return oiShort_ The current open interest on the short side.
    function oiShort () external view returns (uint oiShort_) {
        (  ,oiShort_,, ) = oi();
    }


    /// @notice Exposes important info for calculating position metrics.
    /// @dev These values are required to feed to the position calculations.
    /// @param _isLong Whether position is on short or long side of market.
    /// @param _priceEntry Index of entry price
    /// @return oi_ The current open interest on the chosen side.
    /// @return oiShares_ The current open interest shares on the chosen side.
    /// @return priceFrame_ Price frame resulting from e entry and exit prices.
    function positionInfo (
        bool _isLong,
        uint _priceEntry
    ) external view returns (
        uint256 oi_,
        uint256 oiShares_,
        uint256 priceFrame_
    ) {

        (   uint _compoundings, ) = epochs(block.timestamp, compounded);

        priceFrame_ = priceFrame(
            _isLong,
            _priceEntry
        );

        (   uint _oiLong,
            uint _oiShort,
            uint _oiLongShares,
            uint _oiShortShares ) = _oi(_compoundings);

        if (_isLong) ( oi_ = _oiLong, oiShares_ = _oiLongShares );
        else ( oi_ = _oiShort, oiShares_ = _oiShortShares );

    }


    /// @notice Computes the price frame for a given position
    /// @dev Computes the price frame conditionally giving shorts the bid
    /// on entry and ask on exit and longs the bid on exit and short on
    /// entry. Capped at the priceFrameCap for longs.
    /// @param _isLong If price frame is for a long or a short.
    /// @param _entryIndex The index of the entry price.
    /// @return priceFrame_ The exit price divided by the entry price.
    function priceFrame (
        bool _isLong,
        uint _entryIndex
    ) internal view returns (
        uint256 priceFrame_
    ) {

        PricePoint memory _priceEntry = _pricePoints[_entryIndex];

        PricePoint memory _priceExit;

        if (updated != block.timestamp) _priceExit = price();
        else _priceExit = _pricePoints[_pricePoints.length - 1];

        priceFrame_ = _isLong
            ? Math.min(_priceExit.bid.divDown(_priceEntry.ask), priceFrameCap)
            : _priceExit.ask.divUp(_priceEntry.bid);

    }

}
