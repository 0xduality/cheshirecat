// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
//import "@openzeppelin/contracts/access/Ownable.sol";
import "hardhat/console.sol";

interface IRouter {

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

interface IPair {

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

    function bondInfo(address _account) external view returns (uint256 payout, uint256 pricePaid, uint32 last, uint32 vesting);

    function deposit(uint _amount, uint _maxPrice, address _depositor) external returns (uint);

    function bondPrice() external view returns (uint);
}

interface IStaking {
    function unstake(uint _amount, bool _trigger) external;
}



contract MaxiAutoBond {

    address stable = 0xd586E7F844cEa2F87f50152665BCbc2C279D8d70;
    address staked = 0xEcE4D1b3C2020A312Ec41A7271608326894076b4;
    address mainToken = 0x7C08413cbf02202a1c13643dB173f2694e0F73f0;
    address wavax = 0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7;
    address staking = 0x6d7AD602Ec2EFdF4B7d34A9A53f92F06d27b82B1;
    address joeRouter = 0x60aE616a2155Ee3d9A68541Ba4544862310933d4;
    address pngRouter = 0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106;
    address png = 0x60781C2586D68229fde47564546784ab3fACA982;

    mapping (address => address) lp;
    mapping (address => address) wavaxlp;
    mapping (address => address) bond;


    constructor()
    {
        lp[stable] = 0xfBDC4aa69114AA11Fae65E858e92DC5D013b2EA9;
        lp[wavax] = 0xbb700450811a30c5ee0dB80925Cf1BA53dBBd60A;
        wavaxlp[png] = 0xd7538cABBf8605BdE1f4901B47B8D42c61DE0367; 
        bond[wavax] = 0xA4D6757E6F313eA8857F50547F0CE4946fF1EB84;
        bond[stable] = 0x103F6bd55C192b86aD576C0c36Be7AB0945Ebe48;
        bond[lp[stable]] = 0xA4EbD64423a6FF9baE958Bd0A38Fc216F41b3ef6;
        bond[lp[wavax]] = 0x03F40AC35171E2ab7451B1410cF4e00f1D1915ce;
        bond[wavaxlp[png]] = 0x20F91e4b39f405EFa821a11543a8C03265045b84;
    }


    function _swap(address _to, uint256 _amount) internal {
        require(_to != address(0));
        address router = (_to == wavax ? pngRouter : joeRouter);
        IERC20(mainToken).approve(router, _amount);
        address[] memory path = new address[](2);
        path[0] = mainToken;
        path[1] = _to;
        IRouter(router).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            block.timestamp + 60
        );
    }

