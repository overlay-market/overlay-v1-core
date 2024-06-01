pragma solidity ^0.8.0;

interface IBalancerFeed {

    enum Variable { PAIR_PRICE, BPT_PRICE, INVARIANT }

    struct Query {
        Variable variable;
        uint256 secs;
        uint256 ago;
    }

    /**
     * @dev Returns the raw data of the sample at `index`.
     */
    function getSample(uint256 index)
        external
        view
        returns (
            int256 logPairPrice,
            int256 accLogPairPrice,
            int256 logBptPrice,
            int256 accLogBptPrice,
            int256 logInvariant,
            int256 accLogInvariant,
            uint256 timestamp
        );

    /**
     * @dev Returns the total number of samples.
     */
    function getTotalSamples() external view returns (uint256);

    function getTimeWeightedAverage(
        Query[] memory queries
    ) external view returns (
        uint256[] memory results
    );

    function getLatest(Variable variable) external view returns (uint256);

    function getNormalizedWeights () external view returns (
        uint256[] memory
    );

    function getPoolId () external view returns (bytes32 poolId_);

}