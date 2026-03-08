#!/usr/bin/env python3
import cgi
import mysql.connector
import html
from datetime import datetime

form = cgi.FieldStorage()
action = form.getvalue("action", "")
username = form.getvalue("username", "")
password = form.getvalue("password", "")
school_year = form.getvalue("school_year", "")

login_error = ""
step = 1  # 1 = show username/password form, 2 = show school year dropdown

# Generate school year options dynamically
def get_school_year_options(selected=""):
    options = []
    current_year = datetime.now().year
    for year in range(current_year - 2, current_year + 4):
        for sem in ["1stsem", "2ndsem", "summer"]:
            value = f"{sem}_sy{year}_{year+1}"
            label = f"{sem}, sy{year}_{year+1}"
            sel = ' selected' if value == selected else ''
            options.append(f'<option value="{value}"{sel}>{label}</option>')
    return "\n".join(options)

if action == "login" and username and password:
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=username,
            password=password,
            database="sample"
        )
        conn.close()
        step = 2  # Credentials valid, move to step 2
    except mysql.connector.Error:
        login_error = "Invalid username or password."
        step = 1

elif action == "continue" and username and password and school_year:
    # Final step: verify credentials again and redirect
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=username,
            password=password,
            database="sample"
        )
        conn.close()
        print("Content-Type: text/html\n")
        sy_param = html.escape(school_year)
        print(f"<script>window.location.href='students.py?school_year={sy_param}';</script>")
        exit()
    except mysql.connector.Error:
        login_error = "Session expired. Please login again."
        step = 1

print("Content-Type: text/html\n")

current_year = datetime.now().year
default_sy = school_year if school_year else f"1stsem_sy{current_year}_{current_year+1}"

print(f"""
<html>
    <head>
        <title>Student Information System - Login</title>
        <style>
          body {{
            margin-left: 10%;
            margin-right: 10%;
            border: 2px outset;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
            font-family: Arial, sans-serif;
          }}
          .header-logo {{
            width: 100px;
            height: 100px;
          }}
          header {{
            display: flex;
            flex-direction: row;
            background: #020024;
            background: linear-gradient(90deg, rgba(2, 0, 36, 1) 0%, rgba(9, 9, 121, 1) 35%, rgba(0, 212, 255, 1) 100%);
            color: white;
          }}
          .header_alignment {{
            display: flex;
            flex-direction: column;
            justify-content: center;
          }}
          table.content-table {{
            width: 100%;
          }}
          .login-section {{
            padding: 10px;
            vertical-align: top;
            width: 30%;
          }}
          .welcome-section {{
            padding: 10px;
            vertical-align: top;
          }}
          .login-section h3 {{
            margin-top: 10px;
            margin-bottom: 4px;
          }}
          .error-msg {{
            color: red;
            font-weight: bold;
            margin-top: 8px;
          }}
          label {{
            display: block;
            margin-top: 4px;
            margin-bottom: 2px;
          }}
          input[type="text"], input[type="password"] {{
            display: block;
            margin-bottom: 4px;
            width: 200px;
          }}
          select {{
            display: block;
            margin-bottom: 8px;
            width: 205px;
          }}
        </style>
    </head>
    <body>
    <header>
        <img src="https://png.pngtree.com/png-vector/20250426/ourmid/pngtree-a-stylized-silver-phoenix-with-fiery-orange-flames-at-its-base-png-image_16114552.png" class="header-logo">
        <div class="header_alignment">
            <h1>Student Information System</h1>
            <div>Silvercrest University</div>
        </div>
    </header>

    <table class="content-table" cellpadding="10">
        <tr>
            <td class="login-section">
                <h3>Login</h3>
""")

if step == 1:
    # Step 1: Username and Password
    print(f"""
                <form action="index.py" method="post">
                    <input type="hidden" name="action" value="login">
                    <label>Username:</label>
                    <input type="text" name="username" id="username" value="{html.escape(username)}">
                    <label>Password:</label>
                    <input type="password" name="password" id="password">
                    <br>
                    <input type="submit" value="Login">
                </form>
                {"<div class='error-msg'>" + html.escape(login_error) + "</div>" if login_error else ""}
    """)

elif step == 2:
    # Step 2: Show school year dropdown and Continue button
    print(f"""
                <form action="index.py" method="post">
                    <input type="hidden" name="action" value="continue">
                    <input type="hidden" name="username" value="{html.escape(username)}">
                    <input type="hidden" name="password" value="{html.escape(password)}">
                    <label>Username:</label>
                    <input type="text" value="{html.escape(username)}" disabled>
                    <label>Password:</label>
                    <input type="password" value="****" disabled>
                    <label>School Year:</label>
                    <select name="school_year" id="school_year">
                        {get_school_year_options(default_sy)}
                    </select>
                    <input type="submit" value="Continue">
                </form>
    """)

print("""
            </td>
            <td class="welcome-section">
                <h2>Welcome to Student System</h2>
                <p>Please login to continue.</p>
            </td>
        </tr>
    </table>
    </body>
</html>
""")