    function _swapAVAX(address _to, uint256 _amount) internal {
        require(_to != address(0));
        IERC20(wavax).approve(pngRouter, _amount);
        address[] memory path = new address[](2);
        path[0] = wavax;
        path[1] = _to;
        IRouter(pngRouter).swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            block.timestamp + 60
        );
    }

    function _poolReserves(address _token) internal view returns (uint256, uint256)
    {
        uint256 rmain;
        uint256 rtoken;
        address lpToken = lp[_token];
        require(lpToken != address(0));
        (uint256 r0, uint256 r1,) = IPair(lpToken).getReserves();
        address token0 = IPair(lpToken).token0();
        address token1 = IPair(lpToken).token1();
        if (token0 == _token && token1 == mainToken)
        {
            rmain = r1;
            rtoken = r0;
        }
        else if (token1 == _token && token0 == mainToken)
        {
            rmain = r0;
            rtoken = r1;
        }
        else
        {
            require(false, "bad LP token");
        }
        return (rmain, rtoken);
    }

    function _poolReservesAVAX(address _token) internal view returns (uint256, uint256)
    {
        uint256 ravax;
        uint256 rtoken;
        address lpToken = wavaxlp[_token];
        require(lpToken != address(0));
        (uint256 r0, uint256 r1,) = IPair(lpToken).getReserves();
        address token0 = IPair(lpToken).token0();
        address token1 = IPair(lpToken).token1();
        if (token0 == _token && token1 == wavax)
        {
            ravax = r1;
            rtoken = r0;
        }
        else if (token1 == _token && token0 == wavax)
        {
            ravax = r0;
            rtoken = r1;
        }
        else
        {
            require(false, "bad LP token");
        }
        return (ravax, rtoken);
    }

    function _mintLP(address _token) internal {
        uint256 mytoken = IERC20(_token).balanceOf(address(this));
        uint256 mymain = IERC20(mainToken).balanceOf(address(this));
        address router = (_token == wavax ? pngRouter : joeRouter);
        IERC20(_token).approve(router, mytoken);
        IERC20(mainToken).approve(router, mymain);
        IRouter(router).addLiquidity(
                mainToken,
                _token,
                mymain,
                mytoken,
                0,
                0,
                address(this),
                block.timestamp + 60
            );
        
    }

    function _mintAVAXLP(address _token) internal {
        uint256 mytoken = IERC20(_token).balanceOf(address(this));
        uint256 mywavax = IERC20(wavax).balanceOf(address(this));
        IERC20(_token).approve(pngRouter, mytoken);
        IERC20(wavax).approve(pngRouter, mywavax);
        IRouter(pngRouter).addLiquidity(
                wavax,
                _token,
                mywavax,
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
        uint256 r = 1997 * _reserve;
        uint256 rm = 1000 * _reserve * _mine;
        uint256 x = _mine / 2;
        x = (997 * x * x + rm) / (1994 * x + r);
        x = (997 * x * x + rm) / (1994 * x + r);
        x = (997 * x * x + rm) / (1994 * x + r);
        return x;
    }


    function _refundLeftovers(address _token, address _beneficiary) internal
    {
        uint256 leftover = IERC20(_token).balanceOf(address(this));
        if (leftover > 0)
        {
            IERC20(_token).transfer(_beneficiary, leftover);
        }
    }


    function _unstake(uint256 _amount) internal
    {
        IERC20(staked).approve(staking, _amount);
        IStaking(staking).unstake(_amount, true);
    }


    function payoutForERC20(address _token, uint256 _amount) public returns (uint256) 
    {
        IERC20(staked).transferFrom(msg.sender, address(this), _amount);
        _unstake(_amount);
        _swap(_token, _amount);
        return _mintBond(_token, msg.sender);
    }


    function payoutForLP(address _token, uint256 _amount) public returns (uint256) 
    {
        IERC20(staked).transferFrom(msg.sender, address(this), _amount);
        _unstake(_amount);
        (uint256 rmain,) = _poolReserves(_token);
        uint256 sell = _zap(rmain, _amount);
        _swap(_token, sell);
        _mintLP(_token);
        return _mintBond(lp[_token], msg.sender);
    }

    
    function payoutForAVAXLP(address _token, uint256 _amount) public returns (uint256) 
    {
        IERC20(staked).transferFrom(msg.sender, address(this), _amount);
        _unstake(_amount);
        _swap(wavax, _amount);
        (uint256 ravax,) = _poolReservesAVAX(_token);
        uint256 sell = _zap(ravax, IERC20(wavax).balanceOf(address(this)));
        _swapAVAX(_token, sell);
        _mintAVAXLP(_token);
        return _mintBond(wavaxlp[_token], msg.sender);
    }


    function mintWithERC20(address _token, uint256 _amount, uint256 _minimum) public
    {
        address beneficiary = msg.sender;
        uint256 payout = payoutForERC20(_token, _amount);
        require (payout >= _minimum, "insufficient profit, either ROI plummeted or your slippage is too tight");
        _refundLeftovers(_token, beneficiary);
        _refundLeftovers(mainToken, beneficiary);
    }


    function mintWithLP(address _token, uint256 _amount, uint256 _minimum) public
    {
        address beneficiary = msg.sender;
        uint256 payout = payoutForLP(_token, _amount);
        require (payout >= _minimum, "insufficient profit, either ROI plummeted or your slippage is too tight");
        _refundLeftovers(_token, beneficiary);
        _refundLeftovers(mainToken, beneficiary);
    }

    
    function mintWithAVAXLP(address _token, uint256 _amount, uint256 _minimum) public
    {
        address beneficiary = msg.sender;
        uint256 payout = payoutForAVAXLP(_token, _amount);
        require (payout >= _minimum, "insufficient profit, either ROI plummeted or your slippage is too tight");
        _refundLeftovers(_token, beneficiary);
        _refundLeftovers(wavax, beneficiary);
    }
 }