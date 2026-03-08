#!/usr/bin/env python3
import cgi
import mysql.connector
import html

form = cgi.FieldStorage()
action = form.getvalue("action", "")
teacherid = form.getvalue("teacherid", "")
name = form.getvalue("name", "")
department = form.getvalue("department", "")
address = form.getvalue("address", "")
contact = form.getvalue("contact", "")
status = form.getvalue("status", "")
selected_subject = form.getvalue("selected_subject", "")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sample"
    )
    cursor = conn.cursor()
    
    # Get the next teacher ID
    cursor.execute("SELECT MAX(tid) FROM teachers")
    max_id = cursor.fetchone()[0]
    next_teacher_id = max_id + 1 if max_id and max_id >= 3000 else 3000
    
    if action == "insert" and teacherid and name:
        cursor.execute("INSERT INTO teachers (tid, tname, tdept, tadd, tcontact, tstatus) VALUES (%s, %s, %s, %s, %s, %s)", (teacherid, name, department, address, contact, status))
        conn.commit()
        conn.close()
        print("Content-Type: text/html\n")
        print("<script>window.location.href='teachers.py';</script>")
        exit()
    elif action == "update" and teacherid and name:
        cursor.execute("UPDATE teachers SET tname=%s, tdept=%s, tadd=%s, tcontact=%s, tstatus=%s WHERE tid=%s",(name, department, address, contact, status, teacherid))
        conn.commit()
    elif action == "delete" and teacherid:
        # First delete all assignments for this teacher
        cursor.execute("DELETE FROM assign WHERE TID=%s",(teacherid,))
        # Then delete the teacher
        cursor.execute("DELETE FROM teachers WHERE tid=%s",(teacherid,))
        conn.commit()
#----------------------------------------------------------------------------assign & unassign----------------------------------------------------------------------------#
    
    assignment_result = None
    schedule_conflict = None
    
    # Check for schedule conflicts whenever a subject is selected
    if teacherid and selected_subject:
        try:
            # Check schedule conflict first
            cursor.execute("CALL checkteachersched(%s, %s, @sched_result)", (teacherid, selected_subject))
            cursor.execute("SELECT @sched_result")
            schedule_conflict = cursor.fetchone()[0]
        except Exception as e:
            schedule_conflict = None
        
        try:
            # Check if subject is assigned to ANY teacher
            cursor.execute("SELECT TID FROM assign WHERE SubjID = %s", (selected_subject,))
            result = cursor.fetchone()
            
            if result:
                assigned_teacher_id = result[0]
                if str(assigned_teacher_id) == str(teacherid):
                    # Same teacher - already assigned
                    assignment_result = "CONFLICT:This teacher (already assigned)"
                else:
                    # Different teacher - use stored procedure to get full info
                    cursor.execute("CALL checkassignment(%s, %s, @result)", (teacherid, selected_subject))
                    cursor.execute("SELECT @result")
                    assignment_result = cursor.fetchone()[0]
        except Exception as e:
            assignment_result = None
    
    if action == "assign" and teacherid and selected_subject:
        try:
            # Check schedule conflict first
            cursor.execute("CALL checkteachersched(%s, %s, @sched_result)", (teacherid, selected_subject))
            cursor.execute("SELECT @sched_result")
            sched_result = cursor.fetchone()[0]
            
            # Then check assignment conflict
            cursor.execute("CALL checkassignment(%s, %s, @result)", (teacherid, selected_subject))
            cursor.execute("SELECT @result")
            assignment_result = cursor.fetchone()[0]
        
            if sched_result == 'OK' and assignment_result == 'OK':
                cursor.execute("INSERT INTO assign (TID, SubjID) VALUES (%s, %s)", (teacherid, selected_subject))
                conn.commit()
                # Redirect to clear the selected_subject parameter
                print("Content-Type: text/html\n")
                print("<script>window.location.href='teachers.py?teacherid=" + teacherid + "&name=" + name + "&department=" + department + "&address=" + address + "&contact=" + contact + "&status=" + status + "';</script>")
                exit()
        except mysql.connector.IntegrityError:
            pass  # Teacher already assigned to this subject
