// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../market/OverlayV1PricePoint.sol";
import "../market/OverlayV1Comptroller.sol";
import "../interfaces/IOverlayToken.sol";
import "../interfaces/IUniswapV3Pool.sol";
import "../libraries/UniswapV3OracleLibrary/UniswapV3OracleLibraryV2.sol";
import "../libraries/FixedPoint.sol";

contract ComptrollerShim is OverlayV1Comptroller {

    using FixedPoint for uint256;

    uint256 internal X96 = 0x1000000000000000000000000;

    IOverlayToken public ovl;

    address public ovlFeed;
    address public marketFeed;
    address public eth;

    bool public ethIs0;

    uint public macroWindow;
    uint public microWindow;

    struct Tempo {
        uint32 updated;
        uint32 compounded;
        uint8 impactCycloid;
        uint8 brrrrdCycloid;
        uint32 brrrrdFiling;
    }

    Tempo public tempo;

    /**
      @notice Constructor method
      @param _lmbda market impact
      @param _staticCap open interest cap
      @param _brrrrdExpected expected worst-case inflation rate
      @param _brrrrdWindowMacro macro rolling price window in which _brrrrdExpected is calculated over
      @param _brrrrdWindowMicro micro rolling price window in which _brrrrdExpected is calculated over
      @param _priceWindowMacro only the main TWAP, only used for the price
      @param _priceWindowMicro short TWAP to temper the bid-ask spread, compounding period, impact window
      @param _marketFeed Oracle address providing the market feed data
      @param _ovlFeed Oracle address providing the depth feed data (the OVL feed)
      @param _ovl OVL token contract address
      @param _eth Wrapped eth contract address
     */
    constructor (
        uint _lmbda,
        uint _staticCap,
        uint _brrrrdExpected,
        uint _brrrrdWindowMacro,
        uint _brrrrdWindowMicro,
        uint _priceWindowMacro,
        uint _priceWindowMicro,
        address _marketFeed,
        address _ovlFeed,
        address _ovl,
        address _eth
    ) OverlayV1Comptroller (
        _priceWindowMicro
    ){

        lmbda = _lmbda;
        staticCap = _staticCap;
        brrrrdExpected = _brrrrdExpected;
        brrrrdWindowMacro = uint32(_brrrrdWindowMacro);
        brrrrdWindowMicro = uint32(_brrrrdWindowMicro);
        macroWindow = _priceWindowMacro;
        microWindow = _priceWindowMicro;
        marketFeed = _marketFeed;
        ovlFeed = _ovlFeed;
        ethIs0 = IUniswapV3Pool(_ovlFeed).token0() == _eth;

        tempo.brrrrdFiling = uint32(block.timestamp);

    }


    function depth () public view override returns (uint depth_) {

        depth_ = staticCap;

    }

    function pressure (
        bool _isLong,
        uint _oi,
        uint _cap
    ) public view override returns (uint pressure_) {

        pressure_ = _pressure(
            _isLong,
            _oi,
            _cap,
            tempo.impactCycloid
        );

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
    function oiCap () public view virtual override returns (
        uint cap_
    ) {

        cap_ = _oiCap( depth() , tempo.brrrrdCycloid);

    }

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

    function readFeed () public view returns (
        uint256 depth_
    ) { 

        int56[] memory _ticks;
        uint160[] memory _liqs;

        uint32[] memory _secondsAgo = new uint32[](2);

        _secondsAgo[1] = uint32(microWindow);

        ( _ticks, _liqs ) = IUniswapV3Pool(marketFeed).observe(_secondsAgo);

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
            address(ovl),
            eth
        );

        depth_ = lmbda.mulUp(( _ethAmount * 1e18 ) / _ovlPrice).divDown(2e18);

    }

    function setRoller (
        uint index,
        uint __timestamp,
        uint __longPressure,
        uint __shortPressure
    ) public {

        impactRollers[index].time = __timestamp;
        impactRollers[index].ying = __longPressure;
        impactRollers[index].yang = __shortPressure;

    }

    function viewScry(
        uint _ago
    ) public view returns (
        Roller memory rollerNow_,
        Roller memory rollerThen_
    ) {

        uint lastMoment;

        (   lastMoment,
            rollerNow_,
            rollerThen_ ) = scry(
                impactRollers, 
                tempo.impactCycloid, 
                _ago
            );


    }

    function brrrrBatch (
        uint[] memory _brrrr,
        uint[] memory _antiBrrrr
    ) public {

        uint len = _brrrr.length;

        for (uint i = 0; i < len; i++) {

            (   tempo.brrrrdCycloid, 
                tempo.brrrrdFiling ) = brrrr( 
                    _brrrr[i], 
                    _antiBrrrr[i],
                    tempo.brrrrdCycloid,
                    tempo.brrrrdFiling
                );

        }

    }

    function impactBatch (
        bool[] memory _isLong,
        uint[] memory _oi
    ) public returns (
        uint impact_
    ) {

        uint len = _isLong.length;

        for (uint i = 0; i < len; i++) {

            uint _cap = oiCap();

            (   impact_,
                tempo.impactCycloid,
                tempo.brrrrdCycloid,
                tempo.brrrrdFiling )= intake(
                    _isLong[i], 
                    _oi[i], 
                    _cap,
                    tempo.impactCycloid,
                    tempo.brrrrdCycloid,
                    tempo.brrrrdFiling
                );

        }

    }

    function viewImpact (
        bool _isLong,
        uint _oi
    ) public view returns (
        uint impact_
    ) {

        uint _cap = oiCap();

        ( ,,impact_ ) = _intake(
            _isLong, 
            _oi, 
            _cap,
            tempo.impactCycloid
        );

    }

}
