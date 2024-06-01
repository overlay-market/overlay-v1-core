pragma solidity ^0.8.0;

interface IBalancerVault {

    function getPoolTokens (
        bytes32 _poolId 
    ) external view returns (
        address[] memory tokens_,
        uint256[] memory balances_,
        uint256 lastChangeBlock
    );

}