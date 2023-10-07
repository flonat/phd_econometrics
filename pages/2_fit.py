import os
import random
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import streamlit as st
from matplotlib import pyplot as plt
from scipy.stats import t
from st_pages import add_page_title

import src.scripts.plot_themes as thm
import src.scripts.utils as utl

### PAGE CONFIGS ###

st.set_page_config(
    page_title="PhD Econometrics - Fit",
    page_icon="📈",
    layout="wide",
)
utl.local_css("src/styles/styles_pages.css")

random_seed = 0

## Data viz part
# How R-sq is calculated
# How R-sq and other measures depend on sample size, error variance, and true parameters
# Also how much R-sq, AIC, and BIC are penalized by adding more regressors?

## Theory part
# TBD

# create one column with consistent width
s1, c01, s2 = utl.wide_col()

### PAGE START ###
# Dashboard header

with c01:
    st.title("Model fit and selection measures")
    st.header("1. Visualizing R squared")

    st.write(
        "Play around with sliders to see how the data and estimates change."
    )
    st.write(
        r"Suppose you have the following true population relationship between $X$ and $y$, with parameters defined by slider values."
    )
    st.write(
        r"You then draw a sample of size $n$ from that population and estimate OLS coefficients, $b_0$ and $b_1$."
    )


def gen_lin_data(b0, b1, sd, N, rseed):
    np.random.seed(rseed)
    # generate X
    K = 2
    X = np.random.uniform(-10, 10, (N, K - 1))
    X = np.column_stack((np.ones(N), X))

    # generate  error term
    eps = np.random.normal(0, sd, N)

    # y = xB + eps
    y = np.dot(X, np.array([b0, b1])) + eps

    # fit reg
    model = sm.OLS(y, X).fit()

    # get fitted values and CI
    predictions = model.get_prediction(X)
    y_hat = predictions.predicted_mean
    y_hat_se = predictions.se_mean

    # get 95% confidence interval
    ci = predictions.conf_int(alpha=0.05)  # 95% CI
    deg_freedom = X.shape[0] - X.shape[1]  # n - K

    # get CI manually - not needed
    # t_score = t.ppf(0.975, deg_freedom)
    # ci = np.column_stack(
    #     (y_hat - t_score * y_hat_se, y_hat + t_score * y_hat_se)
    # )

    # get error parameters - not needed
    e = y - y_hat
    s = np.sqrt(np.sum(e**2) / deg_freedom)

    # calculate R^2 manually - not needed
    y_bar = np.mean(y)
    ss_tot = np.sum((y - y_bar) ** 2)
    ss_res = np.sum((y - y_hat) ** 2)
    r_squared = 1 - ss_res / ss_tot

    return {
        "y": y,
        "x": X,
        "s": s,
        "y_hat": y_hat,
        "ci": ci,
        "model": model,
    }


slider_col, s1, chart_col = st.columns((0.8, 0.1, 1))

with slider_col:
    st.latex(
        r"""
            y_i = \beta_0 + \beta_1x_i + \varepsilon_i \text{, where }  \varepsilon \sim N(0, \sigma^2)
        """
    )
    st.latex(r"""\hat{y_i} = """ + r"""b_0 + b_1 x_i""")

    # Sliders
    b0_cust = st.slider(
        r"Intercept, $\beta_0$",
        min_value=-10.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
    )
    b1_cust = st.slider(
        r"Slope, $\beta_1$", min_value=-5.0, max_value=5.0, value=0.0, step=0.1
    )
    var_cust = st.slider(
        r"Error SD, $\sqrt{var(\varepsilon)} = \sigma$",
        min_value=0.1,
        max_value=20.0,
        value=10.0,
        step=0.1,
    )

    n_cust = st.slider(
        "Sample size, $n$",
        min_value=10,
        max_value=1000,
        value=500,
        step=10,
    )

custom_data = gen_lin_data(b0_cust, b1_cust, var_cust, n_cust, random_seed)