#----------------------------------------------------------------------------assign & unassign----------------------------------------------------------------------------#
    
    # Check if teacher is already assigned to the selected subject
    is_assigned = False
    if teacherid and selected_subject:
        cursor.execute("SELECT COUNT(*) FROM assign WHERE TID = %s AND SubjID = %s", (teacherid, selected_subject))
        is_assigned = cursor.fetchone()[0] > 0
    
    print("Content-Type: text/html\n")
    
    cursor.execute("""
        SELECT t.tid, t.tname, t.tdept, t.tcontact, t.tstatus,
        COUNT(a.SubjID) as subject_count,
        COALESCE(SUM(s.subjunits), 0) as total_units
        FROM teachers t
        LEFT JOIN assign a ON t.tid = a.TID
        LEFT JOIN subjects s ON a.SubjID = s.subjid
        GROUP BY t.tid, t.tname, t.tdept, t.tcontact, t.tstatus
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
        function fillForm(teacherid, name, department, address, contact, status){
            var selectedSubject = """ + ('"' + html.escape(selected_subject) + '"' if selected_subject else '""') + """;
            var url = 'teachers.py?teacherid=' + teacherid + '&name=' + encodeURIComponent(name) + '&department=' + encodeURIComponent(department) + '&address=' + encodeURIComponent(address) + '&contact=' + encodeURIComponent(contact) + '&status=' + encodeURIComponent(status);
            if (selectedSubject) {
                url += '&selected_subject=' + selectedSubject;
            }
            window.location.href = url;
        }
        
        function updateButtons() {
            var selectedSubject = """ + ('"' + html.escape(selected_subject) + '"' if selected_subject else '""') + """;
            var teacherId = document.getElementById("teacherid").value;
            var isAssigned = """ + ("true" if is_assigned else "false") + """;
            var assignmentConflict = """ + ('"' + assignment_result.split(':', 1)[1].strip() + '"' if assignment_result and assignment_result.startswith('CONFLICT:') else '""') + """;
            var scheduleConflict = """ + ('"' + schedule_conflict.split(':', 1)[1].strip() + '"' if schedule_conflict and schedule_conflict.startswith('CONFLICT:') else '""') + """;
            var assignBtn = document.getElementById("assignBtn");
            var conflictMsg = document.getElementById("conflictMsg");
            
            // Hide button and message initially
            assignBtn.style.display = "none";
            conflictMsg.style.display = "none";
            
            // Priority 1: Show assignment conflict message if exists (subject already assigned to someone)
            if (assignmentConflict && assignmentConflict !== "") {
                conflictMsg.style.display = "block";
                conflictMsg.innerHTML = "Subject already assigned to another teacher";
                return; // Don't show assign button
            }
            
            // Priority 2: Show schedule conflict message if exists (teacher's schedule conflicts)
            if (scheduleConflict && scheduleConflict !== "") {
                conflictMsg.style.display = "block";
                conflictMsg.innerHTML = "Schedule conflict with " + scheduleConflict;
                return; // Don't show assign button
            }
            
            // Show assign button only if selected_subject is set and not already assigned
            if (selectedSubject && !isAssigned) {
                assignBtn.style.display = "inline-block";
                if (teacherId && teacherId !== """ + ('"' + str(next_teacher_id) + '"') + """) {
                    assignBtn.value = "Assign Teacher ID: " + teacherId + " to Subject ID: " + selectedSubject;
                } else {
                    assignBtn.value = "Assign Teacher ID: ? to Subject ID: " + selectedSubject;
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
                <a href="subjects.py""" + ("?selected_teacher=" + teacherid if teacherid else "") + """">Subjects</a>
                <a href="teachers.py">Teachers</a>
            </div>
            
                <h3>Teacher Form</h3>
                <form action="teachers.py" method="post">
                    <input type="hidden" name="teacherid" id="teacherid" value=\"""" + (teacherid if teacherid else str(next_teacher_id)) + """\">
                    <input type="hidden" name="selected_subject" id="selected_subject" value=\"""" + html.escape(selected_subject) + """\">
                    Teacher ID: <input type="text" value=\"""" + (teacherid if teacherid else str(next_teacher_id)) + """\" disabled><br>
                    Name: <input type="text" name="name" id="name" value=\"""" + name + """\"><br>
                    Department: <input type="text" name="department" id="department" value=\"""" + department + """\"><br>
                    Address: <input type="text" name="address" id="address" value=\"""" + address + """\"><br>
                    Contact: <input type="text" name="contact" id="contact" value=\"""" + contact + """\"><br>
                    Status: <input type="text" name="status" id="status" value=\"""" + status + """\"><br><br><br>
                    <input type="hidden" name="action" id="action">
                    <input type="submit" value="Insert" onclick="document.getElementById('action').value='insert'">
                    <input type="submit" value="Update" onclick="document.getElementById('action').value='update'">
                    <input type="submit" value="Delete" onclick="document.getElementById('action').value='delete'"><br><br>
                    <input type="submit" id="assignBtn" value="Assign" style="display:none;" onclick="document.getElementById('action').value='assign'">
                    <div id="conflictMsg" style="display:none; color:red; font-weight:bold; margin-top:10px;"></div>
                 </form>
            </td>
            <td width="70%" valign="top">
                <h3>Teachers Table</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="100%">
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Contact</th>
                        <th>Status</th>
                        <th>#Subj</th>
                        <th>TotUnits</th>
                    </tr>
    """)
    
    for row in rows:
        teacherid_val = str(row[0])
        name_val = str(row[1]) if row[1] else ""
        department_val = str(row[2]) if row[2] else ""
        contact_val = str(row[3]) if row[3] else ""
        status_val = str(row[4]) if row[4] else ""
        subject_count = str(row[5])
        total_units = str(row[6])
        
        # Get address for fillForm (need to query it separately since it's not in the main query)
        cursor.execute("SELECT tadd FROM teachers WHERE tid = %s", (teacherid_val,))
        address_result = cursor.fetchone()
        address_val = str(address_result[0]) if address_result and address_result[0] else ""
        
        print("<tr onclick=\"fillForm('{}','{}','{}','{}','{}','{}')\" style=\"cursor:pointer;\">".format(teacherid_val, name_val, department_val, address_val, contact_val, status_val))
        print("<td>" + teacherid_val + "</td>")
        print("<td>" + name_val + "</td>")
        print("<td>" + department_val + "</td>")
        print("<td>" + contact_val + "</td>")
        print("<td>" + status_val + "</td>")
        print("<td>" + subject_count + "</td>")
        print("<td>" + total_units + "</td>")
        print("</tr>")
    
    print("""
                </table>
                <br><br>
                <h3>Assigned Subjects""" + (" for Teacher ID " + teacherid if teacherid else "") + """</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="100%">
                    <tr>
                        <th>Subject ID</th>
                        <th>Code</th>
                        <th>Description</th>
                        <th>Units</th>
                        <th>Schedule</th>
                    </tr>
    """)
    
    if teacherid:
        cursor.execute("""
            SELECT s.subjid, s.subjcode, s.subjdesc, s.subjunits, s.subjsched
            FROM subjects s
            JOIN assign a ON s.subjid = a.SubjID
            WHERE a.TID = %s
        """, (teacherid,))
        assigned = cursor.fetchall()
        for row in assigned:
            subjid_val = html.escape(str(row[0]))
            print("<tr>")
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