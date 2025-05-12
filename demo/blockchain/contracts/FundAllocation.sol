// FundAllocation.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FundAllocation {
    address public stateGovernment;
    mapping(address => uint256) public allocatedFunds;

    event FundRequested(address indexed organization, uint256 amount);
    event FundApproved(address indexed organization, uint256 amount);
    event FundRejected(address indexed organization, string reason);

    modifier onlyGovernment() {
        require(msg.sender == stateGovernment, "Only government can approve/reject funds");
        _;
    }

    constructor() {
        stateGovernment = msg.sender;
    }

    function requestFund(uint256 amount) public {
        emit FundRequested(msg.sender, amount);
    }

    function approveFund(address organization, uint256 amount) public onlyGovernment {
        allocatedFunds[organization] += amount;
        emit FundApproved(organization, amount);
    }

    function rejectFund(address organization, string memory reason) public onlyGovernment {
        emit FundRejected(organization, reason);
    }

    function getAllocatedFunds(address organization) public view returns (uint256) {
        return allocatedFunds[organization];
    }
}
