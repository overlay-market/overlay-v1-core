// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../interfaces/IOverlayV1Mothership.sol";
import "../interfaces/IOverlayToken.sol";
import "../interfaces/IOverlayTokenNew.sol";
import "./OverlayV1Comptroller.sol";
import "./OverlayV1OI.sol";
import "./OverlayV1PricePoint.sol";

abstract contract OverlayV1Governance is
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

    constructor(
        address _mothership
    ) {

        mothership = IOverlayV1Mothership(_mothership);
        ovl = address(IOverlayV1Mothership(_mothership).ovl());

    }

    function addCollateral (address _collateral) public onlyGovernor {

        isCollateral[_collateral] = true;

    }

    function removeCollateral (address _collateral) public onlyGovernor {

        isCollateral[_collateral] = false;

    }

    /// @notice TODO
    /// @dev Inherited by OverlayV1Market -> OverlayV1UniswapV3Market contract
    /// @dev Called by the Governor Role
    /// @param _k Funding constant
    /// @param _pbnj Static spread
    /// @param _compoundPeriod Compounding period
    /// @param _lmbda Market impact
    /// @param _staticCap Open interest cap
    /// @param _brrrrdExpected TODO
    /// @param _brrrrdWindowMacro Rolling window
    /// @param _brrrrdWindowMicro Rolling window
    function setEverything (
        uint256 _k,
        uint256 _pbnj,
        uint256 _compoundPeriod,
        uint256 _lmbda,
        uint256 _staticCap,
        uint256 _brrrrdExpected,
        uint256 _brrrrdWindowMacro,
        uint256 _brrrrdWindowMicro
    ) public onlyGovernor {

        // TODO: if internal function call only -> should prefix with _
        setK(_k);

        // TODO: if internal function call only -> should prefix with _
        setSpread(_pbnj);

        // TODO: if internal function call only -> should prefix with _
        setPeriods(_compoundPeriod);

        // TODO: if internal function call only -> should prefix with _
        setComptrollerParams(
            _lmbda,
            _staticCap,
            _brrrrdExpected,
            _brrrrdWindowMacro,
            _brrrrdWindowMicro
        );

    }

    /// @notice Sets the static spread state variable, pbnj
    /// @dev State variable pbnj is defined in the OverlayV1PricePoint contract
    /// @dev Called by the Governor Role, TODO: is this function ever called
    /// @dev outside this contract? If not, don't expose it.
    /// @dev Called by internal contract function: setEverything
    /// @param _pbnj Static spread
    function setSpread(
        uint256 _pbnj
    ) public onlyGovernor {

        pbnj = _pbnj;

    }

    /// @notice Sets the funding constant state variable, k
    /// @dev State variable k is defined in the OverlayV1OI contract
    /// @dev Called by the Governor Role, TODO: is this function ever called
    /// @dev outside this contract? If not, don't expose it.
    /// @dev Called by internal contract function: setEverything
    /// @param _k Funding constant
    function setK (
        uint256 _k
    ) public onlyGovernor {
        k = _k;
    }

    /// @notice Sets the compounding period state variable, compoundingPeriod
    /// @dev State variable pbnj is defined in the OverlayV1PricePoint contract
    /// @dev Called by the Governor Role, TODO: is this function ever called
    /// @dev outside this contract? If not, don't expose it.
    /// @dev Called by internal contract function: setEverything
    /// @param _compoundingPeriod Compounding period
    function setPeriods(
        uint256 _compoundingPeriod
    ) public onlyGovernor {

        compoundingPeriod = _compoundingPeriod;

    }

    /// @notice Sets the market impact, open interest cap, TODO
    /// @notice (_brrrrExpected), TODO (_brrrrdWindowMacro), TODO
    /// @notice (_brrrrdWindowMicro) state variables which are _lmbda, 
    /// @notice _staticCap, _brrrrExpected, _brrrrdWindowMacro, and 
    /// @notice _brrrrdWindowMicro, respectively
    /// @dev State variable lmbda, staticCap, brrrrExpected, brrrrdWindowMacro,
    /// @dev and brrrrdWindowMicro are defined in the OverlayV1Comptroller
    /// @dev contract
    /// @dev Called by the Governor Role, TODO: is this function ever called
    /// @dev outside this contract? If not, don't expose it.
    /// @dev Called by internal contract function: setEverything
    /// @param _lmbda Market impact
    /// @param _staticCap Open interest cap
    /// @param _brrrrExpected TODO
    /// @param _brrrrdWindowMacro Rolling window
    /// @param _brrrrdWindowMicro Rolling window
    function setComptrollerParams (
        uint256 _lmbda,
        uint256 _staticCap,
        uint256 _brrrrExpected,
        uint256 _brrrrdWindowMacro,
        uint256 _brrrrdWindowMicro
    ) public onlyGovernor {

        lmbda = _lmbda;
        staticCap = _staticCap;
        // TODO: brrrExpected vs brrrr*d*Expected
        brrrrdExpected = _brrrrExpected;
        brrrrdWindowMacro = _brrrrdWindowMacro;
        brrrrdWindowMicro = _brrrrdWindowMicro;

    }

}
