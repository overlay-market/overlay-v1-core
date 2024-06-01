// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "./UniswapV3OracleMock.sol";

/**
  @author Overlay
  @title Uniswap V3 factory mock to create token pairs for testing
  @dev Deployed by a token pair feed owner
 */
contract UniswapV3FactoryMock {

    mapping(address => bool) public isPool;
    address[] public allPools;

    /**
      @param _token0 First token contract address in the token pair
      @param _token1 Second token contract address in the token pair
      @return pool UniswapV3OracleMock contract instance
     */
    function createPool (
        address _token0, 
        address _token1
    ) external returns (
        UniswapV3OracleMock pool
    ) {

        pool = new UniswapV3OracleMock(_token0, _token1);
        isPool[address(pool)] = true;
        allPools.push(address(pool));

    }

    function loadObservations(
        address pool,
        OracleMock.Observation[] calldata _observations,
        UniswapV3OracleMock.Shim[] calldata _shims
    ) external {
        require(isPool[pool], "!pool");
        UniswapV3OracleMock(pool).loadObservations(_observations, _shims);
    }
}
