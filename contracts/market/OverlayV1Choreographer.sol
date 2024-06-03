// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../interfaces/IOverlayV1Mothership.sol";
import "../interfaces/IOverlayToken.sol";
import "../interfaces/IOverlayTokenNew.sol";
import "./OverlayV1Comptroller.sol";
import "./OverlayV1OI.sol";
import "./OverlayV1PricePoint.sol";

abstract contract OverlayV1Choreographer is
    OverlayV1Comptroller,
    OverlayV1OI,
    OverlayV1PricePoint {

    uint constant private ONE = 1e18;

    bytes32 constant private COLLATERAL = keccak256("COLLATERAL");
    bytes32 constant private GOVERNOR = keccak256("GOVERNOR");
    bytes32 constant private MARKET = keccak256("MARKET");

    address public immutable ovl;

    IOverlayV1Mothership public immutable mothership;

    uint256 public leverageMax;

    mapping (address => bool) public isCollateral;

    modifier onlyCollateral () {
        require(isCollateral[msg.sender], "OVLV1:!collateral");
        _;
    }

    modifier onlyGovernor () {
        require(mothership.hasRole(GOVERNOR, msg.sender), "OVLV1:!governor");
        _;
    }

    modifier enabled() {
        require(mothership.hasRole(MARKET, address(this)), "OVLV1:!enabled");
        _;
    }

    struct Tempo {
        uint32 updated;
        uint32 compounded;
        uint8 impactCycloid;
        uint8 brrrrdCycloid;
        uint32 brrrrdFiling;
    }

    Tempo public tempo;

    constructor(
        address _mothership
    ) {

        mothership = IOverlayV1Mothership(_mothership);
        ovl = address(IOverlayV1Mothership(_mothership).ovl());

        uint32 _now = uint32(block.timestamp);

        tempo.updated = _now;
        tempo.compounded = _now;
        tempo.brrrrdFiling = _now;

    }

    function addCollateral (address _collateral) public onlyGovernor {

        isCollateral[_collateral] = true;

    }

    function removeCollateral (address _collateral) public onlyGovernor {

        isCollateral[_collateral] = false;

    }

    function setEverything (
        uint256 _k,
        uint256 _pbnj,
        uint256 _lmbda,
        uint256 _staticCap,
        uint256 _brrrrdExpected,
        uint256 _brrrrdWindowMacro,
        uint256 _brrrrdWindowMicro
    ) public onlyGovernor {

        setK(_k);

        setSpread(_pbnj);

        setComptrollerParams(
            _lmbda,
            _staticCap,
            _brrrrdExpected,
            _brrrrdWindowMacro,
            _brrrrdWindowMicro
        );

    }

    function setSpread(
        uint256 _pbnj
    ) public onlyGovernor {

        pbnj = _pbnj;

    }

    function setK (
        uint256 _k
    ) public onlyGovernor {
        k = _k;
    }

    function setComptrollerParams (
        uint256 _lmbda,
        uint256 _staticCap,
        uint256 _brrrrExpected,
        uint256 _brrrrdWindowMacro,
        uint256 _brrrrdWindowMicro
    ) public onlyGovernor {

        lmbda = _lmbda;
        staticCap = _staticCap;
        brrrrdExpected = _brrrrExpected;
        brrrrdWindowMacro = uint32(_brrrrdWindowMacro);
        brrrrdWindowMicro = uint32(_brrrrdWindowMicro);

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

    function oi () public view override returns (
        uint oiLong_,
        uint oiShort_,
        uint oiLongShares_,
        uint oiShortShares_
    ) {

        (   uint32 _compoundings, ) = epochs(
            uint32(block.timestamp),
            tempo.compounded
        );

        return _oi(_compoundings);

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

        OverlayV1Choreographer.Tempo memory _tempo = tempo;

        (   uint32 _compoundings, ) = epochs(
            uint32(block.timestamp), 
            _tempo.compounded
        );

        (   uint _oiLong,
            uint _oiShort,
            uint _oiLongShares,
            uint _oiShortShares ) = _oi(_compoundings);

        if (_isLong) ( oi_ = _oiLong, oiShares_ = _oiLongShares );
        else ( oi_ = _oiShort, oiShares_ = _oiShortShares );

        priceFrame_ = priceFrame(
            _isLong,
            _priceEntry
        );

    }

}
