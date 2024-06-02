// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract ERC20Mock is ERC20 {

  uint8 immutable _decimals;

  constructor(
    string memory _name,
    string memory _symbol,
    uint8 __decimals
  ) ERC20(_name, _symbol) {

    _decimals = __decimals;

  }

  function decimals() public view virtual override returns (uint8) {
      return _decimals;
  }

  function mint(address _recipient, uint256 _amount) external {
    _mint(_recipient, _amount);
  }

  function burn(address _account, uint256 _amount) external {
    _burn(_account, _amount);
  }

}
