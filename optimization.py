import numpy as np
import cvxpy as cp
from scipy.optimize import minimize

def global_minimum_variance(sigma, constraints: dict, n_):
    w = cp.Variable(n_)
    risk = cp.quad_form(w, sigma)

    constraint_list = _build_constraints_cvxpy(w, constraints)
    objective = cp.Minimize(risk * 1000)
    problem = cp.Problem(objective, constraint_list)
    problem.solve()
    w_opt = w.value
    return w_opt


def risk_parity(sigma , constraints: dict, n_):
    def risk_contribution(w, sigma):
        # function that calculates asset contribution to total risk
        w = np.matrix(w)
        sigma = np.sqrt(_portfolio_variance(w, sigma))
        # Marginal Risk Contribution
        mrc = sigma * w.T
        # Total asset risk contribution
        rc = np.multiply(mrc, w.T) / sigma
        return rc

    def risk_objective(x, params):
        # calculate portfolio risk
        covar = params[0]  # covariance table
        b = params[1]  # risk target in percent of portfolio risk
        sig_p = np.sqrt(_portfolio_variance(x, covar)) # portfolio sigma
        risk_target = np.asmatrix(np.multiply(sig_p, b))
        asset_rc = risk_contribution(x, covar)
        J = sum(np.square(asset_rc - risk_target.T))[0, 0]  # sum of squared error
        return J

    b = np.ones((1, n_))
    b = b / n_  # your risk budget percent of total portfolio risk (equal risk)

    constraint_tup = _build_constraints_scipy(constraints)
    problem = minimize(risk_objective, b, args=[sigma, b], method='SLSQP',
                       constraints=constraint_tup, options={'disp': False})
    w_opt = np.array(problem.x)
    return w_opt

def max_diversification_ratio():
    raise NotImplementedError

def _portfolio_variance(w, sigma):
    w = np.matrix(w)
    sig_p = w * sigma * w.T
    return sig_p[0,0]

def _build_constraints_cvxpy(w_obj, constraints: dict):
    constraint_list = []
    for k, v in constraints.items():
        if k == 'long_only' and v == True:
            constraint_list.append(w_obj * 1000 >= 0)
        if k == 'leverage':
            constraint_list.append(w_obj * 1000 <= v * 1000)
        if k == 'normalizing' and v == True:
            constraint_list.append(cp.sum(w_obj) * 1000 == 1 * 1000)
    return constraint_list

def _build_constraints_scipy(constraints: dict):
    for k, v in constraints.items():
        if k == 'long_only' and v == True:
            long_only = {'type': 'ineq', 'fun' : lambda x: x}
        if k == 'normalizing' and v == True:
            normalizing = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
    constraint_tup = (long_only, normalizing)
    return constraint_tup