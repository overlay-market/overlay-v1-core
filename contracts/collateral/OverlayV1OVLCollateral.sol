
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../libraries/Position.sol";
import "../libraries/FixedPoint.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Supply.sol";
import "../interfaces/IOverlayV1Market.sol";
import "../interfaces/IOverlayV1Mothership.sol";
import "../interfaces/IOverlayToken.sol";
import "../interfaces/IOverlayTokenNew.sol";

contract OverlayV1OVLCollateral is ERC1155Supply {

    event log(string k, uint v);
    event log_addr(string k, address v);

    using Position for Position.Info;
    using FixedPoint for uint256;

    bytes32 constant private GOVERNOR = keccak256("GOVERNOR");

    mapping (uint => mapping(uint => uint)) internal currentBlockPositionsLong;
    mapping (uint => mapping(uint => uint)) internal currentBlockPositionsShort;

    Market[] public marketLineup;
    MarketLiq[] public marketLiqLineup;
    mapping (address => uint) public marketIndexes;

    struct Market {
        address market;
        bool active;
        uint24 fee;
        uint24 maxLeverage;
    }

    struct MarketLiq {
        address market;
        uint24 marginRewardRate;
        uint24 marginMaintenance;
    }

    Position.Info[] public positions;

    IOverlayV1Mothership public immutable mothership;
    IOverlayTokenNew immutable public ovl;

    uint256 public fees;
    uint256 public liquidations;

    event Build(
        address market,
        uint256 positionId,
        uint256 oi,
        uint256 debt
    );

    event Unwind(
        address market,
        uint256 positionId,
        uint256 oi,
        uint256 debt
    );

    event Liquidate(
        uint256 positionId,
        uint256 oi,
        uint256 reward,
        address rewarded
    );

    event Update(
        uint feesCollected,
        uint feesBurned,
        uint liquidationsCollected,
        uint liquidationsBurned
    );

    modifier onlyGovernor () {
        require(mothership.hasRole(GOVERNOR, msg.sender), "OVLV1:!governor");
        _;
    }

    /**
      @notice Constructor method
      @dev  Creates a `Position.Info` struct and appends it to `positions` array to track them
      @param _uri Unique Resource Identifier of a token
      @param _mothership OverlayV1Mothership contract address
     */
    constructor (
        string memory _uri,
        address _mothership
    ) ERC1155(_uri) {

        mothership = IOverlayV1Mothership(_mothership);

        ovl = IOverlayV1Mothership(_mothership).ovl();

        positions.push(Position.Info({
            market: 0,
            isLong: false,
            leverage: 0,
            pricePoint: 0,
            oiShares: 0,
            debt: 0,
            cost: 0
        }));

        marketLineup.push( Market({
            market: address(0), 
            active: false,
            fee: 0, 
            maxLeverage: 0
        }));

        marketLiqLineup.push( MarketLiq({
            market: address(0), 
            marginMaintenance: 0, 
            marginRewardRate: 0
        }));

    }

    function addMarket (
        address _marketAddress,
        uint _fee,
        uint _maxLeverage,
        uint _marginRewardRate,
        uint _marginMaintenance
    ) external onlyGovernor {

        uint _index = marketIndexes[_marketAddress];

        require(_index == 0, "OVLV1:!!market");

        _index = marketLineup.length;

        marketLineup.push( Market({
            market: _marketAddress,
            active: true,
            fee: uint24(_fee / 1e12), 
            maxLeverage: uint24(_maxLeverage)
        }));

        marketLiqLineup.push( MarketLiq({
            market: _marketAddress,
            marginRewardRate: uint24(_marginRewardRate / 1e12),
            marginMaintenance: uint24(_marginMaintenance / 1e12)
        }));

        marketIndexes[_marketAddress] = _index;

    }

    function setMarketInfo (
        address _marketAddress,
        uint _fee,
        uint _maxLeverage,
        uint _marginRewardRate,
        uint _marginMaintenance
    ) external onlyGovernor {

        uint _index = marketIndexes[_marketAddress];

        Market memory _market = marketLineup[_index];
        MarketLiq memory _marketLiq = marketLiqLineup[_index];

        _market.fee = uint24(_fee / 1e12);
        _market.maxLeverage = uint24(_maxLeverage);

        _marketLiq.marginRewardRate = uint24(_marginRewardRate / 1e12);
        _marketLiq.marginMaintenance = uint24(_marginMaintenance / 1e12);

        marketLineup[_index] = _market;
        marketLiqLineup[_index] = _marketLiq;

    }

    function marketLineupLength () public view returns (
        uint length_
    ) {

        length_ = marketLineup.length;

    }

    function fee (
        address _market
    ) external view returns (
        uint fee_
    ) {

        fee_ = uint(marketLineup[
            marketIndexes[_market]
        ].fee) * 1e12;

    }

    function maxLeverage (
        address _market
    ) external view returns (
        uint maxLeverage_
    ) {

        maxLeverage_ = marketLineup[
            marketIndexes[_market]
        ].maxLeverage;

    }

    function marginRewardRate (
        address _market
    ) external view returns (
        uint marginRewardRate_
    ) {

        marginRewardRate_ = uint(marketLiqLineup[
            marketIndexes[_market]
        ].marginRewardRate) * 1e12;

    }

    function marginMaintenance (
        address _market
    ) external view returns (
        uint marginMaintenance_
    ) {

        marginMaintenance_ = uint(marketLiqLineup[
            marketIndexes[_market]
        ].marginMaintenance) * 1e12;

    }

    /// @notice Disburses fees
    function disburse () public {

        (   uint256 _marginBurnRate,
            uint256 _feeBurnRate,
            address _feeTo ) = mothership.getUpdateParams();

        uint _feeForward = fees;
        uint _feeBurn = _feeForward.mulUp(_feeBurnRate);
        _feeForward = _feeForward - _feeBurn;

        uint _liqForward = liquidations;
        uint _liqBurn = _liqForward.mulUp(_marginBurnRate);
        _liqForward -= _liqBurn;

        fees = 0;
        liquidations = 0;

        emit Update(
            _feeForward,
            _feeBurn,
            _liqForward,
            _liqBurn
        );

        ovl.burn(address(this), _feeBurn + _liqBurn);
        ovl.transfer(_feeTo, _feeForward + _liqForward);

    }

    function getCurrentBlockPositionId (
        uint _market,
        bool _isLong,
        uint _leverage,
        uint _pricePointNext
    ) internal returns (
        uint positionId_
    ) {

        mapping(uint=>uint) storage _currentBlockPositions = _isLong
            ? currentBlockPositionsLong[_market]
            : currentBlockPositionsShort[_market];

        positionId_ = _currentBlockPositions[_leverage];

        Position.Info storage position = positions[positionId_];

        // In a block, which is now the update period (past it was longer)
        // (related to not making 1155 sharable)
        // Looks into mapping to see what the position ID of the current
        // leverage is. Given this leverage and market, is there a current
        // position being built in the course of this block because that is the
        // only scenario where the price point would be equal to what we
        // currently have for the price point
        // False: if there is a position being built in the same update period
        // (current block only)
        // price point of that position would be the price point that has
        // already been updated and will be updated no more on the market
        // not smae block then pricepointNext will be greater than prior
        // position price point - > push new one onto stack
        if  (position.pricePoint < _pricePointNext) {

            positions.push(Position.Info({
                market: uint8(_market),
                isLong: _isLong,
                leverage: uint16(_leverage),
                pricePoint: uint32(_pricePointNext),
                oiShares: 0,
                debt: 0,
                cost: 0
            }));

            positionId_ = positions.length - 1;

            _currentBlockPositions[_leverage] = positionId_;

        }

    }

    function build (
        address _market,
        uint256 _collateral,
        uint256 _leverage,
        bool _isLong,
        uint256 _oiMinimum
    ) external returns (
        uint positionId_
    ) {

        return _build(
            marketIndexes[_market],
            _collateral,
            _leverage,
            _isLong,
            _oiMinimum
        );

    }


    /**
      @notice Build a position on Overlay with OVL collateral
      @dev This interacts with an Overlay Market to register oi and hold 
      positions on behalf of users.
      @dev Build event emitted
      @param _marketIx The index in the market lineup of the desired market to interact with
      @param _collateral The amount of OVL to use as collateral in the position
      @param _leverage The amount of leverage to use in the position
      @param _isLong Whether to take out a position on the long or short side
      @return positionId_ Id of the built position for on chain convenience
     */
    function _build (
        uint256 _marketIx,
        uint256 _collateral,
        uint256 _leverage,
        bool _isLong,
        uint256 _oiMinimum
    ) internal returns (
        uint positionId_
    ) {

        Market memory _market = marketLineup[_marketIx];

        require(_market.active, "OVLV1:!market");
        require(_leverage <= _market.maxLeverage, "OVLV1:lev>max");

        (   uint _oiAdjusted,
            uint _collateralAdjusted,
            uint _debtAdjusted,
            uint _exactedFee,
            uint _impact,
            uint _pricePointNext ) = IOverlayV1Market(_market.market)
                .enterOI(
                    _isLong,
                    _collateral,
                    _leverage,
                    uint(_market.fee) * 1e12
                );

        require(_oiAdjusted >= _oiMinimum, "OVLV1:oi<min");

        uint _positionId = getCurrentBlockPositionId(
            _marketIx,
            _isLong,
            _leverage,
            _pricePointNext
        );

        Position.Info storage pos = positions[_positionId];

        pos.oiShares += uint112(_oiAdjusted);
        pos.cost += uint112(_collateralAdjusted);
        pos.debt += uint112(_debtAdjusted);

        fees += _exactedFee;

        emit Build(_market.market, _positionId, _oiAdjusted, _debtAdjusted);

        ovl.transferFromBurn(msg.sender, address(this), _collateralAdjusted + _exactedFee, _impact);

        // ovl.burn(msg.sender, _impact);

        _mint(msg.sender, _positionId, _oiAdjusted, ""); // WARNING: last b/c erc1155 callback

        positionId_ = _positionId;

    }

    /**
      @notice Unwinds shares of an existing position.
      @dev Interacts with a market contract to realize the PnL on a position.
      @param _positionId Id of the position to be unwound.
      @param _shares Number of shars to unwind from the position.
     */
    function unwind (
        uint256 _positionId,
        uint256 _shares
    ) external {

        require( 0 < _shares && _shares <= balanceOf(msg.sender, _positionId), "OVLV1:!shares");

        Position.Info storage pos = positions[_positionId];

        Market memory _market = marketLineup[pos.market];

        require(0 < pos.oiShares, "OVLV1:liquidated");

        {

        (   uint _oi,
            uint _oiShares,
            uint _priceFrame ) = IOverlayV1Market(_market.market)
                .exitData(
                    pos.isLong,
                    pos.pricePoint
                );

        uint _totalPosShares = totalSupply(_positionId);

        uint _userOiShares = _shares;
        uint _userNotional = _shares * pos.notional(_oi, _oiShares, _priceFrame) / _totalPosShares;
        uint _userDebt = _shares * pos.debt / _totalPosShares;
        uint _userCost = _shares * pos.cost / _totalPosShares;
        uint _userOi = _shares * pos.oi(_oi, _oiShares) / _totalPosShares;

        emit Unwind(_market.market, _positionId, _userOi, _userDebt);

        // TODO: think through edge case of underwater position ... and fee adjustments ...
        uint _feeAmount = _userNotional.mulUp(uint(_market.fee) * 1e12);

        uint _userValueAdjusted = _userNotional - _feeAmount;
        if (_userValueAdjusted > _userDebt) _userValueAdjusted -= _userDebt;
        else _userValueAdjusted = 0;

        fees += _feeAmount; // adds to fee pot, which is transferred on update

        pos.debt -= uint112(_userDebt);
        pos.cost -= uint112(_userCost);
        pos.oiShares -= uint112(_userOiShares);

        // ovl.transfer(msg.sender, _userCost);

        // mint/burn excess PnL = valueAdjusted - cost
        if (_userCost < _userValueAdjusted) {

            ovl.transferMint(
                msg.sender, 
                _userCost, 
                _userValueAdjusted - _userCost
            );

        } else {

            ovl.transferBurn(
                msg.sender, 
                _userValueAdjusted, 
                _userCost - _userValueAdjusted
            );

        }


        IOverlayV1Market(_market.market).exitOI(
            pos.isLong,
            _userOi,
            _userOiShares,
            _userCost < _userValueAdjusted ? _userValueAdjusted - _userCost : 0,
            _userCost < _userValueAdjusted ? 0 : _userCost - _userValueAdjusted
        );

        }

        _burn(msg.sender, _positionId, _shares);

    }

    /**
    @notice Liquidates an existing position.
    @dev Interacts with an Overlay Market to exit all open interest
    associated with a liquidatable positoin.
    @param _positionId ID of the position being liquidated.
    @param _rewardsTo Address to send liquidation reward to.
    */
    function liquidate (
        uint256 _positionId,
        address _rewardsTo
    ) external {

        Position.Info storage pos = positions[_positionId];

        require(0 < pos.oiShares, "OVLV1:liquidated");

        MarketLiq memory _marketLiq = marketLiqLineup[pos.market];

        bool _isLong = pos.isLong;

        (   uint _oi,
            uint _oiShares,
            uint _priceFrame ) = IOverlayV1Market(_marketLiq.market)
                .exitData(
                    _isLong,
                    pos.pricePoint
                );

        require(pos.isLiquidatable(
            _oi,
            _oiShares,
            _priceFrame,
            uint(_marketLiq.marginMaintenance) * 1e12
        ), "OVLV1:!liquidatable");

        uint _value = pos.value(_oi, _oiShares, _priceFrame);

        IOverlayV1Market(_marketLiq.market).exitOI(
            _isLong,
            pos.oi(_oi, _oiShares),
            pos.oiShares,
            0,
            pos.cost - _value
        );

        // TODO: which is better on gas
        pos.oiShares = 0;
        pos.debt = 0;
        // positions[positionId].oiShares = 0;


        uint _toReward = _value.mulUp(uint(_marketLiq.marginRewardRate) * 1e12);

        liquidations += _value - _toReward;

        emit Liquidate(
            _positionId,
            _oi,
            _toReward,
            _rewardsTo
        );

        // ovl.burn(address(this), pos.cost - _value);
        ovl.transferBurn(_rewardsTo, _toReward, pos.cost - _value);

    }


    /**
    @notice Retrieves required information from market contract to calculate
    @notice position value with.
    @dev Gets price frame, total open interest and total open interest shares
    @dev from an Overlay market.
    @param _positionId ID of position to determine value of
    @return value_ Value of the position
    */
    function value (
        uint _positionId
    ) public view returns (
        uint256 value_
    ) {

        Position.Info storage pos = positions[_positionId];

        Market memory _market = marketLineup[pos.market];

        (   uint _oi,
            uint _oiShares,
            uint _priceFrame ) = IOverlayV1Market(_market.market)
            .positionInfo(
                pos.isLong,
                pos.pricePoint
            );

        value_ = pos.value(
            _oi,
            _oiShares,
            _priceFrame
        );

    }

}
