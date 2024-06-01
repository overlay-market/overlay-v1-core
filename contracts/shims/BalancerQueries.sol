// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "../interfaces/IBalancerFeed.sol";
import "../interfaces/IBalancerVault.sol";
import "../libraries/FixedPoint.sol";


contract BalancerQueries {

    using FixedPoint for uint256;

    IBalancerFeed immutable balancer;
    IBalancerVault immutable vault;

    constructor (
        address _oracleAddress,
        address _vault
    ) {

        balancer = IBalancerFeed(_oracleAddress);
        vault = IBalancerVault(_vault);

    }

        int256 private constant _LOG_COMPRESSION_FACTOR = 1e14;
    int256 private constant _HALF_LOG_COMPRESSION_FACTOR = 0.5e14;

    function toLowResLog(uint256 value) internal pure returns (int256) {
        int256 ln = LogExpMath.ln(int256(value));

        // Rounding division for signed numerator
        int256 lnWithError = (ln > 0 ? ln + _HALF_LOG_COMPRESSION_FACTOR : ln - _HALF_LOG_COMPRESSION_FACTOR);
        return lnWithError / _LOG_COMPRESSION_FACTOR;
    }

    function fromLowResLog(int256 value) internal pure returns (uint256) {
        return uint256(LogExpMath.exp(value * _LOG_COMPRESSION_FACTOR));
    }

    function twa () public view returns (
        uint ten_,
        uint hour_,
        uint tenInv_
    ) { 

        IBalancerFeed.Query[] memory queries = new IBalancerFeed.Query[](3);

        queries[0] = IBalancerFeed.Query( IBalancerFeed.Variable.PAIR_PRICE, 15, 0 );
        queries[1] = IBalancerFeed.Query( IBalancerFeed.Variable.PAIR_PRICE, 3600, 0 );
        queries[2] = IBalancerFeed.Query( IBalancerFeed.Variable.INVARIANT, 15, 0 );

        uint256[] memory _results = balancer.getTimeWeightedAverage(queries);

        ten_ = _results[0];
        hour_ = _results[1];
        tenInv_ = _results[2];

    }

    function weights () public view returns (uint256[] memory weights_) {

        weights_ = balancer.getNormalizedWeights();

    }

    function id () public view returns (bytes32 id_) {

        id_ = balancer.getPoolId();

    }

    function tokens () public view returns (address[] memory tokens_) {

        bytes32 _id = id();

        (  tokens_,, ) = vault.getPoolTokens(_id);

    }

    function balances () public view returns (uint256[] memory balances_) {

        bytes32 _id = id();

        (  ,balances_, ) = vault.getPoolTokens(_id);

    }

    function depth () public view returns (uint256 depth_) {
        
        bytes32 _id = id();

        (   address[] memory _tokens,, ) = vault.getPoolTokens(_id);

        uint256[] memory _weights = balancer.getNormalizedWeights();

        uint _w0;
        uint _w1;
        address _t0;
        address _t1;

        if (_weights[0] < _weights[1]) {

            _w0 = _weights[0];
            _t0 = _tokens[0];
            _w1 = _weights[1];
            _t1 = _tokens[1];

        } else {

            _w0 = _weights[1];
            _t0 = _tokens[1];
            _w1 = _weights[0];
            _t1 = _tokens[0];

        }

        (   uint _ten,,
            uint _tenInv ) = twa();

        depth_ = _ten
            .mulDown(_w0.divUp(_w1))
            .powUp(_w1)
            .mulUp(_tenInv);

    }


}