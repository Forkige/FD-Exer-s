#!/usr/bin/env python3
import cgi
import mysql.connector
import html

form = cgi.FieldStorage()
action = form.getvalue("action", "")
subjectid = form.getvalue("subjectid", "")
code = form.getvalue("code", "")
description = form.getvalue("description", "")
units = form.getvalue("units", "")
schedule = form.getvalue("schedule", "")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sample"
    )
    cursor = conn.cursor()
    
    # Get the next subject ID
    cursor.execute("SELECT MAX(subjid) FROM subjects")
    max_id = cursor.fetchone()[0]
    next_subject_id = max_id + 1 if max_id and max_id >= 2000 else 2000
    
    if action == "insert" and subjectid and code:
        cursor.execute("INSERT INTO subjects (subjid, subjcode, subjdesc, subjunits, subjsched) VALUES (%s, %s, %s, %s, %s)", (subjectid, code, description, units, schedule))
        conn.commit()
        conn.close()
        print("Location: subjects.py\n")
        exit()
    elif action == "update" and subjectid and code:
        cursor.execute("UPDATE subjects SET subjcode=%s, subjdesc=%s, subjunits=%s, subjsched=%s WHERE subjid=%s",(code, description, units, schedule, subjectid))
        conn.commit()
    elif action == "delete" and subjectid:
        cursor.execute("DELETE FROM enroll WHERE subjid=%s",(subjectid,))
        cursor.execute("DELETE FROM subjects WHERE subjid=%s",(subjectid,))
        conn.commit()
    
    print("Content-Type: text/html\n")
    
    cursor.execute("""
        SELECT s.subjid, s.subjcode, s.subjdesc, s.subjunits, s.subjsched, 
        COUNT(e.studid) as student_count
        FROM subjects s
        LEFT JOIN enroll e ON s.subjid = e.subjid
        GROUP BY s.subjid, s.subjcode, s.subjdesc, s.subjunits, s.subjsched
    """)
    rows = cursor.fetchall()
    
    print("""
    <html>
        <style>
          body{
            margin-left:10%;
            margin-right:10%;
            border: 2px outset;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
          }
          .header-logo{
            width: 100px;
            height: 100px;
          
          }
          header{
            display: flex;
            flex-direction: row;
            background: #020024;
            background: linear-gradient(90deg, rgba(2, 0, 36, 1) 0%, rgba(9, 9, 121, 1) 35%, rgba(0, 212, 255, 1) 100%);
            color: white;
          }
          .header_alignment{
            display: flex;
            flex-direction: column;
          }
        </style>
        <script>
        function fillForm(subjectid, code, description, units, schedule){
            var url = 'subjects.py?subjectid=' + subjectid + '&code=' + encodeURIComponent(code) + '&description=' + encodeURIComponent(description) + '&units=' + units + '&schedule=' + encodeURIComponent(schedule);
            window.location.href = url;
        }
        </script>
    <body>
    <header>
        <img src=https://png.pngtree.com/png-vector/20250426/ourmid/pngtree-a-stylized-silver-phoenix-with-fiery-orange-flames-at-its-base-png-image_16114552.png class="header-logo">
        <div class="header_alignment">
            <h1>Student Information System</h1>
            <div>Silvercrest University</div>
        </div>
    </header>
   
    <table width="100%" cellpadding="10">
        <tr>
            <td width="30%" valign="top">
            <div class = "pages">
                <a href="students.py""" + ("?selected_subject=" + subjectid if subjectid else "") + """">Students</a>
                <a href="subjects.py">Subjects</a>
                <a href="teachers.py""" + ("?selected_subject=" + subjectid if subjectid else "") + """">Teachers</a>
            </div>

                <h3>Subject Form</h3>
                <form action="subjects.py" method="post">
                    <input type="hidden" name="subjectid" id="subjectid" value=\"""" + (subjectid if subjectid else str(next_subject_id)) + """\">
                    Subject ID: <input type="text" id="subjectid_display" value=\"""" + (subjectid if subjectid else str(next_subject_id)) + """\" disabled><br>
                    Subject Code: <input type="text" name="code" id="code" value=\"""" + code + """\"><br>
                    Description: <input type="text" name="description" id="description" value=\"""" + description + """\"><br>
                    Units: <input type="text" name="units" id="units" value=\"""" + units + """\"><br>
                    Schedule: <input type="text" name="schedule" id="schedule" value=\"""" + schedule + """\"><br><br><br>
                    <input type="hidden" name="action" id="action">
                    <input type="submit" value="Insert" onclick="document.getElementById('action').value='insert'">
                    <input type="submit" value="Update" onclick="document.getElementById('action').value='update'">
                    <input type="submit" value="Delete" onclick="document.getElementById('action').value='delete'">
                 </form>
            </td>
            <td width="70%" valign="top">
                <h3>Subjects Table</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="100%">
                    <tr>
                        <th>ID</th>
                        <th>Code</th>
                        <th>Description</th>
                        <th>Units</th>
                        <th>Schedule</th>
                        <th>#Students</th>
                    </tr>
    """)
    
    for row in rows:
        subjectid_val = str(row[0])
        code_val = str(row[1]) if row[1] else ""
        description_val = str(row[2]) if row[2] else ""
        units_val = str(row[3]) if row[3] else ""
        schedule_val = str(row[4]) if row[4] else ""
        student_count = str(row[5])
        print("<tr onclick=\"fillForm('{}','{}','{}','{}','{}')\" style=\"cursor:pointer;\">".format(subjectid_val, code_val, description_val, units_val, schedule_val))
        print("<td>" + subjectid_val + "</td>")
        print("<td>" + code_val + "</td>")
        print("<td>" + description_val + "</td>")
        print("<td>" + units_val + "</td>")
        print("<td>" + schedule_val + "</td>")
        print("<td>" + student_count + "</td>")
        print("</tr>")
    
    print("""
                </table>
                <br><br>
                <h3>Students Enrolled in Subject ID """ + (subjectid if subjectid else "") + """</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="100%">
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Address</th>
                        <th>Gender</th>
                        <th>Course</th>
                        <th>Year Level</th>
                    </tr>
    """)
    
    if subjectid:
        cursor.execute("""
            SELECT st.studid, st.studname, st.studadd, st.studgender, st.studcrs, st.yrlvl
            FROM students st
            JOIN enroll e ON st.studid = e.studid
            WHERE e.subjid = %s
        """, (subjectid,))
        enrolled = cursor.fetchall()
        for row in enrolled:
            print("<tr>")
            print("<td>" + str(row[0]) + "</td>")
            print("<td>" + str(row[1]) + "</td>")
            print("<td>" + (str(row[2]) if row[2] else "") + "</td>")
            print("<td>" + (str(row[3]) if row[3] else "") + "</td>")
            print("<td>" + (str(row[4]) if row[4] else "") + "</td>")
            print("<td>" + (str(row[5]) if row[5] else "") + "</td>")
            print("</tr>")
    
    print("""
                </table>
            </td>
        </tr>
    </table>
    </body>
    </html>
    """)
except Exception as e:
    print("Content-Type: text/html\n")
    print("<h2>Error</h2>")
    print(f"<pre>{e}</pre>")
    
finally:
    if 'conn' in locals():
        conn.close()