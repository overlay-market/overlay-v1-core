// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../libraries/FixedPoint.sol";

contract OverlayV1OI {

    event log(string k , uint v);

    using FixedPoint for uint256;

    uint256 private constant ONE = 1e18;

    uint256 public compoundingPeriod;
    uint256 public compounded;

    uint256 internal __oiLong__; // total long open interest
    uint256 internal __oiShort__; // total short open interest

    uint256 public oiLongShares; // total shares of long open interest outstanding
    uint256 public oiShortShares; // total shares of short open interest outstanding

    uint256 public k;

    event FundingPaid(uint oiLong, uint oiShort, int fundingPaid);

    function computeFunding (
        uint256 _oiLong,
        uint256 _oiShort,
        uint256 _epochs,
        uint256 _k
    ) internal pure returns (
        uint256 oiLong_,
        uint256 oiShort_,
        int256  fundingPaid_
    ) {

        if (_oiLong == 0 && 0 == _oiShort) return (0, 0, 0);

        if (0 == _epochs) return ( _oiLong, _oiShort, 0 );

        uint _fundingFactor = ONE.sub(_k.mulUp(ONE*2));

        _fundingFactor = _fundingFactor.powUp(ONE*_epochs);

        uint _funder = _oiLong;
        uint _funded = _oiShort;
        bool payingLongs = _funder <= _funded;
        if (payingLongs) (_funder, _funded) = (_funded, _funder);

        if (_funded == 0) {

            uint _oiNow = _fundingFactor.mulDown(_funder);
            fundingPaid_ = int(_funder - _oiNow);
            _funder = _oiNow;

        } else {

            // TODO: we can make an unsafe mul function here
            uint256 _oiImbNow = _fundingFactor.mulDown(_funder - _funded);
            uint256 _total = _funder + _funded;

            fundingPaid_ = int( ( _funder - _funded ) / 2 );
            _funder = ( _total + _oiImbNow ) / 2;
            _funded = ( _total - _oiImbNow ) / 2;

        }

        ( oiLong_, oiShort_, fundingPaid_) = payingLongs
            ? ( _funded, _funder, fundingPaid_ )
            : ( _funder, _funded, -fundingPaid_ );

    }

    /// @notice Transfers funding payments
    /// @dev oiImbalance(m) = oiImbalance(0) * (1 - 2k)**m
    function payFunding (
        uint256 _k,
        uint256 _epochs
    ) internal returns (
        int256 fundingPaid_
    ) {

        uint _oiLong;
        uint _oiShort;

        ( _oiLong, _oiShort, fundingPaid_ ) = computeFunding(
            __oiLong__,
            __oiShort__,
            _epochs,
            _k
        );

        __oiLong__ = _oiLong;
        __oiShort__ = _oiShort;

        emit FundingPaid(_oiLong, _oiShort, fundingPaid_);

    }

    function addOi(
        bool _isLong,
        uint256 _oi,
        uint256 _oiCap
    ) internal {

        if (_isLong) {

            uint _oiLong = __oiLong__ + _oi;

            require(_oiLong <= _oiCap, "OVLV1:>cap");

            __oiLong__ = _oiLong;

        } else {

            uint _oiShort = __oiShort__ + _oi;

            require(_oiShort <= _oiCap, "OVLV1:>cap");

            __oiShort__ = _oiShort;

        }

    }

}