def plot_ols(data_custom, b0, b1):
    fig, ax = plt.subplots(figsize=(4, 4))
    plt.subplots_adjust(left=0)  # remove margin

    # Sample data
    ax.scatter(
        data_custom["x"][:, 1],
        data_custom["y"],
        # label="Custom Data",
        color=thm.cols_set1_plt[1],
        alpha=0.5,
    )

    include_pop = False
    if include_pop:
        # True pop line
        x_values = np.linspace(-10, 10, 100)
        y_values = b0 + b1 * x_values
        if b1 >= 0:
            label = rf"$\bar{{y}} = {b0:.2f} + {b1:.2f}x$"
        else:
            label = rf"$\hat{{y}} = {b0:.2f} - {-b1:.2f}x$"

        ax.plot(
            x_values,
            y_values,
            label=label,
            color=thm.cols_set1_plt[1],
        )

    # Sample line
    b0_s = data_custom["model"].params[0]
    b1_s = data_custom["model"].params[1]

    if b1_s >= 0:
        label_s = rf"$\hat{{y}} = {b0_s:.2f} + {b1_s:.2f}x$"
    else:
        label_s = rf"$\hat{{y}} = {b0_s:.2f} - {-b1_s:.2f}x$"

    ax.plot(
        data_custom["x"][:, 1],
        data_custom["y_hat"],
        label=label_s,
        color=thm.cols_set1_plt[4],
    )

    sorted_indices = np.argsort(data_custom["x"][:, 1])
    sorted_x = data_custom["x"][:, 1][sorted_indices]
    sorted_ci_lower = data_custom["ci"][:, 0][sorted_indices]
    sorted_ci_upper = data_custom["ci"][:, 1][sorted_indices]

    ax.fill_between(
        sorted_x,
        sorted_ci_lower,
        sorted_ci_upper,
        color=thm.cols_set1_plt[4],
        alpha=0.3,
        label="95% Confidence Interval",
    )

    plt.xlim([-11, 11])
    plt.ylim([-50, 50])
    plt.xlabel("X", fontweight="bold")
    plt.ylabel("Y", fontweight="bold")
    ax.yaxis.set_label_coords(-0.08, 0.5)
    plt.legend(loc="upper left", fontsize="small")

    return fig


def create_summary(data):
    coefficients = pd.DataFrame(
        {
            "Coefficient": [r"Intercept", "Slope"],
            "Population Parameters": [b0_cust, b1_cust],
            "Sample Estimates": [
                data["model"].params[0],
                data["model"].params[1],
            ],
            "Standard Errors": [
                data["model"].bse[0],
                data["model"].bse[1],
            ],
        }
    )

    # Apply formatting to the "True Pop" and "Estimate" columns
    coefficients[
        ["Population Parameters", "Sample Estimates", "Standard Errors"]
    ] = coefficients[
        ["Population Parameters", "Sample Estimates", "Standard Errors"]
    ].applymap(
        lambda x: f"{x:.2f}"
    )

    return coefficients


with slider_col:
    if st.button("Resample data", type="primary"):
        random_seed = random.randint(0, 10000)
        custom_data = gen_lin_data(
            b0_cust, b1_cust, var_cust, n_cust, random_seed
        )


coefficients = create_summary(custom_data)

with chart_col:
    chart_col.pyplot(
        plot_ols(custom_data, b0_cust, b1_cust), use_container_width=True
    )


# CSS styles for the table (center and header)
table_styler = [
    {
        "selector": "th",  # Apply to header cells
        "props": [("background-color", "lightblue")],
    },
    {
        "selector": "td",  # Apply to data cells
        "props": [
            ("font-size", "20px"),
            ("text-align", "center"),
            ("background-color", "white"),
        ],
    },
]

# Apply CSS styles to the DataFrame
styled_coefficients = coefficients.style.set_table_styles(table_styler)

# Create a centered and styled HTML representation of the DataFrame
styled_table = styled_coefficients.hide(axis="index").to_html()

# Define custom CSS to style the table and center it
table_css = """
<style>
    table {
        margin: 0 auto;
        text-align: center;
    }
</style>
"""

s0, c02, s1 = utl.narrow_col()

with slider_col:
    st.write("")
    # display table and plot
    st.write(
        f"{table_css}{styled_table}",
        unsafe_allow_html=True,
    )
    st.write("")

    st.latex(
        f"n= {n_cust} ,"
        + f"R^2 = {custom_data['model'].rsquared:.2f}"
        + r", \hat{\sigma}"
        + f"= {custom_data['s']:.2f}"
    )

s0, c03, s1 = utl.wide_col()

