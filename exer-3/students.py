#!/usr/bin/env python3
import cgi
import mysql.connector
import html

form = cgi.FieldStorage()
action = form.getvalue("action", "")
studentid = form.getvalue("studentid", "")
name = form.getvalue("name", "")
address = form.getvalue("address", "")
gender = form.getvalue("gender", "")
course = form.getvalue("course", "")
yearlevel = form.getvalue("yearlevel", "")
selected_subject = form.getvalue("selected_subject", "")
drop_subject = form.getvalue("drop_subject", "")
conflict_sched = form.getvalue("conflict_sched", "")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sample"
    )
    cursor = conn.cursor()
    
    # Get the next student ID
    cursor.execute("SELECT MAX(studid) FROM students")
    max_id = cursor.fetchone()[0]
    next_student_id = max_id + 1 if max_id and max_id >= 1000 else 1000
#-------------------------------------------------------------------------Insert,update,delete-------------------------------------------------------------------------#
    if action == "insert" and studentid and name:
        cursor.execute("INSERT INTO students (studid, studname, studadd, studgender, studcrs, yrlvl) VALUES (%s, %s, %s, %s, %s, %s)", (studentid, html.escape(name), html.escape(address), html.escape(gender), html.escape(course), html.escape(yearlevel)))
        conn.commit()
        conn.close()
        # Redirect to refresh with incremented ID
        print("Content-Type: text/html\n")
        print("<script>window.location.href='students.py';</script>")
        exit()

    elif action == "update" and studentid and name:
        cursor.execute("UPDATE students SET studname=%s, studadd=%s, studgender=%s, studcrs=%s, yrlvl=%s WHERE studid=%s",(html.escape(name), html.escape(address), html.escape(gender), html.escape(course), html.escape(yearlevel), studentid))
        conn.commit()

    elif action == "delete" and studentid:
        # First delete all enrollments for this student
        cursor.execute("DELETE FROM enroll WHERE studid=%s",(studentid,))
        # Then delete the student
        cursor.execute("DELETE FROM students WHERE studid=%s",(studentid,))
        conn.commit()
#-------------------------------------------------------------------------Insert,update,delete-------------------------------------------------------------------------#
#----------------------------------------------------------------------------enroll & drop----------------------------------------------------------------------------#

    schedule_result = None
    
    # Check for schedule conflicts whenever a subject is selected
    if studentid and selected_subject and not drop_subject:
        try:
            cursor.execute("CALL checksched(%s, %s, @result)", (studentid, selected_subject))
            cursor.execute("SELECT @result")
            schedule_result = cursor.fetchone()[0]
        except:
            schedule_result = None
    
    if action == "enroll" and studentid and selected_subject:
        try:
            # Call stored procedure to check schedule conflict
            cursor.execute("CALL checksched(%s, %s, @result)", (studentid, selected_subject))
            cursor.execute("SELECT @result")
            schedule_result = cursor.fetchone()[0]
        
            if schedule_result == 'OK':
                cursor.execute("INSERT INTO enroll (studid, subjid) VALUES (%s, %s)", (studentid, selected_subject))
                conn.commit()
                schedule_result = None  # Clear after successful enrollment
        except mysql.connector.IntegrityError:
            pass  # Student already enrolled
    
    elif action == "drop" and studentid and drop_subject:
        cursor.execute("DELETE FROM enroll WHERE studid = %s AND subjid = %s", (studentid, drop_subject))
        conn.commit()
