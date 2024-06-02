// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "../interfaces/IOverlayV1Market.sol";
import "../OverlayToken.sol";

contract OverlayV1Mothership is AccessControlEnumerable {

    uint public constant MIN_FEE = 1e14; // 0.01%
    uint public constant MAX_FEE = 1e16; // 1.00%

    uint public constant MAX_FEE_BURN = 1e18; // 100%
    uint public constant MAX_MARGIN_BURN = 1e18; // 100%

    bytes32 public constant ADMIN = 0x00;
    bytes32 public constant GOVERNOR = keccak256("GOVERNOR");

    // ovl erc20 token
    address public immutable ovl;

    // global params adjustable by gov
    // address to send fees to
    address public feeTo;
    // build/unwind trading fee
    uint public fee;
    // portion of build/unwind fee burnt
    uint public feeBurnRate;
    // portion of liquidations to burn on update
    uint public marginBurnRate;

    mapping(address => bool) public marketActive;
    mapping(address => bool) public marketExists;
    address[] public allMarkets;

    mapping(address => bool) public collateralExists;
    mapping(address => bool) public collateralActive;
    address[] public allCollaterals;

    event UpdateCollateral(address collateral, bool active);
    event UpdateMarket(address market, bool active);

    event UpdateFeeTo(address feeTo);
    event UpdateFee(uint fee);
    event UpdateFeeBurnRate(uint feeBurnRate);
    event UpdateMarginBurnRate(uint marginBurnRate);

    modifier onlyGovernor () {
        require(hasRole(GOVERNOR, msg.sender), "OVLV1:!gov");
        _;
    }

    constructor(
        address _ovl,
        address _feeTo,
        uint _fee,
        uint _feeBurnRate,
        uint _marginBurnRate
    ) {

        _setupRole(ADMIN, msg.sender);
        _setupRole(GOVERNOR, msg.sender);
        _setRoleAdmin(GOVERNOR, ADMIN);

        // immutable params
        ovl = _ovl;

        // global params
        _setFeeTo(_feeTo);
        _setFee(_fee);
        _setFeeBurnRate(_feeBurnRate);
        _setMarginBurnRate(_marginBurnRate);
    }

    function totalMarkets () external view returns (uint) {
        return allMarkets.length;
    }

    function totalCollaterals () external view returns (uint) {
        return allCollaterals.length;
    }

    /**
      @notice Make this contract aware of a new market contract's existence
      @dev Should be called after contract deployment in specific market factory.createMarket
      @dev Only the Governor can initialize a market
      @dev Appends new market address to `allMarkets` array to track them
      @param _market Overlay market contract address
      */
    function initializeMarket(address _market) external onlyGovernor {
        require(!marketExists[_market], "OVLV1: market exists");

        marketExists[_market] = true;
        marketActive[_market] = true;
        allMarkets.push(_market);

        emit UpdateMarket(_market, true);
    }

    function disableMarket(address _market) external onlyGovernor {
        require(marketExists[_market], "OVLV1: market !exists");
        require(marketActive[_market], "OVLV1: market !enabled");

        marketActive[_market] = false;

        emit UpdateMarket(_market, false);
    }

    function enableMarket(address _market) external onlyGovernor {
        require(marketExists[_market], "OVLV1: market !exists");
        require(!marketActive[_market], "OVLV1: market !disabled");

        marketActive[_market] = true;

        emit UpdateMarket(_market, true);
    }

    /**
      @notice Make this contract aware of a new collateral contract's existence
      @dev Adds collateral contract address to the `collateralExists` and `collateralActive` mappings
      @dev Only the Governor can set market info
      @param _collateral Overlay OVL collateral contract address
      */
    function initializeCollateral (address _collateral) external onlyGovernor {
        require(!collateralExists[_collateral], "OVLV1: collateral exists");

        collateralExists[_collateral] = true;
        collateralActive[_collateral] = true;
        allCollaterals.push(_collateral);

        OverlayToken(ovl).grantRole(OverlayToken(ovl).MINTER_ROLE(), _collateral);
        OverlayToken(ovl).grantRole(OverlayToken(ovl).BURNER_ROLE(), _collateral);

        emit UpdateCollateral(_collateral, true);
    }

    function enableCollateral (address _collateral) external onlyGovernor {
        require(collateralExists[_collateral], "OVLV1: collateral !exists");
        require(!collateralActive[_collateral], "OVLV1: collateral !disabled");

        collateralActive[_collateral] = true;

        OverlayToken(ovl).grantRole(OverlayToken(ovl).MINTER_ROLE(), _collateral);
        OverlayToken(ovl).grantRole(OverlayToken(ovl).BURNER_ROLE(), _collateral);

        emit UpdateCollateral(_collateral, true);
    }

    function disableCollateral (address _collateral) external onlyGovernor {
        require(collateralExists[_collateral], "OVLV1: collateral !exists");
        require(collateralActive[_collateral], "OVLV1: collateral !enabled");

        collateralActive[_collateral] = false;

        OverlayToken(ovl).revokeRole(OverlayToken(ovl).MINTER_ROLE(), _collateral);
        OverlayToken(ovl).revokeRole(OverlayToken(ovl).BURNER_ROLE(), _collateral);

        emit UpdateCollateral(_collateral, false);
    }

    function setFeeTo(address _feeTo) external onlyGovernor {
        _setFeeTo(_feeTo);
    }

    function setFee(uint _fee) external onlyGovernor {
        _setFee(_fee);
    }

    function setFeeBurnRate(uint _feeBurnRate) external onlyGovernor {
        _setFeeBurnRate(_feeBurnRate);
    }

    /// @notice Allows gov to adjust global params
    function adjustGlobalParams(
        uint16 _fee,
        uint16 _feeBurnRate,
        address _feeTo
    ) external onlyGovernor {
      _setFee(_fee);
      _setFeeBurnRate(_feeBurnRate);
      _setFeeTo(_feeTo);
    }
    
    function setMarginBurnRate(uint _marginBurnRate) external onlyGovernor {
        _setMarginBurnRate(_marginBurnRate);
    }

    function _setFeeTo(address _feeTo) internal {
        require(_feeTo != address(0), "OVLV1: fees to the zero address");
        feeTo = _feeTo;
        emit UpdateFeeTo(_feeTo);
    }

    function _setFee(uint _fee) internal {
        require(_fee >= MIN_FEE && _fee <= MAX_FEE, "OVLV1: fee rate out of bounds");
        fee = _fee;
        emit UpdateFee(_fee);
    }

    function _setFeeBurnRate(uint _feeBurnRate) internal {
        require(_feeBurnRate <= MAX_FEE_BURN, "OVLV1: fee burn rate out of bounds");
        feeBurnRate = _feeBurnRate;
        emit UpdateFeeBurnRate(_feeBurnRate);
    }

    function _setMarginBurnRate(uint _marginBurnRate) internal {
        require(_marginBurnRate <= MAX_MARGIN_BURN, "OVLV1: margin burn rate out of bounds");
        marginBurnRate = _marginBurnRate;
        emit UpdateMarginBurnRate(_marginBurnRate);
    }

    function getGlobalParams() external view returns (
        address feeTo_,
        uint fee_,
        uint feeBurnRate_,
        uint marginBurnRate_
    ) {
        feeTo_ = feeTo;
        fee_ = fee;
        feeBurnRate_ = feeBurnRate;
        marginBurnRate_ = marginBurnRate;
    }

}