with c03:
    st.markdown("### Interesting takeaways")

    with st.expander("Click to expand."):
        st.markdown(
            r"""
        1. $R^2$ is expected to be 0 if $\beta_1=0$ or if $X_i = \bar{X}$.<br>

            $R^2 = \frac{ (\hat{y} - \bar{y})' (\hat{y} - \bar{y}) }{ (y - \bar{y})' (y - \bar{y}) }
            = \frac{\sum_{i=1}^{N} (\hat{y}_i - \bar{y})^2}{\sum_{i=1}^{N} (y_i - \bar{y})^2}
            = \frac{\sum_{i=1}^{N} (\hat{\beta_1} (X_i - \bar{X}))^2}{\sum_{i=1}^{N} (y_i - \bar{y})^2}$
            , because $\hat{\beta_0} = \bar{y} - \hat{\beta_1}\bar{X}$

        2. $R^2$ is independent of the size of the intercept $b_0$ but is dependent on the size of the slope $b_1$.
        
            """,
            unsafe_allow_html=True,
        )

        # Explain why R^2 increases with \beta - what's the interpretation?

        # ADD FORMULAS FOR CONFIDENCE INTERVALS

        # related - show that R and CI are related?
        # check against statsmodels link below
        # https://www.statsmodels.org/0.9.0/_modules/statsmodels/regression/_prediction.html#PredictionResults
    #     st.markdown(
    #         r"""
    #     e. Confidence interval is visually more sensitive to sample size than to error variance, i.e.,
    #     if $n$ is large enough, even for high $\sigma^2$, the confidence interval is small because it depends only on $s^2$ and not on $\sigma^2$:<br>
    #     Also, CI is wider when further away from mean.<br>
    # """,
    #         unsafe_allow_html=True,
    #     )


