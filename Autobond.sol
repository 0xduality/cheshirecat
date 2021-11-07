// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
//import "hardhat/console.sol";

interface IJoeRouter {

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    ) external returns (
        uint256 amountA,
        uint256 amountB,
        uint256 liquidity
    );

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);
}

interface IJoePair {

    function approve(address spender, uint256 value) external returns (bool);

    function token0() external view returns (address);

    function token1() external view returns (address);

    function getReserves()
        external
        view
        returns (
            uint112 reserve0,
            uint112 reserve1,
            uint32 blockTimestampLast
        );
}

interface IDepository {

    function bondInfo(address _account) external view returns (uint256 payout, uint256 pricePaid, uint32 lastTime, uint32 vesting);

    function deposit(uint _amount, uint _maxPrice, address _depositor) external returns (uint);

    function bondPrice() external view returns (uint);
}

interface ITimeStaking {
    function unstake(uint _amount, bool _trigger) external;
}



contract Autobond {

    address mim = 0x130966628846BFd36ff31a822705796e8cb8C18D;
    address memo = 0x136Acd46C134E8269052c62A67042D6bDeDde3C9;
    address time = 0xb54f16fB19478766A268F172C9480f8da1a7c9C3;
    address wavax = 0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7;
    address staking = 0x4456B87Af11e87E329AB7d7C7A246ed1aC2168B9;
    address joeRouter = 0x60aE616a2155Ee3d9A68541Ba4544862310933d4;

    mapping (address => address) lp;
    mapping (address => address) bond;

    constructor()
    {
        lp[wavax] = 0xf64e1c5B6E17031f5504481Ac8145F4c3eab4917;
        lp[mim] = 0x113f413371fC4CC4C9d6416cf1DE9dFd7BF747Df;
        bond[wavax] = 0xE02B1AA2c4BE73093BE79d763fdFFC0E3cf67318;
        bond[mim] = 0x694738E0A438d90487b4a549b201142c1a97B556;
        bond[lp[wavax]] = 0xc26850686ce755FFb8690EA156E5A6cf03DcBDE1;
        bond[lp[mim]] = 0xA184AE1A71EcAD20E822cB965b99c287590c4FFe;
    }

    function _swapTime(address _to, uint256 _amount) internal {
        require(_to != address(0));
        IERC20(time).approve(joeRouter, _amount);
        address[] memory path = new address[](2);
        path[0] = time;
        path[1] = _to;
        IJoeRouter(joeRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            block.timestamp + 60
        );
    }

    function _timePoolReserves(address _token) internal view returns (uint256, uint256)
    {
        uint256 rtime;
        uint256 rtoken;
        address lpToken = lp[_token];
        require(lpToken != address(0));
        (uint256 r0, uint256 r1,) = IJoePair(lpToken).getReserves();
        address token0 = IJoePair(lpToken).token0();
        address token1 = IJoePair(lpToken).token1();
        if (token0 == _token && token1 == time)
        {
            rtime = r1;
            rtoken = r0;
        }
        else if (token1 == _token && token0 == time)
        {
            rtime = r0;
            rtoken = r1;
        }
        else
        {
            require(false, "bad LP token");
        }
        return (rtime, rtoken);
    }

    function _mintLP(address _token) internal {
        uint256 mytoken = IERC20(_token).balanceOf(address(this));
        uint256 mytime = IERC20(time).balanceOf(address(this));
        IERC20(_token).approve(joeRouter, mytoken);
        IERC20(time).approve(joeRouter, mytime);
        IJoeRouter(joeRouter).addLiquidity(
                time,
                _token,
                mytime,
                mytoken,
                0,
                0,
                address(this),
                block.timestamp + 60
            );
    }


    function _mintBond(address _token, address _beneficiary) internal returns (uint256)
    {
        uint256 amount = IERC20(_token).balanceOf(address(this));
        address depo = bond[_token];
        IERC20(_token).approve(depo, amount);
        uint256 price = IDepository(depo).bondPrice();
        (uint256 payoutBefore,,,) = IDepository(depo).bondInfo(_beneficiary);
        IDepository(depo).deposit(amount, price, _beneficiary);
        (uint256 payoutAfter,,,) = IDepository(depo).bondInfo(_beneficiary);
        uint256 payout = payoutAfter - payoutBefore;
        return payout;
    }


    function _zap(uint256 _reserve, uint256 _mine) internal pure returns (uint256)
    {
        uint256 guess = _mine / 2;
        guess = (guess * guess + _reserve * _mine) / (2 * (_reserve + guess));
        guess = (guess * guess + _reserve * _mine) / (2 * (_reserve + guess));
        return guess;
    }


    function _refundLeftovers(address _token, address _beneficiary) internal
    {
        uint256 leftover = IERC20(_token).balanceOf(address(this));
        if (leftover > 0)
        {
            IERC20(_token).transfer(_beneficiary, leftover);
        }
    }


    function _unstake() internal
    {
        uint256 amount = IERC20(memo).balanceOf(address(this));
        IERC20(memo).approve(staking, amount);
        ITimeStaking(staking).unstake(amount, true);
    }


    function _transferIn(address _beneficiary) internal
    {
        uint256 amount = IERC20(memo).balanceOf(_beneficiary);
        IERC20(memo).transferFrom(_beneficiary, address(this), amount);
    }

    function payoutForERC20(address _token) public returns (uint256) 
    {
        address beneficiary = msg.sender;
        _transferIn(beneficiary);
        _unstake();
        uint256 amount = IERC20(time).balanceOf(address(this));
        _swapTime(_token, amount);
        return _mintBond(_token, beneficiary);
    }

    function payoutForLP(address _token) public returns (uint256) 
    {
        address beneficiary = msg.sender;
        _transferIn(beneficiary);
        _unstake();
        uint256 amount = IERC20(time).balanceOf(address(this));
        (uint256 rtime,) = _timePoolReserves(_token);
        uint256 sell = _zap(rtime, amount);
        _swapTime(_token, sell);
        _mintLP(_token);
        return _mintBond(lp[_token], beneficiary);
    }

    function mintWithERC20(address _token, uint256 _minimum) public
    {
        address beneficiary = msg.sender;
        uint256 payout = payoutForERC20(_token);
        require (payout >= _minimum, "insufficient profit, either ROI plummeted or your minimum is too high");
        _refundLeftovers(_token, beneficiary);
        _refundLeftovers(time, beneficiary);

    }


    function mintWithLP(address _token, uint256 _minimum) public
    {
        address beneficiary = msg.sender;
        uint256 payout = payoutForLP(_token);
        require (payout >= _minimum, "insufficient profit, either ROI plummeted or your minimum is too high");
        _refundLeftovers(_token, beneficiary);
        _refundLeftovers(time, beneficiary);
    }
 }