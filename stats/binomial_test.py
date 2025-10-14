from scipy.stats import binomtest

def site_ctr_test(clicks: int, impressions: int, target_ctr: float = 0.001, alpha: float = 0.05):
    """
    Performs a one-sided binomial test to check if a site's CTR is significantly below the target CTR.
    
    Parameters
    ----------
    clicks : int
        Number of clicks observed.
    impressions : int
        Number of impressions (trials).
    target_ctr : float
        Expected CTR under the null hypothesis (default = 0.001 = 0.1%).
    alpha : float
        Significance level for the test (default = 0.05).
        
    Returns
    -------
    dict
        A dictionary with:
        - observed_ctr: Observed click-through rate.
        - p_value: One-sided p-value for H1: true CTR < target CTR.
        - significant: Boolean, True if CTR is statistically below target at given alpha.
        - interpretation: Human-readable summary.
    """
    if impressions <= 0:
        raise ValueError("Impressions must be greater than 0.")
    if not (0 <= clicks <= impressions):
        raise ValueError("Clicks must be between 0 and impressions.")

    # One-sided test for p < target_ctr
    result = binomtest(clicks, impressions, target_ctr, alternative="less")
    
    observed_ctr = clicks / impressions
    significant = result.pvalue < alpha
    
    interpretation = (
        f"CTR is significantly below {target_ctr*100:.3f}% (p={result.pvalue:.4g})"
        if significant
        else f"No evidence CTR is below {target_ctr*100:.3f}% (p={result.pvalue:.4g})"
    )
    
    return {
        "observed_ctr": observed_ctr,
        "p_value": result.pvalue,
        "significant": significant,
        "interpretation": interpretation
    }

if __name__ == "__main__":
    # Example usage
    clicks = 0
    impressions = 5000
    target_ctr = 0.001  # 0.1%
    alpha = 0.01

    result = site_ctr_test(clicks, impressions, target_ctr, alpha)
    print(result)