with c03:
    st.header("2. Interpretation")
    st.markdown(r"""<h5>R-squared indicates:</h5>""", unsafe_allow_html=True)
    st.markdown(
        r"""
    1. "Whether variation in $x$ is a good predictor of variation in $y$" - useful for prediction accuracy (Greene Ch 3.5).<br>
    2. Proportion of total variation in $y$ that is accounted by variation in $x$ - useful for model comparison (if models are similar).<br>
    3. Measure of fit - how close the data are to the estimated model - useful to get a sense of over/under fitting.
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        r"""<h5>R-squared does NOT indicate:</h5>""", unsafe_allow_html=True
    )
    st.markdown(
        r"""
        1. Causality
        2. Unbiasedness of the coefficients
        3. Appropriateness of the model
        4. Whether OOS predictions are reasonable (e.g., high R^2 doesn't prevent forecasting of negative wages)
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        r"""<h5>R-sq and R-sq adj. vs AIC and BIC</h5>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        r"""Since R-sq increases by including more regressors, we need a measure that penalizes for adding regressors.<br>
        It has been argued that the adjusted R-sq doesn't penalize heavily enough, thus AIC and BIC measures have been proposed (Greene p. 47).<br>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        r"""
        "Choosing a model based on the lowest AIC is logically the same as using $\bar{R}^2$ in the linear model, nonstatistical, albeit widely accepted.
        The AIC and BIC are information criteria, not fit measures as such." (Greene, p.561)<br>
        APC has a direct relationship to $R^2$.<br>
        """,
        unsafe_allow_html=True,
    )

    st.header("3. More details")
    st.write("Check out the following website: TBD")
    # st.link_button(
    #     "OLS Algebra",
    #     "https://matteocourthoud.github.io/course/metrics/05_ols_algebra/",
    #     type="primary",
    # )


s0, c04, s1 = utl.wide_col()

with c04:
    st.header("4. Theory with Code")

    def tabs_code_theory():
        return st.tabs(["Theory", "Code numpy", "Code statsmodels"])

    ### Error sums
    st.markdown(
        "#### Error sums",
        unsafe_allow_html=True,
    )
    st.markdown(
        """NB: Hayashi and Greene classically disagree on notation for the sum of squared residuals (SSE or SSR), so I'll follow Greene.""",
        unsafe_allow_html=True,
    )

    f2_c1, f2_c2, f2_c3 = tabs_code_theory()
    with f2_c1:
        st.markdown(
            r"""
            Error Sum of Squares (SSE) aka Sum of Squared Residuals (SSR or RSS, hence confusion):<br>
            $SSE = \sum_{i=1}^n (y_i-\hat{y_i})^2 = \sum_{i=1}^n (e_i)^2 =  \mathbf{e'e = \varepsilon' M \varepsilon}$<br>
            (this is SSR according to Hayashi)<br>

            Regression sum of squares (SSR) aka Explained Sum of Squares (ESS):<br>
            $SSR = \sum_{i=1}^n (\hat{y_i} - \bar{y})^2 = \sum_{i=1}^n (\hat{y_i} - \bar{\hat{y}})^2$<br>
            $SSR =  \mathbf{b'X'M^0Xb}$, where $\mathbf{M^0}$ is the centering matrix<br>

            Total sum of squares (SST) aka Total Variation:<br>
            $SST = \sum_{i=1}^n (y_i-\bar{y_i})^2 = \sum_{i=1}^n (\hat{y_i} - \bar{y})^2 + \sum_{i=1}^n (e_i)^2$ <br>
            $SST = \mathbf{y'M^0y = b'X'M^0Xb + e'e = SSR + SSE}$<br>
         """,
            unsafe_allow_html=True,
        )

    with f2_c2:
        ols_code_err = """
        import numpy as np

        # Sum of squared errors
        SSE = e.dot(e)
        
        # Regression sum of squares
        y_hat_centered = y_hat - np.mean(y_hat)
        SSR = y_hat_centered.dot(y_hat_centered)

        # Total sum of squares
        y_centered = y - np.mean(y)
        SST = y_centered.dot(y_centered)
        """
        st.code(ols_code_err, language="python")

    with f2_c3:
        ols_code_err_b = """
        import statsmodels.api as sm
        model = sm.OLS(y, X).fit()

        # Sum of squared errors
        SSE = model.ssr # this is SSE according to Greene

        # Regression sum of squares
        SSR = model.ess
        
        # Total sum of squares
        SST = SSE + SSR
        """

        st.code(ols_code_err_b, language="python")

    st.divider()

    st.markdown("#### Model fit and selection measures")
    st.markdown(
        r"""
        NB: $R^2$ definition below requires a constant term to be included in the model.<br>
        """,
        unsafe_allow_html=True,
    )

    f3_c1, f3_c2, f3_c3 = tabs_code_theory()

    # Sources for AIC and BIC
    sas_source = "https://documentation.sas.com/doc/en/vfcdc/8.5/vfug/p0uawamu7dmtc2n1cllfwajyvlko.htm"
    stata_source = "https://www.stata.com/manuals13/restatic.pdf"
    stack_ex = "https://stats.stackexchange.com/questions/490056/aic-bic-formula-wrong-in-james-witten"

    with f3_c1:
        st.markdown(
            r"""          
            R-sq, Adjusted R-sq, and Pseudo R-sq:<br>
            $R^2 = \frac{SSR}{SST} = \frac{SST - SSE}{SST} = 1 - \frac{SSE}{SST}= 1- \mathbf{\frac{e'e}{y'M^0y}}$<br>
            $\bar{R}^2 = 1 - \frac{n - 1}{n - K} (1 - R^2)$<br>
            McFadden Pseudo  $R^2 = 1 - \frac{\text{ln} L}{\text{ln} L_0} = \frac{-\text{ln}(1-R^2)}{1+\text{ln}(2\pi) + \text{ln}(s_y^2)}$<br>
            
            Amemiya's Prediction Criterion (APC):<br>
            $APC=\frac{SSE}{n-K}(1+\frac{K}{n}) = SSE \frac{n+K}{n-K}$<br>

            AIC and BIC for OLS, when error variance is known (Greene p. 47):<br>
            $AIC = \text{ln}(\frac{SSE}{n}) + \frac{2K}{n}$<br>
            $BIC = \text{ln}(\frac{SSE}{n}) + \frac{\text{ln}(n) K}{n}$<br>
            
            AIC and BIC are more often calculated for any MLE as follows (Greene p. 561):<br>
            $AIC = -2 \text{ln}(L)+2K$<br>
            $BIC = -2 \text{ln}(L) + \text{ln}(n) K  $<br>
            
            In OLS, SSE is proportional to log-likelihood, so the two formulas would lead to the same model selection.<br>
            NB: Even for OLS, Python *statsmodels*, STATA *estat ic*, and R *lm* use the latter definition, whereas SAS uses the former multiplied by $n$.
            """,
            unsafe_allow_html=True,
        )

    with f3_c2:
        r2_code = """
        import numpy as np
        # R-sq and R-sq adjusted
        y_centered = y - np.mean(y)
        r_sq = 1 - e.dot(e) / y_centered.dot(y_centered)
        r_sq_adj = 1 - ((n - 1) / (n - K)) * (1 - r_sq)

        # Pseudo R-sq
        var_y = np.var(y)
        pseudo_r_sq = (-1 * np.log(1 - r_sq) / (1 + np.log(2 * np.pi) + np.log(var_y)))
                
        # Amemiya's Prediction Criterion
        APC = (e.dot(e) / n) * (n + K) / (n - K)

        # AIC and BIC, first get log likelihood
        ln_L = (-n / 2) * (1 + np.log(2 * np.pi) + np.log(SSE / n))
        AIC = -2 * ln_L + 2 * K
        BIC = -2 * ln_L + K * np.log(n)
        """
        st.code(r2_code, language="python")

    with f3_c3:
        r2_code_built_in = """
        import statsmodels.api as sm
        import numpy as np

        model = sm.OLS(y, X).fit()

        # R-sq and R-sq adjusted
        r_sq = model.rsquared
        r_sq_adj = model.rsquared_adj

        # Pseudo R-sq
        ln_L = model.llf
        model_constant = sm.OLS(y, np.ones(n)).fit()
        ln_L_0 = model_constant.llf
        pseudo_r_sq = 1 - ln_L / ln_L_0

        # Amemiya's Prediction Criterion - no built-in module
        APC = (e.dot(e) / n) * (n + K) / (n - K)

        # AIC and BIC
        AIC = model.aic
        BIC = model.bic

        """

        st.code(r2_code_built_in, language="python")

    st.divider()

s0, c05, s1 = utl.wide_col()
with c05:
    st.header("5. Proofs to remember")
    sst_proof = "https://stats.stackexchange.com/questions/207841/why-is-sst-sse-ssr-one-variable-linear-regression/401299#401299"

    with st.expander("SST = SSR + SSE"):
        st.markdown(
            rf"Proof from Greene Section 3.5 (also see [Stack Exchange]({sst_proof})):<br>"
            + r"""
                $y_i - \bar{y} = \mathbf{x}_i'\mathbf{b} + e_i$<br>
                $y_i - \bar{y} = \hat{y}_i - \bar{y} + e_i = (\mathbf{x}_i - \mathbf{\bar{x}})'\mathbf{b} + e_i$<br>
                $\mathbf{M^0y= M^0Xb + M^0e}$<br>
                $SST = \mathbf{y'M^0y = b'X'M^0Xb + e'e} = SSR + SSE$<br>
                (need to expand between last two steps, but main trick is that $\mathbf{e'M^0X = e'X=0}$)<br>
                """,
            unsafe_allow_html=True,
        )

    with st.expander(
        "Relating two formulations of AIC (Greene pp. 47 and 561)"
    ):
        st.markdown(
            r"""
            Not sure if this is useful, but it clarified things in my head.<br>
            
            Recall, $SSE = \mathbf{e'e}$<br>
            In the linear model with normally distributed disturbances, the maximized log likelihood is<br>
            $\text{ln} L = -\frac{n}{2} [1 + \text{ln}(2 \pi) + \text{ln}(\frac{SSE}{n})]$<br>
            Ignore the constants and notice that<br>
            $\text{ln} L \propto -\frac{n}{2} \text{ln}(\frac{SSE}{n})$<br>
            $-2 \text{ln} L \propto n \text{ln}(\frac{SSE}{n})$<br>
            $-2 \text{ln} L + 2K \propto n \text{ln}(\frac{SSE}{n}) + 2K$<br>
            $-2 \text{ln} L + 2K \propto \text{ln}(\frac{SSE}{n}) + \frac{2K}{n}$<br>
            Which we wanted to show.<br>
            Might have been enough to just state that $\text{ln} L \propto -\text{ln}(\frac{SSE}{n})$.
""",
            unsafe_allow_html=True,
        )
