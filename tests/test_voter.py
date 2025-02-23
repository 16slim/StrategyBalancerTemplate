import pytest
import brownie

# tests that the voter can convert from BAL -> the BPT that turns into veBAL and back
def test_convert(
    chain, yearn_balancer_voter, bal, bal_weth_bpt, whale, gov, RELATIVE_APPROX
):
    # Assumptions
    assert bal.balanceOf(yearn_balancer_voter) == 0
    assert bal_weth_bpt.balanceOf(yearn_balancer_voter) == 0

    whale_bal_balance = bal.balanceOf(whale)

    original_bal_transfer = whale_bal_balance / 100

    bal.transfer(yearn_balancer_voter, original_bal_transfer, {"from": whale})

    yearn_balancer_voter.convertBALIntoBPT(original_bal_transfer, {"from": gov})

    assert bal.balanceOf(yearn_balancer_voter) == 0
    bpt_balance = bal_weth_bpt.balanceOf(yearn_balancer_voter)
    assert bpt_balance > 0

    chain.mine(1)
    chain.sleep(1)

    yearn_balancer_voter.convertBPTIntoBAL(bpt_balance, {"from": gov})  # Convert back

    assert bal.balanceOf(yearn_balancer_voter) > original_bal_transfer * 0.99
    assert bal_weth_bpt.balanceOf(yearn_balancer_voter) == 0


def test_create_lock(
    chain,
    yearn_balancer_voter,
    bal,
    bal_weth_bpt,
    ve_bal,
    whale,
    gov,
    RELATIVE_APPROX,
):
    whale_bal_balance = bal.balanceOf(whale)

    original_bal_transfer = whale_bal_balance / 10

    bal.transfer(yearn_balancer_voter, original_bal_transfer, {"from": whale})

    assert ve_bal.balanceOf(yearn_balancer_voter) == 0

    yearn_balancer_voter.convertBALIntoBPT(original_bal_transfer, {"from": gov})
    yearn_balancer_voter.createLock(
        bal_weth_bpt.balanceOf(yearn_balancer_voter),
        chain.time() + (60 * 60 * 24 * 60),
        {"from": gov},
    )  # lock for 30 days

    first_ve_bal_balance = ve_bal.balanceOf(yearn_balancer_voter)
    assert first_ve_bal_balance > 0

    chain.sleep(60 * 60 * 24 * 20)

    second_bal_transfer = whale_bal_balance / 1000

    bal.transfer(yearn_balancer_voter, second_bal_transfer, {"from": whale})

    yearn_balancer_voter.convertLooseBALIntoBPT({"from": gov})
    yearn_balancer_voter.increaseAmountMax({"from": gov})

    second_ve_bal_balance = ve_bal.balanceOf(yearn_balancer_voter)

    assert (
        second_ve_bal_balance < first_ve_bal_balance
    )  # voting power should decrease with time

    third_bal_transfer = whale_bal_balance / 100

    bal.transfer(yearn_balancer_voter, third_bal_transfer, {"from": whale})

    yearn_balancer_voter.convertLooseBALIntoBPT({"from": gov})
    yearn_balancer_voter.increaseAmountMax({"from": gov})

    third_ve_bal_balance = ve_bal.balanceOf(yearn_balancer_voter)

    assert third_ve_bal_balance > second_ve_bal_balance

    fourth_bal_transfer = whale_bal_balance / 200

    bal.transfer(yearn_balancer_voter, fourth_bal_transfer, {"from": whale})

    yearn_balancer_voter.convertLooseBALIntoBPT({"from": gov})
    yearn_balancer_voter.increaseAmountExact(
        bal_weth_bpt.balanceOf(yearn_balancer_voter), {"from": gov}
    )

    fourth_ve_bal_balance = ve_bal.balanceOf(yearn_balancer_voter)

    assert fourth_ve_bal_balance > third_ve_bal_balance
