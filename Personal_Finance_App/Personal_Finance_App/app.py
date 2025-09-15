from flask import Flask, render_template, request, redirect, url_for 
import sqlite3

app = Flask(__name__)
DATABASE = 'finance_database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return redirect(url_for('account_view', account_id=1))  # Standardvisning: Primær konto (Opsparing)

@app.route('/account/<int:account_id>')
def account_view(account_id):
    conn = get_db_connection()

    # Hent transaktioner for den valgte konto
    transactions = conn.execute("""
        SELECT "Category", SUM("Amount (DKK)") as total
        FROM "Transactions"
        WHERE "Account_ID" = ?
        GROUP BY "Category"
    """, (account_id,)).fetchall()

    # Hent kontonavnet
    account_name = conn.execute("""
        SELECT "Account_Name" FROM "Accounts" WHERE "Account_ID" = ?
    """, (account_id,)).fetchone()

    conn.close()

    # Konverter resultater til JSON-venligt format
    account_data = [{"label": row["Category"], "y": row["total"]} for row in transactions]

   # print(f"Viser data for konto {account_id}: {account_data}")  # Debugging (Tjek data når man trykker på Konto)

    return render_template('home.html', account_data=account_data, account_name=account_name["Account_Name"] if account_name else "Ukendt Konto")


@app.route('/index')
def index_overblik():
    conn = get_db_connection()

    # Hent alle konti
    accounts = conn.execute("SELECT Account_ID, Account_Name FROM Accounts").fetchall()

    all_account_data = []

    for account in accounts:
        account_id = account["Account_ID"]
        account_name = account["Account_Name"]

        transactions = conn.execute("""
            SELECT "Category", SUM("Amount (DKK)") as total
            FROM "Transactions"
            WHERE "Account_ID" = ?
            GROUP BY "Category"
        """, (account_id,)).fetchall()

        chart_data = [{"label": row["Category"], "y": row["total"]} for row in transactions]

        all_account_data.append({
            "account_id": account_id,
            "account_name": account_name,
            "chart_data": chart_data
        })

    conn.close()
    return render_template("index_overblik.html", all_account_data=all_account_data)

@app.route('/transactions/<int:account_id>')
def transaction(account_id):
    conn = get_db_connection()

    # Hent transaktioner for valgt konto
    transactions = conn.execute("""
        SELECT "Date", "Amount (DKK)", "Category", "Vendor"
        FROM Transactions
        WHERE Account_ID = ?
        ORDER BY Date DESC
    """, (account_id,)).fetchall()

    conn.close()

    return render_template('transaction.html', transactions=transactions, account_id=account_id)


@app.route('/goals', methods=['GET', 'POST'])
def goals():
    conn = get_db_connection()

    if request.method == 'POST':
        goal_name = request.form['goal-name']
        account_id = request.form['account-id']
        target_amount = request.form['target-amount']
        current_amount = request.form['current-amount']
        deadline = request.form['deadline']

        conn.execute("""
            INSERT INTO Goals (Goal_Name, Account_ID, "Target_Amount (DKK)", "Current_Amount (DKK)", Deadline)
            VALUES (?, ?, ?, ?, ?)
        """, (goal_name, account_id, target_amount, current_amount, deadline))
        conn.commit()

    # Hent alle mål og tilhørende konto-navne
    goals = conn.execute("""
        SELECT g.Goal_ID, g.Goal_Name, g."Target_Amount (DKK)", g."Current_Amount (DKK)", g.Deadline, a.Account_Name
        FROM Goals g
        JOIN Accounts a ON g.Account_ID = a.Account_ID
    """).fetchall()

    # Hent kontoliste til dropdown
    accounts = conn.execute("SELECT Account_ID, Account_Name FROM Accounts").fetchall()
    conn.close()

    return render_template('goals.html', goals=goals, accounts=accounts)

@app.route('/delete_goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Goals WHERE Goal_ID = ?", (goal_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('goals'))

@app.route('/data')
def Data_overview():
    conn = get_db_connection()

    # Hent de mest købte fra (Top 10 butikker)
    top_merchants = conn.execute("""
        SELECT "Merchant_Name", "Purchase_Count"
        FROM "Top Merchants" 
        ORDER BY "Purchase_Count" DESC
        LIMIT 10
    """).fetchall()

    # Højeste forbrug (Top 10 kategorier)
    highest_spending = conn.execute("""
        SELECT "Category", SUM("Amount (DKK)") as total
        FROM "Transactions"
        GROUP BY "Category"
        ORDER BY total DESC
        LIMIT 10
    """).fetchall()

    # Laveste forbrug (Bund 10 kategorier)
    lowest_spending = conn.execute("""
        SELECT "Category", SUM("Amount (DKK)") as total
        FROM "Transactions"
        GROUP BY "Category"
        ORDER BY total ASC
        LIMIT 10
    """).fetchall()

    conn.close()
    return render_template(
        'Data_overview.html', 
        top_merchants=top_merchants, 
        highest_spending=highest_spending, 
        lowest_spending=lowest_spending
    )

if __name__ == '__main__':
    app.run(debug=True)
