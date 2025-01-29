from flask import Flask, request, render_template, jsonify
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import io
import base64

matplotlib.use('Agg')  # Use a non-interactive backend

# Initialize Flask app
app = Flask(__name__)

# Define functions from your provided code
def calculate_mortgage_payment(loan_amt, interest_rate, loan_term):
    monthly_interest_rate = interest_rate / 12
    number_of_payments = loan_term * 12
    return loan_amt * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments) / ((1 + monthly_interest_rate) ** number_of_payments - 1)

def generate_amortization_schedule(principal: float, annual_rate: float, monthly_payment: float, loan_term: int) -> list:
    amortization_schedule = []
    monthly_rate = annual_rate / 12
    total_payments = loan_term * 12
    current_balance = principal

    for month in range(1, total_payments + 1):
        interest_payment = current_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        current_balance -= principal_payment

        amortization_schedule.append({
            "Month": month,
            "Year": (month - 1) // 12 + 1,
            "MonthlyPayment": monthly_payment,
            "PrincipalPayment": principal_payment,
            "InterestPayment": interest_payment,
            "RemainingBalance": current_balance
        })

    return amortization_schedule

def calculate_cumulative_annual_principal_paid(amortization_schedule: list) -> dict:
    annual_principal_payments = {}
    cumulative_principal = 0

    for payment in amortization_schedule:
        year = payment["Year"]
        principal_payment = payment["PrincipalPayment"]

        if year not in annual_principal_payments:
            annual_principal_payments[year] = 0

        cumulative_principal += principal_payment
        annual_principal_payments[year] = cumulative_principal

    return annual_principal_payments

def get_equity(loan_val, interest):
    mort_pmt = calculate_mortgage_payment(loan_val, interest, 30)
    am_sch = generate_amortization_schedule(loan_val, interest, mort_pmt, 30)
    equity = calculate_cumulative_annual_principal_paid(am_sch)
    return equity.get(1, 0)

def calculate_payment_range(loan_amt: float, interest_val: float, down_pmt_pct: int):
    equity_list = []
    mortgage_payments = []
    pmi_vals = []
    alow = 0.0159
    ahigh = 0.0577
    ap_pct = 0.10  # percent of anticipated appreciation to apply to payment
    eq_pct = 0.40  # percent of expected equity to apply to payment
    for r in range(99):
        lv = loan_amt - loan_amt * (r / 100)
        # 0.7% PMI
        pmi = 0.007/12*lv if (loan_amt * (r / 100)) / loan_amt < 0.20 else 0
        mp = calculate_mortgage_payment(lv, interest_val, 30)
        equity_list.append(get_equity(lv, interest_val))
        mortgage_payments.append(mp)
        pmi_vals.append(pmi)

    equity_appreciation_low = [((e * eq_pct) + (loan_amt * alow * ap_pct)) / 12 for e in equity_list]
    equity_appreciation_high = [((e * eq_pct) + (loan_amt * ahigh * ap_pct)) / 12 for e in equity_list]
    min_pmt = [p - e for p, e in zip(mortgage_payments, equity_appreciation_high)]
    max_pmt = [p + e for p, e in zip(mortgage_payments, equity_appreciation_low)]
    property_tax = 0.011/12*loan_amt
    base_insurance = 167
    # mortgage_payments = [mort*(1+property_tax) for mort in mortgage_payments]
    mortgage_payments = [m+v+base_insurance+property_tax for m, v in zip(mortgage_payments, pmi_vals)]
    mdf = pd.DataFrame({
        'Mortgage Payment': [round(mo, 2) for mo in mortgage_payments],
        'min pmt': [round(mip, 2) for mip in min_pmt],
        'max pmt': [round(mxp, 2) for mxp in max_pmt],
        'equity_low': equity_appreciation_low,
        'equity_high': equity_appreciation_high
    })

    return mdf.iloc[down_pmt_pct]

def generate_equity_chart(loan_amt, interest_rate, selected_payment):
    am_sch = generate_amortization_schedule(loan_amt, interest_rate, selected_payment, 30)
    equity_data = calculate_cumulative_annual_principal_paid(am_sch)
    # Prepare data for 5 years
    years = list(range(2025, 2030))
    equity_values = [equity_data.get(val, 0) for val in range(1, 6)]
    appreciation_values = calculate_appreciation(loan_amt)
    # Generate bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(years, equity_values, color='skyblue', label='Equity')
    plt.bar(years, appreciation_values, bottom=equity_values, color='orange', label='Appreciation')
    plt.title('Equity & Appreciation Over 5 Years')
    plt.xlabel('Year')
    plt.ylabel('Equity & Appreciation ($)')
    plt.legend()

    # Save plot to a string buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return chart_url


# Forecast from fhfa.gov US appreciation data
five_yr_appreciation = [105.24375510234167,
                        105.32217190206609,
                        105.4005887017905,
                        105.47900550151492,
                        105.55742230123933]
def calculate_appreciation(original_property_value: float):
    yearly_appreciation = []
    cv = original_property_value
    for i, yr in enumerate(five_yr_appreciation):
        if i == 0:
            cv = yr/100*original_property_value
            yearly_appreciation.append(round(cv, 2) - original_property_value)
        else:
            cv = cv*yr/100
            yearly_appreciation.append(round(cv, 2) - original_property_value)
    return yearly_appreciation

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            # Get user inputs
            # Add closing costs as part of "purchase price"
            # On selling a home the closing costs would be allocated to the investment bucket 13%
            loan_amt = float(request.form['loan_amt'])
            interest_val = float(request.form['interest_val']) / 100  # Convert percentage to decimal #TODO: connect to API
            down_pmt_pct = int(request.form['down_pmt_pct'])

            # Call the calculate_payment_range function
            result = calculate_payment_range(loan_amt, interest_val, down_pmt_pct)
            # print(result['equity_low'], result['equity_high'])

            # Format the result as a dictionary to display on the page
            result_dict = {
                'Mortgage Payment': result['Mortgage Payment'],
                'Minimum Payment': result['min pmt'],
                'Maximum Payment': result['max pmt'],
                'LoanAmount': loan_amt,
                'InterestRate': interest_val
            }

            return render_template('index.html', result=result_dict)
        except Exception as e:
            return render_template('index.html', error=str(e))

    # For GET requests, pass a default empty result and no error
    return render_template('index.html', result=None, error=None, default_loan_amt=420000, default_interest_val=5.5, default_down_pmt_pct=7)

@app.route('/chart', methods=['POST'])
def chart():
    try:
        # Parse JSON input
        data = request.get_json()
        loan_amt = float(data['loan_amt'])
        interest_val = float(data['interest_val'])
        selected_payment = float(data['selected_payment'])

        # Generate equity chart
        chart_url = generate_equity_chart(loan_amt, interest_val, selected_payment)

        return jsonify({'chart_url': chart_url})
    except Exception as e:
        return jsonify({'error': str(e)})


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