#----------------------------------------------------------------------------enroll & drop----------------------------------------------------------------------------#
    
    # Check if student is already enrolled in the selected subject
    is_enrolled = False
    if studentid and selected_subject:
        cursor.execute("SELECT COUNT(*) FROM enroll WHERE studid = %s AND subjid = %s", (studentid, selected_subject))
        is_enrolled = cursor.fetchone()[0] > 0
    
    print("Content-Type: text/html\n")
    
    cursor.execute("""
        SELECT s.studid, s.studname, s.studadd, s.studgender, s.studcrs, s.yrlvl, 
        COALESCE(SUM(subj.subjunits), 0) as total_units
        FROM students s
        LEFT JOIN enroll e ON s.studid = e.studid
        LEFT JOIN subjects subj ON e.subjid = subj.subjid
        GROUP BY s.studid, s.studname, s.studadd, s.studgender, s.studcrs, s.yrlvl
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
        function fillForm(studentid, name, address, gender, course, yearlevel){
            var selectedSubject = """ + ('"' + html.escape(selected_subject) + '"' if selected_subject else '""') + """;
            var url = 'students.py?studentid=' + studentid + '&name=' + encodeURIComponent(name) + '&address=' + encodeURIComponent(address) + '&gender=' + encodeURIComponent(gender) + '&course=' + encodeURIComponent(course) + '&yearlevel=' + encodeURIComponent(yearlevel);
            if (selectedSubject) {
                url += '&selected_subject=' + selectedSubject;
            }
            window.location.href = url;
        }
        
        function selectEnrolledSubject(subjid) {
            var studentId = document.getElementById("studentid").value;
            var url = 'students.py?studentid=' + studentId;
            url += '&name=' + encodeURIComponent(document.getElementById("name").value);
            url += '&address=' + encodeURIComponent(document.getElementById("address").value);
            url += '&gender=' + encodeURIComponent(document.getElementById("gender").value);
            url += '&course=' + encodeURIComponent(document.getElementById("course").value);
            url += '&yearlevel=' + encodeURIComponent(document.getElementById("yearlevel").value);
            url += '&drop_subject=' + subjid;
            window.location.href = url;
        }
        
        function updateButtons() {
            var selectedSubject = """ + ('"' + html.escape(selected_subject) + '"' if selected_subject else '""') + """;
            var dropSubject = """ + ('"' + html.escape(drop_subject) + '"' if drop_subject else '""') + """;
            var studentId = document.getElementById("studentid").value;
            var isEnrolled = """ + ("true" if is_enrolled else "false") + """;
            var scheduleConflict = """ + ('"' + schedule_result.split(':', 1)[1].strip() + '"' if schedule_result and schedule_result.startswith('CONFLICT:') else '""') + """;
            var enrollBtn = document.getElementById("enrollBtn");
            var dropBtn = document.getElementById("dropBtn");
            var conflictMsg = document.getElementById("conflictMsg");
    
        // Hide both buttons and message initially
        enrollBtn.style.display = "none";
        dropBtn.style.display = "none";
        conflictMsg.style.display = "none";
    
    // Show conflict message if exists
    if (scheduleConflict && scheduleConflict !== "") {
        conflictMsg.style.display = "block";
        conflictMsg.innerHTML = "Conflict with " + scheduleConflict;
        return; // Don't show enroll button
    }
            
            // Show drop button if drop_subject is set
            if (dropSubject && studentId) {
                dropBtn.style.display = "inline-block";
                dropBtn.value = "Drop Student ID: " + studentId + " from Subject ID: " + dropSubject;
            }
            // Show enroll button only if selected_subject is set and not already enrolled
            else if (selectedSubject && !isEnrolled) {
                enrollBtn.style.display = "inline-block";
                if (studentId && studentId !== """ + ('"' + str(next_student_id) + '"') + """) {
                    enrollBtn.value = "Enroll Student ID: " + studentId + " to Subject ID: " + selectedSubject;
                } else {
                    enrollBtn.value = "Enroll Student ID: ? to Subject ID: " + selectedSubject;
                }
            }
        }
        
        window.onload = function() {
            updateButtons();
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
                <a href="students.py">Students</a>
                <a href="subjects.py">Subjects</a>
                <a href="teachers.py">Teachers</a>
            </div>
            
                <h3>Student Form</h3>
                <form action="students.py" method="post">
                    <input type="hidden" name="studentid" id="studentid" value=\"""" + (html.escape(studentid) if studentid else str(next_student_id)) + """\">
                    Student ID: <input type="text" id="studentid_display" value=\"""" + (html.escape(studentid) if studentid else str(next_student_id)) + """\" disabled><br>
                    Name: <input type="text" name="name" id="name" value=\"""" + html.escape(name if name else "") + """\"><br>
                    Address: <input type="text" name="address" id="address" value=\"""" + html.escape(address if address else "") + """\"><br>
                    Gender: <input type="text" name="gender" id="gender" value=\"""" + html.escape(gender if gender else "") + """\"><br>
                    Course: <input type="text" name="course" id="course" value=\"""" + html.escape(course if course else "") + """\"><br>
                    Year Level: <input type="text" name="yearlevel" id="yearlevel" value=\"""" + html.escape(yearlevel if yearlevel else "") + """\"><br><br><br>
                    <input type="hidden" name="action" id="action">
                    <input type="hidden" name="selected_subject" id="selected_subject" value=\"""" + html.escape(selected_subject) + """\">
                    <input type="hidden" name="drop_subject" id="drop_subject" value=\"""" + html.escape(drop_subject) + """\">
                    <input type="submit" value="Insert" onclick="document.getElementById('action').value='insert'">
                    <input type="submit" value="Update" onclick="document.getElementById('action').value='update'">
                    <input type="submit" value="Delete" onclick="document.getElementById('action').value='delete'"><br><br>
                    <input type="submit" id="enrollBtn" value="Enroll" style="display:none;" onclick="document.getElementById('action').value='enroll'">
                    <input type="submit" id="dropBtn" value="Drop" style="display:none;" onclick="document.getElementById('action').value='drop'">
                    <div id="conflictMsg" style="display:none; color:red; font-weight:bold; margin-top:10px;"></div>
                 </form>
            </td>
            <td width="70%" valign="top">
                <h3>Students Table</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="100%">
                    <tr>
                        <th>Student ID</th>
                        <th>Name</th>
                        <th>Address</th>
                        <th>Gender</th>
                        <th>Course</th>
                        <th>Year Level</th>
                        <th>Total Units</th>
                    </tr>
    """)
    for i in range(len(rows)):
        studentid_val = html.escape(str(rows[i][0]))
        name_val = html.escape(str(rows[i][1]))
        address_val = html.escape(str(rows[i][2])) if rows[i][2] else ""
        gender_val = html.escape(str(rows[i][3])) if rows[i][3] else ""
        course_val = html.escape(str(rows[i][4])) if rows[i][4] else ""
        yearlevel_val = html.escape(str(rows[i][5])) if rows[i][5] else ""
        total_units = str(rows[i][6])
        print("<tr onclick=\"fillForm('{}','{}','{}','{}','{}','{}')\" style=\"cursor:pointer;\">".format(studentid_val, name_val, address_val, gender_val, course_val, yearlevel_val))
        print("<td>" + studentid_val + "</td>")
        print("<td>" + name_val + "</td>")
        print("<td>" + address_val + "</td>")
        print("<td>" + gender_val + "</td>")
        print("<td>" + course_val + "</td>")
        print("<td>" + yearlevel_val + "</td>")
        print("<td>" + total_units + "</td>")
        print("</tr>")
    print("""
                </table>
                <br><br>
                <h3>Enrolled Subjects</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="100%">
                    <tr>
                        <th>Subject ID</th>
                        <th>Code</th>
                        <th>Description</th>
                        <th>Units</th>
                        <th>Schedule</th>
                    </tr>
    """)
    
    if studentid:
        cursor.execute("""
            SELECT subj.subjid, subj.subjcode, subj.subjdesc, subj.subjunits, subj.subjsched
            FROM subjects subj
            JOIN enroll e ON subj.subjid = e.subjid
            WHERE e.studid = %s
        """, (studentid,))
        enrolled = cursor.fetchall()
        for row in enrolled:
            subjid_val = html.escape(str(row[0]))
            print("<tr onclick=\"selectEnrolledSubject('{}')\" style=\"cursor:pointer;\">".format(subjid_val))
            print("<td>" + subjid_val + "</td>")
            print("<td>" + (html.escape(str(row[1])) if row[1] else "") + "</td>")
            print("<td>" + (html.escape(str(row[2])) if row[2] else "") + "</td>")
            print("<td>" + (html.escape(str(row[3])) if row[3] else "") + "</td>")
            print("<td>" + (html.escape(str(row[4])) if row[4] else "") + "</td>")
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